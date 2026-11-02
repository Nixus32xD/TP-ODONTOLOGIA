"""Prueba de migración C-18 real sobre un schema PostgreSQL efímero."""
from pathlib import Path
import os
import unittest
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


class PatientSelfServiceMigrationPostgreSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        if (base_url.host not in ('127.0.0.1', 'localhost', '::1')
                or base_url.port != 55432
                or not (base_url.database or '').lower().endswith('_test')):
            raise unittest.SkipTest('C-18 exige localhost:55432 y una base *_test.')

        cls.schema = f'c18_migracion_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {cls.schema}'))
        cls.url = str(base_url.update_query_dict({'options': f'-csearch_path={cls.schema}'}))
        cls.engine = create_engine(cls.url)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = cls.url
        cls.config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        cls.config.set_main_option('script_location', str(Path(__file__).parents[1] / 'alembic'))
        cls.config.config_file_name = None
        try:
            command.upgrade(cls.config, '20261102_0012_appointment_reminders')
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

    def test_upgrade_0012_a_0013_preserva_datos_y_aplica_vinculos_e_idempotencia(self):
        with self.engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO pacientes(id,nombre,activo) "
                "VALUES ('paciente-c18-a','Paciente ficticio A',true), "
                "('paciente-c18-b','Paciente ficticio B',true)"))
            connection.execute(text(
                "INSERT INTO profesionales(id,nombre,activo) "
                "VALUES ('profesional-c18','Profesional ficticio',true)"))
            connection.execute(text(
                "INSERT INTO boxes(id,nombre,activo) VALUES ('box-c18','Box ficticio',true)"))
            connection.execute(text(
                "INSERT INTO usuarios(id,identificador,password_hash,rol,activo) "
                "VALUES ('admin-c18','admin.c18','hash-sintetico','administrador',true)"))
            connection.execute(text(
                "INSERT INTO usuarios(id,identificador,password_hash,rol,activo,profesional_id) "
                "VALUES ('prof-c18','prof.c18','hash-sintetico','profesional',true,'profesional-c18')"))
            connection.execute(text(
                "INSERT INTO sesiones(id,usuario_id,jti,expira_en,creado_en) "
                "VALUES ('sesion-c18','prof-c18','jti-c18',5000,1000)"))
            connection.execute(text(
                "INSERT INTO eventos_auditoria(created_at,actor_id,action,resource_type,resource_id,result) "
                "VALUES (now(),'prof-c18','cuenta.creada','cuenta','prof-c18','confirmado')"))
            turno_id = connection.execute(text(
                "INSERT INTO turnos(paciente_id,profesional_id,box_id,inicio_minuto,fin_minuto) "
                "VALUES ('paciente-c18-a','profesional-c18','box-c18',100,130) RETURNING id"
            )).scalar_one()

        command.upgrade(self.config, 'head')

        with self.engine.begin() as connection:
            revision = connection.execute(text(
                'SELECT version_num FROM alembic_version')).scalar_one()
            self.assertEqual(revision, '20261102_0013_patient_self_service')
            self.assertEqual(connection.execute(text(
                "SELECT rol, profesional_id, paciente_id FROM usuarios WHERE id='prof-c18'"
            )).one(), ('profesional', 'profesional-c18', None))
            self.assertEqual(connection.execute(text(
                "SELECT usuario_id FROM sesiones WHERE id='sesion-c18'"
            )).scalar_one(), 'prof-c18')
            self.assertEqual(connection.execute(text(
                "SELECT actor_id FROM eventos_auditoria WHERE resource_id='prof-c18'"
            )).scalar_one(), 'prof-c18')
            self.assertIn('idempotencia_portal_paciente', {
                row[0] for row in connection.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema=current_schema()"))})
            connection.execute(text(
                "INSERT INTO usuarios(id,identificador,password_hash,rol,activo,paciente_id) "
                "VALUES ('pac-c18','pac.c18','hash-sintetico','paciente',true,'paciente-c18-a')"))
            connection.execute(text(
                "INSERT INTO idempotencia_portal_paciente(id,paciente_id,operacion,clave,"
                "fingerprint,turno_id,respuesta_json,created_at) VALUES "
                "('idem-c18','paciente-c18-a','reserva','clave-c18',repeat('a',64),:turno_id,"
                ":respuesta_json,now())"), {
                    'turno_id': turno_id, 'respuesta_json': '{"turno_id":1}'})
            self.assertEqual(connection.execute(text(
                "SELECT count(*) FROM idempotencia_portal_paciente WHERE paciente_id='paciente-c18-a'"
            )).scalar_one(), 1)
            for action, resource in (
                    ('horario.actualizado', 'horario'),
                    ('excepcion.creada', 'excepcion'),
                    ('bloqueo.creado', 'bloqueo')):
                connection.execute(text(
                    "INSERT INTO eventos_auditoria(created_at,action,resource_type,result) "
                    "VALUES (now(),:action,:resource,'confirmado')"), {
                        'action': action, 'resource': resource})

        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO usuarios(id,identificador,password_hash,rol,activo,paciente_id) "
                    "VALUES ('pac-c18-2','pac.c18.2','hash-sintetico','paciente',true,'paciente-c18-a')"))
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO usuarios(id,identificador,password_hash,rol,activo,paciente_id) "
                    "VALUES ('admin-c18-2','admin.c18.2','hash-sintetico','administrador',true,'paciente-c18-b')"))


if __name__ == '__main__':
    unittest.main()
