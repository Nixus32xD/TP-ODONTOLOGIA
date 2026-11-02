from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia import crear_turno
from datetime import datetime


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
            self.assertEqual(conexion.execute('SELECT version FROM auth_schema_version').fetchone()[0], 3)

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

    def test_migracion_agrega_ficha_minima_y_conserva_ids_y_turnos(self):
        turno = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))

        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            columnas = {fila[1] for fila in conexion.execute('PRAGMA table_info(pacientes)')}
            self.assertTrue({'id', 'nombre', 'telefono', 'activo'} <= columnas)
            self.assertEqual(
                conexion.execute(
                    'SELECT nombre, telefono, activo FROM pacientes WHERE id=?',
                    ('paciente-A',)).fetchone(),
                ('Paciente de demostración paciente-A', None, 1))
            self.assertEqual(
                conexion.execute('SELECT id, paciente_id FROM turnos').fetchone(),
                (turno.id, 'paciente-A'))
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (3,))
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "INSERT INTO pacientes(id, nombre, telefono, activo) "
                    "VALUES ('paciente-vacio', '', NULL, 1)")

    def test_migracion_repetida_conserva_nombre_y_eventos_previos(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute(
                "UPDATE pacientes SET nombre='Nombre ficticio personalizado' WHERE id='paciente-A'")
            conexion.execute(
                "INSERT INTO eventos_auditoria(created_at, action, resource_type, result) "
                "VALUES ('2026-11-02T12:00:00+00:00', 'cuenta.bootstrap', 'cuenta', 'confirmado')")
            conexion.commit()

        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                "SELECT nombre FROM pacientes WHERE id='paciente-A'").fetchone(),
                ('Nombre ficticio personalizado',))
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='cuenta.bootstrap'").fetchone(),
                (1,))

    def test_upgrade_desde_version_v2_agrega_ficha_y_preserva_turno_y_auditoria(self):
        turno = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T10:30:00-03:00'))
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('DROP TRIGGER pacientes_validar_insert')
            conexion.execute('DROP TRIGGER pacientes_validar_update')
            conexion.execute('ALTER TABLE pacientes DROP COLUMN telefono')
            conexion.execute('ALTER TABLE pacientes DROP COLUMN activo')
            conexion.execute('ALTER TABLE pacientes DROP COLUMN nombre')
            conexion.execute('UPDATE auth_schema_version SET version=2')
            conexion.execute(
                "INSERT INTO eventos_auditoria(created_at, action, resource_type, result) "
                "VALUES ('2026-11-02T12:00:00+00:00', 'cuenta.bootstrap', 'cuenta', 'confirmado')")
            conexion.commit()

        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                "SELECT nombre, telefono, activo FROM pacientes WHERE id='paciente-A'"
            ).fetchone(), ('Paciente de demostración paciente-A', None, 1))
            self.assertEqual(conexion.execute(
                'SELECT id, paciente_id FROM turnos').fetchone(), (turno.id, 'paciente-A'))
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='cuenta.bootstrap'"
            ).fetchone(), (1,))
