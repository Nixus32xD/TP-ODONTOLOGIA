"""Registro append-only y lectura segura de auditoría local."""
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError


class ErrorAuditoria(RuntimeError):
    """Fallo genérico de persistencia o lectura de auditoría."""

_MATRIZ_EVENTOS = {
    'turno.creado': ('turno', 'confirmado'),
    'turno.estado_actualizado': ('turno', 'confirmado'),
    'turno.reprogramado': ('turno', 'confirmado'),
    'paciente.creado': ('paciente', 'confirmado'),
    'paciente.actualizado': ('paciente', 'confirmado'),
    'paciente.desactivado': ('paciente', 'confirmado'),
    'paciente.reactivado': ('paciente', 'confirmado'),
    'profesional.creado': ('profesional', 'confirmado'),
    'profesional.actualizado': ('profesional', 'confirmado'),
    'profesional.desactivado': ('profesional', 'confirmado'),
    'profesional.reactivado': ('profesional', 'confirmado'),
    'box.creado': ('box', 'confirmado'),
    'box.actualizado': ('box', 'confirmado'),
    'box.desactivado': ('box', 'confirmado'),
    'box.reactivado': ('box', 'confirmado'),
    'prestacion.creada': ('prestacion', 'confirmado'),
    'prestacion.actualizada': ('prestacion', 'confirmado'),
    'prestacion.desactivada': ('prestacion', 'confirmado'),
    'prestacion.reactivada': ('prestacion', 'confirmado'),
    'horario.actualizado': ('horario', 'confirmado'),
    'excepcion.creada': ('excepcion', 'confirmado'),
    'excepcion.actualizada': ('excepcion', 'confirmado'),
    'excepcion.eliminada': ('excepcion', 'confirmado'),
    'bloqueo.creado': ('bloqueo', 'confirmado'),
    'bloqueo.eliminado': ('bloqueo', 'confirmado'),
    'cuenta.bootstrap': ('cuenta', 'confirmado'),
    'cuenta.creada': ('cuenta', 'confirmado'),
    'cuenta.actualizada': ('cuenta', 'confirmado'),
    'sesion.iniciada': ('sesion', 'confirmado'),
    'sesion.cerrada': ('sesion', 'confirmado'),
    'sesion.rechazada': ('sesion', 'rechazado'),
    'historia.consultada': ('historia', 'confirmado'),
    'historia.denegada': ('historia', 'rechazado'),
    'historia.atenciones_listadas': ('historia', 'confirmado'),
    'evolucion.creada': ('evolucion', 'confirmado'),
    'evolucion.corregida': ('evolucion', 'confirmado'),
    'odontograma.consultada': ('odontograma', 'confirmado'),
    'odontograma.denegada': ('odontograma', 'rechazado'),
    'odontograma.version_creada': ('odontograma', 'confirmado'),
    'plan.consultado': ('plan', 'confirmado'),
    'plan.denegado': ('plan', 'rechazado'),
    'plan.creado': ('plan', 'confirmado'),
    'plan.estado_actualizado': ('plan', 'confirmado'),
}


def _normalizar_evento(*, action, resource_type, result, actor_id, resource_id, instante):
    if _MATRIZ_EVENTOS.get(action) != (resource_type, result):
        raise ValueError('Evento de auditoría fuera del catálogo permitido.')
    if action == 'sesion.rechazada' and (actor_id is not None or resource_id is not None):
        raise ValueError('El rechazo de sesión no admite identificadores.')
    if resource_type == 'sesion' and resource_id is not None:
        raise ValueError('La auditoría no admite identificadores de sesión.')
    if actor_id is not None and (not isinstance(actor_id, str) or not actor_id):
        raise ValueError('Actor de auditoría inválido.')
    if resource_id is not None and (not isinstance(resource_id, str) or not resource_id):
        raise ValueError('Recurso de auditoría inválido.')
    fecha = instante or datetime.now(timezone.utc)
    if not isinstance(fecha, datetime) or fecha.tzinfo is None or fecha.utcoffset() is None:
        raise ValueError('El instante de auditoría debe incluir zona horaria.')
    return fecha.astimezone(timezone.utc).isoformat(timespec='microseconds')


def registrar_evento_sqlite(conexion, *, action, resource_type, result,
                             actor_id=None, resource_id=None, instante=None):
    created_at = _normalizar_evento(
        action=action, resource_type=resource_type, result=result,
        actor_id=actor_id, resource_id=resource_id, instante=instante)
    cursor = conexion.execute(
        'INSERT INTO eventos_auditoria '
        '(created_at, actor_id, action, resource_type, resource_id, result) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (created_at, actor_id, action, resource_type, resource_id, result))
    return cursor.lastrowid


def listar_eventos_sqlite(conexion, *, limit=50, offset=0):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit fuera de rango')
    if type(offset) is not int or offset < 0:
        raise ValueError('offset fuera de rango')
    columnas = ('id', 'created_at', 'actor_id', 'action', 'resource_type', 'resource_id', 'result')
    filas = conexion.execute(
        'SELECT id, created_at, actor_id, action, resource_type, resource_id, result '
        'FROM eventos_auditoria ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?',
        (limit, offset),
    ).fetchall()
    return [dict(zip(columnas, fila)) for fila in filas]


def registrar_evento_session(session, *, action, resource_type, result,
                             actor_id=None, resource_id=None, instante=None):
    created_at = datetime.fromisoformat(_normalizar_evento(
        action=action, resource_type=resource_type, result=result,
        actor_id=actor_id, resource_id=resource_id, instante=instante))
    try:
        if session.bind.dialect.name == 'sqlite':
            session.execute(text(
                'INSERT INTO eventos_auditoria '
                '(created_at, actor_id, action, resource_type, resource_id, result) '
                'VALUES (:created_at, :actor_id, :action, :resource_type, :resource_id, :result)'), {
                    'created_at': created_at.isoformat(timespec='microseconds'),
                    'actor_id': actor_id, 'action': action, 'resource_type': resource_type,
                    'resource_id': resource_id, 'result': result,
                })
        else:
            from odontologia.db.models import EventoAuditoria

            session.add(EventoAuditoria(
                created_at=created_at, actor_id=actor_id, action=action,
                resource_type=resource_type, resource_id=resource_id, result=result))
        session.flush()
    except SQLAlchemyError as exc:
        raise ErrorAuditoria('No se pudo registrar la auditoría.') from exc


def listar_eventos_session(session, *, limit=50, offset=0):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit fuera de rango')
    if type(offset) is not int or offset < 0:
        raise ValueError('offset fuera de rango')
    if session.bind.dialect.name == 'sqlite':
        filas = session.execute(text(
            'SELECT id, created_at, actor_id, action, resource_type, resource_id, result '
            'FROM eventos_auditoria ORDER BY created_at DESC, id DESC '
            'LIMIT :limit OFFSET :offset'), {'limit': limit, 'offset': offset}).mappings()
        return [dict(fila) for fila in filas]
    from odontologia.db.models import EventoAuditoria

    eventos = session.scalars(select(EventoAuditoria).order_by(
        EventoAuditoria.created_at.desc(), EventoAuditoria.id.desc()
    ).limit(limit).offset(offset)).all()
    return [{
        'id': evento.id,
        'created_at': evento.created_at.astimezone(timezone.utc).isoformat(timespec='microseconds'),
        'actor_id': evento.actor_id,
        'action': evento.action,
        'resource_type': evento.resource_type,
        'resource_id': evento.resource_id,
        'result': evento.result,
    } for evento in eventos]


def listar_eventos(engine, *, limit=50, offset=0):
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    try:
        with Session(engine) as session:
            return listar_eventos_session(session, limit=limit, offset=offset)
    except (SQLAlchemyError, OSError) as exc:
        raise RuntimeError('No se pudo consultar la auditoría.') from exc
