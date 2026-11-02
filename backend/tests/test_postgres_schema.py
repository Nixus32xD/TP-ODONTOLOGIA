import importlib.util
from pathlib import Path
import unittest

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from odontologia.db.models import (
    AgendaMutex, Base, BloqueoAgenda, EventoAuditoria, ExcepcionHorario,
    HorarioSemanal, Paciente, Turno, TramoExcepcion,
)


class EsquemaPostgreSQLTests(unittest.TestCase):
    def test_esquema_representa_catalogos_turnos_y_mutex(self):
        self.assertEqual(
            set(Base.metadata.tables),
            {'pacientes', 'profesionales', 'boxes', 'prestaciones', 'turnos', 'agenda_mutex',
             'usuarios', 'sesiones', 'eventos_auditoria', 'horarios_semanales',
             'excepciones_horario', 'tramos_excepcion', 'bloqueos_agenda'},
        )
        self.assertEqual(
            set(Turno.__table__.columns.keys()),
            {'id', 'paciente_id', 'profesional_id', 'box_id', 'inicio_minuto', 'fin_minuto'},
        )
        self.assertIn('inicio_minuto < fin_minuto', {
            str(constraint.sqltext) for constraint in Turno.__table__.constraints
            if getattr(constraint, 'sqltext', None) is not None
        })
        self.assertIsNotNone(Turno.__table__.c.id.identity)
        self.assertEqual(AgendaMutex.__table__.primary_key.columns.keys(), ['id'])
        self.assertIn('profesional_id', HorarioSemanal.__table__.columns)
        self.assertIn('fecha_local', ExcepcionHorario.__table__.columns)
        self.assertIn('excepcion_id', TramoExcepcion.__table__.columns)
        self.assertIn('box_id', BloqueoAgenda.__table__.columns)
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


if __name__ == '__main__':
    unittest.main()
