from contextlib import closing
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest
from threading import Barrier, Thread
from unittest.mock import patch

from sqlalchemy import create_engine, text

from odontologia.auth.migraciones import migrar_sqlite
from odontologia.agenda import ErrorAgenda, inicializar_agenda
from odontologia.audit import ErrorAuditoria
from odontologia.disponibilidad import guardar_horario
from odontologia.agenda import crear_turno
from odontologia.turnos import transicionar_estado_turno


class CicloVidaTurnoTests(unittest.TestCase):
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
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto) VALUES ('paciente-A','profesional-A','box-A',29700000,29700030)"))
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.turno_id = conexion.execute('SELECT id FROM turnos').fetchone()[0]

    def _estado(self):
        with self.engine.connect() as conexion:
            return conexion.execute(
                text('SELECT estado FROM turnos WHERE id=:id'), {'id': self.turno_id}
            ).scalar_one()

    def _version(self):
        with self.engine.connect() as conexion:
            return conexion.execute(
                text('SELECT version FROM turnos WHERE id=:id'), {'id': self.turno_id}
            ).scalar_one()

    def test_transiciones_permitidas_persisten_estado(self):
        for destino in ('confirmado', 'atendido'):
            resultado = transicionar_estado_turno(
                self.engine, self.turno_id, destino, actor_id='usuario-admin')
            self.assertEqual(resultado.estado, destino)
            self.assertEqual(self._estado(), destino)
            if destino == 'confirmado':
                resultado = transicionar_estado_turno(
                    self.engine, self.turno_id, 'atendido', actor_id='usuario-admin')
                self.assertEqual(resultado.estado, 'atendido')
                self.assertEqual(self._estado(), 'atendido')
                break

    def test_transicion_desde_estado_terminal_rechaza_sin_mutar(self):
        transicionar_estado_turno(
            self.engine, self.turno_id, 'cancelado', actor_id='usuario-admin')
        with self.assertRaises(ErrorAgenda) as error:
            transicionar_estado_turno(
                self.engine, self.turno_id, 'confirmado', actor_id='usuario-admin')
        self.assertEqual(error.exception.codigo, 'transicion_invalida')
        self.assertEqual(self._estado(), 'cancelado')

    def test_reservado_no_puede_saltar_a_estado_terminal(self):
        with self.assertRaises(ErrorAgenda) as error:
            transicionar_estado_turno(
                self.engine, self.turno_id, 'atendido', actor_id='usuario-admin')
        self.assertEqual(error.exception.codigo, 'transicion_invalida')
        self.assertEqual(self._estado(), 'reservado')

    def test_confirmado_admite_ausente_o_cancelado(self):
        for destino in ('ausente', 'cancelado'):
            with self.subTest(destino=destino):
                with self.engine.begin() as conexion:
                    conexion.execute(text('UPDATE turnos SET estado="reservado" WHERE id=:id'),
                                     {'id': self.turno_id})
                transicionar_estado_turno(
                    self.engine, self.turno_id, 'confirmado', actor_id='usuario-admin')
                resultado = transicionar_estado_turno(
                    self.engine, self.turno_id, destino, actor_id='usuario-admin')
                self.assertEqual(resultado.estado, destino)

    def test_cancelacion_repetida_devuelve_estado_sin_auditar_de_nuevo(self):
        primera = transicionar_estado_turno(
            self.engine, self.turno_id, 'cancelado', actor_id='usuario-admin')
        repetida = transicionar_estado_turno(
            self.engine, self.turno_id, 'cancelado', actor_id='usuario-admin')
        self.assertEqual(primera.estado, 'cancelado')
        self.assertEqual(repetida, primera)
        with self.engine.connect() as conexion:
            eventos = conexion.execute(text(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='turno.estado_actualizado' "
                "AND resource_id=:id"), {'id': str(self.turno_id)}).scalar_one()
        self.assertEqual(eventos, 1)

    def test_transicion_efectiva_incrementa_version(self):
        self.assertEqual(self._version(), 1)
        transicionar_estado_turno(
            self.engine, self.turno_id, 'confirmado', actor_id='usuario-admin')
        self.assertEqual(self._version(), 2)
        transicionar_estado_turno(
            self.engine, self.turno_id, 'atendido', actor_id='usuario-admin')
        self.assertEqual(self._version(), 3)

    def test_cancelacion_idempotente_no_incrementa_version(self):
        transicionar_estado_turno(
            self.engine, self.turno_id, 'cancelado', actor_id='usuario-admin')
        version_cancelado = self._version()
        repetida = transicionar_estado_turno(
            self.engine, self.turno_id, 'cancelado', actor_id='usuario-admin')
        self.assertEqual(repetida.estado, 'cancelado')
        self.assertEqual(version_cancelado, 2)
        self.assertEqual(self._version(), version_cancelado)

    def test_fallo_de_auditoria_revierte_la_transicion(self):
        with patch('odontologia.turnos.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo de prueba')):
            with self.assertRaises(ErrorAgenda) as error:
                transicionar_estado_turno(
                    self.engine, self.turno_id, 'cancelado', actor_id='usuario-admin')
        self.assertEqual(error.exception.codigo, 'almacenamiento_error')
        self.assertEqual(self._estado(), 'reservado')

    def test_cancelacion_se_serializa_con_alta_del_mismo_intervalo(self):
        barrera = Barrier(2)
        resultados = []

        def cancelar():
            barrera.wait()
            resultados.append(('cancelar', transicionar_estado_turno(
                self.engine, self.turno_id, 'cancelado', actor_id='usuario-admin')))

        def reservar():
            barrera.wait()
            try:
                turno = crear_turno(
                    self.ruta, paciente_id='paciente-B', profesional_id='profesional-A',
                    box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T12:00:00+00:00'),
                    fin=datetime.fromisoformat('2026-11-02T12:30:00+00:00'))
                resultados.append(('reservar', turno))
            except ErrorAgenda as error:
                resultados.append(('reservar', error.codigo))

        hilos = [Thread(target=cancelar), Thread(target=reservar)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(5)
        self.assertTrue(all(not hilo.is_alive() for hilo in hilos))
        alta = next(resultado for nombre, resultado in resultados if nombre == 'reservar')
        self.assertEqual(self._estado(), 'cancelado')
        if not isinstance(alta, str):
            self.assertEqual(alta.paciente_id, 'paciente-B')
        else:
            self.assertEqual(alta, 'conflicto_profesional')

    def test_timeout_de_lock_sqlite_no_modifica_turno(self):
        with closing(sqlite3.connect(self.ruta, isolation_level=None)) as bloqueo:
            bloqueo.execute('BEGIN IMMEDIATE')
            try:
                with self.assertRaises(ErrorAgenda) as error:
                    transicionar_estado_turno(
                        self.engine, self.turno_id, 'cancelado', actor_id='usuario-admin',
                        timeout_segundos=0.05)
                self.assertEqual(error.exception.codigo, 'agenda_ocupada')
            finally:
                bloqueo.execute('ROLLBACK')
        self.assertEqual(self._estado(), 'reservado')


if __name__ == '__main__':
    unittest.main()
