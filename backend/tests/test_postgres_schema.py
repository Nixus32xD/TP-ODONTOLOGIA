import importlib.util
from pathlib import Path
import unittest

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from odontologia.db.models import (
    AgendaMutex, Base, BloqueoAgenda, EventoAuditoria, EvolucionClinica, ExcepcionHorario,
    HorarioSemanal, Paciente, Turno, TramoExcepcion,
    RecordatorioOutbox, IdempotenciaPortalPaciente, Usuario,
)
from odontologia.db.postgresql import REVISION_ESQUEMA_ACTUAL


class EsquemaPostgreSQLTests(unittest.TestCase):
    def test_esquema_representa_catalogos_turnos_y_mutex(self):
        self.assertEqual(
            set(Base.metadata.tables),
            {'pacientes', 'profesionales', 'boxes', 'prestaciones', 'turnos', 'agenda_mutex',
             'usuarios', 'sesiones', 'eventos_auditoria', 'horarios_semanales',
             'excepciones_horario', 'tramos_excepcion', 'bloqueos_agenda',
             'evoluciones_clinicas', 'versiones_odontograma', 'hallazgos_odontograma',
             'planes_tratamiento', 'etapas_plan_tratamiento', 'recordatorios_outbox',
             'idempotencia_portal_paciente', 'cargos_financieros', 'cobros_financieros',
             'reversiones_cobros', 'idempotencia_financiera'},
        )
        self.assertEqual(
            set(Turno.__table__.columns.keys()),
            {'id', 'paciente_id', 'profesional_id', 'box_id', 'inicio_minuto', 'fin_minuto', 'estado', 'version'},
        )
        self.assertIn('inicio_minuto < fin_minuto', {
            str(constraint.sqltext) for constraint in Turno.__table__.constraints
            if getattr(constraint, 'sqltext', None) is not None
        })
        self.assertIsNotNone(Turno.__table__.c.id.identity)
        self.assertEqual(AgendaMutex.__table__.primary_key.columns.keys(), ['id'])
        self.assertIn('nota', EvolucionClinica.__table__.columns)
        self.assertIn('turno_id', EvolucionClinica.__table__.columns)
        self.assertIn('profesional_id', HorarioSemanal.__table__.columns)
        self.assertIn('fecha_local', ExcepcionHorario.__table__.columns)
        self.assertIn('excepcion_id', TramoExcepcion.__table__.columns)
        self.assertIn('box_id', BloqueoAgenda.__table__.columns)
        self.assertIn('generation', RecordatorioOutbox.__table__.columns)
        self.assertIn('ck_recordatorios_generation', {
            constraint.name for constraint in RecordatorioOutbox.__table__.constraints
        })
        self.assertIn('uq_recordatorios_turno_version_tipo_generation', {
            constraint.name for constraint in RecordatorioOutbox.__table__.constraints
        })
        self.assertIn('paciente_id', Usuario.__table__.columns)
        self.assertIn('paciente_id', IdempotenciaPortalPaciente.__table__.columns)
        self.assertIn('uq_idempotencia_portal_paciente_operacion_clave', {
            constraint.name for constraint in IdempotenciaPortalPaciente.__table__.constraints
        })
        self.assertEqual(
            set(EventoAuditoria.__table__.columns.keys()),
            {'id', 'created_at', 'actor_id', 'action', 'resource_type', 'resource_id', 'result'},
        )
        self.assertTrue({
            'ck_eventos_auditoria_rechazo_generico',
            'ck_eventos_auditoria_combinacion',
        } <= {
            constraint.name for constraint in EventoAuditoria.__table__.constraints
        })

    def test_lock_de_agenda_se_compila_como_bloqueo_de_fila_postgres(self):
        statement = select(AgendaMutex.id).with_for_update()

        sql = str(statement.compile(dialect=postgresql.dialect()))

        self.assertIn('FOR UPDATE', sql)
        self.assertIn('agenda_mutex', sql)

    def test_paciente_tiene_campos_minimos_y_migracion_postgres_encadenada(self):
        self.assertTrue({'id', 'nombre', 'telefono', 'activo'} <= set(Paciente.__table__.columns.keys()))
        self.assertFalse(Paciente.__table__.c.nombre.nullable)
        self.assertFalse(Paciente.__table__.c.activo.nullable)

        ruta = Path(__file__).parents[1] / 'alembic' / 'versions' / '20261102_0004_patient_management.py'
        spec = importlib.util.spec_from_file_location('revision_patients', ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        self.assertEqual(modulo.revision, '20261102_0004_patient_management')
        self.assertEqual(modulo.down_revision, '20261101_0003_audit')

    def test_migracion_c15_encadena_sobre_c10(self):
        ruta = Path(__file__).parents[1] / 'alembic' / 'versions' / '20261102_0010_clinical_history.py'
        spec = importlib.util.spec_from_file_location('revision_clinical_history', ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        self.assertEqual(modulo.revision, '20261102_0010_clinical_history')
        self.assertEqual(modulo.down_revision, '20261102_0009_turn_rescheduling')
        self.assertTrue(callable(modulo.upgrade))
        self.assertTrue(callable(modulo.downgrade))
        self.assertEqual(REVISION_ESQUEMA_ACTUAL, '20261102_0014_financial_ledger')

    def test_migracion_c18_agrega_vinculo_paciente_y_tabla_idempotencia(self):
        ruta = Path(__file__).parents[1] / 'alembic' / 'versions' / '20261102_0013_patient_self_service.py'
        spec = importlib.util.spec_from_file_location('revision_patient_self_service', ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        self.assertEqual(modulo.revision, '20261102_0013_patient_self_service')
        self.assertEqual(modulo.down_revision, '20261102_0012_appointment_reminders')
        self.assertTrue(callable(modulo.upgrade))
        self.assertTrue(callable(modulo.downgrade))
        self.assertEqual(REVISION_ESQUEMA_ACTUAL, '20261102_0014_financial_ledger')

    def test_migracion_c19_encadena_el_ledger_despues_de_c18(self):
        ruta = Path(__file__).parents[1] / 'alembic' / 'versions' / '20261102_0014_financial_ledger.py'
        spec = importlib.util.spec_from_file_location('revision_financial_ledger', ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        self.assertEqual(modulo.revision, '20261102_0014_financial_ledger')
        self.assertEqual(modulo.down_revision, '20261102_0013_patient_self_service')


if __name__ == '__main__':
    unittest.main()
