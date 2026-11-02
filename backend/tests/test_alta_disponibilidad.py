from datetime import datetime, timezone
from pathlib import Path
import unittest
from threading import Event, Thread
from tempfile import TemporaryDirectory
from unittest.mock import patch

from sqlalchemy import create_engine

from odontologia import ErrorAgenda, crear_turno, inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.disponibilidad import (
    ErrorDisponibilidad, crear_bloqueo, guardar_excepcion, guardar_horario,
)


class AltaDisponibilidadTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = create_engine(f'sqlite:///{self.ruta.as_posix()}')
        self.addCleanup(self.engine.dispose)
        self.turno_hora_local = (
            datetime(2026, 11, 2, 12, tzinfo=timezone.utc),
            datetime(2026, 11, 2, 12, 30, tzinfo=timezone.utc),
        )
        self._horarios_lunes()

    def _horarios_lunes(self):
        for tipo, recurso in (('profesional', 'profesional-A'), ('box', 'box-A')):
            guardar_horario(self.engine, tipo, recurso, {
                '1': [{'inicio': '09:00', 'fin': '12:00'}]})

    def _crear(self, inicio=None, fin=None):
        return crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=inicio or self.turno_hora_local[0],
            fin=fin or self.turno_hora_local[1])

    def test_acepta_turno_dentro_de_horario_local_de_ambos_recursos(self):
        turno = self._crear()
        self.assertEqual(turno.inicio, self.turno_hora_local[0])

    def test_sqlite_v5_sin_horarios_nace_cerrado(self):
        ruta = Path(self.temporal.name) / 'agenda-cerrada.sqlite3'
        inicializar_agenda(ruta)
        migrar_sqlite(ruta)
        with self.assertRaises(ErrorAgenda) as error:
            crear_turno(
                ruta, paciente_id='paciente-A', profesional_id='profesional-A',
                box_id='box-A', inicio=self.turno_hora_local[0], fin=self.turno_hora_local[1])
        self.assertEqual(error.exception.codigo, 'fuera_de_disponibilidad')

    def test_esquema_standalone_c01_sin_migrar_conserva_contrato_historico(self):
        ruta = Path(self.temporal.name) / 'agenda-c01.sqlite3'
        inicializar_agenda(ruta)
        turno = crear_turno(
            ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=self.turno_hora_local[0], fin=self.turno_hora_local[1])
        self.assertGreater(turno.id, 0)

    def test_rechaza_turno_fuera_del_horario_de_un_solo_recurso(self):
        guardar_horario(self.engine, 'box', 'box-A', {
            '1': [{'inicio': '09:30', 'fin': '12:00'}]})
        with self.assertRaises(ErrorAgenda) as error:
            self._crear()
        self.assertEqual(error.exception.codigo, 'fuera_de_disponibilidad')

    def test_rechaza_turno_que_no_cabe_en_horario_del_profesional(self):
        guardar_horario(self.engine, 'profesional', 'profesional-A', {
            '1': [{'inicio': '09:30', 'fin': '12:00'}]})
        with self.assertRaises(ErrorAgenda) as error:
            self._crear()
        self.assertEqual(error.exception.codigo, 'fuera_de_disponibilidad')

    def test_excepcion_con_tramo_reemplaza_semanal_aunque_semanal_siga_abierto(self):
        guardar_excepcion(self.engine, 'profesional', 'profesional-A', '2026-11-02', [
            {'inicio': '10:00', 'fin': '11:00'}])
        with self.assertRaises(ErrorAgenda) as error:
            self._crear()
        self.assertEqual(error.exception.codigo, 'fuera_de_disponibilidad')

    def test_excepcion_vacia_reemplaza_y_cierra_horario_semanal(self):
        guardar_excepcion(self.engine, 'profesional', 'profesional-A', '2026-11-02', [])
        with self.assertRaises(ErrorAgenda) as error:
            self._crear()
        self.assertEqual(error.exception.codigo, 'fuera_de_disponibilidad')

    def test_bloqueo_de_cualquiera_de_los_recursos_rechaza_reserva(self):
        crear_bloqueo(
            self.engine, 'box', 'box-A', self.turno_hora_local[0], self.turno_hora_local[1])
        with self.assertRaises(ErrorAgenda) as error:
            self._crear()
        self.assertEqual(error.exception.codigo, 'fuera_de_disponibilidad')

    def test_bloqueo_del_profesional_rechaza_reserva(self):
        crear_bloqueo(
            self.engine, 'profesional', 'profesional-A',
            self.turno_hora_local[0], self.turno_hora_local[1])
        with self.assertRaises(ErrorAgenda) as error:
            self._crear()
        self.assertEqual(error.exception.codigo, 'fuera_de_disponibilidad')

    def test_rechaza_turno_que_cruza_medianoche_local(self):
        for tipo, recurso in (('profesional', 'profesional-A'), ('box', 'box-A')):
            guardar_horario(self.engine, tipo, recurso, {
                '1': [{'inicio': '22:00', 'fin': '24:00'}]})
        with self.assertRaises(ErrorAgenda) as error:
            self._crear(
                datetime(2026, 11, 3, 2, 30, tzinfo=timezone.utc),
                datetime(2026, 11, 3, 3, 30, tzinfo=timezone.utc))
        self.assertEqual(error.exception.codigo, 'fuera_de_disponibilidad')

    def test_acepta_turno_que_termina_exactamente_a_medianoche(self):
        for tipo, recurso in (('profesional', 'profesional-A'), ('box', 'box-A')):
            guardar_horario(self.engine, tipo, recurso, {
                '1': [{'inicio': '23:00', 'fin': '24:00'}]})

        turno = self._crear(
            datetime.fromisoformat('2026-11-02T23:00:00-03:00'),
            datetime.fromisoformat('2026-11-03T00:00:00-03:00'))

        self.assertEqual(turno.inicio, datetime(2026, 11, 3, 2, tzinfo=timezone.utc))
        self.assertEqual(turno.fin, datetime(2026, 11, 3, 3, tzinfo=timezone.utc))

    def test_carrera_cambio_primero_luego_reserva_usa_lock_sqlite(self):
        import odontologia.disponibilidad as disponibilidad

        dentro_cambio = Event()
        continuar_cambio = Event()
        resultado = []
        validar = disponibilidad._validar_turnos_existentes

        def pausar_cambio(*args, **kwargs):
            dentro_cambio.set()
            if not continuar_cambio.wait(5):
                raise AssertionError('Timeout esperando continuar mutación.')
            return validar(*args, **kwargs)

        def cambiar():
            try:
                guardar_horario(self.engine, 'profesional', 'profesional-A', {
                    '1': [{'inicio': '10:00', 'fin': '12:00'}]})
                resultado.append('cambio-confirmado')
            except Exception as exc:  # Se captura en el hilo para afirmar en el principal.
                resultado.append(exc)

        def reservar():
            try:
                self._crear()
                resultado.append('turno-confirmado')
            except ErrorAgenda as exc:
                resultado.append(exc.codigo)

        with patch.object(disponibilidad, '_validar_turnos_existentes', side_effect=pausar_cambio):
            hilo_cambio = Thread(target=cambiar)
            hilo_cambio.start()
            self.assertTrue(dentro_cambio.wait(5))
            hilo_turno = Thread(target=reservar)
            hilo_turno.start()
            continuar_cambio.set()
            hilo_cambio.join(5)
            hilo_turno.join(5)
        self.assertFalse(hilo_cambio.is_alive())
        self.assertFalse(hilo_turno.is_alive())
        self.assertEqual(resultado, ['cambio-confirmado', 'fuera_de_disponibilidad'])

    def test_carrera_reserva_primero_bloquea_cambio_horario_sqlite(self):
        import odontologia.disponibilidad as disponibilidad

        dentro_reserva = Event()
        continuar_reserva = Event()
        resultado = []
        validar = disponibilidad.validar_disponibilidad_sqlite

        def pausar_reserva(*args, **kwargs):
            dentro_reserva.set()
            if not continuar_reserva.wait(5):
                raise AssertionError('Timeout esperando continuar reserva.')
            return validar(*args, **kwargs)

        def reservar():
            try:
                self._crear()
                resultado.append('turno-confirmado')
            except Exception as exc:
                resultado.append(exc)

        def cambiar():
            try:
                guardar_horario(self.engine, 'profesional', 'profesional-A', {
                    '1': [{'inicio': '10:00', 'fin': '12:00'}]})
                resultado.append('cambio-confirmado')
            except ErrorDisponibilidad as exc:
                resultado.append(exc.codigo)

        with patch.object(disponibilidad, 'validar_disponibilidad_sqlite',
                          side_effect=pausar_reserva):
            hilo_turno = Thread(target=reservar)
            hilo_turno.start()
            self.assertTrue(dentro_reserva.wait(5))
            hilo_cambio = Thread(target=cambiar)
            hilo_cambio.start()
            continuar_reserva.set()
            hilo_turno.join(5)
            hilo_cambio.join(5)
        self.assertFalse(hilo_turno.is_alive())
        self.assertFalse(hilo_cambio.is_alive())
        self.assertEqual(resultado, ['turno-confirmado', 'turnos_afectados'])


if __name__ == '__main__':
    unittest.main()
