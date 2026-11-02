"""Integración C-16 de backup/restore PostgreSQL con datos sólo sintéticos."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from odontologia.backup.postgresql import crear_bundle_postgresql
from odontologia.backup.restauracion_postgresql import restaurar_bundle_postgresql
from odontologia.db.models import (
    EtapaPlanTratamiento, HallazgoOdontograma, OdontogramaVersion, Paciente,
    PlanTratamiento, Prestacion, Profesional,
)


class BackupOdontogramaPostgreSQLIntegracionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        if (base_url.host not in ('127.0.0.1', '::1', 'localhost')
                or base_url.port != 55432
                or not (base_url.database or '').lower().endswith('_test')):
            raise unittest.SkipTest(
                'C-16 requiere una DB *_test en loopback y puerto 55432.')

        cls.schema = f'c16_backup_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as conexion:
            conexion.execute(text(f'CREATE SCHEMA {cls.schema}'))
        cls.database_url = str(base_url.update_query_dict(
            {'options': f'-csearch_path={cls.schema}'}))
        cls.engine = create_engine(cls.database_url, pool_pre_ping=True)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        cls.previous_persistence = os.environ.get('ODONTOLOGIA_PERSISTENCIA')
        os.environ['DATABASE_URL'] = cls.database_url
        os.environ['ODONTOLOGIA_PERSISTENCIA'] = 'postgresql'
        config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        config.set_main_option('script_location', str(Path(__file__).parents[1] / 'alembic'))
        config.config_file_name = None
        try:
            command.upgrade(config, 'head')
        except Exception:
            cls.engine.dispose()
            with cls.root_engine.begin() as conexion:
                conexion.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
            cls.root_engine.dispose()
            cls._restore_environment()
            raise

    @classmethod
    def _restore_environment(cls):
        if cls.previous_database_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = cls.previous_database_url
        if cls.previous_persistence is None:
            os.environ.pop('ODONTOLOGIA_PERSISTENCIA', None)
        else:
            os.environ['ODONTOLOGIA_PERSISTENCIA'] = cls.previous_persistence

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, 'root_engine'):
            return
        cls.engine.dispose()
        with cls.root_engine.begin() as conexion:
            conexion.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
        cls.root_engine.dispose()
        cls._restore_environment()

    def test_bundle_y_restore_preservan_odontograma_planes_y_recuentos(self):
        paciente_id = f'paciente-c16-{uuid4().hex}'
        profesional_id = f'profesional-c16-{uuid4().hex}'
        version_id = str(uuid4())
        hallazgo_id = str(uuid4())
        plan_id = str(uuid4())
        etapa_id = str(uuid4())
        prestacion_id = f'prestacion-c16-{uuid4().hex}'
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id=paciente_id, nombre='Paciente sintético C-16', telefono=None,
                         activo=True),
                Profesional(id=profesional_id, nombre='Profesional sintético C-16', activo=True),
                Prestacion(id=prestacion_id, nombre='Prestación sintética C-16',
                           duracion_minutos=30, activo=True),
            ])
            session.flush()
            session.add_all([
                OdontogramaVersion(
                    id=version_id, paciente_id=paciente_id, profesional_id=profesional_id,
                    version=1, created_at=datetime.now(timezone.utc)),
                PlanTratamiento(
                    id=plan_id, paciente_id=paciente_id, profesional_id=profesional_id,
                    estado='propuesto', created_at=datetime.now(timezone.utc)),
            ])
            session.flush()
            session.add_all([
                HallazgoOdontograma(
                    id=hallazgo_id, version_id=version_id, pieza_fdi='16',
                    superficie_fdi='O', observacion='Dato clínico sintético C-16.'),
                EtapaPlanTratamiento(
                    id=etapa_id, plan_id=plan_id, prestacion_id=prestacion_id, orden=1),
            ])

        destino = f'c16_restore_{uuid4().hex[:12]}_test'
        with TemporaryDirectory() as temporal:
            bundle = Path(temporal) / 'bundle-c16'
            manifiesto = crear_bundle_postgresql(self.engine, bundle)
            tablas = (
                'versiones_odontograma', 'hallazgos_odontograma',
                'planes_tratamiento', 'etapas_plan_tratamiento',
            )
            for tabla in tablas:
                self.assertEqual(manifiesto['table_counts'][tabla], 1)
            contenido_manifiesto = (bundle / 'manifest.json').read_text(encoding='utf-8')
            self.assertNotIn('Dato clínico sintético C-16.', contenido_manifiesto)
            self.assertNotIn('Prestación sintética C-16', contenido_manifiesto)

            resultado = restaurar_bundle_postgresql(self.engine, bundle, destino)
            self.assertTrue(resultado['restored'])
            self.assertEqual(resultado['table_counts'], manifiesto['table_counts'])
            restored = create_engine(self.engine.url.set(database=destino), pool_pre_ping=True)
            try:
                with restored.connect() as conexion:
                    self.assertEqual(conexion.execute(text(
                        'SELECT paciente_id, profesional_id, version FROM versiones_odontograma '
                        'WHERE id=:id'), {'id': version_id}).one(),
                        (paciente_id, profesional_id, 1))
                    self.assertEqual(conexion.execute(text(
                        'SELECT pieza_fdi, superficie_fdi, observacion '
                        'FROM hallazgos_odontograma WHERE id=:id'),
                        {'id': hallazgo_id}).one(),
                        ('16', 'O', 'Dato clínico sintético C-16.'))
                    self.assertEqual(conexion.execute(text(
                        'SELECT estado FROM planes_tratamiento WHERE id=:id'),
                        {'id': plan_id}).scalar_one(), 'propuesto')
                    self.assertEqual(conexion.execute(text(
                        'SELECT prestacion_id, orden FROM etapas_plan_tratamiento WHERE id=:id'),
                        {'id': etapa_id}).one(), (prestacion_id, 1))
            finally:
                restored.dispose()
                admin = create_engine(
                    self.engine.url.set(database='postgres'), isolation_level='AUTOCOMMIT')
                try:
                    with admin.connect() as conexion:
                        conexion.exec_driver_sql(f'DROP DATABASE IF EXISTS "{destino}"')
                finally:
                    admin.dispose()


if __name__ == '__main__':
    unittest.main()
