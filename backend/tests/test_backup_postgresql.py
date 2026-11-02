from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest
from unittest.mock import patch
import sqlalchemy  # noqa: F401 - carga antes del mock de subprocess usado por SQLAlchemy

from odontologia.backup.errors import ErrorBackup
from odontologia.backup.manifest import TABLAS_ESQUEMA_ACTUAL
from odontologia.backup.postgresql import _entorno, crear_bundle_postgresql


class _Resultado:
    def __init__(self, valor):
        self.valor = valor

    def scalar_one(self):
        return self.valor

    def scalars(self):
        return self

    def all(self):
        return self.valor


class _Conexion:
    def __init__(self, engine):
        self.engine = engine

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.engine.transaction_active = False
        self.engine.snapshot_active = False
        pass

    def execute(self, consulta):
        consulta = str(consulta)
        if 'server_version_num' in consulta:
            return _Resultado(self.engine.server_version_num)
        if 'SELECT count(*)' in consulta:
            tabla = consulta.split('"')[1]
            if not (self.engine.transaction_active and self.engine.repeatable_read):
                raise AssertionError('los recuentos requieren REPEATABLE READ activo')
            return _Resultado(self.engine.table_counts[tabla])
        if 'alembic_version' in consulta:
            return _Resultado(self.engine.revision)
        if 'pg_export_snapshot' in consulta:
            self.engine.snapshot_active = True
            return _Resultado('00000001-00000001-1')
        if 'FROM pg_tables' in consulta:
            return _Resultado(sorted(TABLAS_ESQUEMA_ACTUAL['postgresql']))
        raise AssertionError(f'Consulta inesperada: {consulta}')

    def execution_options(self, **_kwargs):
        self.engine.repeatable_read = True
        return self

    def begin(self):
        self.engine.transaction_active = True
        return self


class _URL:
    host = '127.0.0.1'
    port = 55432
    username = 'odontologia'
    password = 'password-ficticio'
    database = 'agenda_test'
    query = {}


class _Engine:
    url = _URL()

    def __init__(self, revision='20261102_0013_patient_self_service', server_version_num=160002):
        self.revision = revision
        self.server_version_num = server_version_num
        self.repeatable_read = False
        self.transaction_active = False
        self.snapshot_active = False
        self.table_counts = {tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['postgresql']}
        self.dump_in_snapshot = False

    def connect(self):
        return _Conexion(self)


class BackupPostgresqlTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.directorio = Path(self.temporal.name)
        self.bundle = self.directorio / 'bundle'

    def tearDown(self):
        self.temporal.cleanup()

    def _ejecutor(self, registro, *, engine=None, error_dump=False,
                  commit_after_snapshot=False):
        def ejecutar(command, **kwargs):
            registro.append((command, kwargs))
            self.assertFalse(kwargs['shell'])
            if '--version' not in command:
                self.assertNotIn('password-ficticio', command)
                self.assertNotIn('JWT_SECRETO', kwargs['env'])
            if command[0].endswith('pg_dump') and command[1:] == ['--version']:
                return subprocess.CompletedProcess(command, 0, 'pg_dump (PostgreSQL) 16.3\n', '')
            if command[0].endswith('pg_restore') and command[1:] == ['--version']:
                return subprocess.CompletedProcess(command, 0, 'pg_restore (PostgreSQL) 16.3\n', '')
            if command[0].endswith('pg_dump'):
                self.assertIn('--snapshot=00000001-00000001-1', command)
                if engine is not None:
                    self.assertTrue(engine.transaction_active)
                    self.assertTrue(engine.snapshot_active)
                    engine.dump_in_snapshot = True
                    if commit_after_snapshot:
                        engine.table_counts['pacientes'] += 1
                if error_dump:
                    return subprocess.CompletedProcess(command, 1, '', 'password-ficticio')
                archivo = Path(command[command.index('--file') + 1])
                archivo.write_bytes(b'fake PostgreSQL custom archive with fictitious data')
                return subprocess.CompletedProcess(command, 0, '', '')
            if command[0].endswith('pg_restore') and '--list' in command:
                return subprocess.CompletedProcess(command, 0, 'TABLE public pacientes\n', '')
            raise AssertionError(command)
        return ejecutar

    def test_crea_bundle_custom_con_revision_hash_y_sin_url_en_manifest(self):
        registro = []
        engine = _Engine()
        engine.table_counts['pacientes'] = 2
        with patch('odontologia.backup.postgresql_tools.shutil.which',
                   side_effect=['/pg/pg_dump', '/pg/pg_restore']), \
                patch('odontologia.backup.postgresql_tools.subprocess.run',
                      side_effect=self._ejecutor(
                          registro, engine=engine, commit_after_snapshot=True)), \
                patch.dict('os.environ', {'JWT_SECRETO': 'secreto-jwt-ficticio'}, clear=True):
            manifiesto = crear_bundle_postgresql(engine, self.bundle)

        self.assertEqual(manifiesto['backend'], 'postgresql')
        self.assertTrue((self.bundle / 'agenda.dump').is_file())
        self.assertTrue((self.bundle / 'manifest.json').is_file())
        manifiesto_texto = (self.bundle / 'manifest.json').read_text(encoding='utf-8')
        self.assertNotIn('password-ficticio', manifiesto_texto)
        self.assertNotIn('127.0.0.1', manifiesto_texto)
        dump_command, dump_options = next(
            (command, options) for command, options in registro
            if command[0].endswith('pg_dump') and '--version' not in command)
        self.assertIn('--format=custom', dump_command)
        self.assertIn('--snapshot=00000001-00000001-1', dump_command)
        self.assertIn('agenda_test', dump_command)
        self.assertEqual(dump_options['env']['PGPASSWORD'], 'password-ficticio')
        self.assertTrue(engine.dump_in_snapshot)
        self.assertFalse(engine.transaction_active)
        self.assertEqual(manifiesto['table_counts']['pacientes'], 2)
        self.assertEqual(engine.table_counts['pacientes'], 3)

    def test_esquema_incompatible_falla_antes_de_crear_bundle(self):
        with self.assertRaises(ErrorBackup) as contexto:
            crear_bundle_postgresql(_Engine(revision='revision-antigua'), self.bundle)
        self.assertEqual(contexto.exception.codigo, 'esquema_incompatible')
        self.assertFalse(self.bundle.exists())

    def test_entorno_libpq_preserva_options_de_url_sin_incluir_secretos_globales(self):
        engine = _Engine()
        engine.url.query = {'options': '-csearch_path=backup_test'}
        with patch.dict('os.environ', {'JWT_SECRETO': 'secreto-no-heredado'}, clear=True):
            entorno = _entorno(engine)
        self.assertEqual(entorno['PGOPTIONS'], '-csearch_path=backup_test')
        self.assertNotIn('JWT_SECRETO', entorno)
        self.assertFalse(list(self.directorio.glob('.tmp-backup-*')))

    def test_error_pg_dump_limpia_staging_y_no_filtra_detalles(self):
        with patch('odontologia.backup.postgresql_tools.shutil.which',
                   side_effect=['/pg/pg_dump', '/pg/pg_restore']), \
                patch('odontologia.backup.postgresql_tools.subprocess.run',
                      side_effect=self._ejecutor([], error_dump=True)):
            with self.assertRaises(ErrorBackup) as contexto:
                crear_bundle_postgresql(_Engine(), self.bundle)
        self.assertNotIn('password-ficticio', str(contexto.exception))
        self.assertFalse(self.bundle.exists())
        self.assertFalse(list(self.directorio.glob('.tmp-backup-*')))

    def test_destino_existente_se_preserva_sin_invocar_proceso(self):
        self.bundle.mkdir()
        marcador = self.bundle / 'conservar.txt'
        marcador.write_text('conservar', encoding='utf-8')
        with self.assertRaises(ErrorBackup) as contexto:
            crear_bundle_postgresql(_Engine(), self.bundle)
        self.assertEqual(contexto.exception.codigo, 'destino_existente')
        self.assertEqual(marcador.read_text(encoding='utf-8'), 'conservar')

    def test_cliente_ausente_falla_antes_de_crear_staging(self):
        with patch('odontologia.backup.postgresql_tools.shutil.which', return_value=None):
            with self.assertRaises(ErrorBackup) as contexto:
                crear_bundle_postgresql(_Engine(), self.bundle)
        self.assertEqual(contexto.exception.codigo, 'herramienta_ausente')
        self.assertFalse(self.bundle.exists())
        self.assertFalse(list(self.directorio.glob('.tmp-backup-*')))

    def test_major_clientes_incompatible_falla_sin_abrir_salida(self):
        def ejecutar(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, 'pg (PostgreSQL) 15.8\n', '')

        with patch('odontologia.backup.postgresql_tools.shutil.which',
                   side_effect=['/pg/pg_dump', '/pg/pg_restore']), \
                patch('odontologia.backup.postgresql_tools.subprocess.run', side_effect=ejecutar):
            with self.assertRaises(ErrorBackup) as contexto:
                crear_bundle_postgresql(_Engine(server_version_num=160002), self.bundle)
        self.assertEqual(contexto.exception.codigo, 'version_incompatible')
        self.assertFalse(self.bundle.exists())
        self.assertFalse(list(self.directorio.glob('.tmp-backup-*')))


if __name__ == '__main__':
    unittest.main()
