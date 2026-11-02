"""Integración C-18 de reservas sintéticas contra PostgreSQL aislado."""
from datetime import datetime, time, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import unittest
from threading import Barrier
from uuid import uuid4
from zoneinfo import ZoneInfo

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from odontologia.auth.usuarios import crear_usuario
from odontologia.disponibilidad import guardar_horario
from odontologia.portal_paciente import (
    cancelar_turno_portal,
    listar_turnos_portal,
    reprogramar_turno_portal,
    reservar_turno_paciente,
)
from odontologia.db.models import Box, Paciente, Profesional
from sqlalchemy.orm import Session


class PortalPacientePostgreSQLIntegracionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        if (base_url.host not in ('127.0.0.1', 'localhost', '::1')
                or base_url.port != 55432
                or not (base_url.database or '').lower().endswith('_test')):
            raise unittest.SkipTest('C-18 requiere DB *_test en loopback:55432.')
        cls.schema = f'c18_portal_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {cls.schema}'))
        cls.url = str(base_url.update_query_dict({'options': f'-csearch_path={cls.schema}'}))
        cls.engine = create_engine(cls.url, pool_pre_ping=True)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        cls.previous_persistence = os.environ.get('ODONTOLOGIA_PERSISTENCIA')
        os.environ['DATABASE_URL'] = cls.url
        os.environ['ODONTOLOGIA_PERSISTENCIA'] = 'postgresql'
        config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        config.set_main_option('script_location', str(Path(__file__).parents[1] / 'alembic'))
        config.config_file_name = None
        command.upgrade(config, 'head')

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, 'root_engine'):
            return
        cls.engine.dispose()
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
        cls.root_engine.dispose()
        for name, value in (
                ('DATABASE_URL', cls.previous_database_url),
                ('ODONTOLOGIA_PERSISTENCIA', cls.previous_persistence)):
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_reserva_reprograma_y_cancela_atomicos_con_auditoria(self):
        sufijo = uuid4().hex[:12]
        paciente_id, profesional_id, box_id = (
            f'pac-{sufijo}', f'prof-{sufijo}', f'box-{sufijo}')
        actor_id = None
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id=paciente_id, nombre='Paciente sintético C18', activo=True,
                         acepta_recordatorios=False),
                Profesional(id=profesional_id, nombre='Profesional sintético', activo=True),
                Box(id=box_id, nombre='Box sintético', activo=True),
            ])
        cuenta = crear_usuario(
            self.engine, f'paciente.{sufijo}', 'frase-larga-segura-pg-2026',
            'paciente', paciente_id=paciente_id)
        actor_id = cuenta['id']
        horario = {str(dia): [{'inicio': '08:00', 'fin': '12:00'}]
                   for dia in range(1, 8)}
        guardar_horario(self.engine, 'profesional', profesional_id, horario)
        guardar_horario(self.engine, 'box', box_id, horario)

        zona = ZoneInfo('America/Argentina/Mendoza')
        ahora = datetime.now(zona).replace(second=0, microsecond=0)
        fecha_turno = ahora.date() + timedelta(days=3)
        inicio = datetime.combine(fecha_turno, time(9, 0), zona).isoformat()
        destino = datetime.combine(fecha_turno, time(10, 0), zona).isoformat()
        reservado = reservar_turno_paciente(
            self.engine, paciente_id=paciente_id, actor_id=actor_id,
            inicio=inicio, clave='pg-reserva', ahora=ahora)
        repetido = reservar_turno_paciente(
            self.engine, paciente_id=paciente_id, actor_id=actor_id,
            inicio=inicio, clave='pg-reserva', ahora=ahora)
        self.assertEqual(reservado, repetido)
        movido = reprogramar_turno_portal(
            self.engine, paciente_id=paciente_id, actor_id=actor_id,
            turno_id=reservado['turno_id'], version=reservado['version'],
            inicio=destino, clave='pg-reprograma', ahora=ahora)
        cancelado = cancelar_turno_portal(
            self.engine, paciente_id=paciente_id, actor_id=actor_id,
            turno_id=reservado['turno_id'], clave='pg-cancela', ahora=ahora)
        self.assertEqual((movido['version'], cancelado['estado']), (2, 'cancelado'))
        listado = listar_turnos_portal(
            self.engine, paciente_id=paciente_id, actor_id=actor_id)
        self.assertEqual(len(listado['items']), 1)
        self.assertEqual(listado['items'][0]['estado'], 'cancelado')
        with self.engine.connect() as connection:
            acciones = connection.execute(text(
                "SELECT action, resource_type, result FROM eventos_auditoria "
                "WHERE actor_id=:actor ORDER BY id"), {'actor': actor_id}).all()
        self.assertEqual(
            [fila[0] for fila in acciones if fila[0].startswith('portal.')],
            ['portal.turno.reservado', 'portal.turno.reprogramado',
             'portal.turno.cancelado', 'portal.turnos.consultados'])
        self.assertTrue(all(fila[1] in ('portal', 'turno') and fila[2] == 'confirmado'
                            for fila in acciones))

    def test_dos_pacientes_compiten_por_la_misma_franja_y_solo_uno_reserva(self):
        from odontologia.portal_paciente import ErrorPortalPaciente

        sufijo = uuid4().hex[:12]
        profesionales_id, box_id = f'prof-race-{sufijo}', f'box-race-{sufijo}'
        pacientes_id = [f'pac-race-{sufijo}-a', f'pac-race-{sufijo}-b']
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id=paciente_id, nombre='Paciente de carrera sintética', activo=True,
                         acepta_recordatorios=False) for paciente_id in pacientes_id
            ] + [Profesional(id=profesionales_id, nombre='Profesional sintético', activo=True),
                 Box(id=box_id, nombre='Box sintético', activo=True)])
        cuentas = [crear_usuario(
            self.engine, f'paciente.race.{sufijo}.{indice}',
            'frase-larga-segura-pg-2026', 'paciente', paciente_id=paciente_id)
            for indice, paciente_id in enumerate(pacientes_id)]
        horario = {str(dia): [{'inicio': '08:00', 'fin': '12:00'}]
                   for dia in range(1, 8)}
        guardar_horario(self.engine, 'profesional', profesionales_id, horario)
        guardar_horario(self.engine, 'box', box_id, horario)
        zona = ZoneInfo('America/Argentina/Mendoza')
        ahora = datetime.now(zona).replace(second=0, microsecond=0)
        fecha = ahora.date() + timedelta(days=4)
        inicio = datetime.combine(fecha, time(9, 0), zona).isoformat()
        barrera = Barrier(2)

        def reservar(indice):
            barrera.wait(timeout=3)
            try:
                return reservar_turno_paciente(
                    self.engine, paciente_id=pacientes_id[indice],
                    actor_id=cuentas[indice]['id'], inicio=inicio,
                    clave=f'race-{indice}', ahora=ahora)
            except ErrorPortalPaciente as exc:
                return exc.estado

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = [f.result(timeout=8) for f in (
                executor.submit(reservar, 0), executor.submit(reservar, 1))]
        self.assertEqual(sum(isinstance(resultado, dict) for resultado in resultados), 1)
        self.assertEqual(resultados.count(409), 1)

    def test_replays_vencidos_preservan_idempotencia_conflictos_y_titularidad(self):
        from odontologia.portal_paciente import ErrorPortalPaciente

        sufijo = uuid4().hex[:12]
        paciente_a, paciente_b = f'pac-replay-a-{sufijo}', f'pac-replay-b-{sufijo}'
        profesional_id, box_id = f'prof-replay-{sufijo}', f'box-replay-{sufijo}'
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id=paciente_a, nombre='Paciente replay A sintético', activo=True,
                         acepta_recordatorios=False),
                Paciente(id=paciente_b, nombre='Paciente replay B sintético', activo=True,
                         acepta_recordatorios=False),
                Profesional(id=profesional_id, nombre='Profesional replay sintético', activo=True),
                Box(id=box_id, nombre='Box replay sintético', activo=True),
            ])
        cuentas = [crear_usuario(
            self.engine, f'paciente.replay.{sufijo}.{letra}',
            'frase-larga-segura-pg-2026', 'paciente', paciente_id=paciente_id)
            for letra, paciente_id in (('a', paciente_a), ('b', paciente_b))]
        horario = {str(dia): [{'inicio': '08:00', 'fin': '12:00'}]
                   for dia in range(1, 8)}
        guardar_horario(self.engine, 'profesional', profesional_id, horario)
        guardar_horario(self.engine, 'box', box_id, horario)
        zona = ZoneInfo('America/Argentina/Mendoza')
        ahora = datetime.now(zona).replace(second=0, microsecond=0)
        fecha = ahora.date() + timedelta(days=3)
        inicio = datetime.combine(fecha, time(9, 0), zona).isoformat()
        destino = datetime.combine(fecha, time(10, 0), zona).isoformat()
        destino_conflictivo = datetime.combine(fecha, time(10, 30), zona).isoformat()
        turno = reservar_turno_paciente(
            self.engine, paciente_id=paciente_a, actor_id=cuentas[0]['id'],
            inicio=inicio, clave='pg-replay-reserva', ahora=ahora)
        reloj_vencido = ahora + timedelta(days=40)

        replay_reserva = reservar_turno_paciente(
            self.engine, paciente_id=paciente_a, actor_id=cuentas[0]['id'],
            inicio=inicio, clave='pg-replay-reserva', ahora=reloj_vencido)
        self.assertEqual(replay_reserva, turno)
        with self.assertRaises(ErrorPortalPaciente) as conflicto_reserva:
            reservar_turno_paciente(
                self.engine, paciente_id=paciente_a, actor_id=cuentas[0]['id'],
                inicio=destino, clave='pg-replay-reserva', ahora=reloj_vencido)
        self.assertEqual(conflicto_reserva.exception.estado, 409)

        cambio = reprogramar_turno_portal(
            self.engine, paciente_id=paciente_a, actor_id=cuentas[0]['id'],
            turno_id=turno['turno_id'], version=turno['version'], inicio=destino,
            clave='pg-replay-reprogramacion', ahora=ahora)
        replay_cambio = reprogramar_turno_portal(
            self.engine, paciente_id=paciente_a, actor_id=cuentas[0]['id'],
            turno_id=turno['turno_id'], version=turno['version'], inicio=destino,
            clave='pg-replay-reprogramacion', ahora=reloj_vencido)
        self.assertEqual(replay_cambio, cambio)
        with self.assertRaises(ErrorPortalPaciente) as conflicto_reprogramacion:
            reprogramar_turno_portal(
                self.engine, paciente_id=paciente_a, actor_id=cuentas[0]['id'],
                turno_id=turno['turno_id'], version=turno['version'],
                inicio=destino_conflictivo, clave='pg-replay-reprogramacion',
                ahora=reloj_vencido)
        self.assertEqual(conflicto_reprogramacion.exception.estado, 409)
        with self.assertRaises(ErrorPortalPaciente) as ajeno:
            reprogramar_turno_portal(
                self.engine, paciente_id=paciente_b, actor_id=cuentas[1]['id'],
                turno_id=turno['turno_id'], version=turno['version'], inicio=destino,
                clave='pg-replay-reprogramacion', ahora=reloj_vencido)
        self.assertEqual(ajeno.exception.estado, 404)


if __name__ == '__main__':
    unittest.main()
