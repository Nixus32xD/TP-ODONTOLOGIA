from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
from threading import Event, Thread
import unittest
from unittest.mock import patch
from datetime import timedelta

from odontologia import crear_turno, inicializar_agenda
from odontologia.db.migracion import ErrorMigracion, leer_agenda_sqlite


class LectorSQLiteTests(unittest.TestCase):
    def _insertar_turnos_directos(self, ruta, filas):
        inicializar_agenda(ruta)
        with closing(sqlite3.connect(ruta)) as conexion:
            conexion.executemany(
                'INSERT INTO turnos '
                '(paciente_id, profesional_id, box_id, inicio_minuto, fin_minuto) '
                'VALUES (?, ?, ?, ?, ?)', filas)
            conexion.commit()

    def test_lee_c01_en_solo_lectura_y_preserva_ids_y_minutos(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            turno = crear_turno(
                ruta, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio=datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
                fin=datetime(2026, 10, 1, 12, 30, tzinfo=timezone.utc),
            )
            original = ruta.read_bytes()

            agenda = leer_agenda_sqlite(ruta)

            self.assertEqual(ruta.read_bytes(), original)
        self.assertEqual(agenda.pacientes, ('paciente-A', 'paciente-B'))
        self.assertEqual(agenda.profesionales, ('profesional-A', 'profesional-B'))
        self.assertEqual(agenda.boxes, ('box-A', 'box-B'))
        self.assertEqual(agenda.turnos[0].id, turno.id)
        self.assertEqual(agenda.turnos[0].paciente_id, 'paciente-A')
        esperado = int((datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
                        - datetime(1970, 1, 1, tzinfo=timezone.utc)) / timedelta(minutes=1))
        self.assertEqual(agenda.turnos[0].inicio_minuto, esperado)
        self.assertEqual(agenda.turnos[0].fin_minuto, esperado + 30)

    def test_ruta_ausente_y_esquema_incompatible_se_rechazan(self):
        with tempfile.TemporaryDirectory() as temporal:
            ausente = Path(temporal) / 'ausente.sqlite3'
            corrupta = Path(temporal) / 'corrupta.sqlite3'
            with closing(sqlite3.connect(corrupta)) as conexion:
                conexion.execute('CREATE TABLE pacientes (id TEXT PRIMARY KEY)')

            for ruta in (ausente, corrupta):
                with self.subTest(ruta=ruta):
                    with self.assertRaises(ErrorMigracion):
                        leer_agenda_sqlite(ruta)

    def test_referencias_rotas_se_rechazan(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            crear_turno(
                ruta, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio=datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
                fin=datetime(2026, 10, 1, 12, 30, tzinfo=timezone.utc),
            )
            with closing(sqlite3.connect(ruta)) as conexion:
                conexion.execute('PRAGMA foreign_keys=OFF')
                conexion.execute('DELETE FROM pacientes WHERE id = ?', ('paciente-A',))
                conexion.commit()

            with self.assertRaises(ErrorMigracion) as contexto:
                leer_agenda_sqlite(ruta)
            self.assertEqual(contexto.exception.codigo, 'fuente_invalida')

    def test_indice_con_nombre_c01_y_columnas_distintas_se_rechaza(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            with closing(sqlite3.connect(ruta)) as conexion:
                conexion.execute('DROP INDEX turnos_profesional')
                conexion.execute(
                    'CREATE INDEX turnos_profesional ON turnos(box_id, inicio_minuto)')
                conexion.commit()

            with self.assertRaises(ErrorMigracion):
                leer_agenda_sqlite(ruta)

    def test_rechaza_solapamiento_de_profesional(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            self._insertar_turnos_directos(ruta, [
                ('paciente-A', 'profesional-A', 'box-A', 100, 140),
                ('paciente-B', 'profesional-A', 'box-B', 120, 160),
            ])

            with self.assertRaises(ErrorMigracion) as contexto:
                leer_agenda_sqlite(ruta)

        self.assertEqual(contexto.exception.codigo, 'conflicto_profesional')

    def test_rechaza_solapamiento_de_box(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            self._insertar_turnos_directos(ruta, [
                ('paciente-A', 'profesional-A', 'box-A', 100, 140),
                ('paciente-B', 'profesional-B', 'box-A', 120, 160),
            ])

            with self.assertRaises(ErrorMigracion) as contexto:
                leer_agenda_sqlite(ruta)

        self.assertEqual(contexto.exception.codigo, 'conflicto_box')

    def test_prioriza_conflicto_profesional_si_tambien_se_solapa_el_box(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            self._insertar_turnos_directos(ruta, [
                ('paciente-A', 'profesional-A', 'box-A', 100, 140),
                ('paciente-B', 'profesional-A', 'box-A', 120, 160),
            ])

            with self.assertRaises(ErrorMigracion) as contexto:
                leer_agenda_sqlite(ruta)

        self.assertEqual(contexto.exception.codigo, 'conflicto_profesional')

    def test_adyacencia_anterior_y_posterior_no_es_solapamiento(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            self._insertar_turnos_directos(ruta, [
                ('paciente-A', 'profesional-A', 'box-A', 70, 100),
                ('paciente-B', 'profesional-A', 'box-A', 100, 130),
                ('paciente-A', 'profesional-A', 'box-A', 130, 160),
            ])

            agenda = leer_agenda_sqlite(ruta)

        self.assertEqual(len(agenda.turnos), 3)

    def test_snapshot_sqlite_no_mezcla_catalogo_y_turnos_durante_writer(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            self._insertar_turnos_directos(ruta, [
                ('paciente-A', 'profesional-A', 'box-A', 100, 130),
            ])
            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(conexion.execute('PRAGMA journal_mode=WAL').fetchone()[0], 'wal')

            selector_paciente = Event()
            writer_finalizado = Event()
            resultado = []
            error = []
            original_connect = sqlite3.connect

            def conectar(*args, **kwargs):
                conexion = original_connect(*args, **kwargs)
                if args and 'mode=ro' in args[0]:
                    observado = Event()

                    def trazar(sentencia):
                        if (not observado.is_set()
                                and sentencia.lower().startswith('select id from pacientes')):
                            observado.set()
                            selector_paciente.set()
                            writer_finalizado.wait(5)

                    conexion.set_trace_callback(trazar)
                return conexion

            def leer():
                try:
                    resultado.append(leer_agenda_sqlite(ruta))
                except Exception as exc:  # el hilo devuelve el error al test principal
                    error.append(exc)

            hilo = Thread(target=leer)
            with patch('odontologia.db.migracion.sqlite3.connect', side_effect=conectar):
                hilo.start()
                try:
                    self.assertTrue(selector_paciente.wait(5))
                    with closing(original_connect(ruta)) as writer:
                        writer.execute('PRAGMA foreign_keys=OFF')
                        writer.execute('DELETE FROM pacientes WHERE id = ?', ('paciente-A',))
                        writer.commit()
                finally:
                    writer_finalizado.set()
                    hilo.join(timeout=5)

        self.assertFalse(hilo.is_alive())
        self.assertEqual(error, [])
        self.assertEqual(resultado[0].pacientes, ('paciente-A', 'paciente-B'))
        self.assertEqual(len(resultado[0].turnos), 1)


if __name__ == '__main__':
    unittest.main()
