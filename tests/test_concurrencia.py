"""Procesos reales Windows spawn sobre un mismo archivo temporal local."""

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import multiprocessing
import os
import sqlite3
import tempfile
import unittest

from odontologia import ErrorAgenda, crear_turno, inicializar_agenda


def solicitar_turno(ruta, profesional, box, preparados, salida, inicio):
    preparados.put(os.getpid())
    if not inicio.wait(10):
        raise RuntimeError('No se recibió la señal de inicio')
    try:
        turno = crear_turno(ruta, paciente_id='paciente-A', profesional_id=profesional, box_id=box,
                            inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                            fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc), timeout_segundos=5.0)
        salida.put(('ok', turno.id))
    except ErrorAgenda as exc:
        salida.put(('error', exc.codigo))


class ConcurrenciaTests(unittest.TestCase):
    def competir(self, recursos, esperado):
        contexto = multiprocessing.get_context('spawn')
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            preparados, salida = contexto.Queue(), contexto.Queue()
            inicio = contexto.Event()
            procesos = [contexto.Process(target=solicitar_turno,
                        args=(str(ruta), profesional, box, preparados, salida, inicio))
                        for profesional, box in recursos]
            try:
                for proceso in procesos:
                    proceso.start()
                pids = [preparados.get(timeout=15), preparados.get(timeout=15)]
                self.assertEqual(len(set(pids)), 2)
                self.assertNotIn(os.getpid(), pids)
                inicio.set()
                resultados = [salida.get(timeout=15), salida.get(timeout=15)]
                for proceso in procesos:
                    proceso.join(timeout=15)
                    self.assertFalse(proceso.is_alive())
                    self.assertEqual(proceso.exitcode, 0)
                self.assertEqual(sorted(r[0] for r in resultados), sorted(esperado))
                with closing(sqlite3.connect(ruta)) as conexion:
                    filas = conexion.execute('SELECT id FROM turnos').fetchall()
                self.assertEqual(len(filas), sum(tipo == 'ok' for tipo in esperado))
                return resultados
            finally:
                inicio.set()
                for proceso in procesos:
                    if proceso.is_alive():
                        proceso.terminate()
                        proceso.join(timeout=5)
                    if proceso.exitcode is not None:
                        proceso.close()
                for cola in [preparados, salida]:
                    cola.close()
                    cola.join_thread()

    def test_dos_procesos_profesional(self):
        for repeticion in range(3):
            with self.subTest(repeticion=repeticion):
                resultados = self.competir([('profesional-A', 'box-A'), ('profesional-A', 'box-B')],
                                           ['ok', 'error'])
                self.assertEqual([valor for tipo, valor in resultados if tipo == 'error'], ['conflicto_profesional'])

    def test_dos_procesos_box(self):
        for repeticion in range(3):
            with self.subTest(repeticion=repeticion):
                resultados = self.competir([('profesional-A', 'box-A'), ('profesional-B', 'box-A')],
                                           ['ok', 'error'])
                self.assertEqual([valor for tipo, valor in resultados if tipo == 'error'], ['conflicto_box'])

    def test_dos_procesos_recursos_distintos(self):
        self.competir([('profesional-A', 'box-A'), ('profesional-B', 'box-B')], ['ok', 'ok'])


if __name__ == '__main__':
    unittest.main()
