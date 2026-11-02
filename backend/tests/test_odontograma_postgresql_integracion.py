from pathlib import Path
import os
import unittest
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import SQLAlchemyError

from odontologia.odontograma import listar_atenciones_atendidas


class OdontogramaPostgreSQLIntegracionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        host = (base_url.host or '').lower()
        if host not in ('127.0.0.1', 'localhost', '::1') or base_url.port != 55432 \
                or not (base_url.database or '').lower().endswith('_test'):
            raise unittest.SkipTest('C-16 exige localhost:55432 y base *_test.')

        cls.schema = f'c16_odontograma_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {cls.schema}'))
        cls.url = str(base_url.update_query_dict({'options': f'-csearch_path={cls.schema}'}))
        cls.engine = create_engine(cls.url, pool_pre_ping=True)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = cls.url
        cls.config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        cls.config.set_main_option('script_location', str(Path(__file__).parents[1] / 'alembic'))
        cls.config.config_file_name = None
        try:
            command.upgrade(cls.config, '20261102_0010_clinical_history')
            with cls.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO pacientes(id, nombre, activo) "
                    "VALUES ('paciente-c16', 'Paciente ficticio C16', true)"))
                connection.execute(text(
                    "INSERT INTO profesionales(id, nombre, activo) "
                    "VALUES ('profesional-c16', 'Profesional ficticio C16', true)"))
                connection.execute(text(
                    "INSERT INTO prestaciones(id, nombre, duracion_minutos, activo) "
                    "VALUES ('prestacion-c16', 'Prestación sintética', 30, true)"))
        except Exception:
            cls.engine.dispose()
            with cls.root_engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
            cls.root_engine.dispose()
            raise

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, 'root_engine'):
            return
        cls.engine.dispose()
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
        cls.root_engine.dispose()
        if cls.previous_database_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = cls.previous_database_url

    def test_upgrade_0010_a_0011_agrega_constraints_y_append_only(self):
        command.upgrade(self.config, 'head')
        with self.engine.begin() as connection:
            revision = connection.execute(text(
                'SELECT version_num FROM alembic_version')).scalar_one()
            self.assertEqual(revision, '20261102_0013_patient_self_service')

            connection.execute(text(
                "INSERT INTO versiones_odontograma"
                "(id, paciente_id, profesional_id, version, created_at) "
                "VALUES ('odonto-v1', 'paciente-c16', 'profesional-c16', 1, now())"))
            connection.execute(text(
                "INSERT INTO hallazgos_odontograma"
                "(id, version_id, pieza_fdi, superficie_fdi, observacion) "
                "VALUES ('hallazgo-v1', 'odonto-v1', '11', 'M', 'dato sintético')"))
            connection.execute(text(
                "INSERT INTO planes_tratamiento"
                "(id, paciente_id, profesional_id, estado, created_at) "
                "VALUES ('plan-v1', 'paciente-c16', 'profesional-c16', 'propuesto', now())"))
            connection.execute(text(
                "INSERT INTO etapas_plan_tratamiento"
                "(id, plan_id, prestacion_id, orden) "
                "VALUES ('etapa-v1', 'plan-v1', 'prestacion-c16', 1)"))
            connection.execute(text(
                "INSERT INTO eventos_auditoria(created_at, action, resource_type, resource_id, result) "
                "VALUES (now(), 'odontograma.version_creada', 'odontograma', 'odonto-v1', 'confirmado')"))

        with self.assertRaises(SQLAlchemyError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "UPDATE hallazgos_odontograma SET observacion='corregido' "
                    "WHERE id='hallazgo-v1'"))
        with self.assertRaises(SQLAlchemyError):
            with self.engine.begin() as connection:
                connection.execute(text("DELETE FROM etapas_plan_tratamiento WHERE id='etapa-v1'"))
        with self.assertRaises(SQLAlchemyError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO hallazgos_odontograma"
                    "(id, version_id, pieza_fdi, superficie_fdi) "
                    "VALUES ('hallazgo-invalido', 'odonto-v1', '11', 'Z')"))
        with self.assertRaises(SQLAlchemyError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO versiones_odontograma"
                    "(id, paciente_id, profesional_id, version, created_at) "
                    "VALUES ('odonto-huerfano', 'paciente-ausente', 'profesional-c16', 1, now())"))
        with self.assertRaises(SQLAlchemyError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO eventos_auditoria(created_at, action, resource_type, result) "
                    "VALUES (now(), 'plan.creado', 'odontograma', 'confirmado')"))
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text(
                "SELECT count(*) FROM hallazgos_odontograma WHERE id='hallazgo-v1'"
            )).scalar_one(), 1)
            self.assertEqual(connection.execute(text(
                "SELECT count(*) FROM eventos_auditoria "
                "WHERE action='odontograma.version_creada'"
            )).scalar_one(), 1)

    def test_lista_atenciones_postgresql_aisla_profesionales_y_audita(self):
        command.upgrade(self.config, 'head')
        with self.engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO boxes(id, nombre, activo) VALUES ('box-c16', 'Box sintético', true)"))
            connection.execute(text(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-c16-b', 'Otro profesional sintético', true)"))
            connection.execute(text(
                "INSERT INTO usuarios(id, identificador, password_hash, rol, activo, profesional_id) "
                "VALUES ('usuario-c16-a', 'prof-a', 'hash-sintetico', 'profesional', true, "
                "'profesional-c16'), ('usuario-c16-b', 'prof-b', 'hash-sintetico', "
                "'profesional', true, 'profesional-c16-b')"))
            turno_a = connection.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES ('paciente-c16', 'profesional-c16', "
                "'box-c16', 29700000, 29700030, 'atendido', 1) RETURNING id")).scalar_one()
            turno_b = connection.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES ('paciente-c16', 'profesional-c16-b', "
                "'box-c16', 29700060, 29700090, 'atendido', 1) RETURNING id")).scalar_one()

        propia_a = listar_atenciones_atendidas(self.engine, identidad={
            'usuario_id': 'usuario-c16-a', 'rol': 'profesional',
            'profesional_id': 'profesional-c16',
        })
        propia_b = listar_atenciones_atendidas(self.engine, identidad={
            'usuario_id': 'usuario-c16-b', 'rol': 'profesional',
            'profesional_id': 'profesional-c16-b',
        })
        self.assertEqual([item['turno_id'] for item in propia_a['items']], [turno_a])
        self.assertEqual([item['turno_id'] for item in propia_b['items']], [turno_b])
        with self.engine.connect() as connection:
            evento = connection.execute(text(
                "SELECT count(*) FROM eventos_auditoria "
                "WHERE action='historia.atenciones_listadas' AND resource_id IS NULL"
            )).scalar_one()
        self.assertEqual(evento, 2)
