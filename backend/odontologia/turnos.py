"""Operaciones de ciclo de vida para turnos ya migrados."""
from dataclasses import dataclass
from math import ceil
import sqlite3

from sqlalchemy import Engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.agenda import ErrorAgenda
from odontologia.audit import ErrorAuditoria, registrar_evento_session
from odontologia.db.models import AgendaMutex, Turno


_TRANSICIONES_PERMITIDAS = {
    'reservado': frozenset({'confirmado', 'cancelado'}),
    'confirmado': frozenset({'atendido', 'ausente', 'cancelado'}),
    'atendido': frozenset(),
    'ausente': frozenset(),
    'cancelado': frozenset(),
}


@dataclass(frozen=True)
class ResultadoEstadoTurno:
    id: int
    estado: str


def transicionar_estado_turno(engine: Engine, turno_id: int, destino: str, *,
                              actor_id: str, timeout_segundos: float = 5.0) -> ResultadoEstadoTurno:
    """Persistir una transición permitida con versión y auditoría atómicas."""
    try:
        with Session(engine) as session, session.begin():
            if session.bind.dialect.name == 'sqlite':
                timeout_ms = max(1, ceil(timeout_segundos * 1000))
                session.connection().exec_driver_sql(f'PRAGMA busy_timeout = {timeout_ms}')
                session.execute(text('BEGIN IMMEDIATE'))
            else:
                session.execute(text("SELECT set_config('lock_timeout', :timeout, true)"), {
                    'timeout': f'{max(1, ceil(timeout_segundos * 1000))}ms'})
                mutex_id = session.scalar(
                    select(AgendaMutex.id).where(AgendaMutex.id == 1).with_for_update())
                if mutex_id != 1:
                    raise ErrorAgenda('almacenamiento_error')
            turno = session.get(Turno, turno_id)
            if turno is None:
                raise ErrorAgenda('turno_no_encontrado')
            if destino == 'cancelado' and turno.estado == 'cancelado':
                return ResultadoEstadoTurno(turno.id, turno.estado)
            if destino not in _TRANSICIONES_PERMITIDAS.get(turno.estado, frozenset()):
                raise ErrorAgenda('transicion_invalida')
            turno.estado = destino
            turno.version += 1
            session.flush()
            registrar_evento_session(
                session, action='turno.estado_actualizado', resource_type='turno',
                resource_id=str(turno.id), actor_id=actor_id, result='confirmado')
            resultado = ResultadoEstadoTurno(turno.id, turno.estado)
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
