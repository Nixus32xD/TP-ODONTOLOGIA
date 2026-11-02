from contextlib import closing
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador
from odontologia.audit import ErrorAuditoria
from sqlalchemy import text
from odontologia.pacientes import (
    ErrorPacientes, actualizar_paciente, crear_paciente, listar_pacientes,
    obtener_paciente,
)


class PacientesServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        admin = crear_primer_administrador(
            self.engine, 'admin.one', 'frase-larga-segura-2026')
        self.actor_id = admin['id']

    def test_crear_y_listar_con_datos_minimos_y_homonimos(self):
        uno = crear_paciente(
            self.engine, '  Ana   Pérez  ', '+54 (261) 555-0101', actor_id=self.actor_id)
        dos = crear_paciente(self.engine, 'Ana Pérez', None, actor_id=self.actor_id)

        self.assertEqual(uno['nombre'], 'Ana Pérez')
        self.assertEqual(uno['telefono'], '+54 (261) 555-0101')
        self.assertTrue(uno['activo'])
        self.assertNotEqual(uno['id'], dos['id'])
        self.assertEqual(len(listar_pacientes(self.engine, limit=1, offset=0)), 1)
        self.assertEqual(obtener_paciente(self.engine, uno['id']), uno)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            evento = conexion.execute(
                "SELECT action, resource_type, resource_id FROM eventos_auditoria "
                "WHERE action='paciente.creado' ORDER BY id LIMIT 1").fetchone()
        self.assertEqual(evento, ('paciente.creado', 'paciente', uno['id']))

    def test_consentimiento_empieza_desactivado_y_cambio_es_explicito_y_auditado(self):
        paciente = crear_paciente(self.engine, 'Paciente ficticio', actor_id=self.actor_id)

        self.assertFalse(paciente['acepta_recordatorios'])
        actualizado = actualizar_paciente(
            self.engine, paciente['id'], {'acepta_recordatorios': True},
            actor_id=self.actor_id)

        self.assertTrue(actualizado['acepta_recordatorios'])
        with closing(sqlite3.connect(self.ruta)) as conexion:
            eventos = conexion.execute(
                "SELECT action, resource_type, resource_id FROM eventos_auditoria "
                "WHERE resource_id=? ORDER BY id", (paciente['id'],)).fetchall()
        self.assertEqual(eventos[-1], ('paciente.actualizado', 'paciente', paciente['id']))
        con_consentimiento = crear_paciente(
            self.engine, 'Paciente con consentimiento explícito',
            acepta_recordatorios=True, actor_id=self.actor_id)
        self.assertTrue(con_consentimiento['acepta_recordatorios'])
        with self.assertRaises(ErrorPacientes):
            actualizar_paciente(
                self.engine, paciente['id'], {'acepta_recordatorios': 1},
                actor_id=self.actor_id)

    def test_consentimiento_en_turnos_confirmados_programa_y_luego_invalida(self):
        paciente = crear_paciente(self.engine, 'Paciente ficticio', actor_id=self.actor_id)
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-consentimiento', 'Profesional ficticio', 1)"))
            conexion.execute(text(
                "INSERT INTO boxes(id, nombre, activo) "
                "VALUES ('box-consentimiento', 'Box ficticio', 1)"))
            inicio = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)
            turno_id = conexion.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES (:paciente, 'profesional-consentimiento', "
                "'box-consentimiento', :inicio, :fin, 'confirmado', 1) RETURNING id"), {
                    'paciente': paciente['id'],
                    'inicio': int(inicio.timestamp() // 60),
                    'fin': int((inicio + timedelta(minutes=30)).timestamp() // 60),
                }).scalar_one()
        ahora = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)

        actualizar_paciente(
            self.engine, paciente['id'], {'acepta_recordatorios': True},
            actor_id=self.actor_id, ahora=ahora)
        with self.engine.connect() as conexion:
            estado_al_habilitar = conexion.execute(text(
                'SELECT turno_version, estado FROM recordatorios_outbox '
                'WHERE turno_id=:id'), {'id': turno_id}).one()

        actualizar_paciente(
            self.engine, paciente['id'], {'acepta_recordatorios': False},
            actor_id=self.actor_id, ahora=ahora + timedelta(hours=1))
        with self.engine.connect() as conexion:
            estado_al_retirar = conexion.execute(text(
                'SELECT estado FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).scalar_one()
        self.assertEqual(tuple(estado_al_habilitar), (1, 'pendiente'))
        self.assertEqual(estado_al_retirar, 'invalidado')

    def test_habilitaciones_concurrentes_crean_un_solo_recordatorio(self):
        paciente = crear_paciente(self.engine, 'Paciente ficticio', actor_id=self.actor_id)
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-concurrente', 'Profesional ficticio', 1)"))
            conexion.execute(text(
                "INSERT INTO boxes(id, nombre, activo) "
                "VALUES ('box-concurrente', 'Box ficticio', 1)"))
            inicio = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)
            turno_id = conexion.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES (:paciente, 'profesional-concurrente', "
                "'box-concurrente', :inicio, :fin, 'confirmado', 1) RETURNING id"), {
                    'paciente': paciente['id'],
                    'inicio': int(inicio.timestamp() // 60),
                    'fin': int((inicio + timedelta(minutes=30)).timestamp() // 60),
                }).scalar_one()
        ahora = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)

        def habilitar():
            return actualizar_paciente(
                self.engine, paciente['id'], {'acepta_recordatorios': True},
                actor_id=self.actor_id, ahora=ahora)

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(lambda _: habilitar(), range(2)))
        self.assertTrue(all(resultado['acepta_recordatorios'] for resultado in resultados))
        with self.engine.connect() as conexion:
            recordatorios = conexion.execute(text(
                'SELECT turno_version, estado, idempotency_key FROM recordatorios_outbox '
                'WHERE turno_id=:id'), {'id': turno_id}).all()
        self.assertEqual(len(recordatorios), 1)
        self.assertEqual(tuple(recordatorios[0][:2]), (1, 'pendiente'))
        self.assertTrue(recordatorios[0].idempotency_key.endswith(':generacion:1'))

    def test_fallo_de_auditoria_al_retirar_revierte_consentimiento_y_outbox(self):
        paciente = crear_paciente(self.engine, 'Paciente ficticio', actor_id=self.actor_id)
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-rollback', 'Profesional ficticio', 1)"))
            conexion.execute(text(
                "INSERT INTO boxes(id, nombre, activo) "
                "VALUES ('box-rollback', 'Box ficticio', 1)"))
            inicio = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)
            turno_id = conexion.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES (:paciente, 'profesional-rollback', "
                "'box-rollback', :inicio, :fin, 'confirmado', 1) RETURNING id"), {
                    'paciente': paciente['id'],
                    'inicio': int(inicio.timestamp() // 60),
                    'fin': int((inicio + timedelta(minutes=30)).timestamp() // 60),
                }).scalar_one()
        ahora = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        actualizar_paciente(
            self.engine, paciente['id'], {'acepta_recordatorios': True},
            actor_id=self.actor_id, ahora=ahora)

        with patch('odontologia.recordatorios.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            with self.assertRaises(ErrorPacientes):
                actualizar_paciente(
                    self.engine, paciente['id'], {'acepta_recordatorios': False},
                    actor_id=self.actor_id, ahora=ahora + timedelta(hours=1))

        self.assertTrue(obtener_paciente(
            self.engine, paciente['id'])['acepta_recordatorios'])
        with self.engine.connect() as conexion:
            estado = conexion.execute(text(
                'SELECT estado FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).scalar_one()
        self.assertEqual(estado, 'pendiente')

    def test_falla_auditoria_restaura_consentimiento_anterior(self):
        paciente = crear_paciente(self.engine, 'Paciente ficticio', actor_id=self.actor_id)
        actualizar_paciente(
            self.engine, paciente['id'], {'acepta_recordatorios': True},
            actor_id=self.actor_id)

        with patch('odontologia.pacientes.registrar_evento_session', side_effect=ErrorAuditoria):
            with self.assertRaises(ErrorPacientes):
                actualizar_paciente(
                    self.engine, paciente['id'], {'acepta_recordatorios': False},
                    actor_id=self.actor_id)

        self.assertTrue(obtener_paciente(self.engine, paciente['id'])['acepta_recordatorios'])

    def test_validacion_de_nombre_telefono_y_paginacion(self):
        for nombre, telefono in (
                ('   ', None), ('x' * 121, None), ('Paciente\x00 oculto', None),
                ('Paciente', 'abc1234567'),
                ('Paciente', '12345'), ('Paciente', '+1+2345678')):
            with self.subTest(nombre=nombre, telefono=telefono):
                with self.assertRaises(ErrorPacientes) as contexto:
                    crear_paciente(self.engine, nombre, telefono, actor_id=self.actor_id)
                self.assertEqual(contexto.exception.estado, 422)

        for params in ({'limit': 101}, {'limit': 0}, {'offset': -1}):
            with self.subTest(params=params), self.assertRaises(ErrorPacientes):
                listar_pacientes(self.engine, **params)

    def test_actualizacion_baja_y_reactivacion_conservan_ficha(self):
        paciente = crear_paciente(self.engine, 'Paciente ficticio', None, actor_id=self.actor_id)
        actualizado = actualizar_paciente(
            self.engine, paciente['id'], {'nombre': 'Nombre actualizado', 'telefono': '2615550101'},
            actor_id=self.actor_id)
        inactivo = actualizar_paciente(
            self.engine, paciente['id'], {'activo': False}, actor_id=self.actor_id)
        reactivado = actualizar_paciente(
            self.engine, paciente['id'], {'activo': True}, actor_id=self.actor_id)

        self.assertEqual(actualizado['nombre'], 'Nombre actualizado')
        self.assertEqual(inactivo['telefono'], '2615550101')
        self.assertFalse(inactivo['activo'])
        self.assertTrue(reactivado['activo'])
        self.assertEqual(obtener_paciente(self.engine, paciente['id']), reactivado)

    def test_fallo_de_auditoria_revierte_alta_y_actualizacion(self):
        with patch('odontologia.pacientes.registrar_evento_session', side_effect=ErrorAuditoria):
            with self.assertRaises(ErrorPacientes):
                crear_paciente(self.engine, 'No guardar', None, actor_id=self.actor_id)

        self.assertEqual(len(listar_pacientes(self.engine)), 2)
        paciente = crear_paciente(self.engine, 'Ficha original', None, actor_id=self.actor_id)
        with patch('odontologia.pacientes.registrar_evento_session', side_effect=ErrorAuditoria):
            with self.assertRaises(ErrorPacientes):
                actualizar_paciente(
                    self.engine, paciente['id'], {'nombre': 'Cambio sin auditoría'},
                    actor_id=self.actor_id)
        self.assertEqual(obtener_paciente(self.engine, paciente['id'])['nombre'], 'Ficha original')

    def test_paciente_inexistente_devuelve_error_404(self):
        with self.assertRaises(ErrorPacientes) as contexto:
            obtener_paciente(self.engine, 'no-existe')
        self.assertEqual(contexto.exception.estado, 404)


if __name__ == '__main__':
    unittest.main()
