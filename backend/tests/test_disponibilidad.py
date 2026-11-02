from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from sqlalchemy import create_engine

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.disponibilidad import (
    ErrorDisponibilidad,
    crear_bloqueo,
    guardar_excepcion,
    guardar_horario,
    normalizar_fecha_local,
    normalizar_horario_semanal,
    normalizar_intervalo_bloqueo,
    normalizar_tramos_locales,
)


class ValidacionesDisponibilidadTests(unittest.TestCase):
    def test_dias_iso_y_varios_tramos_adyacentes(self):
        resultado = normalizar_horario_semanal({
            '1': [
                {'inicio': '09:00', 'fin': '12:00'},
                {'inicio': '12:00', 'fin': '13:00'},
                {'inicio': '14:00', 'fin': '18:00'},
            ],
            '7': [],
        })

        self.assertEqual(resultado[1], ((540, 720), (720, 780), (840, 1080)))
        self.assertEqual(resultado[7], ())

    def test_acepta_limites_del_dia_y_rechaza_24_como_inicio(self):
        self.assertEqual(normalizar_tramos_locales([
            {'inicio': '00:00', 'fin': '24:00'},
        ]), ((0, 1440),))
        with self.assertRaises(ErrorDisponibilidad):
            normalizar_tramos_locales([{'inicio': '24:00', 'fin': '24:00'}])

    def test_rechaza_dias_formato_cruces_y_solapamientos(self):
        for dias in (
            {'0': []}, {'8': []}, {'lunes': []}, {True: []},
        ):
            with self.subTest(dias=dias), self.assertRaises(ErrorDisponibilidad):
                normalizar_horario_semanal(dias)
        for tramos in (
            [{'inicio': '10:00', 'fin': '10:00'}],
            [{'inicio': '10:00', 'fin': '09:00'}],
            [{'inicio': '23:00', 'fin': '01:00'}],
            [{'inicio': '9:00', 'fin': '10:00'}],
            [{'inicio': '09:00', 'fin': '10:00:00'}],
            [
                {'inicio': '09:00', 'fin': '11:00'},
                {'inicio': '10:00', 'fin': '12:00'},
            ],
        ):
            with self.subTest(tramos=tramos), self.assertRaises(ErrorDisponibilidad):
                normalizar_tramos_locales(tramos)

    def test_fecha_de_excepcion_debe_ser_iso_estricta(self):
        self.assertEqual(normalizar_fecha_local('2026-11-02').isoformat(), '2026-11-02')
        for fecha in ('2026-02-30', '02-11-2026', '2026-1-02', '', None):
            with self.subTest(fecha=fecha), self.assertRaises(ErrorDisponibilidad):
                normalizar_fecha_local(fecha)

    def test_bloqueo_exige_offset_minuto_exacto_y_intervalo_positivo(self):
        inicio, fin = normalizar_intervalo_bloqueo(
            datetime.fromisoformat('2026-11-02T23:30:00-03:00'),
            datetime.fromisoformat('2026-11-03T00:30:00-03:00'),
        )
        self.assertEqual(inicio.utcoffset(), timedelta(0))
        self.assertLess(inicio, fin)
        for inicio_local, fin_local in (
            (datetime(2026, 11, 2, 9), datetime(2026, 11, 2, 10)),
            (datetime.fromisoformat('2026-11-02T09:00:01-03:00'),
             datetime.fromisoformat('2026-11-02T10:00:00-03:00')),
            (datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
             datetime.fromisoformat('2026-11-02T10:00:00-03:00')),
            (datetime.fromisoformat('2026-11-02T11:00:00-03:00'),
             datetime.fromisoformat('2026-11-02T10:00:00-03:00')),
        ):
            with self.subTest(inicio=inicio_local, fin=fin_local), self.assertRaises(ErrorDisponibilidad):
                normalizar_intervalo_bloqueo(inicio_local, fin_local)

    def test_horario_invalido_no_escribe_configuracion(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                with self.assertRaises(ErrorDisponibilidad):
                    guardar_horario(engine, 'profesional', 'profesional-A', {
                        '1': [
                            {'inicio': '09:00', 'fin': '11:00'},
                            {'inicio': '10:00', 'fin': '12:00'},
                        ],
                    })
            finally:
                engine.dispose()
            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(
                    conexion.execute('SELECT COUNT(*) FROM horarios_semanales').fetchone(), (0,))

    def test_excepcion_y_bloqueo_invalidos_no_escriben(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                with self.assertRaises(ErrorDisponibilidad):
                    guardar_excepcion(engine, 'profesional', 'profesional-A', '2026-11-02', [
                        {'inicio': '09:00', 'fin': '11:00'},
                        {'inicio': '10:00', 'fin': '12:00'},
                    ])
                with self.assertRaises(ErrorDisponibilidad):
                    crear_bloqueo(
                        engine, 'box', 'box-A', datetime(2026, 11, 2, 9),
                        datetime.fromisoformat('2026-11-02T10:00:00-03:00'))
            finally:
                engine.dispose()
            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(
                    conexion.execute('SELECT COUNT(*) FROM excepciones_horario').fetchone(), (0,))
                self.assertEqual(
                    conexion.execute('SELECT COUNT(*) FROM bloqueos_agenda').fetchone(), (0,))


if __name__ == '__main__':
    unittest.main()
