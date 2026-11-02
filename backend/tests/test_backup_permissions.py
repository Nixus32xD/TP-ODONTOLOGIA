import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.backup.bundle import crear_bundle_sqlite
from odontologia.backup.manifest import TABLAS_ESQUEMA_ACTUAL
from odontologia.backup import bundle as modulo_sqlite
from odontologia.backup import postgresql as modulo_postgresql


def _modo(ruta: Path) -> int | None:
    try:
        return stat.S_IMODE(ruta.stat().st_mode)
    except FileNotFoundError:
        return None


@unittest.skipUnless(os.name == 'posix', 'Los modos POSIX se validan en un runner POSIX.')
class PermisosBundlePosixTests(unittest.TestCase):
    def setUp(self):
        mascara_previa = os.umask(0o022)
        try:
            self.temporal = TemporaryDirectory()
            self.directorio = Path(self.temporal.name)
            self.origen = self.directorio / 'origen.sqlite3'
            self.bundle = self.directorio / 'bundle'
            inicializar_agenda(self.origen)
            migrar_sqlite(self.origen)
        finally:
            os.umask(mascara_previa)

    def tearDown(self):
        self.temporal.cleanup()

    def test_sqlite_mantiene_staging_y_archivos_privados_antes_y_despues_de_publicar(self):
        modos_staging = []
        leer_manifiesto_original = modulo_sqlite.leer_manifiesto

        def observar_staging(manifiesto, payload=None):
            ruta_manifest = Path(manifiesto)
            if ruta_manifest.parent.name.startswith('.tmp-backup-'):
                modos_staging.append((
                    _modo(ruta_manifest.parent),
                    _modo(Path(payload)),
                    _modo(ruta_manifest),
                ))
            return leer_manifiesto_original(manifiesto, payload)

        with patch.object(modulo_sqlite, 'leer_manifiesto', side_effect=observar_staging):
            crear_bundle_sqlite(self.origen, self.bundle)

        self.assertEqual(modos_staging, [(0o700, 0o600, 0o600)])
        self.assertEqual(_modo(self.bundle), 0o700)
        self.assertEqual(_modo(self.bundle / 'agenda.sqlite3'), 0o600)
        self.assertEqual(_modo(self.bundle / 'manifest.json'), 0o600)

    def test_postgresql_payload_y_manifest_se_mantienen_privados_en_staging_y_publicados(self):
        observaciones_dump = []
        observaciones_staging = []
        conteos = {tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['postgresql']}

        def escribir_dump(_engine, _herramientas, payload):
            ruta_payload = Path(payload)
            observaciones_dump.append((_modo(ruta_payload.parent), _modo(ruta_payload)))
            ruta_payload.write_bytes(b'archivo ficticio pg_dump')
            return conteos

        leer_manifiesto_original = modulo_postgresql.leer_manifiesto

        def observar_staging(manifiesto, payload=None):
            ruta_manifest = Path(manifiesto)
            if ruta_manifest.parent.name.startswith('.tmp-backup-'):
                observaciones_staging.append((
                    _modo(ruta_manifest.parent),
                    _modo(Path(payload)),
                    _modo(ruta_manifest),
                ))
            return leer_manifiesto_original(manifiesto, payload)

        with patch.object(modulo_postgresql, '_validar_revision'), \
                patch.object(modulo_postgresql, 'validar_runtime_postgresql', return_value={}), \
                patch.object(modulo_postgresql, '_capturar_snapshot_y_dump', side_effect=escribir_dump), \
                patch.object(modulo_postgresql, '_validar_archive'), \
                patch.object(modulo_postgresql, 'leer_manifiesto', side_effect=observar_staging):
            modulo_postgresql.crear_bundle_postgresql(object(), self.bundle)

        self.assertEqual(observaciones_dump, [(0o700, 0o600)])
        self.assertEqual(observaciones_staging, [(0o700, 0o600, 0o600)])
        self.assertEqual(_modo(self.bundle), 0o700)
        self.assertEqual(_modo(self.bundle / 'agenda.dump'), 0o600)
        self.assertEqual(_modo(self.bundle / 'manifest.json'), 0o600)


if __name__ == '__main__':
    unittest.main()
