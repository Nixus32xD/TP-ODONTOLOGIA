"""Reprogramación atómica de turnos migrados, compartiendo el lock de agenda."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import ceil
import sqlite3
from zoneinfo import ZoneInfo

from sqlalchemy import Engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.agenda import (
    ErrorAgenda,
    SolicitudTurnoValidada,
    _minutos,
    validar_solicitud_turno,
)
from odontologia.audit import ErrorAuditoria, registrar_evento_session
from odontologia.db.models import AgendaMutex, Box, Paciente, Profesional, Turno
from odontologia.disponibilidad import validar_disponibilidad_session


_ZONA_AGENDA = ZoneInfo('America/Argentina/Mendoza')
_ESTADOS_REPROGRAMABLES = ('reservado', 'confirmado')


@dataclass(frozen=True)
class ResultadoReprogramacion:
    id: int
    paciente_id: str
    profesional_id: str
    box_id: str
    inicio: datetime
    fin: datetime
    estado: str
    version: int


def _iniciar_escritura(session: Session, timeout_segundos: float) -> None:
    if session.bind.dialect.name == 'sqlite':
        timeout_ms = max(1, ceil(timeout_segundos * 1000))
        session.connection().exec_driver_sql(f'PRAGMA busy_timeout = {timeout_ms}')
        session.execute(text('BEGIN IMMEDIATE'))
        return
    session.execute(text("SELECT set_config('lock_timeout', :timeout, true)"), {
        'timeout': f'{max(1, ceil(timeout_segundos * 1000))}ms'})
    mutex_id = session.scalar(
        select(AgendaMutex.id).where(AgendaMutex.id == 1).with_for_update())
    if mutex_id != 1:
        raise ErrorAgenda('almacenamiento_error')


def _validar_solicitud(turno: Turno, *, inicio: datetime, fin: datetime, profesional_id: str,
                       box_id: str, timeout_segundos: float) -> SolicitudTurnoValidada:
    solicitud = validar_solicitud_turno(
        paciente_id=turno.paciente_id, profesional_id=profesional_id,
        box_id=box_id, inicio=inicio, fin=fin,
        timeout_segundos=timeout_segundos)
    if solicitud.fin_minuto - solicitud.inicio_minuto != (
            turno.fin_minuto - turno.inicio_minuto):
        raise ErrorAgenda('entrada_invalida', 'intervalo')
    inicio_local = solicitud.inicio.astimezone(_ZONA_AGENDA)
    fin_local = solicitud.fin.astimezone(_ZONA_AGENDA)
    termina_exactamente_a_medianoche = (
        fin_local.date() == inicio_local.date() + timedelta(days=1)
        and fin_local.hour == 0 and fin_local.minute == 0
    )
    if (inicio_local.date() != fin_local.date()
            and not termina_exactamente_a_medianoche):
        raise ErrorAgenda('fuera_de_disponibilidad')
    return solicitud


def _exigir_recurso_activo(session: Session, modelo, recurso_id: str,
                           campo: str):
    recurso = session.get(modelo, recurso_id)
    if recurso is None:
        raise ErrorAgenda('recurso_desconocido', campo)
    if not recurso.activo:
        raise ErrorAgenda('recurso_inactivo', campo)
    return recurso


def _validar_ocupacion(session: Session, turno_id: int,
                       solicitud: SolicitudTurnoValidada) -> None:
    for campo, recurso_id in (
        ('profesional', solicitud.profesional_id), ('box', solicitud.box_id),
    ):
        columna = getattr(Turno, f'{campo}_id')
        conflicto = session.scalar(select(Turno.id).where(
            Turno.id != turno_id,
            Turno.estado.in_(_ESTADOS_REPROGRAMABLES),
            columna == recurso_id,
            Turno.inicio_minuto < solicitud.fin_minuto,
            Turno.fin_minuto > solicitud.inicio_minuto,
        ).limit(1))
        if conflicto is not None:
            raise ErrorAgenda(f'conflicto_{campo}', campo)


def reprogramar_turno(engine: Engine, turno_id: int, *,
                      version_esperada: int, inicio: datetime, fin: datetime,
                      profesional_id: str, box_id: str, actor_id: str | None,
                      timeout_segundos: float = 5.0,
                      ahora: datetime | None = None) -> ResultadoReprogramacion:
    """Validar y mover una fila existente con versión y auditoría atómicas."""
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session, timeout_segundos)
            turno = session.get(Turno, turno_id)
            if turno is None:
                raise ErrorAgenda('turno_no_encontrado')
            if type(version_esperada) is not int or version_esperada <= 0:
                raise ErrorAgenda('entrada_invalida', 'version')
            if turno.version != version_esperada:
                raise ErrorAgenda('version_desactualizada')
            if turno.estado not in _ESTADOS_REPROGRAMABLES:
                raise ErrorAgenda('turno_no_reprogramable')
            solicitud = _validar_solicitud(
                turno, inicio=inicio, fin=fin,
                profesional_id=profesional_id, box_id=box_id,
                timeout_segundos=timeout_segundos)
            _exigir_recurso_activo(session, Paciente, turno.paciente_id, 'paciente')
            _exigir_recurso_activo(
                session, Profesional, solicitud.profesional_id, 'profesional')
            _exigir_recurso_activo(session, Box, solicitud.box_id, 'box')
            validar_disponibilidad_session(
                session, solicitud.inicio, solicitud.fin,
                solicitud.inicio_minuto, solicitud.fin_minuto,
                solicitud.profesional_id, solicitud.box_id)
            _validar_ocupacion(session, turno.id, solicitud)
            estaba_confirmado = turno.estado == 'confirmado'
            if estaba_confirmado:
                from odontologia.recordatorios import invalidar_recordatorios_pendientes

                invalidar_recordatorios_pendientes(
                    session, turno, actor_id=actor_id, ahora=ahora)
            turno.profesional_id = solicitud.profesional_id
            turno.box_id = solicitud.box_id
            turno.inicio_minuto = solicitud.inicio_minuto
            turno.fin_minuto = solicitud.fin_minuto
            turno.version += 1
            session.flush()
            if estaba_confirmado:
                from odontologia.recordatorios import programar_recordatorio_confirmacion

                programar_recordatorio_confirmacion(
                    session, turno, actor_id=actor_id, ahora=ahora)
            registrar_evento_session(
                session, action='turno.reprogramado', resource_type='turno',
                resource_id=str(turno.id), actor_id=actor_id, result='confirmado')
            resultado = ResultadoReprogramacion(
                id=turno.id, paciente_id=turno.paciente_id,
                profesional_id=turno.profesional_id, box_id=turno.box_id,
                inicio=datetime(1970, 1, 1, tzinfo=timezone.utc)
                + timedelta(minutes=turno.inicio_minuto),
                fin=datetime(1970, 1, 1, tzinfo=timezone.utc)
                + timedelta(minutes=turno.fin_minuto),
                estado=turno.estado, version=turno.version)
        return resultado
    except ErrorAgenda:
        raise
    except ErrorAuditoria as exc:
        raise ErrorAgenda('almacenamiento_error') from exc
    except SQLAlchemyError as exc:
        if engine.dialect.name == 'sqlite':
            codigo_sqlite = getattr(getattr(exc, 'orig', exc), 'sqlite_errorcode', 0) & 0xff
            codigo = ('agenda_ocupada' if codigo_sqlite in
                      (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) else 'almacenamiento_error')
        else:
            from odontologia.db.postgresql import codigo_error_postgresql

            codigo = codigo_error_postgresql(exc)
        raise ErrorAgenda(codigo) from exc
