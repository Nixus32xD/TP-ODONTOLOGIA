"""Consultas de sólo lectura sobre la agenda persistida."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.agenda import ErrorAgenda, _fecha_utc, _minutos
from odontologia.db.models import Box, Paciente, Profesional, Turno


ESTADOS_TURNO = {'reservado', 'confirmado', 'atendido', 'ausente', 'cancelado'}
_DURACION_MAXIMA = timedelta(days=31)


class ErrorConsultaTurnos(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int = 422):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


def _validar_id(valor: object, campo: str) -> str:
    if (not isinstance(valor, str) or not valor or len(valor) > 64
            or valor.strip() != valor):
        raise ErrorConsultaTurnos('entrada_invalida', f'El filtro {campo} no es válido.')
    return valor


def _minuto_a_fecha(minuto: int) -> datetime:
    return datetime.fromtimestamp(minuto * 60, tz=timezone.utc)


def listar_turnos(engine, *, desde: datetime, hasta: datetime,
                  profesional_id: str | None = None, box_id: str | None = None,
                  estado: str | None = None, limit: int = 50, offset: int = 0,
                  profesional_vinculado_id: str | None = None) -> dict[str, object]:
    """Lista turnos que intersectan [desde, hasta), con una proyección por rol."""
    try:
        inicio_utc = _fecha_utc(desde, 'desde')
        fin_utc = _fecha_utc(hasta, 'hasta')
    except (ErrorAgenda, TypeError, ValueError, OverflowError) as exc:
        raise ErrorConsultaTurnos('entrada_invalida', 'El rango requiere fechas con offset.') from exc
    if inicio_utc >= fin_utc or fin_utc - inicio_utc > _DURACION_MAXIMA:
        raise ErrorConsultaTurnos('entrada_invalida', 'El rango debe durar hasta 31 días.')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ErrorConsultaTurnos('entrada_invalida', 'El límite debe estar entre 1 y 100.')
    if type(offset) is not int or offset < 0:
        raise ErrorConsultaTurnos('entrada_invalida', 'El offset debe ser no negativo.')
    if estado is not None and (not isinstance(estado, str) or estado not in ESTADOS_TURNO):
        raise ErrorConsultaTurnos('entrada_invalida', 'El estado del turno no es válido.')
    if profesional_id is not None:
        profesional_id = _validar_id(profesional_id, 'profesional_id')
    if box_id is not None:
        box_id = _validar_id(box_id, 'box_id')
    if profesional_vinculado_id is not None:
        profesional_vinculado_id = _validar_id(
            profesional_vinculado_id, 'profesional_vinculado_id')
        if profesional_id is not None and profesional_id != profesional_vinculado_id:
            raise ErrorConsultaTurnos(
                'permiso_denegado', 'Sólo puede consultar su propia agenda.', 403)
        profesional_id = profesional_vinculado_id

    minuto_desde = _minutos(inicio_utc)
    minuto_hasta = _minutos(fin_utc)
    try:
        with Session(engine) as session:
            if profesional_id is not None and session.get(Profesional, profesional_id) is None:
                raise ErrorConsultaTurnos('recurso_desconocido', 'El profesional no existe.', 404)
            if box_id is not None and session.get(Box, box_id) is None:
                raise ErrorConsultaTurnos('recurso_desconocido', 'El box no existe.', 404)
            consulta = select(Turno, Paciente, Profesional, Box).join(
                Paciente, Paciente.id == Turno.paciente_id).join(
                Profesional, Profesional.id == Turno.profesional_id).join(
                Box, Box.id == Turno.box_id).where(
                    Turno.inicio_minuto < minuto_hasta,
                    Turno.fin_minuto > minuto_desde)
            if profesional_id is not None:
                consulta = consulta.where(Turno.profesional_id == profesional_id)
            if box_id is not None:
                consulta = consulta.where(Turno.box_id == box_id)
            if estado is not None:
                consulta = consulta.where(Turno.estado == estado)
            filas = session.execute(consulta.order_by(
                Turno.inicio_minuto, Turno.id).limit(limit).offset(offset)).all()
            if profesional_vinculado_id is not None:
                items = [{
                    'inicio': _minuto_a_fecha(turno.inicio_minuto),
                    'fin': _minuto_a_fecha(turno.fin_minuto),
                    'paciente_nombre': paciente.nombre,
                } for turno, paciente, _profesional, _box in filas]
            else:
                items = [{
                    'id': turno.id,
                    'paciente_id': paciente.id,
                    'paciente_nombre': paciente.nombre,
                    'profesional_id': profesional.id,
                    'profesional_nombre': profesional.nombre,
                    'box_id': box.id,
                    'box_nombre': box.nombre,
                    'inicio': _minuto_a_fecha(turno.inicio_minuto),
                    'fin': _minuto_a_fecha(turno.fin_minuto),
                    'estado': turno.estado,
                    'version': turno.version,
                } for turno, paciente, profesional, box in filas]
            return {'items': items, 'limit': limit, 'offset': offset}
    except ErrorConsultaTurnos:
        raise
    except SQLAlchemyError as exc:
        raise ErrorConsultaTurnos(
            'almacenamiento_error', 'No se pudo consultar la agenda.', 503) from exc
