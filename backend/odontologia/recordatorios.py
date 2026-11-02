"""Programación persistida de recordatorios locales y simulados."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from odontologia.audit import registrar_evento_session
from odontologia.db.models import Paciente, RecordatorioOutbox, Turno


_ZONA_AGENDA = ZoneInfo('America/Argentina/Mendoza')
_TIPO_TURNO = 'turno_24h'


def programar_recordatorio_confirmacion(
        session: Session, turno: Turno, *, actor_id: str | None,
        ahora: datetime | None = None) -> RecordatorioOutbox | None:
    """Agregar outbox si una confirmación sintética conserva consentimiento y plazo."""
    if turno.estado != 'confirmado':
        return None
    paciente = session.get(Paciente, turno.paciente_id)
    if paciente is None or not paciente.acepta_recordatorios:
        return None

    reloj = ahora or datetime.now(timezone.utc)
    if reloj.tzinfo is None or reloj.utcoffset() is None:
        raise ValueError('El reloj debe incluir zona horaria.')
    ahora_utc = reloj.astimezone(timezone.utc)
    inicio_utc = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
        minutes=turno.inicio_minuto)
    inicio_local = inicio_utc.astimezone(_ZONA_AGENDA)
    vencimiento_local = (inicio_utc - timedelta(hours=24)).astimezone(_ZONA_AGENDA)
    programado_para = vencimiento_local.astimezone(timezone.utc)
    if inicio_local.tzinfo is None:  # Guardia defensiva para preservar el contrato IANA.
        return None
    if inicio_utc <= ahora_utc:
        return None
    if programado_para <= ahora_utc:
        return None

    existente = session.scalar(select(RecordatorioOutbox).where(
        RecordatorioOutbox.turno_id == turno.id,
        RecordatorioOutbox.turno_version == turno.version,
        RecordatorioOutbox.tipo == _TIPO_TURNO,
    ).order_by(RecordatorioOutbox.generation.desc()).limit(1))
    if existente is not None and existente.estado != 'invalidado':
        return existente

    generation = 1 if existente is None else existente.generation + 1

    recordatorio_id = str(uuid4())
    clave = (
        f'turno:{turno.id}:version:{turno.version}:tipo:{_TIPO_TURNO}:'
        f'generacion:{generation}')
    fecha = ahora_utc
    recordatorio = RecordatorioOutbox(
        id=recordatorio_id, turno_id=turno.id, turno_version=turno.version,
        generation=generation, tipo=_TIPO_TURNO,
        programado_para=programado_para, estado='pendiente',
        intentos=0, idempotency_key=clave, created_at=fecha, updated_at=fecha)
    session.add(recordatorio)
    session.flush()
    registrar_evento_session(
        session, action='recordatorio.programado', resource_type='recordatorio',
        resource_id=recordatorio.id, actor_id=actor_id, result='confirmado', instante=fecha)
    return recordatorio


def invalidar_recordatorios_pendientes(
        session: Session, turno: Turno, *, actor_id: str | None,
        ahora: datetime | None = None) -> int:
    """Invalidar y auditar los pendientes de un turno en su transacción actual."""
    reloj = ahora or datetime.now(timezone.utc)
    if reloj.tzinfo is None or reloj.utcoffset() is None:
        raise ValueError('El reloj debe incluir zona horaria.')
    instante = reloj.astimezone(timezone.utc)
    recordatorios = session.scalars(select(RecordatorioOutbox).where(
        RecordatorioOutbox.turno_id == turno.id,
        RecordatorioOutbox.estado == 'pendiente',
    ).order_by(RecordatorioOutbox.turno_version, RecordatorioOutbox.id)).all()
    for recordatorio in recordatorios:
        recordatorio.estado = 'invalidado'
        recordatorio.updated_at = instante
        session.flush()
        registrar_evento_session(
            session, action='recordatorio.invalidado', resource_type='recordatorio',
            resource_id=recordatorio.id, actor_id=actor_id, result='confirmado',
            instante=instante)
    return len(recordatorios)
