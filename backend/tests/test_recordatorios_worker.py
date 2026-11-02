from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.db.models import Paciente, Profesional, Box, Turno
from odontologia.recordatorios import programar_recordatorio_confirmacion


class RecordatoriosWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = create_engine(f'sqlite:///{self.ruta.as_posix()}')
        self.addCleanup(self.engine.dispose)
        self.ahora = datetime(2026, 11, 2, 18, tzinfo=timezone.utc)
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "UPDATE pacientes SET acepta_recordatorios=1 WHERE id='paciente-A'"))
            conexion.execute(text(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-worker', 'Profesional ficticio', 1)"))
            conexion.execute(text(
                "INSERT INTO boxes(id, nombre, activo) "
                "VALUES ('box-worker', 'Box ficticio', 1)"))

    def _crear_pendiente(self, sufijo: str, inicio: datetime | None = None,
                         paciente_id: str = 'paciente-A') -> int:
        inicio = inicio or (self.ahora + timedelta(hours=24))
        with self.engine.begin() as conexion:
            if paciente_id != 'paciente-A':
                conexion.execute(text(
                    'INSERT INTO pacientes(id, nombre, activo, acepta_recordatorios) '
                    'VALUES (:id, :nombre, 1, 1)'),
                    {'id': paciente_id, 'nombre': f'Paciente ficticio {sufijo}'})
            turno_id = conexion.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES (:paciente, 'profesional-worker', "
                "'box-worker', :inicio, :fin, 'confirmado', 1) RETURNING id"), {
                    'paciente': paciente_id,
                    'inicio': int(inicio.timestamp() // 60),
                    'fin': int((inicio + timedelta(minutes=30)).timestamp() // 60),
                }).scalar_one()
        with Session(self.engine) as session, session.begin():
            turno = session.get(Turno, turno_id)
            programar_recordatorio_confirmacion(
                session, turno, actor_id=None,
                ahora=self.ahora - timedelta(hours=24))
        return turno_id

    def test_procesa_vencido_elegible_y_no_modifica_turno(self):
        from odontologia.workers.recordatorios import procesar_recordatorios

        turno_id = self._crear_pendiente('elegible')
        resultado = procesar_recordatorios(self.engine, limite=10, ahora=self.ahora)

        with self.engine.connect() as conexion:
            estado_recordatorio = conexion.execute(text(
                'SELECT estado FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).scalar_one()
            estado_turno, version = conexion.execute(text(
                'SELECT estado, version FROM turnos WHERE id=:id'), {'id': turno_id}).one()
            eventos = conexion.execute(text(
                "SELECT action, resource_type, result FROM eventos_auditoria "
                "WHERE action='recordatorio.procesado'")).all()
        self.assertEqual(resultado, {'procesados': 1, 'invalidados': 0, 'fallidos': 0})
        self.assertEqual((estado_recordatorio, estado_turno, version),
                         ('procesado_simulado', 'confirmado', 1))
        self.assertEqual(eventos, [('recordatorio.procesado', 'recordatorio', 'confirmado')])

    def test_respeta_limite_y_no_toma_avisos_futuros(self):
        from odontologia.workers.recordatorios import procesar_recordatorios

        primeros = [self._crear_pendiente(str(indice)) for indice in range(3)]
        futuro = self._crear_pendiente(
            'futuro', inicio=self.ahora + timedelta(hours=25))
        resultado = procesar_recordatorios(self.engine, limite=2, ahora=self.ahora)

        with self.engine.connect() as conexion:
            estados = dict(conexion.execute(text(
                'SELECT turno_id, estado FROM recordatorios_outbox')).all())
        self.assertEqual(resultado['procesados'], 2)
        self.assertEqual(sum(estado == 'procesado_simulado' for estado in estados.values()), 2)
        self.assertEqual(sum(estado == 'pendiente' for estado in estados.values()), 2)
        self.assertEqual(sum(estados[turno_id] == 'procesado_simulado'
                             for turno_id in primeros), 2)
        self.assertEqual(sum(estados[turno_id] == 'pendiente'
                             for turno_id in primeros), 1)
        self.assertEqual(estados[futuro], 'pendiente')

    def test_invalida_si_cambio_consentimiento_estado_version_o_fecha(self):
        from odontologia.workers.recordatorios import procesar_recordatorios

        casos = ('consentimiento', 'estado', 'version', 'turno_pasado')
        turnos = {caso: self._crear_pendiente(caso, paciente_id=f'paciente-{caso}')
                  for caso in casos}
        with self.engine.begin() as conexion:
            conexion.execute(text(
                'UPDATE pacientes SET acepta_recordatorios=0 WHERE id=:id'),
                {'id': 'paciente-consentimiento'})
            conexion.execute(text(
                "UPDATE turnos SET estado='cancelado', version=2 WHERE id=:id"),
                {'id': turnos['estado']})
            conexion.execute(text(
                'UPDATE turnos SET version=2 WHERE id=:id'), {'id': turnos['version']})
            conexion.execute(text(
                'UPDATE turnos SET inicio_minuto=:inicio WHERE id=:id'), {
                    'inicio': int((self.ahora - timedelta(minutes=1)).timestamp() // 60),
                    'id': turnos['turno_pasado'],
                })

        resultado = procesar_recordatorios(self.engine, limite=20, ahora=self.ahora)
        with self.engine.connect() as conexion:
            estados = dict(conexion.execute(text(
                'SELECT turno_id, estado FROM recordatorios_outbox')).all())
        self.assertEqual(resultado['invalidados'], len(casos))
        for turno_id in turnos.values():
            self.assertEqual(estados[turno_id], 'invalidado')
        self.assertEqual(resultado['procesados'], 0)

    def test_fallo_de_auditoria_restaura_el_estado_pendiente(self):
        from odontologia.audit import ErrorAuditoria
        from odontologia.workers.recordatorios import procesar_recordatorios

        turno_id = self._crear_pendiente('auditoria')
        with patch('odontologia.workers.recordatorios.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            with self.assertRaises(ErrorAuditoria):
                procesar_recordatorios(self.engine, limite=1, ahora=self.ahora)
        with self.engine.connect() as conexion:
            estado = conexion.execute(text(
                'SELECT estado FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).scalar_one()
        self.assertEqual(estado, 'pendiente')

    def test_fallos_sinteticos_se_reintentan_hasta_tres_veces_y_terminan(self):
        from odontologia.workers.recordatorios import procesar_recordatorios

        turno_id = self._crear_pendiente('fallos')
        with patch('odontologia.workers.recordatorios._canal_simulado', return_value=False):
            for intento in range(1, 4):
                resultado = procesar_recordatorios(
                    self.engine, limite=1, ahora=self.ahora)
                self.assertEqual(resultado['fallidos'], 1)
                with self.engine.connect() as conexion:
                    estado, intentos = conexion.execute(text(
                        'SELECT estado, intentos FROM recordatorios_outbox '
                        'WHERE turno_id=:id'), {'id': turno_id}).one()
                self.assertEqual(intentos, intento)
                self.assertEqual(estado, 'fallido' if intento == 3 else 'pendiente')

        resultado = procesar_recordatorios(self.engine, limite=1, ahora=self.ahora)
        self.assertEqual(resultado, {'procesados': 0, 'invalidados': 0, 'fallidos': 0})

    def test_fallo_de_auditoria_revierte_intento_sintetico(self):
        from odontologia.audit import ErrorAuditoria
        from odontologia.workers.recordatorios import procesar_recordatorios

        turno_id = self._crear_pendiente('fallo-auditoria')
        with (
            patch('odontologia.workers.recordatorios._canal_simulado', return_value=False),
            patch('odontologia.workers.recordatorios.registrar_evento_session',
                  side_effect=ErrorAuditoria('fallo sintético')),
        ):
            with self.assertRaises(ErrorAuditoria):
                procesar_recordatorios(self.engine, limite=1, ahora=self.ahora)
        with self.engine.connect() as conexion:
            estado, intentos = conexion.execute(text(
                'SELECT estado, intentos FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).one()
        self.assertEqual((estado, intentos), ('pendiente', 0))


if __name__ == '__main__':
    unittest.main()
