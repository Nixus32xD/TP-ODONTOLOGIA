"""Operaciones de ficha mínima de paciente para la agenda local ficticia."""
import re
import unicodedata
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.audit import ErrorAuditoria, registrar_evento_session
from odontologia.db.models import AgendaMutex, Paciente, Turno


class ErrorPacientes(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


def _nombre(valor: object) -> str:
    if not isinstance(valor, str):
        raise ErrorPacientes('entrada_invalida', 'El nombre no es válido.', 422)
    normalizado = ' '.join(valor.split())
    if (not normalizado or len(normalizado) > 120
            or any(unicodedata.category(caracter) == 'Cc' for caracter in normalizado)):
        raise ErrorPacientes('entrada_invalida', 'El nombre no es válido.', 422)
    return normalizado


def _telefono(valor: object) -> str | None:
    if valor is None:
        return None
    if not isinstance(valor, str) or len(valor) > 32:
        raise ErrorPacientes('entrada_invalida', 'El teléfono no es válido.', 422)
    if (not re.fullmatch(r'\+?[0-9() -]+', valor)
            or not 7 <= sum(caracter.isdigit() for caracter in valor) <= 15):
        raise ErrorPacientes('entrada_invalida', 'El teléfono no es válido.', 422)
    return valor


def _iniciar_escritura(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
        return
    mutex = session.scalar(select(AgendaMutex.id).where(
        AgendaMutex.id == 1).with_for_update())
    if mutex != 1:
        raise ErrorPacientes(
            'almacenamiento_error', 'El esquema de agenda no está preparado.', 503)


def _publico(paciente: Paciente) -> dict[str, object]:
    return {
        'id': paciente.id,
        'nombre': paciente.nombre,
        'telefono': paciente.telefono,
        'activo': paciente.activo,
        'acepta_recordatorios': paciente.acepta_recordatorios,
    }


def _registrar(session: Session, accion: str, paciente: Paciente,
               actor_id: str | None) -> None:
    if actor_id is not None:
        registrar_evento_session(
            session, action=accion, resource_type='paciente', resource_id=paciente.id,
            actor_id=actor_id, result='confirmado')


def crear_paciente(engine, nombre: object, telefono: object = None,
                   acepta_recordatorios: object = False,
                   *, actor_id: str | None = None) -> dict[str, object]:
    if type(acepta_recordatorios) is not bool:
        raise ErrorPacientes('entrada_invalida', 'El consentimiento no es válido.', 422)
    paciente = Paciente(
        id=str(uuid4()), nombre=_nombre(nombre), telefono=_telefono(telefono), activo=True,
        acepta_recordatorios=acepta_recordatorios)
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            session.add(paciente)
            session.flush()
            _registrar(session, 'paciente.creado', paciente, actor_id)
            resultado = _publico(paciente)
        return resultado
    except ErrorPacientes:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorPacientes(
            'almacenamiento_error', 'No se pudo guardar la ficha.', 503) from exc


def listar_pacientes(engine, *, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ErrorPacientes('entrada_invalida', 'El límite de página no es válido.', 422)
    if type(offset) is not int or offset < 0:
        raise ErrorPacientes('entrada_invalida', 'El desplazamiento no es válido.', 422)
    try:
        with Session(engine) as session:
            pacientes = session.scalars(select(Paciente).order_by(
                Paciente.id.asc()).limit(limit).offset(offset)).all()
            return [_publico(paciente) for paciente in pacientes]
    except SQLAlchemyError as exc:
        raise ErrorPacientes(
            'almacenamiento_error', 'No se pudieron consultar las fichas.', 503) from exc


def obtener_paciente(engine, paciente_id: str) -> dict[str, object]:
    if not isinstance(paciente_id, str) or not paciente_id or len(paciente_id) > 64:
        raise ErrorPacientes('entrada_invalida', 'El ID no es válido.', 422)
    try:
        with Session(engine) as session:
            paciente = session.get(Paciente, paciente_id)
            if paciente is None:
                raise ErrorPacientes('paciente_desconocido', 'El paciente no existe.', 404)
            return _publico(paciente)
    except ErrorPacientes:
        raise
    except SQLAlchemyError as exc:
        raise ErrorPacientes(
            'almacenamiento_error', 'No se pudo consultar la ficha.', 503) from exc


def actualizar_paciente(engine, paciente_id: str, cambios: dict[str, object],
                        *, actor_id: str | None = None,
                        ahora: datetime | None = None) -> dict[str, object]:
    permitidos = {'nombre', 'telefono', 'activo', 'acepta_recordatorios'}
    if (not isinstance(cambios, dict) or not cambios or not set(cambios) <= permitidos):
        raise ErrorPacientes('entrada_invalida', 'Debe indicar cambios válidos.', 422)
    normalizados = dict(cambios)
    if 'nombre' in normalizados:
        normalizados['nombre'] = _nombre(normalizados['nombre'])
    if 'telefono' in normalizados:
        normalizados['telefono'] = _telefono(normalizados['telefono'])
    if 'activo' in normalizados and type(normalizados['activo']) is not bool:
        raise ErrorPacientes('entrada_invalida', 'El estado no es válido.', 422)
    if ('acepta_recordatorios' in normalizados
            and type(normalizados['acepta_recordatorios']) is not bool):
        raise ErrorPacientes('entrada_invalida', 'El consentimiento no es válido.', 422)
    if not isinstance(paciente_id, str) or not paciente_id or len(paciente_id) > 64:
        raise ErrorPacientes('entrada_invalida', 'El ID no es válido.', 422)

    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            paciente = session.get(Paciente, paciente_id)
            if paciente is None:
                raise ErrorPacientes('paciente_desconocido', 'El paciente no existe.', 404)
            anteriores = _publico(paciente)
            for campo, valor in normalizados.items():
                setattr(paciente, campo, valor)
            session.flush()
            consentimiento_cambio = (
                'acepta_recordatorios' in normalizados
                and paciente.acepta_recordatorios != anteriores['acepta_recordatorios'])
            if consentimiento_cambio:
                from odontologia.recordatorios import (
                    invalidar_recordatorios_pendientes,
                    programar_recordatorio_confirmacion,
                )

                turnos_confirmados = session.scalars(select(Turno).where(
                    Turno.paciente_id == paciente.id,
                    Turno.estado == 'confirmado',
                ).order_by(Turno.id)).all()
                for turno in turnos_confirmados:
                    if paciente.acepta_recordatorios:
                        programar_recordatorio_confirmacion(
                            session, turno, actor_id=actor_id, ahora=ahora)
                    else:
                        invalidar_recordatorios_pendientes(
                            session, turno, actor_id=actor_id, ahora=ahora)
            actualizado = _publico(paciente)
            if actualizado != anteriores:
                cambio_estado = (
                    'activo' in normalizados and paciente.activo != anteriores['activo'])
                if any(campo in normalizados for campo in (
                        'nombre', 'telefono', 'acepta_recordatorios')):
                    _registrar(session, 'paciente.actualizado', paciente, actor_id)
                if cambio_estado:
                    accion = 'paciente.reactivado' if paciente.activo else 'paciente.desactivado'
                    _registrar(session, accion, paciente, actor_id)
            resultado = actualizado
        return resultado
    except ErrorPacientes:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorPacientes(
            'almacenamiento_error', 'No se pudo actualizar la ficha.', 503) from exc
