"""Administración y validación de la disponibilidad ficticia de agenda."""
from datetime import date, datetime, timedelta, timezone
import re
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.agenda import ErrorAgenda, _fecha_utc, _minutos
from odontologia.audit import ErrorAuditoria, registrar_evento_session
from odontologia.db.models import (
    AgendaMutex,
    BloqueoAgenda,
    Box,
    ExcepcionHorario,
    HorarioSemanal,
    Profesional,
    Turno,
    TramoExcepcion,
)


class ErrorDisponibilidad(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


_ZONA_AGENDA = ZoneInfo('America/Argentina/Mendoza')


def turno_cabe_en_tramos(inicio_utc: datetime, fin_utc: datetime,
                         tramos: list[tuple[int, int]]) -> bool:
    """Evaluar un turno contra tramos locales ya seleccionados por recurso/fecha."""
    inicio_local = inicio_utc.astimezone(_ZONA_AGENDA)
    fin_local = fin_utc.astimezone(_ZONA_AGENDA)
    if inicio_local.date() == fin_local.date():
        minuto_fin = fin_local.hour * 60 + fin_local.minute
    elif (fin_local.date() == inicio_local.date() + timedelta(days=1)
          and fin_local.hour == 0 and fin_local.minute == 0):
        minuto_fin = 1440
    else:
        return False
    minuto_inicio = inicio_local.hour * 60 + inicio_local.minute
    return any(desde <= minuto_inicio and minuto_fin <= hasta
               for desde, hasta in tramos)


def validar_disponibilidad_sqlite(conexion, inicio_utc: datetime, fin_utc: datetime,
                                  inicio_minuto: int, fin_minuto: int,
                                  profesional_id: str, box_id: str) -> None:
    inicio_local = inicio_utc.astimezone(_ZONA_AGENDA)
    dia_iso = inicio_local.isoweekday()
    fecha = inicio_local.date().isoformat()
    recursos = (
        (profesional_id, 'profesional_id'),
        (box_id, 'box_id'),
    )
    for recurso_id, columna in recursos:
        excepcion = conexion.execute(
            f'SELECT id FROM excepciones_horario WHERE {columna}=? AND fecha_local=?',
            (recurso_id, fecha)).fetchone()
        if excepcion is not None:
            filas = conexion.execute(
                'SELECT inicio_minuto_local, fin_minuto_local FROM tramos_excepcion '
                'WHERE excepcion_id=? ORDER BY inicio_minuto_local', (excepcion[0],)).fetchall()
        else:
            filas = conexion.execute(
                f'SELECT inicio_minuto_local, fin_minuto_local FROM horarios_semanales '
                f'WHERE {columna}=? AND dia_iso=? ORDER BY inicio_minuto_local',
                (recurso_id, dia_iso)).fetchall()
        if not turno_cabe_en_tramos(inicio_utc, fin_utc, filas):
            raise ErrorAgenda('fuera_de_disponibilidad')

    bloqueado = conexion.execute(
        'SELECT 1 FROM bloqueos_agenda WHERE '
        '((profesional_id=? AND inicio_minuto < ? AND fin_minuto > ?) OR '
        '(box_id=? AND inicio_minuto < ? AND fin_minuto > ?)) LIMIT 1',
        (profesional_id, fin_minuto, inicio_minuto,
         box_id, fin_minuto, inicio_minuto)).fetchone()
    if bloqueado is not None:
        raise ErrorAgenda('fuera_de_disponibilidad')


def validar_disponibilidad_session(session: Session, inicio_utc: datetime, fin_utc: datetime,
                                   inicio_minuto: int, fin_minuto: int,
                                   profesional_id: str, box_id: str) -> None:
    inicio_local = inicio_utc.astimezone(_ZONA_AGENDA)
    recursos = (
        (profesional_id, 'profesional_id'),
        (box_id, 'box_id'),
    )
    for recurso_id, columna in recursos:
        filas = _tramos_para_recurso_session(
            session, recurso_id, columna, inicio_local.date(), inicio_local.isoweekday())
        if not turno_cabe_en_tramos(inicio_utc, fin_utc, filas):
            raise ErrorAgenda('fuera_de_disponibilidad')

    bloqueado = session.scalar(select(BloqueoAgenda.id).where(
        ((BloqueoAgenda.profesional_id == profesional_id)
         | (BloqueoAgenda.box_id == box_id)),
        BloqueoAgenda.inicio_minuto < fin_minuto,
        BloqueoAgenda.fin_minuto > inicio_minuto,
    ).limit(1))
    if bloqueado is not None:
        raise ErrorAgenda('fuera_de_disponibilidad')


def _tramos_para_recurso_session(session: Session, recurso_id: str, columna: str,
                                 fecha_local: date, dia_iso: int):
    excepcion = session.scalar(select(ExcepcionHorario).where(
        getattr(ExcepcionHorario, columna) == recurso_id,
        ExcepcionHorario.fecha_local == fecha_local))
    if excepcion is not None:
        return session.execute(select(
            TramoExcepcion.inicio_minuto_local, TramoExcepcion.fin_minuto_local
        ).where(TramoExcepcion.excepcion_id == excepcion.id).order_by(
            TramoExcepcion.inicio_minuto_local)).all()
    return session.execute(select(
        HorarioSemanal.inicio_minuto_local, HorarioSemanal.fin_minuto_local
    ).where(
        getattr(HorarioSemanal, columna) == recurso_id,
        HorarioSemanal.dia_iso == dia_iso,
    ).order_by(HorarioSemanal.inicio_minuto_local)).all()


_RECURSOS = {
    'profesional': (Profesional, 'profesional_id'),
    'box': (Box, 'box_id'),
}
_HORA = re.compile(r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$')
_HORA_FINAL = re.compile(r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]|24:00$')


def _error_entrada(mensaje='Los datos de disponibilidad no son válidos.'):
    return ErrorDisponibilidad('entrada_invalida', mensaje, 422)


def _recurso(tipo_recurso: object):
    if not isinstance(tipo_recurso, str) or tipo_recurso not in _RECURSOS:
        raise _error_entrada('El tipo de recurso debe ser profesional o box.')
    return _RECURSOS[tipo_recurso]


def _id_recurso(recurso_id: object) -> str:
    if (not isinstance(recurso_id, str) or not recurso_id or len(recurso_id) > 64
            or recurso_id.strip() != recurso_id):
        raise _error_entrada('El identificador del recurso no es válido.')
    return recurso_id


def _minuto_hora(valor: object, *, final: bool) -> int:
    expresion = _HORA_FINAL if final else _HORA
    if not isinstance(valor, str) or expresion.fullmatch(valor) is None:
        raise _error_entrada('La hora local debe usar HH:MM.')
    if valor == '24:00':
        return 1440
    return int(valor[:2]) * 60 + int(valor[3:])


def normalizar_tramos_locales(tramos: object) -> tuple[tuple[int, int], ...]:
    if not isinstance(tramos, list):
        raise _error_entrada('Los tramos deben ser una lista.')
    normalizados = []
    for tramo in tramos:
        if not isinstance(tramo, dict) or set(tramo) != {'inicio', 'fin'}:
            raise _error_entrada('Cada tramo debe incluir inicio y fin.')
        inicio = _minuto_hora(tramo['inicio'], final=False)
        fin = _minuto_hora(tramo['fin'], final=True)
        if inicio >= fin:
            raise _error_entrada('El fin del tramo debe ser posterior al inicio.')
        normalizados.append((inicio, fin))
    normalizados.sort()
    if any(anterior[1] > siguiente[0]
           for anterior, siguiente in zip(normalizados, normalizados[1:])):
        raise _error_entrada('Los tramos de un día no pueden solaparse.')
    return tuple(normalizados)


def normalizar_horario_semanal(dias: object) -> dict[int, tuple[tuple[int, int], ...]]:
    if not isinstance(dias, dict):
        raise _error_entrada('El horario debe ser un objeto por día ISO.')
    resultado = {}
    for clave, tramos in dias.items():
        if type(clave) is int:
            dia = clave
        elif isinstance(clave, str) and re.fullmatch(r'[1-7]', clave):
            dia = int(clave)
        else:
            raise _error_entrada('El día debe ser un número ISO del 1 al 7.')
        if dia in resultado or not 1 <= dia <= 7:
            raise _error_entrada('El día debe aparecer una sola vez y estar entre 1 y 7.')
        resultado[dia] = normalizar_tramos_locales(tramos)
    return resultado


def normalizar_fecha_local(fecha: object) -> date:
    if not isinstance(fecha, str):
        raise _error_entrada('La fecha local debe usar YYYY-MM-DD.')
    try:
        normalizada = date.fromisoformat(fecha)
    except ValueError as exc:
        raise _error_entrada('La fecha local debe usar YYYY-MM-DD.') from exc
    if normalizada.isoformat() != fecha:
        raise _error_entrada('La fecha local debe usar YYYY-MM-DD.')
    return normalizada


def normalizar_intervalo_bloqueo(inicio: object, fin: object) -> tuple[datetime, datetime]:
    try:
        inicio_utc = _fecha_utc(inicio, 'inicio')
        fin_utc = _fecha_utc(fin, 'fin')
    except ErrorAgenda as exc:
        raise _error_entrada('El bloqueo requiere instantes con offset y precisión de minuto.') from exc
    if inicio_utc >= fin_utc:
        raise _error_entrada('El fin del bloqueo debe ser posterior al inicio.')
    return inicio_utc, fin_utc


def _iniciar_escritura(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
        return
    mutex = session.scalar(select(AgendaMutex.id).where(
        AgendaMutex.id == 1).with_for_update())
    if mutex != 1:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'El esquema de agenda no está preparado.', 503)


def _exigir_recurso(session: Session, tipo_recurso: str, recurso_id: str):
    modelo, _ = _recurso(tipo_recurso)
    recurso = session.get(modelo, recurso_id)
    if recurso is None:
        raise ErrorDisponibilidad('recurso_desconocido', 'El recurso no existe.', 404)
    return recurso


def _registrar(session: Session, *, accion: str, tipo: str,
               recurso_id: str, actor_id: str | None) -> None:
    if actor_id is not None:
        registrar_evento_session(
            session, action=accion, resource_type=tipo,
            resource_id=recurso_id, actor_id=actor_id, result='confirmado')


def _validar_turnos_existentes(session: Session, tipo_recurso: str, recurso_id: str,
                               *, fecha_local: date | None = None) -> None:
    _, columna = _recurso(tipo_recurso)
    consulta = select(Turno).where(getattr(Turno, columna) == recurso_id)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    for turno in session.scalars(consulta):
        inicio = epoch + timedelta(minutes=turno.inicio_minuto)
        fin = epoch + timedelta(minutes=turno.fin_minuto)
        inicio_local = inicio.astimezone(_ZONA_AGENDA)
        if fecha_local is not None and inicio_local.date() != fecha_local:
            continue
        tramos = _tramos_para_recurso_session(
            session, recurso_id, columna, inicio_local.date(), inicio_local.isoweekday())
        if not turno_cabe_en_tramos(inicio, fin, tramos):
            raise ErrorDisponibilidad(
                'turnos_afectados', 'El cambio dejaría un turno existente fuera de agenda.', 409
            )


def _exigir_sin_turnos_solapados(session: Session, tipo_recurso: str, recurso_id: str,
                                 inicio_minuto: int, fin_minuto: int) -> None:
    _, columna = _recurso(tipo_recurso)
    turno_id = session.scalar(select(Turno.id).where(
        getattr(Turno, columna) == recurso_id,
        Turno.inicio_minuto < fin_minuto,
        Turno.fin_minuto > inicio_minuto,
    ).limit(1))
    if turno_id is not None:
        raise ErrorDisponibilidad(
            'turnos_afectados', 'El bloqueo se superpone con un turno existente.', 409)


def _hora_publica(minuto: int) -> str:
    if minuto == 1440:
        return '24:00'
    return f'{minuto // 60:02d}:{minuto % 60:02d}'


def _publicar_tramos(tramos) -> list[dict[str, str]]:
    return [{'inicio': _hora_publica(t.inicio_minuto_local),
             'fin': _hora_publica(t.fin_minuto_local)} for t in tramos]


def _publicar_horario(tipo_recurso: str, recurso_id: str, filas) -> dict[str, object]:
    dias = {str(dia): [] for dia in range(1, 8)}
    for fila in filas:
        dias[str(fila.dia_iso)].append({
            'inicio': _hora_publica(fila.inicio_minuto_local),
            'fin': _hora_publica(fila.fin_minuto_local),
        })
    return {'tipo_recurso': tipo_recurso, 'recurso_id': recurso_id, 'dias': dias}


def obtener_horario(engine, tipo_recurso: str, recurso_id: str) -> dict[str, object]:
    _, columna = _recurso(tipo_recurso)
    recurso_id = _id_recurso(recurso_id)
    try:
        with Session(engine) as session:
            _exigir_recurso(session, tipo_recurso, recurso_id)
            filas = session.scalars(select(HorarioSemanal).where(
                getattr(HorarioSemanal, columna) == recurso_id
            ).order_by(HorarioSemanal.dia_iso, HorarioSemanal.inicio_minuto_local)).all()
            return _publicar_horario(tipo_recurso, recurso_id, filas)
    except ErrorDisponibilidad:
        raise
    except SQLAlchemyError as exc:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'No se pudo consultar el horario.', 503) from exc


def guardar_horario(engine, tipo_recurso: str, recurso_id: str, dias: object,
                    *, actor_id: str | None = None) -> dict[str, object]:
    _, columna = _recurso(tipo_recurso)
    recurso_id = _id_recurso(recurso_id)
    normalizados = normalizar_horario_semanal(dias)
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            _exigir_recurso(session, tipo_recurso, recurso_id)
            session.execute(delete(HorarioSemanal).where(
                getattr(HorarioSemanal, columna) == recurso_id))
            filas = []
            for dia, tramos in normalizados.items():
                for inicio, fin in tramos:
                    datos = {
                        'id': str(uuid4()), columna: recurso_id, 'dia_iso': dia,
                        'inicio_minuto_local': inicio, 'fin_minuto_local': fin,
                    }
                    fila = HorarioSemanal(**datos)
                    filas.append(fila)
                    session.add(fila)
            session.flush()
            _validar_turnos_existentes(session, tipo_recurso, recurso_id)
            _registrar(session, accion='horario.actualizado', tipo='horario',
                       recurso_id=recurso_id, actor_id=actor_id)
            resultado = _publicar_horario(
                tipo_recurso, recurso_id,
                sorted(filas, key=lambda fila: (fila.dia_iso, fila.inicio_minuto_local)))
        return resultado
    except ErrorDisponibilidad:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'No se pudo guardar el horario.', 503) from exc


def obtener_excepcion(engine, tipo_recurso: str, recurso_id: str,
                      fecha: object) -> dict[str, object] | None:
    _, columna = _recurso(tipo_recurso)
    recurso_id = _id_recurso(recurso_id)
    fecha_local = normalizar_fecha_local(fecha)
    try:
        with Session(engine) as session:
            _exigir_recurso(session, tipo_recurso, recurso_id)
            excepcion = session.scalar(select(ExcepcionHorario).where(
                getattr(ExcepcionHorario, columna) == recurso_id,
                ExcepcionHorario.fecha_local == fecha_local,
            ))
            if excepcion is None:
                return None
            tramos = session.scalars(select(TramoExcepcion).where(
                TramoExcepcion.excepcion_id == excepcion.id
            ).order_by(TramoExcepcion.inicio_minuto_local)).all()
            return {
                'id': excepcion.id, 'tipo_recurso': tipo_recurso, 'recurso_id': recurso_id,
                'fecha': fecha_local.isoformat(), 'tramos': _publicar_tramos(tramos),
            }
    except ErrorDisponibilidad:
        raise
    except SQLAlchemyError as exc:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'No se pudo consultar la excepción.', 503) from exc


def guardar_excepcion(engine, tipo_recurso: str, recurso_id: str, fecha: object,
                      tramos: object, *, actor_id: str | None = None) -> dict[str, object]:
    modelo_recurso, columna = _recurso(tipo_recurso)
    recurso_id = _id_recurso(recurso_id)
    fecha_local = normalizar_fecha_local(fecha)
    normalizados = normalizar_tramos_locales(tramos)
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            _exigir_recurso(session, tipo_recurso, recurso_id)
            excepcion = session.scalar(select(ExcepcionHorario).where(
                getattr(ExcepcionHorario, columna) == recurso_id,
                ExcepcionHorario.fecha_local == fecha_local,
            ))
            creada = excepcion is None
            if creada:
                excepcion = ExcepcionHorario(
                    id=str(uuid4()), **{columna: recurso_id}, fecha_local=fecha_local)
                session.add(excepcion)
                accion = 'excepcion.creada'
            else:
                session.execute(delete(TramoExcepcion).where(
                    TramoExcepcion.excepcion_id == excepcion.id))
                accion = 'excepcion.actualizada'
            for inicio, fin in normalizados:
                session.add(TramoExcepcion(
                    id=str(uuid4()), excepcion_id=excepcion.id,
                    inicio_minuto_local=inicio, fin_minuto_local=fin))
            session.flush()
            _validar_turnos_existentes(
                session, tipo_recurso, recurso_id, fecha_local=fecha_local)
            _registrar(session, accion=accion, tipo='excepcion',
                       recurso_id=excepcion.id, actor_id=actor_id)
            resultado = {
                'id': excepcion.id, 'tipo_recurso': tipo_recurso, 'recurso_id': recurso_id,
                'fecha': fecha_local.isoformat(),
                'tramos': [{'inicio': _hora_publica(inicio), 'fin': _hora_publica(fin)}
                           for inicio, fin in normalizados],
            }
        return resultado
    except ErrorDisponibilidad:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'No se pudo guardar la excepción.', 503) from exc


def eliminar_excepcion(engine, tipo_recurso: str, recurso_id: str, fecha: object,
                       *, actor_id: str | None = None) -> None:
    _, columna = _recurso(tipo_recurso)
    recurso_id = _id_recurso(recurso_id)
    fecha_local = normalizar_fecha_local(fecha)
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            _exigir_recurso(session, tipo_recurso, recurso_id)
            excepcion = session.scalar(select(ExcepcionHorario).where(
                getattr(ExcepcionHorario, columna) == recurso_id,
                ExcepcionHorario.fecha_local == fecha_local,
            ))
            if excepcion is None:
                raise ErrorDisponibilidad('recurso_desconocido', 'La excepción no existe.', 404)
            session.execute(delete(TramoExcepcion).where(
                TramoExcepcion.excepcion_id == excepcion.id))
            excepcion_id = excepcion.id
            session.delete(excepcion)
            session.flush()
            _validar_turnos_existentes(
                session, tipo_recurso, recurso_id, fecha_local=fecha_local)
            _registrar(session, accion='excepcion.eliminada', tipo='excepcion',
                       recurso_id=excepcion_id, actor_id=actor_id)
    except ErrorDisponibilidad:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'No se pudo eliminar la excepción.', 503) from exc


def _publicar_bloqueo(bloqueo: BloqueoAgenda) -> dict[str, object]:
    if bloqueo.profesional_id is not None:
        tipo, recurso_id = 'profesional', bloqueo.profesional_id
    else:
        tipo, recurso_id = 'box', bloqueo.box_id
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    inicio = epoch + timedelta(minutes=bloqueo.inicio_minuto)
    fin = epoch + timedelta(minutes=bloqueo.fin_minuto)
    return {
        'id': bloqueo.id, 'tipo_recurso': tipo, 'recurso_id': recurso_id,
        'inicio': inicio, 'fin': fin,
    }


def listar_bloqueos(engine, *, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise _error_entrada('El límite de página debe estar entre 1 y 100.')
    if type(offset) is not int or offset < 0:
        raise _error_entrada('El desplazamiento de página no puede ser negativo.')
    try:
        with Session(engine) as session:
            filas = session.scalars(select(BloqueoAgenda).order_by(
                BloqueoAgenda.inicio_minuto, BloqueoAgenda.id
            ).limit(limit).offset(offset)).all()
            return [_publicar_bloqueo(fila) for fila in filas]
    except SQLAlchemyError as exc:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'No se pudieron consultar los bloqueos.', 503) from exc


def crear_bloqueo(engine, tipo_recurso: str, recurso_id: str, inicio: object, fin: object,
                  *, actor_id: str | None = None) -> dict[str, object]:
    _, columna = _recurso(tipo_recurso)
    recurso_id = _id_recurso(recurso_id)
    inicio_utc, fin_utc = normalizar_intervalo_bloqueo(inicio, fin)
    bloqueo = BloqueoAgenda(
        id=str(uuid4()), **{columna: recurso_id},
        inicio_minuto=_minutos(inicio_utc), fin_minuto=_minutos(fin_utc))
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            _exigir_recurso(session, tipo_recurso, recurso_id)
            session.add(bloqueo)
            session.flush()
            _exigir_sin_turnos_solapados(
                session, tipo_recurso, recurso_id,
                bloqueo.inicio_minuto, bloqueo.fin_minuto)
            _registrar(session, accion='bloqueo.creado', tipo='bloqueo',
                       recurso_id=bloqueo.id, actor_id=actor_id)
            resultado = _publicar_bloqueo(bloqueo)
        return resultado
    except ErrorDisponibilidad:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'No se pudo guardar el bloqueo.', 503) from exc


def eliminar_bloqueo(engine, bloqueo_id: str, *, actor_id: str | None = None) -> None:
    if not isinstance(bloqueo_id, str) or not bloqueo_id:
        raise _error_entrada('El identificador del bloqueo no es válido.')
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            bloqueo = session.get(BloqueoAgenda, bloqueo_id)
            if bloqueo is None:
                raise ErrorDisponibilidad('recurso_desconocido', 'El bloqueo no existe.', 404)
            identificador = bloqueo.id
            session.delete(bloqueo)
            _registrar(session, accion='bloqueo.eliminado', tipo='bloqueo',
                       recurso_id=identificador, actor_id=actor_id)
    except ErrorDisponibilidad:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorDisponibilidad(
            'almacenamiento_error', 'No se pudo eliminar el bloqueo.', 503) from exc
