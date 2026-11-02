from contextlib import closing
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from odontologia import crear_turno, inicializar_agenda
from odontologia.agenda import ErrorAgenda
from odontologia.auth.migraciones import (
    VERSION_ESQUEMA_AUTENTICACION,
    migrar_sqlite,
)


class MigracionCicloVidaSQLiteTests(unittest.TestCase):
    def test_c01_standalone_sin_migrar_conserva_su_contrato(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)

            creado = crear_turno(
                ruta,
                paciente_id='paciente-A',
                profesional_id='profesional-A',
                box_id='box-A',
                inicio=datetime.fromisoformat('2026-11-02T12:00:00+00:00'),
                fin=datetime.fromisoformat('2026-11-02T12:30:00+00:00'),
            )
            with self.assertRaises(ErrorAgenda) as error:
                crear_turno(
                    ruta,
                    paciente_id='paciente-B',
                    profesional_id='profesional-A',
                    box_id='box-B',
                    inicio=datetime.fromisoformat('2026-11-02T12:15:00+00:00'),
                    fin=datetime.fromisoformat('2026-11-02T12:45:00+00:00'),
                )

            self.assertEqual(error.exception.codigo, 'conflicto_profesional')
            with closing(sqlite3.connect(ruta)) as conexion:
                tablas = {fila[0] for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                columnas = {fila[1] for fila in conexion.execute('PRAGMA table_info(turnos)')}
                self.assertNotIn('auth_schema_version', tablas)
                self.assertNotIn('estado', columnas)
                self.assertEqual(
                    conexion.execute('SELECT id FROM turnos').fetchall(), [(creado.id,)])

    def test_migracion_v6_preserva_turno_y_lo_inicializa_reservado(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            creado = crear_turno(
                ruta,
                paciente_id='paciente-A',
                profesional_id='profesional-A',
                box_id='box-A',
                inicio=datetime.fromisoformat('2026-11-02T12:00:00+00:00'),
                fin=datetime.fromisoformat('2026-11-02T12:30:00+00:00'),
            )

            migrar_sqlite(ruta)

            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(
                    conexion.execute('SELECT version FROM auth_schema_version').fetchone(),
                    (6,),
                )
                columnas = {fila[1] for fila in conexion.execute('PRAGMA table_info(turnos)')}
                self.assertIn('estado', columnas)
                fila = conexion.execute(
                    'SELECT id, paciente_id, profesional_id, box_id, inicio_minuto, '
                    'fin_minuto, estado FROM turnos'
                ).fetchone()
                self.assertEqual(fila[:4], (
                    creado.id, 'paciente-A', 'profesional-A', 'box-A'))
                self.assertEqual(fila[-1], 'reservado')

                with self.assertRaises(sqlite3.IntegrityError):
                    conexion.execute(
                        "UPDATE turnos SET estado='desconocido' WHERE id=?", (creado.id,))

    def test_migracion_v6_repetida_conserva_estado_y_version(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            migrar_sqlite(ruta)

            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(VERSION_ESQUEMA_AUTENTICACION, 6)
                self.assertEqual(
                    conexion.execute('SELECT version FROM auth_schema_version').fetchone(),
                    (6,),
                )

    def test_migracion_amplia_catalogo_auditoria_y_preserva_eventos(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            with closing(sqlite3.connect(ruta)) as conexion:
                conexion.execute(
                    "INSERT INTO eventos_auditoria(created_at, action, resource_type, "
                    "resource_id, result) VALUES ('2026-11-02T12:00:00+00:00', "
                    "'turno.creado', 'turno', '1', 'confirmado')")
                conexion.execute('UPDATE auth_schema_version SET version=5')
                conexion.commit()

            migrar_sqlite(ruta)

            with closing(sqlite3.connect(ruta)) as conexion:
                historicos = conexion.execute(
                    "SELECT action, resource_type, resource_id, result FROM eventos_auditoria "
                    "WHERE action='turno.creado'").fetchall()
                self.assertEqual(historicos, [('turno.creado', 'turno', '1', 'confirmado')])
                conexion.execute(
                    "INSERT INTO eventos_auditoria(created_at, action, resource_type, "
                    "resource_id, result) VALUES ('2026-11-02T12:01:00+00:00', "
                    "'turno.estado_actualizado', 'turno', '1', 'confirmado')")


if __name__ == '__main__':
    unittest.main()
