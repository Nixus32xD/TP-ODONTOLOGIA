"""Historia clínica demostrativa: evoluciones sintéticas, privadas e inmutables."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.audit import ErrorAuditoria, registrar_evento_session
from odontologia.db.models import AgendaMutex, EvolucionClinica, Paciente, Profesional, Turno, Usuario


_MAX_NOTA = 5000


class ErrorHistoriaClinica(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


def _iniciar_transaccion_clinica(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
        return
    mutex = session.scalar(
        select(AgendaMutex.id).where(AgendaMutex.id == 1).with_for_update())
    if mutex != 1:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'El esquema clínico no está preparado.', 503)


def _validar_nota(valor: object) -> str:
    if not isinstance(valor, str):
        raise ErrorHistoriaClinica('entrada_invalida', 'La nota clínica no es válida.', 422)
    nota = valor.strip()
    if (not nota or len(nota) > _MAX_NOTA
            or any(ord(caracter) < 32 and caracter not in '\n\t' for caracter in nota)):
        raise ErrorHistoriaClinica('entrada_invalida', 'La nota clínica no es válida.', 422)
    return nota


def _validar_paciente_id(valor: object) -> str:
    if not isinstance(valor, str) or not valor or len(valor) > 64 or valor.strip() != valor:
        raise ErrorHistoriaClinica('paciente_desconocido', 'La historia no está disponible.', 404)
    return valor


def _validar_pagina(limit: int, offset: int) -> None:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ErrorHistoriaClinica('entrada_invalida', 'El límite debe estar entre 1 y 100.', 422)
    if type(offset) is not int or offset < 0:
        raise ErrorHistoriaClinica('entrada_invalida', 'El offset debe ser no negativo.', 422)


def _profesional_vigente(session: Session, identidad: dict[str, object]):
    usuario_id = identidad.get('usuario_id')
    if not isinstance(usuario_id, str) or not usuario_id:
        return None
    usuario = session.scalar(select(Usuario).where(Usuario.id == usuario_id).with_for_update())
    if (usuario is None or not usuario.activo or usuario.rol != 'profesional'
            or not usuario.profesional_id
            or usuario.profesional_id != identidad.get('profesional_id')):
        return None
    profesional = session.get(Profesional, usuario.profesional_id)
    if profesional is None or not profesional.activo:
        return None
    return usuario, profesional


def _registrar_denegacion(session: Session, actor_id: str | None) -> None:
    registrar_evento_session(
        session, action='historia.denegada', resource_type='historia', result='rechazado',
        actor_id=actor_id, resource_id=None)


def _publica(evolucion: EvolucionClinica) -> dict[str, object]:
    fecha = evolucion.created_at
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return {
        'id': evolucion.id,
        'paciente_id': evolucion.paciente_id,
        'profesional_id': evolucion.profesional_id,
        'turno_id': evolucion.turno_id,
        'nota': evolucion.nota,
        'created_at': fecha.astimezone(timezone.utc).isoformat(timespec='microseconds'),
        'corrige_a_id': evolucion.corrige_a_id,
    }


def consultar_historia(engine, paciente_id: object, *, identidad: dict[str, object],
                       limit: int = 50, offset: int = 0) -> dict[str, object]:
    paciente_id = _validar_paciente_id(paciente_id)
    _validar_pagina(limit, offset)
    actor_id = identidad.get('usuario_id') if isinstance(identidad, dict) else None
    denegado: ErrorHistoriaClinica | None = None
    resultado: dict[str, object] | None = None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            autorizado = _profesional_vigente(session, identidad)
            paciente = session.get(Paciente, paciente_id) if autorizado else None
            turno_atendido = None
            if autorizado and paciente is not None:
                _usuario, profesional = autorizado
                turno_atendido = session.scalar(select(Turno.id).where(
                    Turno.paciente_id == paciente.id,
                    Turno.profesional_id == profesional.id,
                    Turno.estado == 'atendido').limit(1))
            if autorizado is None:
                _registrar_denegacion(session, actor_id)
                denegado = ErrorHistoriaClinica(
                    'permiso_denegado', 'No tiene permiso para acceder a historia clínica.', 403)
            elif paciente is None or turno_atendido is None:
                _registrar_denegacion(session, actor_id)
                denegado = ErrorHistoriaClinica(
                    'historia_no_disponible', 'La historia no está disponible.', 404)
            else:
                _usuario, profesional = autorizado
                evoluciones = session.scalars(
                    select(EvolucionClinica)
                    .join(Turno, Turno.id == EvolucionClinica.turno_id)
                    .where(
                        EvolucionClinica.paciente_id == paciente.id,
                        EvolucionClinica.profesional_id == profesional.id,
                        Turno.estado == 'atendido')
                    .order_by(EvolucionClinica.created_at, EvolucionClinica.id)
                    .limit(limit).offset(offset)).all()
                items = [_publica(evolucion) for evolucion in evoluciones]
                registrar_evento_session(
                    session, action='historia.consultada', resource_type='historia',
                    result='confirmado', actor_id=actor_id, resource_id=paciente.id)
                resultado = {'items': items, 'limit': limit, 'offset': offset}
        if denegado is not None:
            raise denegado
        assert resultado is not None
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudo consultar la historia clínica.', 503) from exc


def _crear_evolucion_en_sesion(session: Session, *, paciente_id: str, turno_id: int,
                               nota: str, identidad: dict[str, object],
                               corrige_a_id: str | None = None,
                               actor_evento: str = 'evolucion.creada'):
    actor_id = identidad.get('usuario_id')
    autorizado = _profesional_vigente(session, identidad)
    if autorizado is None:
        _registrar_denegacion(session, actor_id if isinstance(actor_id, str) else None)
        return None, ErrorHistoriaClinica(
            'permiso_denegado', 'No tiene permiso para registrar historia clínica.', 403)
    _usuario, profesional = autorizado
    turno = session.scalar(select(Turno).where(Turno.id == turno_id).with_for_update())
    if (turno is None or turno.estado != 'atendido' or turno.paciente_id != paciente_id
            or turno.profesional_id != profesional.id):
        _registrar_denegacion(session, actor_id)
        return None, ErrorHistoriaClinica(
            'atencion_no_disponible', 'La atención no está disponible.', 404)
    if session.get(Paciente, paciente_id) is None:
        _registrar_denegacion(session, actor_id)
        return None, ErrorHistoriaClinica(
            'atencion_no_disponible', 'La atención no está disponible.', 404)
    evolucion = EvolucionClinica(
        id=str(uuid4()), paciente_id=paciente_id, profesional_id=profesional.id,
        turno_id=turno.id, nota=nota, created_at=datetime.now(timezone.utc),
        corrige_a_id=corrige_a_id)
    session.add(evolucion)
    session.flush()
    registrar_evento_session(
        session, action=actor_evento, resource_type='evolucion', result='confirmado',
        actor_id=actor_id, resource_id=evolucion.id)
    return _publica(evolucion), None


def crear_evolucion(engine, *, paciente_id: object, turno_id: object,
                    nota: object, identidad: dict[str, object]) -> dict[str, object]:
    paciente_id = _validar_paciente_id(paciente_id)
    if type(turno_id) is not int or turno_id <= 0:
        raise ErrorHistoriaClinica(
            'atencion_no_disponible', 'La atención no está disponible.', 404)
    nota_validada = _validar_nota(nota)
    error: ErrorHistoriaClinica | None = None
    resultado: dict[str, object] | None = None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            resultado, error = _crear_evolucion_en_sesion(
                session, paciente_id=paciente_id, turno_id=turno_id,
                nota=nota_validada, identidad=identidad)
        if error is not None:
            raise error
        assert resultado is not None
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudo guardar la evolución clínica.', 503) from exc


def corregir_evolucion(engine, *, evolucion_id: object, nota: object,
                        identidad: dict[str, object]) -> dict[str, object]:
    if not isinstance(evolucion_id, str) or not evolucion_id or len(evolucion_id) > 36:
        raise ErrorHistoriaClinica('evolucion_no_disponible', 'La evolución no está disponible.', 404)
    nota_validada = _validar_nota(nota)
    actor_id = identidad.get('usuario_id')
    error: ErrorHistoriaClinica | None = None
    resultado: dict[str, object] | None = None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            autorizado = _profesional_vigente(session, identidad)
            if autorizado is None:
                _registrar_denegacion(session, actor_id)
                error = ErrorHistoriaClinica(
                    'permiso_denegado', 'No tiene permiso para corregir historia clínica.', 403)
            else:
                original = session.scalar(select(EvolucionClinica).where(
                    EvolucionClinica.id == evolucion_id).with_for_update())
                _usuario, profesional = autorizado
                turno = session.get(Turno, original.turno_id) if original else None
                if (original is None or original.profesional_id != profesional.id
                        or turno is None or turno.estado != 'atendido'
                        or turno.paciente_id != original.paciente_id
                        or turno.profesional_id != profesional.id):
                    _registrar_denegacion(session, actor_id)
                    error = ErrorHistoriaClinica(
                        'evolucion_no_disponible', 'La evolución no está disponible.', 404)
                else:
                    resultado, error = _crear_evolucion_en_sesion(
                        session, paciente_id=original.paciente_id, turno_id=original.turno_id,
                        nota=nota_validada, identidad=identidad,
                        corrige_a_id=original.id, actor_evento='evolucion.corregida')
        if error is not None:
            raise error
        assert resultado is not None
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudo corregir la evolución clínica.', 503) from exc
