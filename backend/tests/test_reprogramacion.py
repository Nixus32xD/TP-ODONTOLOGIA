from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Thread
import sqlite3
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text

from odontologia.agenda import ErrorAgenda, crear_turno, inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.audit import ErrorAuditoria
from odontologia.disponibilidad import crear_bloqueo, guardar_horario
from odontologia.turnos import transicionar_estado_turno


class RechazosReprogramacionTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = create_engine(f'sqlite:///{self.ruta.as_posix()}')
        self.addCleanup(self.engine.dispose)
        abierto = {'1': [{'inicio': '08:00', 'fin': '12:00'}]}
        for tipo, recurso in (
            ('profesional', 'profesional-A'), ('profesional', 'profesional-B'),
            ('box', 'box-A'), ('box', 'box-B'),
        ):
            if recurso != 'profesional-B':
                guardar_horario(self.engine, tipo, recurso, abierto)
        self.turno = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))

    def _snapshot(self):
        with self.engine.connect() as conexion:
            turno = conexion.execute(text(
                'SELECT paciente_id, profesional_id, box_id, inicio_minuto, fin_minuto, '
                'estado, version FROM turnos WHERE id=:id'), {'id': self.turno.id}).one()
            eventos = conexion.execute(text(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='turno.reprogramado' "
                'AND resource_id=:id'), {'id': str(self.turno.id)}).scalar_one()
            return tuple(turno), eventos

    def _solicitar(self, *, actor_id=None, **cambios):
        from odontologia.reprogramacion import reprogramar_turno

        solicitud = {
            'version_esperada': 1,
            'inicio': datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
            'fin': datetime.fromisoformat('2026-11-02T10:30:00-03:00'),
            'profesional_id': 'profesional-A', 'box_id': 'box-A',
        }
        solicitud.update(cambios)
        return reprogramar_turno(
            self.engine, self.turno.id, **solicitud, actor_id=actor_id)

    def _rechazo_preserva(self, codigo, **cambios):
        anterior = self._snapshot()
        with self.assertRaises(ErrorAgenda) as error:
            self._solicitar(**cambios)
        self.assertEqual(error.exception.codigo, codigo)
        self.assertEqual(self._snapshot(), anterior)

    def test_version_obsoleta_rechaza_sin_mutar(self):
        self._rechazo_preserva('version_desactualizada', version_esperada=7)

    def test_turno_terminal_rechaza_sin_mutar(self):
        transicionar_estado_turno(
            self.engine, self.turno.id, 'cancelado', actor_id=None)
        self._rechazo_preserva('turno_no_reprogramable', version_esperada=2)

    def test_paciente_inactivo_rechaza_sin_mutar(self):
        with self.engine.begin() as conexion:
            conexion.execute(text("UPDATE pacientes SET activo=0 WHERE id='paciente-A'"))
        self._rechazo_preserva('recurso_inactivo')

    def test_profesional_destino_inactivo_rechaza_sin_mutar(self):
        with self.engine.begin() as conexion:
            conexion.execute(text("UPDATE profesionales SET activo=0 WHERE id='profesional-A'"))
        self._rechazo_preserva('recurso_inactivo')

    def test_duracion_distinta_rechaza_sin_mutar(self):
        self._rechazo_preserva(
            'entrada_invalida', fin=datetime.fromisoformat('2026-11-02T10:45:00-03:00'))

    def test_cruce_de_medianoche_rechaza_sin_mutar(self):
        self._rechazo_preserva(
            'fuera_de_disponibilidad',
            inicio=datetime.fromisoformat('2026-11-02T23:45:00-03:00'),
            fin=datetime.fromisoformat('2026-11-03T00:15:00-03:00'))

    def test_destino_sin_horario_rechaza_sin_mutar(self):
        self._rechazo_preserva('fuera_de_disponibilidad', profesional_id='profesional-B')

    def test_bloqueo_de_destino_rechaza_sin_mutar(self):
        crear_bloqueo(
            self.engine, 'profesional', 'profesional-A',
            datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
            datetime.fromisoformat('2026-11-02T11:00:00-03:00'))
        self._rechazo_preserva('fuera_de_disponibilidad')

    def test_reprogramacion_valida_cambia_recursos_y_conserva_paciente_duracion_estado(self):
        guardar_horario(self.engine, 'profesional', 'profesional-B', {
            '1': [{'inicio': '08:00', 'fin': '12:00'}]})
        resultado = self._solicitar(
            actor_id='usuario-admin', profesional_id='profesional-B', box_id='box-B')
        self.assertEqual(
            (resultado.paciente_id, resultado.profesional_id, resultado.box_id,
             resultado.inicio, resultado.fin, resultado.estado, resultado.version),
            ('paciente-A', 'profesional-B', 'box-B',
             datetime.fromisoformat('2026-11-02T13:00:00+00:00'),
             datetime.fromisoformat('2026-11-02T13:30:00+00:00'), 'reservado', 2))
        with self.engine.connect() as conexion:
            auditoria = conexion.execute(text(
                "SELECT actor_id, action, resource_type, resource_id, result "
                "FROM eventos_auditoria WHERE action='turno.reprogramado'"
            )).one()
        self.assertEqual(tuple(auditoria), (
            'usuario-admin', 'turno.reprogramado', 'turno', str(self.turno.id), 'confirmado'))

    def test_reprogramacion_invalida_version_anterior_y_programa_la_nueva(self):
        ahora = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        inicio_original = datetime.fromisoformat('2026-11-09T09:00:00-03:00')
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "UPDATE pacientes SET acepta_recordatorios=1 WHERE id='paciente-A'"))
            conexion.execute(text(
                'UPDATE turnos SET inicio_minuto=:inicio, fin_minuto=:fin WHERE id=:id'), {
                    'inicio': int(inicio_original.timestamp() // 60),
                    'fin': int((inicio_original + timedelta(minutes=30)).timestamp() // 60),
                    'id': self.turno.id,
                })
        transicionar_estado_turno(
            self.engine, self.turno.id, 'confirmado', actor_id='usuario-admin', ahora=ahora)

        from odontologia.reprogramacion import reprogramar_turno
        nuevo_inicio = datetime.fromisoformat('2026-11-16T10:00:00-03:00')
        resultado = reprogramar_turno(
            self.engine, self.turno.id, version_esperada=2,
            inicio=nuevo_inicio, fin=nuevo_inicio + timedelta(minutes=30),
            profesional_id='profesional-A', box_id='box-A',
            actor_id='usuario-admin', ahora=ahora)

        with self.engine.connect() as conexion:
            recordatorios = conexion.execute(text(
                'SELECT turno_version, estado, idempotency_key FROM recordatorios_outbox '
                'WHERE turno_id=:id ORDER BY turno_version'), {'id': self.turno.id}).all()
            acciones = conexion.execute(text(
                "SELECT action FROM eventos_auditoria WHERE resource_type='recordatorio' "
                'ORDER BY created_at, id')).scalars().all()
        self.assertEqual((resultado.estado, resultado.version), ('confirmado', 3))
        self.assertEqual([tuple(fila[:2]) for fila in recordatorios], [
            (2, 'invalidado'), (3, 'pendiente')])
        self.assertTrue(recordatorios[0].idempotency_key.endswith(':generacion:1'))
        self.assertTrue(recordatorios[1].idempotency_key.endswith(':generacion:1'))
        self.assertEqual(acciones, ['recordatorio.programado',
                                    'recordatorio.invalidado',
                                    'recordatorio.programado'])

    def test_reprogramacion_a_menos_de_24_horas_invalida_sin_nuevo_pendiente(self):
        ahora = datetime(2026, 11, 8, 12, tzinfo=timezone.utc)
        inicio_original = datetime.fromisoformat('2026-11-16T09:00:00-03:00')
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "UPDATE pacientes SET acepta_recordatorios=1 WHERE id='paciente-A'"))
            conexion.execute(text(
                'UPDATE turnos SET inicio_minuto=:inicio, fin_minuto=:fin WHERE id=:id'), {
                    'inicio': int(inicio_original.timestamp() // 60),
                    'fin': int((inicio_original + timedelta(minutes=30)).timestamp() // 60),
                    'id': self.turno.id,
                })
        transicionar_estado_turno(
            self.engine, self.turno.id, 'confirmado', actor_id='usuario-admin', ahora=ahora)

        from odontologia.reprogramacion import reprogramar_turno
        nuevo_inicio = datetime.fromisoformat('2026-11-09T09:00:00-03:00')
        resultado = reprogramar_turno(
            self.engine, self.turno.id, version_esperada=2,
            inicio=nuevo_inicio, fin=nuevo_inicio + timedelta(minutes=30),
            profesional_id='profesional-A', box_id='box-A',
            actor_id='usuario-admin', ahora=ahora)

        with self.engine.connect() as conexion:
            recordatorios = conexion.execute(text(
                'SELECT turno_version, estado FROM recordatorios_outbox '
                'WHERE turno_id=:id ORDER BY turno_version'), {'id': self.turno.id}).all()
        self.assertEqual((resultado.estado, resultado.version), ('confirmado', 3))
        self.assertEqual([tuple(fila) for fila in recordatorios], [(2, 'invalidado')])

    def test_fallo_de_auditoria_al_invalidar_revierte_reprogramacion(self):
        ahora = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        inicio_original = datetime.fromisoformat('2026-11-09T09:00:00-03:00')
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "UPDATE pacientes SET acepta_recordatorios=1 WHERE id='paciente-A'"))
            conexion.execute(text(
                'UPDATE turnos SET inicio_minuto=:inicio, fin_minuto=:fin WHERE id=:id'), {
                    'inicio': int(inicio_original.timestamp() // 60),
                    'fin': int((inicio_original + timedelta(minutes=30)).timestamp() // 60),
                    'id': self.turno.id,
                })
        transicionar_estado_turno(
            self.engine, self.turno.id, 'confirmado', actor_id='usuario-admin', ahora=ahora)
        antes = self._snapshot()
        nuevo_inicio = datetime.fromisoformat('2026-11-16T10:00:00-03:00')
        with patch('odontologia.recordatorios.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo de auditoría sintético')):
            from odontologia.reprogramacion import reprogramar_turno
            with self.assertRaises(ErrorAgenda) as error:
                reprogramar_turno(
                    self.engine, self.turno.id, version_esperada=2,
                    inicio=nuevo_inicio, fin=nuevo_inicio + timedelta(minutes=30),
                    profesional_id='profesional-A', box_id='box-A',
                    actor_id='usuario-admin', ahora=ahora)
        with self.engine.connect() as conexion:
            recordatorio_estado = conexion.execute(text(
                'SELECT estado FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': self.turno.id}).scalar_one()
        self.assertEqual(error.exception.codigo, 'almacenamiento_error')
        self.assertEqual(self._snapshot(), antes)
        self.assertEqual(recordatorio_estado, 'pendiente')

    def test_reprogramacion_conflicto_por_profesional_preserva_turno(self):
        crear_turno(
            self.ruta, paciente_id='paciente-B', profesional_id='profesional-A',
            box_id='box-B', inicio=datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T10:30:00-03:00'))
        self._rechazo_preserva('conflicto_profesional')

    def test_reprogramacion_conflicto_por_box_preserva_turno(self):
        guardar_horario(self.engine, 'profesional', 'profesional-B', {
            '1': [{'inicio': '08:00', 'fin': '12:00'}]})
        crear_turno(
            self.ruta, paciente_id='paciente-B', profesional_id='profesional-B',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T10:30:00-03:00'))
        self._rechazo_preserva('conflicto_box')

    def test_reprogramar_mismo_intervalo_excluye_el_turno_propio(self):
        resultado = self._solicitar(
            actor_id='usuario-admin', inicio=datetime.fromisoformat(
                '2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))
        self.assertEqual(resultado.version, 2)
        self.assertEqual((resultado.profesional_id, resultado.box_id),
                         ('profesional-A', 'box-A'))

    def test_mismo_paciente_en_recursos_distintos_no_impide_reprogramar(self):
        guardar_horario(self.engine, 'profesional', 'profesional-B', {
            '1': [{'inicio': '08:00', 'fin': '12:00'}]})
        crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T10:30:00-03:00'))
        resultado = self._solicitar(
            actor_id='usuario-admin', profesional_id='profesional-B', box_id='box-B')
        self.assertEqual((resultado.paciente_id, resultado.profesional_id,
                          resultado.box_id, resultado.version),
                         ('paciente-A', 'profesional-B', 'box-B', 2))

    def test_dos_reprogramaciones_con_misma_version_confirman_solo_una(self):
        guardar_horario(self.engine, 'profesional', 'profesional-B', {
            '1': [{'inicio': '08:00', 'fin': '12:00'}]})
        barrera = Barrier(2)
        resultados = []

        def ejecutar(hora):
            barrera.wait()
            try:
                resultado = self._solicitar(
                    actor_id='usuario-admin', profesional_id='profesional-B',
                    box_id='box-B',
                    inicio=datetime.fromisoformat(f'2026-11-02T{hora}:00-03:00'),
                    fin=datetime.fromisoformat(
                        f'2026-11-02T{int(hora[:2]):02d}:{int(hora[3:])+30:02d}-03:00'))
                resultados.append(resultado)
            except ErrorAgenda as error:
                resultados.append(error.codigo)

        hilos = [Thread(target=ejecutar, args=(hora,)) for hora in ('10:00', '11:00')]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(5)
        self.assertTrue(all(not hilo.is_alive() for hilo in hilos))
        self.assertEqual(sum(not isinstance(valor, str) for valor in resultados), 1)
        self.assertEqual(resultados.count('version_desactualizada'), 1)
        fila, eventos = self._snapshot()
        self.assertEqual(fila[1], 'profesional-B')
        self.assertEqual(fila[2], 'box-B')
        self.assertEqual(fila[6], 2)
        with self.engine.connect() as conexion:
            cantidad = conexion.execute(text(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='turno.reprogramado' "
                'AND resource_id=:id'), {'id': str(self.turno.id)}).scalar_one()
        self.assertEqual(eventos, 1)
        self.assertEqual(cantidad, 1)

    def test_fallo_de_auditoria_revierte_intervalo_recursos_y_version(self):
        guardar_horario(self.engine, 'profesional', 'profesional-B', {
            '1': [{'inicio': '08:00', 'fin': '12:00'}]})
        anterior = self._snapshot()
        with patch('odontologia.reprogramacion.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo de prueba')):
            with self.assertRaises(ErrorAgenda) as error:
                self._solicitar(
                    actor_id='usuario-admin', profesional_id='profesional-B', box_id='box-B')
        self.assertEqual(error.exception.codigo, 'almacenamiento_error')
        self.assertEqual(self._snapshot(), anterior)

    def test_reprogramar_hasta_medianoche_exacta_cabe_en_tramo_23_a_24(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                guardar_horario(engine, 'profesional', 'profesional-A', {
                    '1': [{'inicio': '23:00', 'fin': '24:00'}]})
                guardar_horario(engine, 'box', 'box-A', {
                    '1': [{'inicio': '23:00', 'fin': '24:00'}]})
                horario_fuente = {'1': [{'inicio': '08:00', 'fin': '12:00'}]}
                guardar_horario(engine, 'profesional', 'profesional-B', horario_fuente)
                guardar_horario(engine, 'box', 'box-B', horario_fuente)
                turno = crear_turno(
                    ruta, paciente_id='paciente-A', profesional_id='profesional-B',
                    box_id='box-B',
                    inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
                    fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))
                from odontologia.reprogramacion import reprogramar_turno

                resultado = reprogramar_turno(
                    engine, turno.id, version_esperada=1,
                    inicio=datetime.fromisoformat('2026-11-02T23:30:00-03:00'),
                    fin=datetime.fromisoformat('2026-11-03T00:00:00-03:00'),
                    profesional_id='profesional-A', box_id='box-A', actor_id=None)
                self.assertEqual(resultado.fin,
                                 datetime.fromisoformat('2026-11-03T03:00:00+00:00'))
                self.assertEqual((resultado.estado, resultado.version), ('reservado', 2))
            finally:
                engine.dispose()


if __name__ == '__main__':
    unittest.main()
