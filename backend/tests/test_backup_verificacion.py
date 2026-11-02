from contextlib import closing
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.backup.errors import ErrorBackup
from odontologia.backup.manifest import (
    TABLAS_ESQUEMA_ACTUAL,
    crear_manifiesto,
    guardar_manifiesto,
)
from odontologia.backup.verificacion import verificar_bundle


class VerificacionBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.root = Path(self.temporal.name)
        self.db = self.root / 'agenda.sqlite3'
        self.bundle = self.root / 'bundle'
        inicializar_agenda(self.db)
        migrar_sqlite(self.db)
        self.bundle.mkdir()
        payload = self.bundle / 'agenda.sqlite3'
        with closing(sqlite3.connect(self.db)) as origen, closing(sqlite3.connect(payload)) as destino:
            origen.backup(destino)
        recuentos = self._contar(payload)
        guardar_manifiesto(
            crear_manifiesto(payload, backend='sqlite', schema_version='9', table_counts=recuentos),
            self.bundle / 'manifest.json',
        )

    def tearDown(self):
        self.temporal.cleanup()

    def test_verifica_bundle_sqlite_hash_integridad_claves_y_sin_mutar_archivos(self):
        antes = {ruta.name: ruta.read_bytes() for ruta in self.bundle.iterdir()}
        resultado = verificar_bundle(self.bundle)
        despues = {ruta.name: ruta.read_bytes() for ruta in self.bundle.iterdir()}
        self.assertEqual(resultado['backend'], 'sqlite')
        self.assertTrue(resultado['verified'])
        self.assertEqual(antes, despues)

    def test_bundle_incompleto_o_con_archivo_extra_se_rechaza(self):
        (self.bundle / 'manifest.json').unlink()
        with self.assertRaises(ErrorBackup):
            verificar_bundle(self.bundle)
        guardar_manifiesto(
            crear_manifiesto(self.bundle / 'agenda.sqlite3', backend='sqlite', schema_version='9',
                             table_counts=self._contar(self.bundle / 'agenda.sqlite3')),
            self.bundle / 'manifest.json',
        )
        (self.bundle / 'extra.txt').write_text('extra', encoding='utf-8')
        with self.assertRaises(ErrorBackup):
            verificar_bundle(self.bundle)

    def test_hash_alterado_formato_desconocido_y_schema_incompatible_fallan(self):
        payload = self.bundle / 'agenda.sqlite3'
        recuentos = self._contar(payload)
        payload.write_bytes(payload.read_bytes() + b'alterado')
        with self.assertRaises(ErrorBackup):
            verificar_bundle(self.bundle)

        payload.write_bytes(b'corrupto')
        manifest = crear_manifiesto(payload, backend='sqlite', schema_version='9',
                                    table_counts=recuentos)
        manifest['format_version'] = 999
        (self.bundle / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaises(ErrorBackup):
            verificar_bundle(self.bundle)

        manifest['format_version'] = 1
        manifest['schema_version'] = '999'
        (self.bundle / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaises(ErrorBackup):
            verificar_bundle(self.bundle)

    def test_manifiesto_hash_correcto_no_oculta_sqlite_corrupto(self):
        payload = self.bundle / 'agenda.sqlite3'
        payload.write_bytes(b'archivo no SQLite')
        (self.bundle / 'manifest.json').unlink()
        guardar_manifiesto(
            crear_manifiesto(payload, backend='sqlite', schema_version='9',
                             table_counts={tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['sqlite']}),
            self.bundle / 'manifest.json',
        )
        with self.assertRaises(ErrorBackup) as contexto:
            verificar_bundle(self.bundle)
        self.assertEqual(contexto.exception.codigo, 'integridad_invalida')

    def test_rechaza_table_counts_distintos_con_hash_correcto(self):
        payload = self.bundle / 'agenda.sqlite3'
        recuentos = self._contar(payload)
        recuentos['pacientes'] += 1
        (self.bundle / 'manifest.json').unlink()
        guardar_manifiesto(
            crear_manifiesto(payload, backend='sqlite', schema_version='9',
                             table_counts=recuentos),
            self.bundle / 'manifest.json',
        )
        with self.assertRaises(ErrorBackup) as contexto:
            verificar_bundle(self.bundle)
        self.assertEqual(contexto.exception.codigo, 'recuentos_incompatibles')

    def test_postgresql_requiere_cliente_y_lista_custom_archive(self):
        (self.bundle / 'agenda.sqlite3').unlink()
        payload = self.bundle / 'agenda.dump'
        payload.write_bytes(b'archivo custom ficticio')
        (self.bundle / 'manifest.json').unlink()
        guardar_manifiesto(
            crear_manifiesto(payload, backend='postgresql',
                             schema_version='20261102_0010_clinical_history',
                             table_counts={tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['postgresql']}),
            self.bundle / 'manifest.json',
        )
        resultado = type('Resultado', (), {'returncode': 0, 'stdout': 'TOC', 'stderr': ''})()
        with patch('odontologia.backup.verificacion.shutil.which', return_value='pg_restore'), \
                patch('odontologia.backup.verificacion.subprocess.run', return_value=resultado) as ejecutar:
            verificado = verificar_bundle(self.bundle)
        self.assertEqual(verificado['backend'], 'postgresql')
        self.assertTrue(verificado['verified'])
        self.assertFalse(ejecutar.call_args.kwargs['shell'])

    def test_postgresql_hash_correcto_no_oculta_archive_corrupto(self):
        (self.bundle / 'agenda.sqlite3').unlink()
        payload = self.bundle / 'agenda.dump'
        payload.write_bytes(b'archive corrupto ficticio')
        (self.bundle / 'manifest.json').unlink()
        guardar_manifiesto(
            crear_manifiesto(payload, backend='postgresql',
                             schema_version='20261102_0010_clinical_history',
                             table_counts={tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['postgresql']}),
            self.bundle / 'manifest.json',
        )
        resultado = type('Resultado', (), {'returncode': 1, 'stdout': '', 'stderr': 'archive corrupto'})()
        with patch('odontologia.backup.verificacion.shutil.which', return_value='pg_restore'), \
                patch('odontologia.backup.verificacion.subprocess.run', return_value=resultado):
            with self.assertRaises(ErrorBackup) as contexto:
                verificar_bundle(self.bundle)
        self.assertEqual(contexto.exception.codigo, 'bundle_invalido')

    def _contar(self, ruta):
        with closing(sqlite3.connect(ruta)) as conexion:
            tablas = {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            self.assertEqual(tablas, TABLAS_ESQUEMA_ACTUAL['sqlite'])
            return {tabla: conexion.execute(f'SELECT count(*) FROM "{tabla}"').fetchone()[0]
                    for tabla in sorted(tablas)}


if __name__ == '__main__':
    unittest.main()
