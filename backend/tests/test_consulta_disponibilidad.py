from datetime import date, datetime, time, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

from sqlalchemy import update
from sqlalchemy.orm import Session

from odontologia import inicializar_agenda
from odontologia.agenda import _minutos
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.db.models import Box, Profesional, Turno
from odontologia.disponibilidad import crear_bloqueo, guardar_horario
from odontologia.consulta_disponibilidad import (
    ErrorConsultaDisponibilidad, calcular_opciones_disponibilidad,
)


class ConsultaDisponibilidadTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        self.fecha = date(2026, 10, 15)  # Jueves, zona America/Argentina/Mendoza
        self.zona = ZoneInfo('America/Argentina/Mendoza')
        abierto = {'4': [{'inicio': '09:00', 'fin': '12:00'}]}
        guardar_horario(self.engine, 'profesional', 'profesional-A', abierto)
        guardar_horario(self.engine, 'box', 'box-A', abierto)
        inicio_turno = datetime.combine(self.fecha, time(9, 30), self.zona)
        fin_turno = datetime.combine(self.fecha, time(10), self.zona)
        with Session(self.engine) as session, session.begin():
            session.add(Turno(
                paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio_minuto=_minutos(inicio_turno), fin_minuto=_minutos(fin_turno),
                estado='reservado'))
            inicio_confirmado = datetime.combine(self.fecha, time(11), self.zona)
            fin_confirmado = datetime.combine(self.fecha, time(11, 30), self.zona)
            session.add(Turno(
                paciente_id='paciente-B', profesional_id='profesional-A', box_id='box-A',
                inicio_minuto=_minutos(inicio_confirmado),
                fin_minuto=_minutos(fin_confirmado), estado='confirmado'))
        crear_bloqueo(
            self.engine, 'box', 'box-A',
            datetime.combine(self.fecha, time(10, 30), self.zona),
            datetime.combine(self.fecha, time(11), self.zona))

    def test_sugerencias_cada_quince_minutos_respetan_horarios_turnos_y_bloqueos(self):
        resultado = calcular_opciones_disponibilidad(
            self.engine, fecha='2026-10-15', profesional_id='profesional-A',
            box_id='box-A', duracion_minutos=30)
        inicios = [opcion['inicio'].astimezone(self.zona).strftime('%H:%M')
                   for opcion in resultado['items']]
        self.assertEqual(inicios, ['09:00', '10:00', '11:30'])
        self.assertTrue(all(opcion['fin'] > opcion['inicio'] for opcion in resultado['items']))

    def test_excepcion_y_recursos_inactivos_restringen_opciones(self):
        # A high-priority date exception replaces the weekly window.
        from odontologia.disponibilidad import guardar_excepcion
        with Session(self.engine) as session, session.begin():
            session.execute(update(Turno).values(estado='atendido'))
        guardar_excepcion(
            self.engine, 'profesional', 'profesional-A', '2026-10-15',
            [{'inicio': '11:00', 'fin': '12:00'}])
        resultado = calcular_opciones_disponibilidad(
            self.engine, fecha='2026-10-15', profesional_id='profesional-A',
            box_id='box-A', duracion_minutos=30)
        inicios = [opcion['inicio'].astimezone(self.zona).strftime('%H:%M')
                   for opcion in resultado['items']]
        self.assertEqual(inicios, ['11:00', '11:15', '11:30'])

        with Session(self.engine) as session, session.begin():
            session.get(Profesional, 'profesional-A').activo = False
            session.get(Box, 'box-A').activo = False
        inactivos = calcular_opciones_disponibilidad(
            self.engine, fecha='2026-10-15', profesional_id='profesional-A',
            box_id='box-A', duracion_minutos=30)
        self.assertEqual(inactivos['items'], [])

    def test_entrada_invalida_y_recurso_desconocido_se_rechazan(self):
        with self.assertRaises(ErrorConsultaDisponibilidad):
            calcular_opciones_disponibilidad(
                self.engine, fecha='15-10-2026', profesional_id='profesional-A',
                box_id='box-A', duracion_minutos=30)
        with self.assertRaises(ErrorConsultaDisponibilidad):
            calcular_opciones_disponibilidad(
                self.engine, fecha='2026-10-15', profesional_id='profesional-A',
                box_id='box-A', duracion_minutos=0)
        with self.assertRaises(ErrorConsultaDisponibilidad) as error:
            calcular_opciones_disponibilidad(
                self.engine, fecha='2026-10-15', profesional_id='inexistente',
                box_id='box-A', duracion_minutos=30)
        self.assertEqual(error.exception.estado, 404)

    def test_profesional_no_puede_consultar_opciones_de_otro_profesional(self):
        with self.assertRaises(ErrorConsultaDisponibilidad) as error:
            calcular_opciones_disponibilidad(
                self.engine, fecha='2026-10-15', profesional_id='profesional-B',
                box_id='box-A', duracion_minutos=30,
                profesional_vinculado_id='profesional-A')
        self.assertEqual((error.exception.codigo, error.exception.estado),
                         ('permiso_denegado', 403))

    def test_duracion_de_quince_minutos_puede_terminar_a_medianoche_local(self):
        with Session(self.engine) as session, session.begin():
            session.execute(update(Turno).values(estado='atendido'))
        from odontologia.disponibilidad import guardar_excepcion
        for tipo in ('profesional', 'box'):
            guardar_excepcion(
                self.engine, tipo, 'profesional-A' if tipo == 'profesional' else 'box-A',
                '2026-10-15', [{'inicio': '23:45', 'fin': '24:00'}])

        resultado = calcular_opciones_disponibilidad(
            self.engine, fecha='2026-10-15', profesional_id='profesional-A',
            box_id='box-A', duracion_minutos=15)
        self.assertEqual(len(resultado['items']), 1)
        self.assertEqual(resultado['items'][0]['inicio'].astimezone(self.zona).strftime('%H:%M'),
                         '23:45')
        self.assertEqual(resultado['items'][0]['fin'].astimezone(self.zona).strftime('%H:%M'),
                         '00:00')


if __name__ == '__main__':
    unittest.main()
