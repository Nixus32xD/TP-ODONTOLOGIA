from contextlib import closing
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from sqlalchemy import create_engine

from odontologia import ErrorAgenda, crear_turno, inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.disponibilidad import guardar_horario


class OcupacionPorEstadoSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = create_engine(f'sqlite:///{self.ruta.as_posix()}')
        self.addCleanup(self.engine.dispose)
        horario = {'1': [{'inicio': '08:00', 'fin': '12:00'}]}
        guardar_horario(self.engine, 'profesional', 'profesional-A', horario)
        guardar_horario(self.engine, 'box', 'box-A', horario)
    def _alta(self, paciente_id, minuto_inicio=0):
        inicio = datetime.fromisoformat('2026-11-02T12:00:00+00:00')
        fin = datetime.fromisoformat('2026-11-02T12:30:00+00:00')
        if minuto_inicio:
            from datetime import timedelta

            inicio += timedelta(minutes=minuto_inicio)
            fin += timedelta(minutes=minuto_inicio)
        return crear_turno(
            self.ruta,
            paciente_id=paciente_id,
            profesional_id='profesional-A',
            box_id='box-A',
            inicio=inicio,
            fin=fin,
        )

    def _estado(self, turno_id, estado):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('UPDATE turnos SET estado=? WHERE id=?', (estado, turno_id))
            conexion.commit()

    def test_reservado_y_confirmado_siguen_ocupando_recursos(self):
        turno = self._alta('paciente-A')
        for estado in ('reservado', 'confirmado'):
            with self.subTest(estado=estado):
                self._estado(turno.id, estado)
                with self.assertRaises(ErrorAgenda) as error:
                    self._alta('paciente-B', minuto_inicio=15)
                self.assertEqual(error.exception.codigo, 'conflicto_profesional')

    def test_estados_terminales_liberan_recursos_sin_borrar_historial(self):
        anterior = self._alta('paciente-A')
        for estado in ('atendido', 'ausente', 'cancelado'):
            with self.subTest(estado=estado):
                self._estado(anterior.id, estado)
                creado = self._alta('paciente-A', minuto_inicio=15)
                self.assertNotEqual(creado.id, anterior.id)
                self._estado(creado.id, 'cancelado')

        with closing(sqlite3.connect(self.ruta)) as conexion:
            filas = conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0]
            self.assertEqual(filas, 4)
