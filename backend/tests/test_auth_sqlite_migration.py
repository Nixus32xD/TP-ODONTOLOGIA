from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.almacenamiento import (
    crear_engine_autenticacion, validar_esquema_autenticacion,
)
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
            self.assertEqual(conexion.execute('SELECT version FROM auth_schema_version').fetchone()[0], 13)

    def test_migracion_repetida_no_modifica_la_agenda(self):
        migrar_sqlite(self.ruta)
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM pacientes').fetchone()[0], 2)
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0], 0)
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM auth_schema_version').fetchone()[0], 1)

    def test_v13_agrega_ledger_append_only_y_auditoria_financiera(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (13,))
            self.assertTrue({'cargos_financieros', 'cobros_financieros',
                             'reversiones_cobros', 'idempotencia_financiera'} <= self.tablas())
            conexion.execute("INSERT INTO cargos_financieros VALUES "
                             "('cargo-1', 'paciente-A', 1200, 'Consulta', '2026-11-02T12:00:00')")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute("UPDATE cargos_financieros SET concepto='cambio' WHERE id='cargo-1'")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute("DELETE FROM cargos_financieros WHERE id='cargo-1'")
            conexion.execute("INSERT INTO eventos_auditoria(created_at, action, resource_type, "
                             "resource_id, result) VALUES "
                             "('2026-11-02T12:00:00', 'cargo.creado', 'finanzas', 'cargo-1', 'confirmado')")
            conexion.commit()

    def test_upgrade_v12_a_v13_conserva_eventos_y_agrega_tablas_financieras(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('PRAGMA foreign_keys=OFF')
            for tabla in ('idempotencia_financiera', 'reversiones_cobros',
                          'cobros_financieros', 'cargos_financieros'):
                conexion.execute(f'DROP TABLE {tabla}')
            conexion.execute('UPDATE auth_schema_version SET version=12')
            conexion.execute("INSERT INTO eventos_auditoria(created_at, action, resource_type, "
                             "result) VALUES ('2026-11-02T11:00:00', 'cuenta.bootstrap', "
                             "'cuenta', 'confirmado')")
            conexion.commit()
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (13,))
            self.assertEqual(conexion.execute(
                "SELECT count(*) FROM eventos_auditoria WHERE action='cuenta.bootstrap'"
            ).fetchone(), (1,))
            self.assertTrue({'cargos_financieros', 'cobros_financieros',
                             'reversiones_cobros', 'idempotencia_financiera'} <= self.tablas())

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
                'SELECT version FROM auth_schema_version').fetchone(), (13,))
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
            conexion.execute('DROP TABLE recordatorios_outbox')
            conexion.execute('ALTER TABLE pacientes DROP COLUMN acepta_recordatorios')
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

    def test_upgrade_desde_v6_agrega_vinculo_profesional_y_preserva_dependencias(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute(
                "INSERT INTO usuarios(id, identificador, password_hash, rol, activo) "
                "VALUES ('usuario-admin', 'admin.one', 'hash-ficticio', 'administrador', 1)")
            conexion.execute(
                "INSERT INTO sesiones(id, usuario_id, jti, expira_en, revocada_en, creado_en) "
                "VALUES ('sesion-1', 'usuario-admin', 'jti-1', 5000, NULL, 1000)")
            conexion.execute(
                "INSERT INTO eventos_auditoria(created_at, actor_id, action, resource_type, "
                "resource_id, result) VALUES ('2026-11-02T12:00:00+00:00', 'usuario-admin', "
                "'cuenta.bootstrap', 'cuenta', 'usuario-admin', 'confirmado')")
            conexion.commit()

        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('PRAGMA foreign_keys=ON')
            columnas = {fila[1] for fila in conexion.execute('PRAGMA table_info(usuarios)')}
            self.assertIn('profesional_id', columnas)
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (13,))
            self.assertEqual(conexion.execute(
                "SELECT id, rol, profesional_id FROM usuarios WHERE id='usuario-admin'"
            ).fetchone(), ('usuario-admin', 'administrador', None))
            self.assertEqual(conexion.execute(
                "SELECT usuario_id FROM sesiones WHERE id='sesion-1'").fetchone(), ('usuario-admin',))
            self.assertEqual(conexion.execute(
                "SELECT actor_id FROM eventos_auditoria WHERE action='cuenta.bootstrap'"
            ).fetchone(), ('usuario-admin',))
            self.assertEqual(conexion.execute('PRAGMA foreign_key_check').fetchall(), [])
            conexion.execute(
                "INSERT INTO usuarios(id, identificador, password_hash, rol, activo, profesional_id) "
                "VALUES ('usuario-prof', 'profesional.a', 'hash-ficticio', 'profesional', 1, "
                "'profesional-A')")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "INSERT INTO usuarios(id, identificador, password_hash, rol, activo, profesional_id) "
                    "VALUES ('usuario-prof-2', 'profesional.b', 'hash-ficticio', 'profesional', 1, "
                    "'profesional-A')")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "INSERT INTO usuarios(id, identificador, password_hash, rol, activo) "
                    "VALUES ('usuario-prof-invalid', 'profesional.c', 'hash-ficticio', 'profesional', 1)")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "INSERT INTO usuarios(id, identificador, password_hash, rol, activo, profesional_id) "
                    "VALUES ('usuario-recep-invalid', 'recepcion.a', 'hash-ficticio', 'recepcion', 1, "
                    "'profesional-B')")

    def test_upgrade_v11_a_v12_agrega_vinculo_paciente_unico_y_tabla_idempotente(self):
        turno = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-10T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-10T09:30:00-03:00'))
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('PRAGMA foreign_keys=ON')
            conexion.execute(
                "INSERT INTO usuarios(id, identificador, password_hash, rol, activo) "
                "VALUES ('usuario-admin', 'admin.sintetico', 'hash-sintetico', 'administrador', 1)")
            conexion.execute(
                "INSERT INTO usuarios(id, identificador, password_hash, rol, activo, profesional_id) "
                "VALUES ('usuario-prof', 'prof.sintetico', 'hash-sintetico', 'profesional', 1, "
                "'profesional-A')")
            conexion.execute(
                "INSERT INTO sesiones(id, usuario_id, jti, expira_en, revocada_en, creado_en) "
                "VALUES ('sesion-prof', 'usuario-prof', 'jti-prof', 5000, NULL, 1000)")
            conexion.execute(
                "INSERT INTO eventos_auditoria(created_at, actor_id, action, resource_type, "
                "resource_id, result) VALUES ('2026-11-02T12:00:00+00:00', 'usuario-prof', "
                "'cuenta.creada', 'cuenta', 'usuario-prof', 'confirmado')")
            conexion.commit()
            conexion.execute('PRAGMA foreign_keys=OFF')
            conexion.execute('''CREATE TABLE usuarios_v11 (
                id TEXT PRIMARY KEY,
                identificador TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL CHECK (rol IN ('administrador', 'recepcion', 'profesional')),
                activo INTEGER NOT NULL CHECK (activo IN (0, 1)),
                profesional_id TEXT UNIQUE REFERENCES profesionales(id) ON DELETE RESTRICT,
                CHECK (
                    (rol = 'profesional' AND profesional_id IS NOT NULL) OR
                    (rol IN ('administrador', 'recepcion') AND profesional_id IS NULL)
                )
            )''')
            conexion.execute('''INSERT INTO usuarios_v11
                (id, identificador, password_hash, rol, activo, profesional_id)
                SELECT id, identificador, password_hash, rol, activo, profesional_id FROM usuarios''')
            conexion.execute('DROP TABLE usuarios')
            conexion.execute('ALTER TABLE usuarios_v11 RENAME TO usuarios')
            conexion.execute('DROP TABLE idempotencia_portal_paciente')
            conexion.execute('UPDATE auth_schema_version SET version=11')
            conexion.commit()

        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('PRAGMA foreign_keys=ON')
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (13,))
            columnas = {fila[1] for fila in conexion.execute('PRAGMA table_info(usuarios)')}
            self.assertIn('paciente_id', columnas)
            self.assertEqual(conexion.execute(
                "SELECT rol, profesional_id, paciente_id FROM usuarios "
                "WHERE id='usuario-admin'").fetchone(), ('administrador', None, None))
            self.assertEqual(conexion.execute(
                "SELECT rol, profesional_id, paciente_id FROM usuarios "
                "WHERE id='usuario-prof'").fetchone(), ('profesional', 'profesional-A', None))
            self.assertEqual(conexion.execute(
                "SELECT usuario_id FROM sesiones WHERE id='sesion-prof'").fetchone(),
                ('usuario-prof',))
            self.assertEqual(conexion.execute(
                "SELECT actor_id FROM eventos_auditoria WHERE resource_id='usuario-prof'"
            ).fetchone(), ('usuario-prof',))
            self.assertEqual(conexion.execute(
                'SELECT id, paciente_id FROM turnos').fetchone(), (turno.id, 'paciente-A'))
            self.assertIn('idempotencia_portal_paciente', {
                fila[0] for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")})
            conexion.execute(
                "INSERT INTO usuarios(id, identificador, password_hash, rol, activo, paciente_id) "
                "VALUES ('usuario-paciente', 'paciente.sintetico', 'hash-sintetico', 'paciente', 1, "
                "'paciente-A')")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "INSERT INTO usuarios(id, identificador, password_hash, rol, activo, paciente_id) "
                    "VALUES ('usuario-paciente-2', 'paciente.dos', 'hash-sintetico', 'paciente', 1, "
                    "'paciente-A')")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "INSERT INTO usuarios(id, identificador, password_hash, rol, activo, paciente_id) "
                    "VALUES ('usuario-rol-invalido', 'admin.paciente', 'hash-sintetico', "
                    "'administrador', 1, 'paciente-A')")
            self.assertEqual(conexion.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_validador_v7_falla_cerrado_si_falta_columna_de_vinculo(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('DROP TABLE usuarios')
            conexion.execute('''CREATE TABLE usuarios (
                id TEXT PRIMARY KEY,
                identificador TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL CHECK (rol IN ('administrador', 'recepcion')),
                activo INTEGER NOT NULL CHECK (activo IN (0, 1))
            )''')
            conexion.execute('UPDATE auth_schema_version SET version=13')
            conexion.commit()
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(engine.dispose)

        with self.assertRaisesRegex(RuntimeError, 'vínculos de cuentas'):
            validar_esquema_autenticacion(engine, 'sqlite', self.ruta)

    def test_validador_falla_cerrado_si_falta_version_de_turno(self):
        from odontologia.auth.migraciones import VERSION_ESQUEMA_AUTENTICACION

        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            columnas = {fila[1] for fila in conexion.execute('PRAGMA table_info(turnos)')}
            if 'version' in columnas:
                conexion.execute('ALTER TABLE turnos DROP COLUMN version')
            conexion.execute(
                'UPDATE auth_schema_version SET version=?',
                (VERSION_ESQUEMA_AUTENTICACION,))
            conexion.commit()
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(engine.dispose)

        with self.assertRaisesRegex(RuntimeError, 'versión'):
            validar_esquema_autenticacion(engine, 'sqlite', self.ruta)

    def test_validador_falla_cerrado_si_falta_tabla_clinica_c16(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('PRAGMA foreign_keys=OFF')
            conexion.execute('DROP TABLE etapas_plan_tratamiento')
            conexion.execute('DROP TABLE planes_tratamiento')
            conexion.commit()
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(engine.dispose)

        with self.assertRaisesRegex(RuntimeError, 'odontograma y planes'):
            validar_esquema_autenticacion(engine, 'sqlite', self.ruta)
