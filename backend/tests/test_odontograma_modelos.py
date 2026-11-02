from datetime import datetime, timezone
import unittest

from sqlalchemy import CheckConstraint, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from odontologia.db.models import (
    Base,
    Box,
    EtapaPlanTratamiento,
    EventoAuditoria,
    HallazgoOdontograma,
    OdontogramaVersion,
    Paciente,
    PlanTratamiento,
    Prestacion,
    Profesional,
)


class ModelosOdontogramaTests(unittest.TestCase):
    def test_metadatos_postgresql_admiten_auditoria_clinica_c16(self):
        checks = [str(constraint.sqltext) for constraint in EventoAuditoria.__table__.constraints
                  if isinstance(constraint, CheckConstraint)]
        self.assertTrue(any('odontograma.version_creada' in check for check in checks))
        self.assertTrue(any("'plan'" in check for check in checks))
        self.assertTrue(any(
            "action = 'plan.estado_actualizado' AND resource_type = 'plan'" in check
            for check in checks))

    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')

        @event.listens_for(self.engine, 'connect')
        def habilitar_claves_foraneas(conexion, _registro):
            conexion.execute('PRAGMA foreign_keys=ON')

        Base.metadata.create_all(self.engine)
        self.addCleanup(self.engine.dispose)
        with Session(self.engine) as session:
            session.add_all([
                Paciente(id='paciente-A', nombre='Paciente sintético A', activo=True),
                Profesional(id='profesional-A', nombre='Profesional sintético A', activo=True),
                Profesional(id='profesional-B', nombre='Profesional sintético B', activo=True),
                Box(id='box-A', nombre='Box sintético A', activo=True),
                Prestacion(id='prestacion-A', nombre='Prestación sintética A',
                           duracion_minutos=30, activo=True),
            ])
            session.commit()

    def test_entidades_clinicas_son_separadas_y_restringen_referencias(self):
        self.assertEqual(OdontogramaVersion.__tablename__, 'versiones_odontograma')
        self.assertEqual(HallazgoOdontograma.__tablename__, 'hallazgos_odontograma')
        self.assertEqual(PlanTratamiento.__tablename__, 'planes_tratamiento')
        self.assertEqual(EtapaPlanTratamiento.__tablename__, 'etapas_plan_tratamiento')

        version_fks = {str(fk.column) for fk in OdontogramaVersion.__table__.foreign_keys}
        hallazgo_fks = {str(fk.column) for fk in HallazgoOdontograma.__table__.foreign_keys}
        plan_fks = {str(fk.column) for fk in PlanTratamiento.__table__.foreign_keys}
        etapa_fks = {str(fk.column) for fk in EtapaPlanTratamiento.__table__.foreign_keys}
        self.assertEqual(version_fks, {'pacientes.id', 'profesionales.id'})
        self.assertEqual(hallazgo_fks, {'versiones_odontograma.id'})
        self.assertEqual(plan_fks, {'pacientes.id', 'profesionales.id'})
        self.assertEqual(etapa_fks, {'planes_tratamiento.id', 'prestaciones.id'})
        self.assertTrue(all(fk.ondelete == 'RESTRICT' for tabla in (
            OdontogramaVersion.__table__, HallazgoOdontograma.__table__,
            PlanTratamiento.__table__, EtapaPlanTratamiento.__table__)
            for fk in tabla.foreign_keys))

    def test_versiones_y_etapas_conservan_historial_y_orden_unico(self):
        ahora = datetime.now(timezone.utc)
        with Session(self.engine) as session:
            primera = OdontogramaVersion(
                id='odonto-v1', paciente_id='paciente-A', profesional_id='profesional-A',
                version=1, created_at=ahora)
            plan = PlanTratamiento(
                id='plan-A', paciente_id='paciente-A', profesional_id='profesional-A',
                estado='propuesto', created_at=ahora)
            session.add_all([primera, plan])
            session.flush()
            session.add_all([
                HallazgoOdontograma(
                    id='hallazgo-v1', version_id=primera.id, pieza_fdi='11',
                    superficie_fdi='I', observacion='Observación sintética'),
                EtapaPlanTratamiento(
                    id='etapa-A', plan_id=plan.id, prestacion_id='prestacion-A', orden=1),
            ])
            session.commit()

        with Session(self.engine) as session:
            segunda = OdontogramaVersion(
                id='odonto-v2', paciente_id='paciente-A', profesional_id='profesional-A',
                version=2, created_at=ahora)
            session.add(segunda)
            session.commit()

        with Session(self.engine) as session:
            versiones = session.query(OdontogramaVersion).order_by(
                OdontogramaVersion.version).all()
            etapas = session.query(EtapaPlanTratamiento).order_by(
                EtapaPlanTratamiento.orden).all()
            self.assertEqual([row.version for row in versiones], [1, 2])
            self.assertEqual([row.orden for row in etapas], [1])

            session.add(OdontogramaVersion(
                id='odonto-duplicada', paciente_id='paciente-A',
                profesional_id='profesional-A', version=2, created_at=ahora))
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_planes_no_agregan_precio_ni_turno_y_restringen_etapas(self):
        self.assertNotIn('turno_id', PlanTratamiento.__table__.columns)
        self.assertNotIn('precio', EtapaPlanTratamiento.__table__.columns)
        with Session(self.engine) as session:
            plan = PlanTratamiento(
                id='plan-B', paciente_id='paciente-A', profesional_id='profesional-A',
                estado='propuesto', created_at=datetime.now(timezone.utc))
            session.add(plan)
            session.flush()
            session.add(EtapaPlanTratamiento(
                id='etapa-invalida', plan_id=plan.id, prestacion_id='inexistente', orden=1))
            with self.assertRaises(IntegrityError):
                session.commit()

        with Session(self.engine) as session:
            self.assertEqual(session.query(EtapaPlanTratamiento).count(), 0)

    def test_restricciones_ddl_rechazan_codigos_y_estados_invalidos(self):
        ahora = datetime.now(timezone.utc)
        with Session(self.engine) as session:
            for version in (0, -1):
                session.add(OdontogramaVersion(
                    id=f'v-invalida-{version}', paciente_id='paciente-A',
                    profesional_id='profesional-A', version=version, created_at=ahora))
                with self.subTest(version=version), self.assertRaises(IntegrityError):
                    session.flush()
                session.rollback()

            version_valida = OdontogramaVersion(
                id='v-valida', paciente_id='paciente-A', profesional_id='profesional-A',
                version=1, created_at=ahora)
            session.add(version_valida)
            session.flush()
            hallazgos_invalidos = (
                ('pieza-larga', '111', 'I', None),
                ('superficie-compuesta', '11', 'MO', None),
                ('observacion-larga', '11', 'I', 'x' * 501),
            )
            for id_, pieza, superficie, observacion in hallazgos_invalidos:
                session.add(HallazgoOdontograma(
                    id=id_, version_id=version_valida.id, pieza_fdi=pieza,
                    superficie_fdi=superficie, observacion=observacion))
                with self.subTest(hallazgo=id_), self.assertRaises(IntegrityError):
                    session.flush()
                session.rollback()
                session.add(version_valida)
                session.flush()

    def test_fk_restrict_y_orden_unico_conservan_referencias_historicas(self):
        ahora = datetime.now(timezone.utc)
        with Session(self.engine) as session:
            plan = PlanTratamiento(
                id='plan-C', paciente_id='paciente-A', profesional_id='profesional-A',
                estado='propuesto', created_at=ahora)
            version = OdontogramaVersion(
                id='odonto-C', paciente_id='paciente-A', profesional_id='profesional-A',
                version=1, created_at=ahora)
            session.add_all([plan, version])
            session.flush()
            session.add_all([
                EtapaPlanTratamiento(
                    id='etapa-C1', plan_id=plan.id, prestacion_id='prestacion-A', orden=1),
                HallazgoOdontograma(
                    id='hallazgo-C1', version_id=version.id, pieza_fdi='11',
                    superficie_fdi='I', observacion=None),
            ])
            session.commit()

        with Session(self.engine) as session:
            session.add(EtapaPlanTratamiento(
                id='etapa-C2', plan_id='plan-C', prestacion_id='prestacion-A', orden=1))
            with self.assertRaises(IntegrityError):
                session.commit()
            session.rollback()
            session.delete(session.get(Prestacion, 'prestacion-A'))
            with self.assertRaises(IntegrityError):
                session.commit()

        with Session(self.engine) as session:
            self.assertEqual(session.query(EtapaPlanTratamiento).count(), 1)
            self.assertEqual(session.query(HallazgoOdontograma).count(), 1)


if __name__ == '__main__':
    unittest.main()
