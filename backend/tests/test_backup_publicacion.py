from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.backup import bundle as modulo_sqlite
from odontologia.backup import permisos as modulo_permisos
from odontologia.backup import postgresql as modulo_postgresql
from odontologia.backup.errors import ErrorBackup
from odontologia.backup.manifest import TABLAS_ESQUEMA_ACTUAL


class PublicacionBundleAtomicaTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.directorio = Path(self.temporal.name)
        self.origen = self.directorio / 'origen.sqlite3'
        self.bundle = self.directorio / 'bundle'
        inicializar_agenda(self.origen)
        migrar_sqlite(self.origen)

    def tearDown(self):
        self.temporal.cleanup()

    def _preparar_postgresql(self, publicador):
        stack = ExitStack()
        stack.enter_context(patch.object(modulo_postgresql, '_validar_revision'))
        stack.enter_context(patch.object(
            modulo_postgresql, 'validar_runtime_postgresql', return_value={}))

        def dump_ficticio(_engine, _herramientas, payload):
            Path(payload).write_bytes('dump ficticio para test de publicación'.encode('utf-8'))
            return {tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['postgresql']}

        stack.enter_context(patch.object(
            modulo_postgresql, '_capturar_snapshot_y_dump', side_effect=dump_ficticio))
        stack.enter_context(patch.object(modulo_postgresql, '_validar_archive'))
        stack.enter_context(patch.object(
            modulo_postgresql, 'publicar_directorio_nuevo',
            side_effect=publicador, create=True))
        return stack

    def test_sqlite_excepcion_despues_de_preparar_staging_no_publica_parcial(self):
        def interrumpir(staging, _destino):
            self.assertEqual(
                {ruta.name for ruta in Path(staging).iterdir()},
                {'agenda.sqlite3', 'manifest.json'},
            )
            raise OSError('interrupción simulada antes del rename')

        with patch.object(modulo_sqlite, 'publicar_directorio_nuevo',
                          side_effect=interrumpir, create=True):
            with self.assertRaises(ErrorBackup):
                modulo_sqlite.crear_bundle_sqlite(self.origen, self.bundle)

        self.assertFalse(self.bundle.exists())
        self.assertEqual(list(self.directorio.glob('.tmp-backup-*')), [])

    def test_postgresql_excepcion_despues_de_preparar_staging_no_publica_parcial(self):
        def interrumpir(staging, _destino):
            self.assertEqual(
                {ruta.name for ruta in Path(staging).iterdir()},
                {'agenda.dump', 'manifest.json'},
            )
            raise OSError('interrupción simulada antes del rename')

        with self._preparar_postgresql(interrumpir):
            with self.assertRaises(ErrorBackup):
                modulo_postgresql.crear_bundle_postgresql(object(), self.bundle)

        self.assertFalse(self.bundle.exists())
        self.assertEqual(list(self.directorio.glob('.tmp-backup-*')), [])

    def test_sqlite_colision_con_directorio_vacio_se_preserva_y_limpia_staging(self):
        def colision(staging, destino):
            self.assertEqual(
                {ruta.name for ruta in Path(staging).iterdir()},
                {'agenda.sqlite3', 'manifest.json'},
            )
            Path(destino).mkdir()
            raise FileExistsError('directorio creado durante la publicación')

        with patch.object(modulo_sqlite, 'publicar_directorio_nuevo',
                          side_effect=colision, create=True):
            with self.assertRaises(ErrorBackup):
                modulo_sqlite.crear_bundle_sqlite(self.origen, self.bundle)

        self.assertTrue(self.bundle.is_dir())
        self.assertEqual(list(self.bundle.iterdir()), [])
        self.assertEqual(list(self.directorio.glob('.tmp-backup-*')), [])

    def test_postgresql_colision_con_directorio_vacio_se_preserva_y_limpia_staging(self):
        def colision(staging, destino):
            self.assertEqual(
                {ruta.name for ruta in Path(staging).iterdir()},
                {'agenda.dump', 'manifest.json'},
            )
            Path(destino).mkdir()
            raise FileExistsError('directorio creado durante la publicación')

        with self._preparar_postgresql(colision):
            with self.assertRaises(ErrorBackup):
                modulo_postgresql.crear_bundle_postgresql(object(), self.bundle)

        self.assertTrue(self.bundle.is_dir())
        self.assertEqual(list(self.bundle.iterdir()), [])
        self.assertEqual(list(self.directorio.glob('.tmp-backup-*')), [])

    def test_primitiva_noreplace_no_reemplaza_directorio_vacio(self):
        publicador = getattr(modulo_permisos, 'publicar_directorio_nuevo', None)
        self.assertIsNotNone(publicador, 'falta primitiva atómica de publicación sin reemplazo')
        staging = self.directorio / '.tmp-backup-prueba'
        staging.mkdir()
        (staging / 'payload').write_bytes(b'fixture ficticio')
        self.bundle.mkdir()

        with self.assertRaises(FileExistsError):
            publicador(staging, self.bundle)

        self.assertTrue(staging.is_dir())
        self.assertEqual((staging / 'payload').read_bytes(), b'fixture ficticio')
        self.assertEqual(list(self.bundle.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
