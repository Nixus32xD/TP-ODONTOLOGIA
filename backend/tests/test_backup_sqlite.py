from pathlib import Path
from contextlib import closing
import sqlite3
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.backup.errors import ErrorBackup
from odontologia.backup.bundle import crear_bundle_sqlite
from odontologia.backup.sqlite import crear_snapshot_sqlite


class BackupSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.directorio = Path(self.temporal.name)
        self.origen = self.directorio / 'origen.sqlite3'
        self.copia = self.directorio / 'copia.sqlite3'
        self.bundle = self.directorio / 'backup'
        inicializar_agenda(self.origen)
        migrar_sqlite(self.origen)
        with closing(sqlite3.connect(self.origen)) as conexion:
            conexion.execute('PRAGMA journal_mode=WAL')
            conexion.executemany(
                'INSERT INTO pacientes(id, nombre, telefono, activo) VALUES (?, ?, NULL, 1)',
                [(f'paciente-prueba-{i:04}', 'Nombre inicial ficticio') for i in range(800)],
            )
            conexion.commit()

    def tearDown(self):
        self.temporal.cleanup()

    def _nombres(self, ruta):
        with closing(sqlite3.connect(ruta)) as conexion:
            return tuple(fila[0] for fila in conexion.execute(
                'SELECT nombre FROM pacientes WHERE id LIKE \'paciente-prueba-%\' ORDER BY id'))

    def test_snapshot_con_wal_acepta_un_commit_concurrente_completo(self):
        cambios = []

        def actualizar_mientras_se_copia(_status, remaining, _total):
            if remaining <= 0 or cambios:
                return

            def escritor():
                with closing(sqlite3.connect(self.origen, timeout=2)) as conexion:
                    conexion.execute('BEGIN IMMEDIATE')
                    conexion.execute(
                        "UPDATE pacientes SET nombre='Nombre confirmado ficticio' "
                        "WHERE id LIKE 'paciente-prueba-%'")
                    conexion.commit()

            hilo = Thread(target=escritor)
            hilo.start()
            hilo.join(timeout=5)
            self.assertFalse(hilo.is_alive(), 'la escritura concurrente no terminó')
            cambios.append(True)

        crear_snapshot_sqlite(
            self.origen, self.copia, pages=1, progress=actualizar_mientras_se_copia)
        self.assertTrue(cambios)
        nombres = self._nombres(self.copia)
        self.assertEqual(len(nombres), 800)
        self.assertTrue(
            all(nombre == nombres[0] for nombre in nombres),
            'el snapshot no debe mezclar filas de dos transacciones',
        )
        self.assertIn(nombres[0], ('Nombre inicial ficticio', 'Nombre confirmado ficticio'))
        self.assertEqual(self._nombres(self.origen)[0], 'Nombre confirmado ficticio')

    def test_snapshot_wal_excluye_escritura_aun_no_confirmada_y_preserva_origen(self):
        escritor = sqlite3.connect(self.origen, isolation_level=None, timeout=2)
        try:
            escritor.execute('BEGIN IMMEDIATE')
            escritor.execute(
                "UPDATE pacientes SET nombre='Cambio sin confirmar' "
                "WHERE id LIKE 'paciente-prueba-%'")
            crear_snapshot_sqlite(self.origen, self.copia, pages=1)
            try:
                raise RuntimeError('fallo ficticio de la escritura')
            except RuntimeError:
                escritor.execute('ROLLBACK')
        finally:
            escritor.close()

        nombres = self._nombres(self.copia)
        self.assertEqual(len(nombres), 800)
        self.assertTrue(all(nombre == 'Nombre inicial ficticio' for nombre in nombres))
        self.assertTrue(all(nombre == 'Nombre inicial ficticio' for nombre in self._nombres(self.origen)))

    def test_bundle_crea_payload_manifiesto_y_validacion_conteos_integridad(self):
        resultado = crear_bundle_sqlite(self.origen, self.bundle, pages=2)

        self.assertEqual(resultado['backend'], 'sqlite')
        self.assertTrue((self.bundle / 'agenda.sqlite3').is_file())
        self.assertTrue((self.bundle / 'manifest.json').is_file())
        self.assertEqual(self._nombres(self.bundle / 'agenda.sqlite3')[0], 'Nombre inicial ficticio')
        with closing(sqlite3.connect(self.bundle / 'agenda.sqlite3')) as conexion:
            self.assertEqual(conexion.execute('PRAGMA integrity_check').fetchone(), ('ok',))
            self.assertIsNone(conexion.execute('PRAGMA foreign_key_check').fetchone())
            self.assertEqual(
                resultado['table_counts']['pacientes'],
                conexion.execute('SELECT count(*) FROM pacientes').fetchone()[0],
            )

    def test_manifest_counts_se_deriva_del_mismo_snapshot_wal(self):
        bundle = self.directorio / 'bundle-concurrente'
        escrituras = []

        def escribir_durante_backup(_status, remaining, _total):
            if remaining <= 0 or escrituras:
                return
            with closing(sqlite3.connect(self.origen)) as conexion:
                conexion.execute(
                    "INSERT INTO pacientes(id, nombre, telefono, activo) "
                    "VALUES ('paciente-concurrente', 'Nombre ficticio', NULL, 1)")
                conexion.commit()
            escrituras.append(True)

        resultado = crear_bundle_sqlite(
            self.origen, bundle, pages=1, progress=escribir_durante_backup)
        self.assertTrue(escrituras)
        with closing(sqlite3.connect(bundle / 'agenda.sqlite3')) as conexion:
            cantidad_payload = conexion.execute('SELECT count(*) FROM pacientes').fetchone()[0]
            self.assertEqual(resultado['table_counts']['pacientes'], cantidad_payload)
            self.assertIn(cantidad_payload, (802, 803))

    def test_origen_ausente_o_schema_incompatible_no_crea_bundle(self):
        faltante = self.directorio / 'faltante.sqlite3'
        with self.assertRaises(ErrorBackup):
            crear_bundle_sqlite(faltante, self.bundle)
        self.assertFalse(self.bundle.exists())

        c01 = self.directorio / 'c01.sqlite3'
        inicializar_agenda(c01)
        with self.assertRaises(ErrorBackup):
            crear_bundle_sqlite(c01, self.bundle)
        self.assertFalse(self.bundle.exists())

    def test_origen_con_fk_invalida_o_archivo_corrupto_no_publica_copia(self):
        with closing(sqlite3.connect(self.origen)) as conexion:
            conexion.execute('PRAGMA foreign_keys=OFF')
            conexion.execute(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES ('desconocido', 'profesional-A', "
                "'box-A', 100, 110, 'reservado', 1)")
            conexion.commit()
        with self.assertRaises(ErrorBackup):
            crear_bundle_sqlite(self.origen, self.bundle)
        self.assertFalse(self.bundle.exists())

        self.origen.write_bytes(b'contenido no SQLite')
        with self.assertRaises(ErrorBackup):
            crear_bundle_sqlite(self.origen, self.bundle)
        self.assertFalse(self.bundle.exists())

    def test_destino_existente_se_preserva_y_fallo_de_copia_limpia_staging(self):
        self.bundle.mkdir()
        sentinel = self.bundle / 'conservar.txt'
        sentinel.write_bytes(b'no reemplazar')
        with self.assertRaises(ErrorBackup):
            crear_bundle_sqlite(self.origen, self.bundle)
        self.assertEqual(sentinel.read_bytes(), b'no reemplazar')

        sentinel.unlink()
        self.bundle.rmdir()

        def fallar_progreso(_status, _remaining, _total):
            raise RuntimeError('fallo ficticio de backup')

        with self.assertRaises(ErrorBackup):
            crear_bundle_sqlite(self.origen, self.bundle, pages=1, progress=fallar_progreso)
        self.assertFalse(self.bundle.exists())
        self.assertFalse(list(self.directorio.glob('.tmp-backup-*')))


if __name__ == '__main__':
    unittest.main()
