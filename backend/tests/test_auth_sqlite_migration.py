from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite


class MigracionAutenticacionSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)

    def tablas(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}

    def test_migracion_agrega_usuarios_sin_alterar_catalogos_c01(self):
        self.assertNotIn('usuarios', self.tablas())
        migrar_sqlite(self.ruta)
        self.assertTrue({'pacientes', 'profesionales', 'boxes', 'turnos', 'usuarios', 'sesiones'} <= self.tablas())
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM pacientes').fetchone()[0], 2)
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0], 0)
            self.assertEqual(conexion.execute('SELECT version FROM auth_schema_version').fetchone()[0], 1)

    def test_migracion_repetida_no_modifica_la_agenda(self):
        migrar_sqlite(self.ruta)
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM pacientes').fetchone()[0], 2)
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0], 0)
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM auth_schema_version').fetchone()[0], 1)

    def test_base_ausente_se_rechaza_y_no_se_crea(self):
        ausente = Path(self.temporal.name) / 'ausente.sqlite3'
        with self.assertRaises(Exception):
            migrar_sqlite(ausente)
        self.assertFalse(ausente.exists())
