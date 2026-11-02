"""Procesamiento local y acotado del outbox de recordatorios."""
from datetime import datetime, timedelta, timezone
from math import ceil

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from odontologia.audit import registrar_evento_session
from odontologia.db.models import AgendaMutex, Paciente, RecordatorioOutbox, Turno


def _canal_simulado(_recordatorio: RecordatorioOutbox) -> bool:
    """Canal local sin E/S; se sustituye sólo en tests para inyectar fallos."""
    return True


def _iniciar_pasada(session: Session, timeout_segundos: float) -> None:
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
        raise RuntimeError('El esquema de agenda no está preparado.')


def procesar_recordatorios(engine, *, limite: int,
                           ahora: datetime | None = None,
                           timeout_segundos: float = 5.0) -> dict[str, int]:
    """Procesar en una transacción los vencidos, revalidando toda su elegibilidad."""
    if type(limite) is not int or not 1 <= limite <= 100:
        raise ValueError('El límite debe estar entre 1 y 100.')
    reloj = ahora or datetime.now(timezone.utc)
    if reloj.tzinfo is None or reloj.utcoffset() is None:
        raise ValueError('El reloj debe incluir zona horaria.')
    instante = reloj.astimezone(timezone.utc)
    conteos = {'procesados': 0, 'invalidados': 0, 'fallidos': 0}

    with Session(engine) as session, session.begin():
        _iniciar_pasada(session, timeout_segundos)
        consulta = select(RecordatorioOutbox).where(
            RecordatorioOutbox.estado == 'pendiente',
            RecordatorioOutbox.programado_para <= instante,
        ).order_by(
            RecordatorioOutbox.programado_para, RecordatorioOutbox.created_at,
            RecordatorioOutbox.id,
        ).limit(limite)
        if session.bind.dialect.name == 'postgresql':
            consulta = consulta.with_for_update(skip_locked=True)
        recordatorios = session.scalars(consulta).all()
        for recordatorio in recordatorios:
            turno = session.get(Turno, recordatorio.turno_id)
            paciente = session.get(Paciente, turno.paciente_id) if turno else None
            inicio = (datetime(1970, 1, 1, tzinfo=timezone.utc)
                      + timedelta(minutes=turno.inicio_minuto)) if turno else None
            vencimiento = recordatorio.programado_para
            if vencimiento is not None:
                vencimiento = (vencimiento.replace(tzinfo=timezone.utc)
                               if vencimiento.tzinfo is None
                               else vencimiento.astimezone(timezone.utc))
            elegible = bool(
                turno is not None
                and paciente is not None
                and paciente.acepta_recordatorios
                and turno.estado == 'confirmado'
                and turno.version == recordatorio.turno_version
                and inicio is not None
                and inicio > instante
                and vencimiento is not None
                and vencimiento <= instante
            )
            recordatorio.updated_at = instante
            if not elegible:
                recordatorio.estado = 'invalidado'
                session.flush()
                registrar_evento_session(
                    session, action='recordatorio.invalidado',
                    resource_type='recordatorio', resource_id=recordatorio.id,
                    actor_id=None, result='confirmado', instante=instante)
                conteos['invalidados'] += 1
                continue

            if not _canal_simulado(recordatorio):
                recordatorio.intentos += 1
                if recordatorio.intentos >= 3:
                    recordatorio.estado = 'fallido'
                session.flush()
                registrar_evento_session(
                    session, action='recordatorio.fallo', resource_type='recordatorio',
                    resource_id=recordatorio.id, actor_id=None, result='rechazado',
                    instante=instante)
                conteos['fallidos'] += 1
                continue

            recordatorio.estado = 'procesado_simulado'
            session.flush()
            registrar_evento_session(
                session, action='recordatorio.procesado', resource_type='recordatorio',
                resource_id=recordatorio.id, actor_id=None, result='confirmado',
                instante=instante)
            conteos['procesados'] += 1
    return conteos
