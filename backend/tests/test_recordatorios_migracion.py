from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from odontologia import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.migraciones import migrar_sqlite


class MigracionRecordatoriosSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('DROP TABLE recordatorios_outbox')
            for tabla in (
                'etapas_plan_tratamiento', 'planes_tratamiento',
                'hallazgos_odontograma', 'versiones_odontograma',
            ):
                conexion.execute(f'DROP TABLE {tabla}')
            conexion.execute('ALTER TABLE pacientes DROP COLUMN acepta_recordatorios')
            conexion.execute('UPDATE auth_schema_version SET version=10')
            conexion.commit()

    def test_arranque_api_no_migra_esquema_v10(self):
        with patch.dict('os.environ', {'JWT_SECRETO': 'c2VjcmV0by1zaW50ZXRpY28tZGUtcHJ1ZWJh'}, clear=True):
            app = crear_app(self.ruta)
            with TestClient(app) as client:
                respuesta = client.post('/sesiones', json={
                    'identificador': 'admin.sintetico', 'password': 'clave-sintetica'})

        self.assertEqual(respuesta.status_code, 503)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (10,))
            self.assertNotIn('recordatorios_outbox', {
                fila[0] for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")})

    def test_repetir_migracion_preserva_consentimiento_existente(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute(
                "UPDATE pacientes SET acepta_recordatorios=1 WHERE id='paciente-A'")
            conexion.commit()

        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT acepta_recordatorios FROM pacientes WHERE id=?',
                ('paciente-A',)).fetchone(), (1,))
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (11,))
            self.assertIn('recordatorios_outbox', {
                fila[0] for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")})

    def test_upgrade_v10_agrega_consentimiento_y_outbox_con_constraints(self):
        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (11,))
            columnas_paciente = {
                fila[1]: fila for fila in conexion.execute('PRAGMA table_info(pacientes)')
            }
            self.assertIn('acepta_recordatorios', columnas_paciente)
            self.assertEqual(columnas_paciente['acepta_recordatorios'][3], 1)
            self.assertEqual(columnas_paciente['acepta_recordatorios'][4], '0')
            self.assertTrue(all(valor == 0 for (valor,) in conexion.execute(
                'SELECT acepta_recordatorios FROM pacientes')))

            tablas = {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn('recordatorios_outbox', tablas)
            columnas_outbox = {fila[1] for fila in conexion.execute(
                'PRAGMA table_info(recordatorios_outbox)')}
            self.assertTrue({
                'id', 'turno_id', 'turno_version', 'generation', 'tipo', 'programado_para',
                'estado', 'intentos', 'idempotency_key', 'created_at', 'updated_at',
            } <= columnas_outbox)
            self.assertEqual(conexion.execute(
                'PRAGMA foreign_key_list(recordatorios_outbox)').fetchone()[2], 'turnos')
            self.assertIsNone(conexion.execute('PRAGMA foreign_key_check').fetchone())
            conexion.execute(
                "INSERT INTO eventos_auditoria(created_at, action, resource_type, "
                "resource_id, result) VALUES ('2026-11-02T13:00:00+00:00', "
                "'recordatorio.programado', 'recordatorio', 'recordatorio-sintetico', "
                "'confirmado')")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "INSERT INTO eventos_auditoria(created_at, action, resource_type, "
                    "resource_id, result) VALUES ('2026-11-02T13:00:00+00:00', "
                    "'recordatorio.programado', 'turno', 'turno-sintetico', 'confirmado')")
            conexion.rollback()

        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('PRAGMA foreign_keys=ON')
            conexion.execute(
                "INSERT INTO turnos (id, paciente_id, profesional_id, box_id, "
                "inicio_minuto, fin_minuto) VALUES (42, 'paciente-A', "
                "'profesional-A', 'box-A', 100, 130)")
            conexion.commit()

            def insertar(reminder_id, turno_id, version, tipo, key, status='pendiente',
                         generation=1):
                conexion.execute('''INSERT INTO recordatorios_outbox
                    (id, turno_id, turno_version, generation, tipo, programado_para, estado, intentos,
                     idempotency_key, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)''',
                    (reminder_id, turno_id, version, generation, tipo,
                     '2026-11-03T13:00:00+00:00',
                     status, key, '2026-11-02T13:00:00+00:00',
                     '2026-11-02T13:00:00+00:00'))

            insertar('recordatorio-1', 42, 1, 'turno_24h', '42:1:turno_24h')
            with self.assertRaises(sqlite3.IntegrityError):
                insertar('recordatorio-duplicado', 42, 1, 'turno_24h',
                         '42:1:turno_24h-duplicado')
            conexion.execute('''INSERT INTO recordatorios_outbox
                (id, turno_id, turno_version, generation, tipo, programado_para, estado,
                 intentos, idempotency_key, created_at, updated_at)
                VALUES ('recordatorio-reconsentido', 42, 1, 2, 'turno_24h',
                    '2026-11-03T13:00:00+00:00', 'pendiente', 0,
                    '42:1:turno_24h:generation:2', '2026-11-02T13:01:00+00:00',
                    '2026-11-02T13:01:00+00:00')''')
            with self.assertRaises(sqlite3.IntegrityError):
                insertar('recordatorio-generacion-invalida', 42, 1, 'turno_24h',
                         '42:1:turno_24h:generation:0', generation=0)
            with self.assertRaises(sqlite3.IntegrityError):
                insertar('recordatorio-huerfano', 999_999, 1, 'turno_24h',
                         '999999:1:turno_24h')
            with self.assertRaises(sqlite3.IntegrityError):
                insertar('recordatorio-tipo-invalido', 42, 1, 'email',
                         '42:1:email')
            conexion.rollback()

    def test_migrar_outbox_v11_asigna_generacion_uno_y_preserva_filas(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('PRAGMA foreign_keys=OFF')
            turno_id = conexion.execute('''INSERT INTO turnos
                (paciente_id, profesional_id, box_id, inicio_minuto, fin_minuto)
                VALUES ('paciente-A', 'profesional-A', 'box-A', 29700000, 29700030)
                RETURNING id''').fetchone()[0]
            conexion.execute('DROP TABLE recordatorios_outbox')
            conexion.execute('''CREATE TABLE recordatorios_outbox (
                id TEXT PRIMARY KEY,
                turno_id INTEGER NOT NULL REFERENCES turnos(id) ON DELETE RESTRICT,
                turno_version INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                programado_para TEXT NOT NULL,
                estado TEXT NOT NULL,
                intentos INTEGER NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(turno_id, turno_version, tipo)
            )''')
            conexion.execute('''INSERT INTO recordatorios_outbox
                (id, turno_id, turno_version, tipo, programado_para, estado, intentos,
                 idempotency_key, created_at, updated_at)
                VALUES ('recordatorio-previo', ?, 1, 'turno_24h',
                    '2026-11-04T18:00:00+00:00', 'invalidado', 0,
                    'turno:previo:turno_24h', '2026-11-02T12:00:00+00:00',
                    '2026-11-02T12:01:00+00:00')''', (turno_id,))
            conexion.execute('UPDATE auth_schema_version SET version=11')
            conexion.commit()

        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT generation, estado, idempotency_key FROM recordatorios_outbox'
            ).fetchone(), (1, 'invalidado', 'turno:previo:turno_24h'))
            self.assertIsNone(conexion.execute('PRAGMA foreign_key_check').fetchone())


if __name__ == '__main__':
    unittest.main()
