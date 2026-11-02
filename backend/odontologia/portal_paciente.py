"""Servicios locales de autoservicio para cuentas de paciente sintéticas."""
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
import sqlite3
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.agenda import ErrorAgenda, _minutos
from odontologia.audit import ErrorAuditoria, registrar_evento_session
from odontologia.db.models import (
    AgendaMutex, Box, IdempotenciaPortalPaciente, Paciente, Profesional, Turno,
)
from odontologia.disponibilidad import validar_disponibilidad_session


_ZONA = ZoneInfo('America/Argentina/Mendoza')
_DURACION_MINUTOS = 30
_ESTADOS_ACTIVOS = ('reservado', 'confirmado')
_OPERACIONES = {'reserva', 'cancelacion', 'reprogramacion'}


class ErrorPortalPaciente(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


def _ahora(valor: datetime | None) -> datetime:
    resultado = valor or datetime.now(timezone.utc)
    if resultado.tzinfo is None or resultado.utcoffset() is None:
        raise ErrorPortalPaciente('entrada_invalida', 'Se requiere zona horaria.', 422)
    return resultado.astimezone(timezone.utc)


def _fecha_portal(valor: object, ahora: datetime) -> date:
    try:
        fecha = date.fromisoformat(valor) if isinstance(valor, str) else valor
    except ValueError as exc:
        raise ErrorPortalPaciente('entrada_invalida', 'La fecha no es válida.', 422) from exc
    hoy = ahora.astimezone(_ZONA).date()
    if type(fecha) is not date or not hoy <= fecha <= hoy + timedelta(days=31):
        raise ErrorPortalPaciente('entrada_invalida', 'La fecha excede el horizonte permitido.', 422)
    return fecha


def _parsear_inicio_turno(valor: object) -> datetime:
    if isinstance(valor, str):
        try:
            valor = datetime.fromisoformat(valor)
        except ValueError as exc:
            raise ErrorPortalPaciente(
                'entrada_invalida', 'El inicio requiere ISO 8601 con offset.', 422) from exc
    if (not isinstance(valor, datetime) or valor.tzinfo is None
            or valor.utcoffset() is None or valor.second or valor.microsecond):
        raise ErrorPortalPaciente('entrada_invalida', 'El inicio requiere ISO 8601 con offset.', 422)
    inicio = valor.astimezone(timezone.utc)
    local = inicio.astimezone(_ZONA)
    if local.minute % 15 != 0:
        raise ErrorPortalPaciente('entrada_invalida', 'El inicio está fuera del rango permitido.', 422)
    if (inicio + timedelta(minutes=_DURACION_MINUTOS)).astimezone(_ZONA).date() != local.date():
        raise ErrorPortalPaciente('entrada_invalida', 'El turno debe terminar el mismo día local.', 422)
    return inicio


def _validar_vigencia_inicio(inicio: datetime, ahora: datetime) -> None:
    local = inicio.astimezone(_ZONA)
    hoy = ahora.astimezone(_ZONA).date()
    if (inicio <= ahora or not hoy <= local.date() <= hoy + timedelta(days=31)):
        raise ErrorPortalPaciente('entrada_invalida', 'El inicio está fuera del rango permitido.', 422)


def _bloquear(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
        return
    mutex = session.scalar(select(AgendaMutex.id).where(
        AgendaMutex.id == 1).with_for_update())
    if mutex != 1:
        raise ErrorPortalPaciente('almacenamiento_error', 'Agenda no disponible.', 503)


def _fingerprint(payload: dict[str, object]) -> str:
    normalizado = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalizado.encode('utf-8')).hexdigest()


def _validar_clave(clave: object) -> str:
    if not isinstance(clave, str) or not 1 <= len(clave) <= 128 or clave.strip() != clave:
        raise ErrorPortalPaciente('entrada_invalida', 'Idempotency-Key no válida.', 422)
    return clave


def _idempotente(session: Session, *, paciente_id: str, operacion: str,
                 clave: str, fingerprint: str) -> dict[str, object] | None:
    existente = session.scalar(select(IdempotenciaPortalPaciente).where(
        IdempotenciaPortalPaciente.paciente_id == paciente_id,
        IdempotenciaPortalPaciente.operacion == operacion,
        IdempotenciaPortalPaciente.clave == clave))
    if existente is None:
        return None
    if existente.fingerprint != fingerprint:
        raise ErrorPortalPaciente('idempotencia_conflictiva', 'La clave ya fue utilizada.', 409)
    return json.loads(existente.respuesta_json)


def _guardar_idempotencia(session: Session, *, paciente_id: str, operacion: str,
                          clave: str, fingerprint: str, turno_id: int,
                          respuesta: dict[str, object], ahora: datetime) -> None:
    session.add(IdempotenciaPortalPaciente(
        id=__import__('uuid').uuid4().hex, paciente_id=paciente_id,
        operacion=operacion, clave=clave, fingerprint=fingerprint,
        turno_id=turno_id,
        respuesta_json=json.dumps(respuesta, sort_keys=True, separators=(',', ':')),
        created_at=ahora))
    session.flush()


def _respuesta(turno: Turno) -> dict[str, object]:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return {
        'turno_id': turno.id,
        'inicio': (epoch + timedelta(minutes=turno.inicio_minuto)).isoformat(),
        'fin': (epoch + timedelta(minutes=turno.fin_minuto)).isoformat(),
        'estado': turno.estado,
        'version': turno.version,
    }


def _auditar(session: Session, *, action: str, actor_id: str,
             resource_id: str | None = None, result: str = 'confirmado') -> None:
    registrar_evento_session(
        session, action=action,
        resource_type='turno' if resource_id else 'portal',
        resource_id=resource_id, actor_id=actor_id, result=result)


def consultar_disponibilidad_portal(engine, *, paciente_id: str, actor_id: str,
                                    fecha: object, ahora: datetime | None = None
                                    ) -> dict[str, object]:
    reloj = _ahora(ahora)
    fecha_local = _fecha_portal(fecha, reloj)
    inicio_dia = datetime.combine(fecha_local, time.min, _ZONA).astimezone(timezone.utc)
    opciones: dict[tuple[datetime, datetime], None] = {}
    try:
        with Session(engine) as session, session.begin():
            profesionales = session.scalars(select(Profesional).where(
                Profesional.activo.is_(True)).order_by(Profesional.id)).all()
            boxes = session.scalars(select(Box).where(Box.activo.is_(True)).order_by(Box.id)).all()
            for profesional in profesionales:
                for box in boxes:
                    for minuto in range(0, 1440, 15):
                        inicio_local = datetime.combine(
                            fecha_local, time(minuto // 60, minuto % 60), _ZONA)
                        inicio = inicio_local.astimezone(timezone.utc)
                        fin = inicio + timedelta(minutes=_DURACION_MINUTOS)
                        if (inicio < inicio_dia or inicio <= reloj
                                or fin.astimezone(_ZONA).date() != fecha_local):
                            continue
                        inicio_minuto, fin_minuto = _minutos(inicio), _minutos(fin)
                        try:
                            validar_disponibilidad_session(
                                session, inicio, fin, inicio_minuto, fin_minuto,
                                profesional.id, box.id)
                        except ErrorAgenda as exc:
                            if exc.codigo == 'fuera_de_disponibilidad':
                                continue
                            raise
                        ocupado = session.scalar(select(Turno.id).where(
                            Turno.estado.in_(_ESTADOS_ACTIVOS),
                            ((Turno.profesional_id == profesional.id)
                             | (Turno.box_id == box.id)),
                            Turno.inicio_minuto < fin_minuto,
                            Turno.fin_minuto > inicio_minuto).limit(1))
                        if ocupado is None:
                            opciones[(inicio, fin)] = None
            _auditar(session, action='portal.disponibilidad.consultada', actor_id=actor_id)
        return {'fecha': fecha_local.isoformat(), 'items': [
            {'inicio': inicio, 'fin': fin}
            for inicio, fin in sorted(opciones)]}
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudo consultar disponibilidad.', 503) from exc


def listar_turnos_portal(engine, *, paciente_id: str, actor_id: str) -> dict[str, object]:
    try:
        with Session(engine) as session, session.begin():
            filas = session.scalars(select(Turno).where(
                Turno.paciente_id == paciente_id).order_by(Turno.inicio_minuto, Turno.id)).all()
            _auditar(session, action='portal.turnos.consultados', actor_id=actor_id)
            return {'items': [_respuesta(turno) for turno in filas]}
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudieron consultar los turnos.', 503) from exc


def _buscar_par_libre(session: Session, *, inicio: datetime, fin: datetime,
                      excluir_turno_id: int | None = None):
    inicio_minuto, fin_minuto = _minutos(inicio), _minutos(fin)
    profesionales = session.scalars(select(Profesional).where(
        Profesional.activo.is_(True)).order_by(Profesional.id)).all()
    boxes = session.scalars(select(Box).where(Box.activo.is_(True)).order_by(Box.id)).all()
    for profesional in profesionales:
        for box in boxes:
            try:
                validar_disponibilidad_session(
                    session, inicio, fin, inicio_minuto, fin_minuto,
                    profesional.id, box.id)
            except ErrorAgenda as exc:
                if exc.codigo == 'fuera_de_disponibilidad':
                    continue
                raise
            ocupado = session.scalar(select(Turno.id).where(
                *([] if excluir_turno_id is None else [Turno.id != excluir_turno_id]),
                Turno.estado.in_(_ESTADOS_ACTIVOS),
                ((Turno.profesional_id == profesional.id) | (Turno.box_id == box.id)),
                Turno.inicio_minuto < fin_minuto,
                Turno.fin_minuto > inicio_minuto).limit(1))
            if ocupado is None:
                return profesional, box, inicio_minuto, fin_minuto
    return None


def reservar_turno_paciente(engine, *, paciente_id: str, actor_id: str,
                            inicio: object, clave: object,
                            ahora: datetime | None = None) -> dict[str, object]:
    reloj = _ahora(ahora)
    comienzo = _parsear_inicio_turno(inicio)
    clave = _validar_clave(clave)
    huella = _fingerprint({'inicio': comienzo.isoformat()})
    fin = comienzo + timedelta(minutes=_DURACION_MINUTOS)
    try:
        with Session(engine) as session, session.begin():
            _bloquear(session)
            paciente = session.get(Paciente, paciente_id)
            if paciente is None or not paciente.activo:
                raise ErrorPortalPaciente('sesion_invalida', 'La sesión no es válida.', 401)
            repetida = _idempotente(
                session, paciente_id=paciente_id, operacion='reserva',
                clave=clave, fingerprint=huella)
            if repetida is not None:
                return repetida
            _validar_vigencia_inicio(comienzo, reloj)
            cantidad = len(session.scalars(select(Turno.id).where(
                Turno.paciente_id == paciente_id, Turno.estado.in_(_ESTADOS_ACTIVOS),
                Turno.inicio_minuto > _minutos(reloj)).limit(3)).all())
            if cantidad >= 3:
                raise ErrorPortalPaciente('limite_turnos', 'Se alcanzó el límite de turnos.', 409)
            par = _buscar_par_libre(session, inicio=comienzo, fin=fin)
            if par is None:
                raise ErrorPortalPaciente('fuera_de_disponibilidad', 'La franja ya no está disponible.', 409)
            profesional, box, inicio_minuto, fin_minuto = par
            turno = Turno(
                paciente_id=paciente_id, profesional_id=profesional.id, box_id=box.id,
                inicio_minuto=inicio_minuto, fin_minuto=fin_minuto,
                estado='reservado', version=1)
            session.add(turno)
            session.flush()
            respuesta = _respuesta(turno)
            _guardar_idempotencia(
                session, paciente_id=paciente_id, operacion='reserva', clave=clave,
                fingerprint=huella, turno_id=turno.id, respuesta=respuesta, ahora=reloj)
            _auditar(session, action='portal.turno.reservado', actor_id=actor_id,
                     resource_id=str(turno.id))
            return respuesta
    except ErrorPortalPaciente:
        raise
    except ErrorAuditoria as exc:
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudo registrar la reserva.', 503) from exc
    except SQLAlchemyError as exc:
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudo registrar la reserva.', 503) from exc


def cancelar_turno_portal(engine, *, paciente_id: str, actor_id: str, turno_id: int,
                          clave: object, ahora: datetime | None = None
                          ) -> dict[str, object]:
    reloj = _ahora(ahora)
    clave = _validar_clave(clave)
    huella = _fingerprint({'turno_id': turno_id})
    try:
        with Session(engine) as session, session.begin():
            _bloquear(session)
            turno = session.get(Turno, turno_id)
            if turno is None or turno.paciente_id != paciente_id:
                raise ErrorPortalPaciente('turno_no_encontrado', 'Turno no encontrado.', 404)
            repetida = _idempotente(
                session, paciente_id=paciente_id, operacion='cancelacion',
                clave=clave, fingerprint=huella)
            if repetida is not None:
                return repetida
            inicio = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
                minutes=turno.inicio_minuto)
            if turno.estado not in _ESTADOS_ACTIVOS or inicio < reloj + timedelta(hours=24):
                raise ErrorPortalPaciente(
                    'turno_no_reprogramable', 'El turno no puede cancelarse en este momento.', 409)
            turno.estado = 'cancelado'
            turno.version += 1
            from odontologia.recordatorios import invalidar_recordatorios_pendientes

            invalidar_recordatorios_pendientes(
                session, turno, actor_id=actor_id, ahora=reloj)
            session.flush()
            respuesta = _respuesta(turno)
            _guardar_idempotencia(
                session, paciente_id=paciente_id, operacion='cancelacion', clave=clave,
                fingerprint=huella, turno_id=turno.id, respuesta=respuesta, ahora=reloj)
            _auditar(session, action='portal.turno.cancelado', actor_id=actor_id,
                     resource_id=str(turno.id))
            return respuesta
    except ErrorPortalPaciente:
        raise
    except ErrorAuditoria as exc:
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudo cancelar el turno.', 503) from exc
    except SQLAlchemyError as exc:
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudo cancelar el turno.', 503) from exc


def reprogramar_turno_portal(engine, *, paciente_id: str, actor_id: str, turno_id: int,
                             version: int, inicio: object, clave: object,
                             ahora: datetime | None = None) -> dict[str, object]:
    reloj = _ahora(ahora)
    comienzo = _parsear_inicio_turno(inicio)
    clave = _validar_clave(clave)
    huella = _fingerprint({'turno_id': turno_id, 'version': version,
                           'inicio': comienzo.isoformat()})
    fin = comienzo + timedelta(minutes=_DURACION_MINUTOS)
    try:
        with Session(engine) as session, session.begin():
            _bloquear(session)
            turno = session.get(Turno, turno_id)
            if turno is None or turno.paciente_id != paciente_id:
                raise ErrorPortalPaciente('turno_no_encontrado', 'Turno no encontrado.', 404)
            repetida = _idempotente(
                session, paciente_id=paciente_id, operacion='reprogramacion',
                clave=clave, fingerprint=huella)
            if repetida is not None:
                return repetida
            _validar_vigencia_inicio(comienzo, reloj)
            fin = comienzo + timedelta(minutes=_DURACION_MINUTOS)
            inicio_actual = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
                minutes=turno.inicio_minuto)
            if type(version) is not int or version != turno.version:
                raise ErrorPortalPaciente(
                    'version_desactualizada', 'La versión del turno cambió.', 409)
            if (turno.estado not in _ESTADOS_ACTIVOS
                    or inicio_actual < reloj + timedelta(hours=24)):
                raise ErrorPortalPaciente(
                    'turno_no_reprogramable', 'El turno no puede reprogramarse ahora.', 409)
            par = _buscar_par_libre(
                session, inicio=comienzo, fin=fin, excluir_turno_id=turno.id)
            if par is None:
                raise ErrorPortalPaciente(
                    'fuera_de_disponibilidad', 'La franja ya no está disponible.', 409)
            profesional, box, inicio_minuto, fin_minuto = par
            estaba_confirmado = turno.estado == 'confirmado'
            if estaba_confirmado:
                from odontologia.recordatorios import invalidar_recordatorios_pendientes

                invalidar_recordatorios_pendientes(
                    session, turno, actor_id=actor_id, ahora=reloj)
            turno.profesional_id = profesional.id
            turno.box_id = box.id
            turno.inicio_minuto = inicio_minuto
            turno.fin_minuto = fin_minuto
            turno.version += 1
            session.flush()
            if estaba_confirmado:
                from odontologia.recordatorios import programar_recordatorio_confirmacion

                programar_recordatorio_confirmacion(
                    session, turno, actor_id=actor_id, ahora=reloj)
            respuesta = _respuesta(turno)
            _guardar_idempotencia(
                session, paciente_id=paciente_id, operacion='reprogramacion', clave=clave,
                fingerprint=huella, turno_id=turno.id, respuesta=respuesta, ahora=reloj)
            _auditar(session, action='portal.turno.reprogramado', actor_id=actor_id,
                     resource_id=str(turno.id))
            return respuesta
    except ErrorPortalPaciente:
        raise
    except ErrorAgenda as exc:
        if exc.codigo == 'fuera_de_disponibilidad':
            raise ErrorPortalPaciente(
                'fuera_de_disponibilidad', 'La franja ya no está disponible.', 409) from exc
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudo reprogramar el turno.', 503) from exc
    except ErrorAuditoria as exc:
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudo reprogramar el turno.', 503) from exc
    except SQLAlchemyError as exc:
        raise ErrorPortalPaciente('almacenamiento_error', 'No se pudo reprogramar el turno.', 503) from exc
