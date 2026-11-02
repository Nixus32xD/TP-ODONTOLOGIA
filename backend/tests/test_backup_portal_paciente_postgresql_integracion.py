"""Integración C-18 de backup/restore PostgreSQL con vínculo y clave sintéticos."""
from datetime import datetime, timedelta, timezone
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
from odontologia.db.models import Box, IdempotenciaPortalPaciente, Paciente, Profesional, Turno, Usuario


class BackupPortalPacientePostgreSQLIntegracionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        if (base_url.host not in ('127.0.0.1', 'localhost', '::1')
                or base_url.port != 55432
                or not (base_url.database or '').lower().endswith('_test')):
            raise unittest.SkipTest('C-18 requiere DB *_test en loopback:55432.')
        cls.schema = f'c18_portal_backup_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {cls.schema}'))
        cls.url = str(base_url.update_query_dict({'options': f'-csearch_path={cls.schema}'}))
        cls.engine = create_engine(cls.url, pool_pre_ping=True)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        cls.previous_persistence = os.environ.get('ODONTOLOGIA_PERSISTENCIA')
        os.environ['DATABASE_URL'] = cls.url
        os.environ['ODONTOLOGIA_PERSISTENCIA'] = 'postgresql'
        config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        config.set_main_option('script_location', str(Path(__file__).parents[1] / 'alembic'))
        config.config_file_name = None
        command.upgrade(config, 'head')

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
        if cls.previous_persistence is None:
            os.environ.pop('ODONTOLOGIA_PERSISTENCIA', None)
        else:
            os.environ['ODONTOLOGIA_PERSISTENCIA'] = cls.previous_persistence

    def test_bundle_restore_conserva_vinculo_y_clave_idempotente(self):
        sufijo = uuid4().hex[:12]
        paciente_id, profesional_id, box_id = (
            f'pac-c18-{sufijo}', f'prof-c18-{sufijo}', f'box-c18-{sufijo}')
        creado = datetime.now(timezone.utc)
        inicio_minuto = int((creado + timedelta(days=3)).timestamp() // 60)
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id=paciente_id, nombre='Paciente C-18 sintético', activo=True,
                         acepta_recordatorios=False),
                Profesional(id=profesional_id, nombre='Profesional C-18', activo=True),
                Box(id=box_id, nombre='Box C-18', activo=True),
            ])
            session.flush()
            usuario_id = f'usuario-{sufijo}'
            session.add(Usuario(
                id=usuario_id, identificador=f'paciente.{sufijo}',
                password_hash='hash-ficticio-sin-credencial', rol='paciente', activo=True,
                paciente_id=paciente_id))
            turno = Turno(
                paciente_id=paciente_id, profesional_id=profesional_id, box_id=box_id,
                inicio_minuto=inicio_minuto, fin_minuto=inicio_minuto + 30,
                estado='reservado', version=1)
            session.add(turno)
            session.flush()
            session.add(IdempotenciaPortalPaciente(
                id=f'idem-{sufijo}', paciente_id=paciente_id, operacion='reserva',
                clave=f'clave-{sufijo}', fingerprint='a' * 64, turno_id=turno.id,
                respuesta_json='{"estado":"reservado"}', created_at=creado))

        destino = f'c18_portal_restore_{sufijo}_test'
        with TemporaryDirectory() as temporal:
            bundle = Path(temporal) / 'bundle-c18'
            manifest = crear_bundle_postgresql(self.engine, bundle)
            self.assertEqual(manifest['schema_version'], '20261102_0014_financial_ledger')
            self.assertEqual(manifest['table_counts']['idempotencia_portal_paciente'], 1)
            texto = (bundle / 'manifest.json').read_text(encoding='utf-8')
            self.assertNotIn(paciente_id, texto)
            self.assertNotIn('Paciente C-18 sintético', texto)
            try:
                restaurado = restaurar_bundle_postgresql(self.engine, bundle, destino)
                self.assertTrue(restaurado['restored'])
                self.assertEqual(restaurado['table_counts'], manifest['table_counts'])
                target = create_engine(self.engine.url.set(database=destino), pool_pre_ping=True)
                try:
                    with target.connect() as connection:
                        self.assertEqual(connection.execute(text(
                            'SELECT paciente_id FROM usuarios WHERE id=:id'),
                            {'id': usuario_id}).scalar_one(), paciente_id)
                        self.assertEqual(connection.execute(text(
                            'SELECT count(*) FROM idempotencia_portal_paciente '
                            'WHERE clave=:clave'), {'clave': f'clave-{sufijo}'}).scalar_one(), 1)
                finally:
                    target.dispose()
            finally:
                admin = create_engine(
                    self.engine.url.set(database='postgres'), isolation_level='AUTOCOMMIT')
                try:
                    with admin.connect() as connection:
                        connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{destino}"')
                finally:
                    admin.dispose()


if __name__ == '__main__':
    unittest.main()
