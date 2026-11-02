from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo
import unittest

from odontologia import inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_usuario
from odontologia.db.models import Box, Paciente, Profesional
from odontologia.disponibilidad import guardar_horario
from sqlalchemy.orm import Session


class PortalPacienteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id='portal-paciente', nombre='Paciente sintético', activo=True,
                         acepta_recordatorios=False),
                Profesional(id='portal-prof', nombre='Profesional sintético', activo=True),
                Box(id='portal-box', nombre='Box sintético', activo=True),
            ])
        self.cuenta = crear_usuario(
            self.engine, 'portal.paciente', 'frase-larga-segura-portal-2026', 'paciente',
            paciente_id='portal-paciente')
        horario = {str(dia): [{'inicio': '08:00', 'fin': '12:00'}]
                   for dia in range(1, 8)}
        guardar_horario(self.engine, 'profesional', 'portal-prof', horario)
        guardar_horario(self.engine, 'box', 'portal-box', horario)
        self.zona = ZoneInfo('America/Argentina/Mendoza')
        self.ahora = datetime(2026, 11, 2, 10, 0, tzinfo=self.zona)

    def test_disponibilidad_opaca_solo_publica_inicio_y_fin(self):
        from odontologia.portal_paciente import consultar_disponibilidad_portal

        resultado = consultar_disponibilidad_portal(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            fecha='2026-11-03', ahora=self.ahora)

        self.assertTrue(resultado['items'])
        self.assertEqual(set(resultado['items'][0]), {'inicio', 'fin'})
        self.assertEqual(resultado['items'][0]['inicio'].astimezone(self.zona).hour, 8)

    def test_reserva_persistente_repite_resultado_y_rechaza_payload_distinto(self):
        from odontologia.portal_paciente import ErrorPortalPaciente, reservar_turno_paciente

        inicio = '2026-11-03T09:00:00-03:00'
        primera = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio=inicio, clave='clave-portal-001', ahora=self.ahora)
        repetida = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio=inicio, clave='clave-portal-001', ahora=self.ahora)
        self.assertEqual(primera, repetida)
        self.assertEqual(set(primera), {'turno_id', 'inicio', 'fin', 'estado', 'version'})
        with self.assertRaises(ErrorPortalPaciente) as error:
            reservar_turno_paciente(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                inicio='2026-11-03T09:30:00-03:00', clave='clave-portal-001',
                ahora=self.ahora)
        self.assertEqual(error.exception.estado, 409)

    def test_reserva_replay_no_revalida_vigencia_ni_horizonte(self):
        from odontologia.portal_paciente import ErrorPortalPaciente, reservar_turno_paciente

        inicio = '2026-11-03T09:00:00-03:00'
        creada = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio=inicio, clave='reserva-expirada', ahora=self.ahora)
        reloj_futuro = datetime(2026, 12, 10, 10, 0, tzinfo=self.zona)

        repetida = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio=inicio, clave='reserva-expirada', ahora=reloj_futuro)
        self.assertEqual(repetida, creada)
        with self.assertRaises(ErrorPortalPaciente) as conflicto:
            reservar_turno_paciente(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                inicio='2026-11-03T09:30:00-03:00', clave='reserva-expirada',
                ahora=reloj_futuro)
        self.assertEqual(conflicto.exception.estado, 409)

    def test_cancelacion_propietaria_exige_anticipacion_y_es_idempotente(self):
        from odontologia.portal_paciente import (
            ErrorPortalPaciente, cancelar_turno_portal, reservar_turno_paciente,
        )

        turno = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio='2026-11-03T10:00:00-03:00', clave='reserva-cancelar', ahora=self.ahora)
        cancelado = cancelar_turno_portal(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            turno_id=turno['turno_id'], clave='cancelar-001', ahora=self.ahora)
        repetido = cancelar_turno_portal(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            turno_id=turno['turno_id'], clave='cancelar-001', ahora=self.ahora)
        self.assertEqual(cancelado, repetido)
        self.assertEqual(cancelado['estado'], 'cancelado')
        with self.assertRaises(ErrorPortalPaciente) as error:
            cancelar_turno_portal(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                turno_id=turno['turno_id'], clave='cancelar-tarde',
                ahora=datetime(2026, 11, 2, 10, 1, tzinfo=self.zona))
        self.assertEqual(error.exception.estado, 409)

    def test_reprogramacion_conserva_titularidad_estado_y_versiona_el_turno(self):
        from odontologia.portal_paciente import (
            ErrorPortalPaciente, reprogramar_turno_portal, reservar_turno_paciente,
        )

        turno = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio='2026-11-03T10:00:00-03:00', clave='reserva-reprogramar', ahora=self.ahora)
        movido = reprogramar_turno_portal(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            turno_id=turno['turno_id'], version=turno['version'],
            inicio='2026-11-03T11:00:00-03:00', clave='reprogramar-001', ahora=self.ahora)
        self.assertEqual(movido['turno_id'], turno['turno_id'])
        self.assertEqual(movido['estado'], 'reservado')
        self.assertEqual(movido['version'], turno['version'] + 1)
        repetido = reprogramar_turno_portal(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            turno_id=turno['turno_id'], version=turno['version'],
            inicio='2026-11-03T11:00:00-03:00', clave='reprogramar-001', ahora=self.ahora)
        self.assertEqual(movido, repetido)
        with self.assertRaises(ErrorPortalPaciente) as error:
            reprogramar_turno_portal(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                turno_id=turno['turno_id'], version=turno['version'],
                inicio='2026-11-03T11:30:00-03:00', clave='reprogramar-obsoleto',
                ahora=self.ahora)
        self.assertEqual(error.exception.estado, 409)

    def test_reprogramacion_replay_vencido_preserva_conflicto_y_verifica_titularidad(self):
        from odontologia.portal_paciente import (
            ErrorPortalPaciente, reprogramar_turno_portal, reservar_turno_paciente,
        )
        from sqlalchemy.orm import Session

        turno = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio='2026-11-03T10:00:00-03:00', clave='reserva-reprogramar-expirada',
            ahora=self.ahora)
        destino = '2026-11-03T11:00:00-03:00'
        movido = reprogramar_turno_portal(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            turno_id=turno['turno_id'], version=turno['version'], inicio=destino,
            clave='reprogramar-expirada', ahora=self.ahora)
        reloj_futuro = datetime(2026, 12, 10, 10, 0, tzinfo=self.zona)

        repetido = reprogramar_turno_portal(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            turno_id=turno['turno_id'], version=turno['version'], inicio=destino,
            clave='reprogramar-expirada', ahora=reloj_futuro)
        self.assertEqual(repetido, movido)
        with self.assertRaises(ErrorPortalPaciente) as conflicto:
            reprogramar_turno_portal(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                turno_id=turno['turno_id'], version=turno['version'],
                inicio='2026-11-03T11:30:00-03:00', clave='reprogramar-expirada',
                ahora=reloj_futuro)
        self.assertEqual(conflicto.exception.estado, 409)

        with Session(self.engine) as session, session.begin():
            session.add(Paciente(
                id='portal-paciente-replay-ajeno', nombre='Ficha ajena sintética', activo=True,
                acepta_recordatorios=False))
        ajena = crear_usuario(
            self.engine, 'portal.replay.ajeno', 'frase-larga-segura-portal-2026', 'paciente',
            paciente_id='portal-paciente-replay-ajeno')
        with self.assertRaises(ErrorPortalPaciente) as no_es_duena:
            reprogramar_turno_portal(
                self.engine, paciente_id='portal-paciente-replay-ajeno',
                actor_id=ajena['id'], turno_id=turno['turno_id'],
                version=turno['version'], inicio=destino,
                clave='reprogramar-expirada', ahora=reloj_futuro)
        self.assertEqual(no_es_duena.exception.estado, 404)

    def test_maximo_tres_turnos_futuros_y_horizonte_de_31_dias(self):
        from odontologia.portal_paciente import ErrorPortalPaciente, reservar_turno_paciente

        for indice, hora in enumerate(('08:00', '08:30', '09:00')):
            reservar_turno_paciente(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                inicio=f'2026-11-03T{hora}:00-03:00', clave=f'maximo-{indice}',
                ahora=self.ahora)
        with self.assertRaises(ErrorPortalPaciente) as limite:
            reservar_turno_paciente(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                inicio='2026-11-03T09:30:00-03:00', clave='maximo-cuarto', ahora=self.ahora)
        self.assertEqual(limite.exception.estado, 409)
        with self.assertRaises(ErrorPortalPaciente) as horizonte:
            reservar_turno_paciente(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                inicio='2026-12-04T09:00:00-03:00', clave='fuera-horizonte', ahora=self.ahora)
        self.assertEqual(horizonte.exception.estado, 422)

    def test_turno_ajeno_y_desconocido_tienen_mismo_404(self):
        from odontologia.portal_paciente import (
            ErrorPortalPaciente, cancelar_turno_portal, reservar_turno_paciente,
        )
        from sqlalchemy.orm import Session

        with Session(self.engine) as session, session.begin():
            session.add(Paciente(
                id='portal-paciente-B', nombre='Otra persona sintética', activo=True,
                acepta_recordatorios=False))
        cuenta_b = crear_usuario(
            self.engine, 'portal.paciente.b', 'frase-larga-segura-portal-2026', 'paciente',
            paciente_id='portal-paciente-B')
        turno = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio='2026-11-03T10:00:00-03:00', clave='titularidad', ahora=self.ahora)
        errores = []
        for turno_id in (turno['turno_id'], 999999):
            with self.assertRaises(ErrorPortalPaciente) as error:
                cancelar_turno_portal(
                    self.engine, paciente_id='portal-paciente-B', actor_id=cuenta_b['id'],
                    turno_id=turno_id, clave=f'no-propio-{turno_id}', ahora=self.ahora)
            errores.append((error.exception.codigo, error.exception.estado, str(error.exception)))
        self.assertEqual(errores[0], errores[1])

    def test_listado_separa_turnos_por_ficha_sin_campos_de_contacto(self):
        from odontologia.portal_paciente import listar_turnos_portal, reservar_turno_paciente
        from sqlalchemy.orm import Session

        with Session(self.engine) as session, session.begin():
            session.add(Paciente(
                id='portal-paciente-C', nombre='Tercera ficha sintética', activo=True,
                acepta_recordatorios=False))
        cuenta_c = crear_usuario(
            self.engine, 'portal.paciente.c', 'frase-larga-segura-portal-2026', 'paciente',
            paciente_id='portal-paciente-C')
        propio = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
            inicio='2026-11-03T09:00:00-03:00', clave='lista-propia', ahora=self.ahora)
        ajeno = reservar_turno_paciente(
            self.engine, paciente_id='portal-paciente-C', actor_id=cuenta_c['id'],
            inicio='2026-11-03T10:00:00-03:00', clave='lista-ajena', ahora=self.ahora)

        resultado = listar_turnos_portal(
            self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'])
        self.assertEqual([fila['turno_id'] for fila in resultado['items']], [propio['turno_id']])
        self.assertNotIn('paciente_id', resultado['items'][0])
        self.assertNotIn('telefono', resultado['items'][0])
        self.assertNotEqual(propio['turno_id'], ajeno['turno_id'])

    def test_falla_auditoria_revierte_reserva_y_clave(self):
        from sqlalchemy import select, func
        from sqlalchemy.orm import Session
        from unittest.mock import patch
        from odontologia.audit import ErrorAuditoria
        from odontologia.db.models import IdempotenciaPortalPaciente, Turno
        from odontologia.portal_paciente import ErrorPortalPaciente, reservar_turno_paciente

        with patch('odontologia.portal_paciente.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            with self.assertRaises(ErrorPortalPaciente):
                reservar_turno_paciente(
                    self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                    inicio='2026-11-03T11:00:00-03:00', clave='rollback-auditoria',
                    ahora=self.ahora)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Turno)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(
                IdempotenciaPortalPaciente)), 0)

    def test_dos_reservas_concurrentes_con_misma_clave_crean_un_solo_turno(self):
        from sqlalchemy import select, func
        from sqlalchemy.orm import Session
        from odontologia.db.models import IdempotenciaPortalPaciente, Turno
        from odontologia.portal_paciente import reservar_turno_paciente

        barrera = Barrier(2)

        def reservar():
            barrera.wait(timeout=3)
            return reservar_turno_paciente(
                self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'],
                inicio='2026-11-03T09:00:00-03:00', clave='misma-clave-concurrente',
                ahora=self.ahora)

        with ThreadPoolExecutor(max_workers=2) as executor:
            uno, dos = [f.result(timeout=5) for f in (
                executor.submit(reservar), executor.submit(reservar))]
        self.assertEqual(uno, dos)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Turno)), 1)
            self.assertEqual(session.scalar(select(func.count()).select_from(
                IdempotenciaPortalPaciente)), 1)

    def test_falla_auditoria_lectura_no_devuelve_datos(self):
        from unittest.mock import patch
        from odontologia.audit import ErrorAuditoria
        from odontologia.portal_paciente import (
            ErrorPortalPaciente, listar_turnos_portal,
        )

        with patch('odontologia.portal_paciente.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            with self.assertRaises(ErrorPortalPaciente) as error:
                listar_turnos_portal(
                    self.engine, paciente_id='portal-paciente', actor_id=self.cuenta['id'])
        self.assertEqual(error.exception.estado, 503)


if __name__ == '__main__':
    unittest.main()
