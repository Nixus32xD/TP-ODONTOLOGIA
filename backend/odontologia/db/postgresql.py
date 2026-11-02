"""Alta de turnos sobre PostgreSQL con semántica compatible con C-01."""

from math import ceil
from datetime import datetime, timezone

from sqlalchemy import Engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.audit import ErrorAuditoria
from odontologia.agenda import (
    ErrorAgenda,
    Turno as TurnoDominio,
    validar_solicitud_turno,
)
from odontologia.db.models import AgendaMutex, Box, Paciente, Profesional, Turno


REVISION_ESQUEMA_ACTUAL = '20261102_0011_odontogram_treatment_plans'


def crear_engine(database_url: str) -> Engine:
    """Crear un engine sin abrir una conexión ni ejecutar DDL."""
    from sqlalchemy import create_engine

    return create_engine(database_url, pool_pre_ping=True)


def timeout_milisegundos(timeout_segundos: float) -> int:
    return max(1, ceil(timeout_segundos * 1000))


def codigo_error_postgresql(error: Exception) -> str:
    """Convertir errores SQL a códigos públicos estables sin filtrar detalles."""
    origen = getattr(error, 'orig', None)
    estado = getattr(origen, 'sqlstate', None)
    if estado is None:
        estado = getattr(getattr(origen, 'diag', None), 'sqlstate', None)
    return 'agenda_ocupada' if estado == '55P03' else 'almacenamiento_error'


def _validar_revision(session: Session) -> None:
    revision = session.execute(text('SELECT version_num FROM alembic_version')).scalar_one_or_none()
    if revision != REVISION_ESQUEMA_ACTUAL:
        raise ErrorAgenda('almacenamiento_error')


def _hay_solapamiento(session: Session, columna: str, recurso_id: str,
                      inicio_minuto: int, fin_minuto: int) -> bool:
    modelo = Turno
    campo = getattr(modelo, columna)
    return session.scalar(
        select(modelo.id)
        .where(
            campo == recurso_id,
            modelo.inicio_minuto < fin_minuto,
            modelo.fin_minuto > inicio_minuto,
            modelo.estado.in_(('reservado', 'confirmado')),
        )
        .limit(1)
    ) is not None


def crear_turno_postgresql(engine: Engine, *, paciente_id: str, profesional_id: str,
                            box_id: str, inicio: datetime, fin: datetime,
                            timeout_segundos: float = 5.0,
                            actor_id: str | None = None) -> TurnoDominio:
    solicitud = validar_solicitud_turno(
        paciente_id=paciente_id, profesional_id=profesional_id, box_id=box_id,
        inicio=inicio, fin=fin, timeout_segundos=timeout_segundos,
    )

    try:
        with Session(engine) as session, session.begin():
            _validar_revision(session)
            session.execute(
                text("SELECT set_config('lock_timeout', :timeout, true)"),
                {'timeout': f'{timeout_milisegundos(solicitud.timeout_segundos)}ms'},
            )
            mutex_id = session.scalar(
                select(AgendaMutex.id).where(AgendaMutex.id == 1).with_for_update()
            )
            if mutex_id != 1:
                raise ErrorAgenda('almacenamiento_error')

            recursos = (
                ('paciente', Paciente, solicitud.paciente_id),
                ('profesional', Profesional, solicitud.profesional_id),
                ('box', Box, solicitud.box_id),
            )
            catalogos = []
            for campo, modelo, identificador in recursos:
                recurso = session.get(modelo, identificador)
                if recurso is None:
                    raise ErrorAgenda('recurso_desconocido', campo)
                catalogos.append((campo, recurso))

            for campo, recurso in catalogos:
                if not recurso.activo:
                    raise ErrorAgenda('recurso_inactivo', campo)

            from odontologia.disponibilidad import validar_disponibilidad_session

            validar_disponibilidad_session(
                session, solicitud.inicio, solicitud.fin,
                solicitud.inicio_minuto, solicitud.fin_minuto,
                solicitud.profesional_id, solicitud.box_id)

            for campo, columna, identificador in (
                    ('profesional', 'profesional_id', solicitud.profesional_id),
                    ('box', 'box_id', solicitud.box_id)):
                if _hay_solapamiento(
                        session, columna, identificador,
                        solicitud.inicio_minuto, solicitud.fin_minuto):
                    raise ErrorAgenda(f'conflicto_{campo}', campo)

            turno = Turno(
                paciente_id=solicitud.paciente_id,
                profesional_id=solicitud.profesional_id,
                box_id=solicitud.box_id,
                inicio_minuto=solicitud.inicio_minuto,
                fin_minuto=solicitud.fin_minuto,
            )
            session.add(turno)
            session.flush()
            nuevo_id = turno.id
            if actor_id is not None:
                from odontologia.audit import registrar_evento_session

                registrar_evento_session(
                    session, action='turno.creado', resource_type='turno',
                    resource_id=str(turno.id), actor_id=actor_id, result='confirmado')
    except ErrorAgenda:
        raise
    except ErrorAuditoria as exc:
        raise ErrorAgenda('almacenamiento_error') from exc
    except SQLAlchemyError as exc:
        raise ErrorAgenda(codigo_error_postgresql(exc)) from exc

    return TurnoDominio(
        nuevo_id,
        solicitud.paciente_id,
        solicitud.profesional_id,
        solicitud.box_id,
        solicitud.inicio.astimezone(timezone.utc),
        solicitud.fin.astimezone(timezone.utc),
    )
