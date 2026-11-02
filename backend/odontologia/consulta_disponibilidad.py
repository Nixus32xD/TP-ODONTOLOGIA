"""Cálculo orientativo y de sólo lectura de inicios de turno disponibles."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.agenda import _minutos
from odontologia.db.models import BloqueoAgenda, Box, Profesional, Turno
from odontologia.disponibilidad import (
    ErrorDisponibilidad,
    _exigir_recurso,
    _id_recurso,
    _tramos_para_recurso_session,
    normalizar_fecha_local,
    turno_cabe_en_tramos,
)


_ZONA_AGENDA = ZoneInfo('America/Argentina/Mendoza')


class ErrorConsultaDisponibilidad(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


def _hora_local(fecha, minuto: int) -> datetime:
    if minuto == 1440:
        fecha = fecha + timedelta(days=1)
        minuto = 0
    return datetime.combine(fecha, time(minuto // 60, minuto % 60), _ZONA_AGENDA)


def calcular_opciones_disponibilidad(engine, *, fecha: object,
                                     profesional_id: object, box_id: object,
                                     duracion_minutos: object,
                                     profesional_vinculado_id: object | None = None
                                     ) -> dict[str, object]:
    """Devuelve opciones que caben en horarios y no cruzan ocupaciones conocidas."""
    try:
        fecha_local = normalizar_fecha_local(fecha)
        profesional_id = _id_recurso(profesional_id)
        box_id = _id_recurso(box_id)
        if profesional_vinculado_id is not None:
            profesional_vinculado_id = _id_recurso(profesional_vinculado_id)
            if profesional_id != profesional_vinculado_id:
                raise ErrorConsultaDisponibilidad(
                    'permiso_denegado', 'Sólo puede consultar su propia disponibilidad.', 403)
    except ErrorDisponibilidad as exc:
        raise ErrorConsultaDisponibilidad('entrada_invalida', str(exc), 422) from exc
    if type(duracion_minutos) is not int or duracion_minutos <= 0:
        raise ErrorConsultaDisponibilidad(
            'entrada_invalida', 'La duración debe ser un entero positivo.', 422)

    try:
        with Session(engine) as session:
            profesional = _exigir_recurso(session, 'profesional', profesional_id)
            box = _exigir_recurso(session, 'box', box_id)
            if not profesional.activo or not box.activo or duracion_minutos > 1440:
                return {'fecha': fecha_local.isoformat(), 'items': []}

            tramos_profesional = _tramos_para_recurso_session(
                session, profesional_id, 'profesional_id', fecha_local,
                fecha_local.isoweekday())
            tramos_box = _tramos_para_recurso_session(
                session, box_id, 'box_id', fecha_local, fecha_local.isoweekday())
            inicio_dia_minuto = _minutos(_hora_local(fecha_local, 0).astimezone(timezone.utc))
            fin_dia_minuto = _minutos(_hora_local(fecha_local, 1440).astimezone(timezone.utc))
            bloqueos = session.scalars(select(BloqueoAgenda).where(
                or_(BloqueoAgenda.profesional_id == profesional_id,
                    BloqueoAgenda.box_id == box_id),
                BloqueoAgenda.inicio_minuto < fin_dia_minuto,
                BloqueoAgenda.fin_minuto > inicio_dia_minuto)).all()
            ocupados = session.scalars(select(Turno).where(
                Turno.estado.in_(('reservado', 'confirmado')),
                or_(Turno.profesional_id == profesional_id,
                    Turno.box_id == box_id),
                Turno.inicio_minuto < fin_dia_minuto,
                Turno.fin_minuto > inicio_dia_minuto)).all()

            opciones = []
            for minuto_inicio in range(0, 1440, 15):
                minuto_fin = minuto_inicio + duracion_minutos
                if minuto_fin > 1440:
                    continue
                inicio = _hora_local(fecha_local, minuto_inicio)
                fin = _hora_local(fecha_local, minuto_fin)
                inicio_utc = inicio.astimezone(timezone.utc)
                fin_utc = fin.astimezone(timezone.utc)
                if (not turno_cabe_en_tramos(inicio_utc, fin_utc, tramos_profesional)
                        or not turno_cabe_en_tramos(inicio_utc, fin_utc, tramos_box)):
                    continue
                inicio_minuto = _minutos(inicio_utc)
                fin_minuto = _minutos(fin_utc)
                if any(b.inicio_minuto < fin_minuto and b.fin_minuto > inicio_minuto
                       for b in bloqueos):
                    continue
                if any(t.inicio_minuto < fin_minuto and t.fin_minuto > inicio_minuto
                       for t in ocupados):
                    continue
                opciones.append({'inicio': inicio_utc, 'fin': fin_utc})
            return {'fecha': fecha_local.isoformat(), 'items': opciones}
    except ErrorDisponibilidad as exc:
        raise ErrorConsultaDisponibilidad(exc.codigo, str(exc), exc.estado) from exc
    except SQLAlchemyError as exc:
        raise ErrorConsultaDisponibilidad(
            'almacenamiento_error', 'No se pudo consultar la disponibilidad.', 503) from exc
