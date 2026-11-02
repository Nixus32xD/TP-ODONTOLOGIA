from datetime import datetime, timezone
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.backup.postgresql import crear_bundle_postgresql
from odontologia.backup.restauracion_postgresql import restaurar_bundle_postgresql
from odontologia.db.models import (
    Box, EventoAuditoria, EvolucionClinica, Paciente, Profesional, Turno,
)


class HistoriaClinicaPostgreSQLIntegracionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        nombre_db = (base_url.database or '').lower()
        host = (base_url.host or '').lower()
        try:
            loopback = host in ('127.0.0.1', '::1', 'localhost')
        except ValueError:
            loopback = False
        if not loopback or base_url.port != 55432 or not nombre_db.endswith('_test'):
            raise unittest.SkipTest(
                'C-15 requiere una DB *_test en loopback y puerto 55432.')

        cls.schema = f'c15_integracion_{uuid4().hex}'
        cls.schema_c15 = f'c15_migracion_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as conexion:
            conexion.execute(text(f'CREATE SCHEMA {cls.schema}'))
            conexion.execute(text(f'CREATE SCHEMA {cls.schema_c15}'))
        cls.database_url = str(base_url.update_query_dict(
            {'options': f'-csearch_path={cls.schema}'}))
        cls.database_url_c15 = str(base_url.update_query_dict(
            {'options': f'-csearch_path={cls.schema_c15}'}))
        cls.engine = create_engine(cls.database_url, pool_pre_ping=True)
        cls.engine_c15 = create_engine(cls.database_url_c15, pool_pre_ping=True)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        cls.previous_persistence = os.environ.get('ODONTOLOGIA_PERSISTENCIA')
        os.environ['DATABASE_URL'] = cls.database_url
        os.environ['ODONTOLOGIA_PERSISTENCIA'] = 'postgresql'
        config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        config.set_main_option(
            'script_location', str(Path(__file__).parents[1] / 'alembic'))
        config.config_file_name = None
        try:
            command.upgrade(config, 'head')
            os.environ['DATABASE_URL'] = cls.database_url_c15
            command.upgrade(config, '20261102_0010_clinical_history')
            os.environ['DATABASE_URL'] = cls.database_url
        except Exception:
            cls.engine.dispose()
            with cls.root_engine.begin() as conexion:
                conexion.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
            cls.root_engine.dispose()
            if cls.previous_database_url is None:
                os.environ.pop('DATABASE_URL', None)
            else:
                os.environ['DATABASE_URL'] = cls.previous_database_url
            if cls.previous_persistence is None:
                os.environ.pop('ODONTOLOGIA_PERSISTENCIA', None)
            else:
                os.environ['ODONTOLOGIA_PERSISTENCIA'] = cls.previous_persistence
            raise
        cls.uvicorn_logger_was_enabled = not logging.getLogger('uvicorn.error').disabled
        if not cls.uvicorn_logger_was_enabled:
            raise RuntimeError('La migración alteró el estado global de logging.')

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, 'root_engine'):
            return
        cls.engine.dispose()
        cls.engine_c15.dispose()
        with cls.root_engine.begin() as conexion:
            conexion.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
            conexion.execute(text(f'DROP SCHEMA {cls.schema_c15} CASCADE'))
        cls.root_engine.dispose()
        if cls.previous_database_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = cls.previous_database_url
        if cls.previous_persistence is None:
            os.environ.pop('ODONTOLOGIA_PERSISTENCIA', None)
        else:
            os.environ['ODONTOLOGIA_PERSISTENCIA'] = cls.previous_persistence

    def _crear_evolucion_ficticia(self, sufijo):
        paciente_id = f'paciente-c15-{sufijo}'
        profesional_id = f'profesional-c15-{sufijo}'
        box_id = f'box-c15-{sufijo}'
        evolucion_id = str(uuid4())
        if self.engine is self.engine_c15:
            with self.engine.begin() as conexion:
                conexion.execute(text(
                    'INSERT INTO pacientes(id, nombre, telefono, activo) '
                    'VALUES (:id, :nombre, NULL, true)'), {
                        'id': paciente_id, 'nombre': 'Paciente sintético C-15'})
                conexion.execute(text(
                    'INSERT INTO profesionales(id, nombre, activo) '
                    'VALUES (:id, :nombre, true)'), {
                        'id': profesional_id, 'nombre': 'Profesional sintético C-15'})
                conexion.execute(text(
                    'INSERT INTO boxes(id, nombre, activo) VALUES (:id, :nombre, true)'), {
                        'id': box_id, 'nombre': 'Box sintético C-15'})
                turno_id = conexion.execute(text(
                    "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                    "fin_minuto, estado, version) VALUES (:paciente, :profesional, :box, "
                    "29700000, 29700030, 'atendido', 1) RETURNING id"), {
                        'paciente': paciente_id, 'profesional': profesional_id, 'box': box_id,
                    }).scalar_one()
                conexion.execute(text(
                    'INSERT INTO evoluciones_clinicas '
                    '(id, paciente_id, profesional_id, turno_id, nota, created_at, corrige_a_id) '
                    'VALUES (:id, :paciente, :profesional, :turno, :nota, :fecha, NULL)'), {
                        'id': evolucion_id, 'paciente': paciente_id,
                        'profesional': profesional_id, 'turno': turno_id,
                        'nota': 'Nota clínica sintética de integración C-15.',
                        'fecha': datetime.now(timezone.utc),
                    })
                conexion.execute(text(
                    "INSERT INTO eventos_auditoria(created_at, actor_id, action, "
                    "resource_type, resource_id, result) VALUES (:fecha, NULL, "
                    "'evolucion.creada', 'evolucion', :id, 'confirmado')"), {
                        'fecha': datetime.now(timezone.utc), 'id': evolucion_id,
                    })
            return paciente_id, profesional_id, box_id, turno_id, evolucion_id
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id=paciente_id, nombre='Paciente sintético C-15', telefono=None,
                         activo=True),
                Profesional(id=profesional_id, nombre='Profesional sintético C-15', activo=True),
                Box(id=box_id, nombre='Box sintético C-15', activo=True),
            ])
            session.flush()
            turno = Turno(
                paciente_id=paciente_id, profesional_id=profesional_id, box_id=box_id,
                inicio_minuto=29_700_000, fin_minuto=29_700_030,
                estado='atendido', version=1)
            session.add(turno)
            session.flush()
            evolucion = EvolucionClinica(
                id=evolucion_id, paciente_id=paciente_id, profesional_id=profesional_id,
                turno_id=turno.id, nota='Nota clínica sintética de integración C-15.',
                created_at=datetime.now(timezone.utc), corrige_a_id=None)
            session.add(evolucion)
            session.flush()
            session.add(EventoAuditoria(
                created_at=datetime.now(timezone.utc), actor_id=None,
                action='evolucion.creada', resource_type='evolucion',
                resource_id=evolucion_id, result='confirmado'))
            return paciente_id, profesional_id, box_id, turno.id, evolucion_id

    def test_migracion_0010_y_restricciones_fk_append_only_en_postgresql(self):
        engine_actual = self.engine
        self.engine = self.engine_c15
        referencias = self._crear_evolucion_ficticia('constraints')
        paciente_id, profesional_id, _box_id, turno_id, evolucion_id = referencias

        with self.engine.connect() as conexion:
            revision = conexion.execute(text(
                'SELECT version_num FROM alembic_version')).scalar_one()
            constraints = set(conexion.execute(text(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid='evoluciones_clinicas'::regclass")).scalars())
            trigger = conexion.execute(text(
                "SELECT count(*) FROM pg_trigger "
                "WHERE tgrelid='evoluciones_clinicas'::regclass "
                "AND tgname='evoluciones_clinicas_append_only' AND NOT tgisinternal"
            )).scalar_one()
            foreign_keys_no_validadas = conexion.execute(text(
                "SELECT count(*) FROM pg_constraint "
                "WHERE conrelid='evoluciones_clinicas'::regclass "
                "AND contype='f' AND NOT convalidated"
            )).scalar_one()
        self.assertEqual(revision, '20261102_0010_clinical_history')
        self.assertIn('ck_evoluciones_clinicas_nota', constraints)
        self.assertEqual(trigger, 1)
        self.assertEqual(foreign_keys_no_validadas, 0)

        for nota in ('   ', 'x' * 5001):
            with self.subTest(nota_length=len(nota)), self.assertRaises(IntegrityError):
                with self.engine.begin() as conexion:
                    conexion.execute(text(
                        'INSERT INTO evoluciones_clinicas '
                        '(id, paciente_id, profesional_id, turno_id, nota, created_at) '
                        'VALUES (:id, :paciente_id, :profesional_id, :turno_id, :nota, :created_at)'), {
                            'id': str(uuid4()), 'paciente_id': paciente_id,
                            'profesional_id': profesional_id, 'turno_id': turno_id,
                            'nota': nota, 'created_at': datetime.now(timezone.utc),
                        })

        append_only = (
            ('UPDATE evoluciones_clinicas SET nota=:nota WHERE id=:id',
             {'nota': 'No debe editarse.', 'id': evolucion_id}),
            ('DELETE FROM evoluciones_clinicas WHERE id=:id', {'id': evolucion_id}),
        )
        for statement, parametros in append_only:
            with self.subTest(statement=statement), self.assertRaises(SQLAlchemyError):
                with self.engine.begin() as conexion:
                    conexion.execute(text(statement), parametros)
        for statement, parametros in (
                ('DELETE FROM pacientes WHERE id=:id', {'id': paciente_id}),
                ('DELETE FROM profesionales WHERE id=:id', {'id': profesional_id}),
                ('DELETE FROM turnos WHERE id=:id', {'id': turno_id})):
            with self.subTest(statement=statement), self.assertRaises(IntegrityError):
                with self.engine.begin() as conexion:
                    conexion.execute(text(statement), parametros)
        self.engine = engine_actual

    def test_bundle_y_restore_postgresql_conservan_evolucion_y_recuentos(self):
        paciente_id, profesional_id, _box_id, turno_id, evolucion_id = (
            self._crear_evolucion_ficticia('backup'))
        config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        config.set_main_option(
            'script_location', str(Path(__file__).parents[1] / 'alembic'))
        config.config_file_name = None
        command.upgrade(config, 'head')
        destino = f'c15_restore_{uuid4().hex}'
        with TemporaryDirectory() as temporal:
            bundle = Path(temporal) / 'bundle-c15'
            manifiesto = crear_bundle_postgresql(self.engine, bundle)
            self.assertEqual(
                manifiesto['schema_version'], '20261102_0013_patient_self_service')
            self.assertEqual(manifiesto['table_counts']['evoluciones_clinicas'], 1)
            self.assertNotIn('Nota clínica sintética de integración C-15.',
                             (bundle / 'manifest.json').read_text(encoding='utf-8'))

            resultado = restaurar_bundle_postgresql(self.engine, bundle, destino)
            self.assertTrue(resultado['restored'])
            self.assertEqual(resultado['table_counts'], manifiesto['table_counts'])
            restored = create_engine(self.engine.url.set(database=destino), pool_pre_ping=True)
            try:
                with restored.connect() as conexion:
                    evolucion = conexion.execute(text(
                        'SELECT paciente_id, profesional_id, turno_id, nota, corrige_a_id '
                        'FROM evoluciones_clinicas WHERE id=:id'),
                        {'id': evolucion_id}).one()
                    self.assertEqual(tuple(evolucion), (
                        paciente_id, profesional_id, turno_id,
                        'Nota clínica sintética de integración C-15.', None))
                    self.assertEqual(conexion.execute(text(
                        "SELECT count(*) FROM eventos_auditoria "
                        "WHERE action='evolucion.creada' AND resource_id=:id"),
                        {'id': evolucion_id}).scalar_one(), 1)
                    self.assertEqual(conexion.execute(text(
                        "SELECT count(*) FROM pg_trigger "
                        "WHERE tgrelid='evoluciones_clinicas'::regclass "
                        "AND tgname='evoluciones_clinicas_append_only' AND NOT tgisinternal"
                    )).scalar_one(), 1)
                    with self.assertRaises(SQLAlchemyError):
                        with restored.begin() as escritura:
                            escritura.execute(text(
                                'DELETE FROM evoluciones_clinicas WHERE id=:id'),
                                {'id': evolucion_id})
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
