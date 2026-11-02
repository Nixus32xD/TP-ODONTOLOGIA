"""Integración C-17 de backup/restore PostgreSQL con outbox sintético."""
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
from odontologia.db.models import Box, Paciente, Profesional, RecordatorioOutbox, Turno


class BackupRecordatoriosPostgreSQLIntegracionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        if (base_url.host not in ('127.0.0.1', '::1', 'localhost')
                or base_url.port != 55432
                or not (base_url.database or '').lower().endswith('_test')):
            raise unittest.SkipTest('C-17 requiere DB *_test en loopback y puerto 55432.')

        cls.schema = f'c17_backup_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {cls.schema}'))
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
            with cls.root_engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
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
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
        cls.root_engine.dispose()
        cls._restore_environment()

    def test_bundle_restore_preserva_estados_claves_y_recuentos_del_outbox(self):
        paciente_id = f'paciente-c17-{uuid4().hex}'
        profesional_id = f'profesional-c17-{uuid4().hex}'
        box_id = f'box-c17-{uuid4().hex}'
        ahora = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        fecha = ahora
        turnos = []
        with Session(self.engine) as session, session.begin():
            paciente = Paciente(
                id=paciente_id, nombre='Nombre ficticio C-17', telefono='+54 261 5550101',
                activo=True, acepta_recordatorios=True)
            session.add_all([
                paciente,
                Profesional(id=profesional_id, nombre='Profesional C-17', activo=True),
                Box(id=box_id, nombre='Box C-17', activo=True),
            ])
            session.flush()
            estados = ('pendiente', 'procesado_simulado', 'invalidado')
            for indice, estado in enumerate(estados, start=1):
                turno = Turno(
                    paciente_id=paciente_id, profesional_id=profesional_id, box_id=box_id,
                    inicio_minuto=int((ahora + timedelta(days=indice)).timestamp() // 60),
                    fin_minuto=int((ahora + timedelta(days=indice, minutes=30)).timestamp() // 60),
                    estado='confirmado', version=indice,
                )
                session.add(turno)
                session.flush()
                clave = (
                    f'turno:{turno.id}:version:{indice}:tipo:turno_24h:generacion:1')
                session.add(RecordatorioOutbox(
                    id=str(uuid4()), turno_id=turno.id, turno_version=indice,
                    generation=1, tipo='turno_24h', programado_para=fecha,
                    estado=estado, intentos=0,
                    idempotency_key=clave, created_at=fecha, updated_at=fecha))
                turnos.append((turno.id, 1, estado, clave))
            session.add(RecordatorioOutbox(
                id=str(uuid4()), turno_id=turnos[0][0], turno_version=1,
                generation=2, tipo='turno_24h', programado_para=fecha,
                estado='pendiente', intentos=0,
                idempotency_key=f'{turnos[0][3]}:generacion:2',
                created_at=fecha, updated_at=fecha))
            turnos.append((turnos[0][0], 2, 'pendiente', f'{turnos[0][3]}:generacion:2'))

        destino = f'c17_restore_{uuid4().hex[:12]}_test'
        with TemporaryDirectory() as temporal:
            bundle = Path(temporal) / 'bundle-c17'
            manifiesto = crear_bundle_postgresql(self.engine, bundle)
            self.assertEqual(
                manifiesto['schema_version'], '20261102_0013_patient_self_service')
            self.assertEqual(manifiesto['table_counts']['recordatorios_outbox'], 4)
            texto_manifest = (bundle / 'manifest.json').read_text(encoding='utf-8')
            self.assertNotIn('Nombre ficticio C-17', texto_manifest)
            self.assertNotIn('+54 261 5550101', texto_manifest)

            try:
                restaurado = restaurar_bundle_postgresql(self.engine, bundle, destino)
                self.assertTrue(restaurado['restored'])
                self.assertEqual(restaurado['table_counts'], manifiesto['table_counts'])
                restored_engine = create_engine(
                    self.engine.url.set(database=destino), pool_pre_ping=True)
                try:
                    with restored_engine.connect() as connection:
                        filas = connection.execute(text(
                            'SELECT turno_id, generation, estado, idempotency_key '
                            'FROM recordatorios_outbox ORDER BY turno_id, generation')).all()
                    self.assertEqual(filas, sorted(turnos))
                    with self.engine.connect() as source:
                        self.assertEqual(source.execute(text(
                            'SELECT count(*) FROM recordatorios_outbox')).scalar_one(), 4)
                finally:
                    restored_engine.dispose()
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
