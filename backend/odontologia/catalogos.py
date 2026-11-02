"""Administración transaccional de catálogos ficticios de agenda."""
import unicodedata
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.audit import ErrorAuditoria, registrar_evento_session
from odontologia.db.models import AgendaMutex, Box, Prestacion, Profesional


class ErrorCatalogos(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


_RECURSOS = {
    'profesionales': {
        'modelo': Profesional, 'tipo': 'profesional', 'creado': 'profesional.creado',
        'actualizado': 'profesional.actualizado', 'desactivado': 'profesional.desactivado',
        'reactivado': 'profesional.reactivado', 'campos': {'nombre'},
    },
    'boxes': {
        'modelo': Box, 'tipo': 'box', 'creado': 'box.creado',
        'actualizado': 'box.actualizado', 'desactivado': 'box.desactivado',
        'reactivado': 'box.reactivado', 'campos': {'nombre'},
    },
    'prestaciones': {
        'modelo': Prestacion, 'tipo': 'prestacion', 'creado': 'prestacion.creada',
        'actualizado': 'prestacion.actualizada', 'desactivado': 'prestacion.desactivada',
        'reactivado': 'prestacion.reactivada', 'campos': {'nombre', 'duracion_minutos'},
    },
}


def _definicion(tipo: str) -> dict[str, object]:
    if not isinstance(tipo, str) or tipo not in _RECURSOS:
        raise ErrorCatalogos('entrada_invalida', 'El tipo de catálogo no es válido.', 422)
    return _RECURSOS[tipo]


def _nombre(valor: object) -> str:
    if not isinstance(valor, str):
        raise ErrorCatalogos('entrada_invalida', 'El nombre no es válido.', 422)
    normalizado = ' '.join(valor.split())
    if (not normalizado or len(normalizado) > 120
            or any(unicodedata.category(caracter) == 'Cc' for caracter in normalizado)):
        raise ErrorCatalogos('entrada_invalida', 'El nombre no es válido.', 422)
    return normalizado


def _duracion(valor: object) -> int:
    if type(valor) is not int or not 1 <= valor <= 2_147_483_647:
        raise ErrorCatalogos('entrada_invalida', 'La duración debe ser un entero positivo.', 422)
    return valor


def _id(valor: object) -> str:
    if (not isinstance(valor, str) or not valor or len(valor) > 64
            or valor.strip() != valor):
        raise ErrorCatalogos('entrada_invalida', 'El ID no es válido.', 422)
    return valor


def _iniciar_escritura(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
        return
    mutex = session.scalar(select(AgendaMutex.id).where(
        AgendaMutex.id == 1).with_for_update())
    if mutex != 1:
        raise ErrorCatalogos(
            'almacenamiento_error', 'El esquema de agenda no está preparado.', 503)


def _publico(recurso, definicion: dict[str, object]) -> dict[str, object]:
    resultado = {'id': recurso.id, 'nombre': recurso.nombre, 'activo': recurso.activo}
    if definicion['tipo'] == 'prestacion':
        resultado['duracion_minutos'] = recurso.duracion_minutos
    return resultado


def _registrar(session: Session, definicion: dict[str, object], accion: str,
               recurso, actor_id: str | None) -> None:
    if actor_id is not None:
        registrar_evento_session(
            session, action=accion, resource_type=definicion['tipo'],
            resource_id=recurso.id, actor_id=actor_id, result='confirmado')


def _validar_campos(tipo: str, definicion: dict[str, object], datos: object,
                    *, permite_estado: bool) -> dict[str, object]:
    permitidos = set(definicion['campos'])
    if permite_estado:
        permitidos.add('activo')
    if not isinstance(datos, dict) or not datos or not set(datos) <= permitidos:
        raise ErrorCatalogos('entrada_invalida', 'Debe indicar datos válidos.', 422)
    normalizados = dict(datos)
    if 'nombre' in normalizados:
        normalizados['nombre'] = _nombre(normalizados['nombre'])
    if tipo == 'prestaciones' and 'duracion_minutos' in normalizados:
        normalizados['duracion_minutos'] = _duracion(normalizados['duracion_minutos'])
    if 'activo' in normalizados and type(normalizados['activo']) is not bool:
        raise ErrorCatalogos('entrada_invalida', 'El estado no es válido.', 422)
    if not permite_estado and 'nombre' not in normalizados:
        raise ErrorCatalogos('entrada_invalida', 'El nombre es obligatorio.', 422)
    if tipo == 'prestaciones' and not permite_estado and 'duracion_minutos' not in normalizados:
        raise ErrorCatalogos('entrada_invalida', 'La duración es obligatoria.', 422)
    return normalizados


def crear_recurso(engine, tipo: str, datos: object, *, actor_id: str | None = None
                  ) -> dict[str, object]:
    definicion = _definicion(tipo)
    normalizados = _validar_campos(tipo, definicion, datos, permite_estado=False)
    recurso = definicion['modelo'](id=str(uuid4()), activo=True, **normalizados)
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            session.add(recurso)
            session.flush()
            _registrar(session, definicion, definicion['creado'], recurso, actor_id)
            resultado = _publico(recurso, definicion)
        return resultado
    except ErrorCatalogos:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorCatalogos(
            'almacenamiento_error', 'No se pudo guardar el catálogo.', 503) from exc


def listar_recursos(engine, tipo: str, *, limit: int = 50, offset: int = 0
                    ) -> list[dict[str, object]]:
    definicion = _definicion(tipo)
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ErrorCatalogos('entrada_invalida', 'El límite de página no es válido.', 422)
    if type(offset) is not int or offset < 0:
        raise ErrorCatalogos('entrada_invalida', 'El desplazamiento no es válido.', 422)
    try:
        with Session(engine) as session:
            modelo = definicion['modelo']
            recursos = session.scalars(select(modelo).order_by(
                modelo.id.asc()).limit(limit).offset(offset)).all()
            return [_publico(recurso, definicion) for recurso in recursos]
    except SQLAlchemyError as exc:
        raise ErrorCatalogos(
            'almacenamiento_error', 'No se pudo consultar el catálogo.', 503) from exc


def obtener_recurso(engine, tipo: str, recurso_id: str) -> dict[str, object]:
    definicion = _definicion(tipo)
    recurso_id = _id(recurso_id)
    try:
        with Session(engine) as session:
            recurso = session.get(definicion['modelo'], recurso_id)
            if recurso is None:
                raise ErrorCatalogos('recurso_desconocido', 'El recurso no existe.', 404)
            return _publico(recurso, definicion)
    except ErrorCatalogos:
        raise
    except SQLAlchemyError as exc:
        raise ErrorCatalogos(
            'almacenamiento_error', 'No se pudo consultar el catálogo.', 503) from exc


def actualizar_recurso(engine, tipo: str, recurso_id: str, cambios: object,
                       *, actor_id: str | None = None) -> dict[str, object]:
    definicion = _definicion(tipo)
    recurso_id = _id(recurso_id)
    normalizados = _validar_campos(tipo, definicion, cambios, permite_estado=True)
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            recurso = session.get(definicion['modelo'], recurso_id)
            if recurso is None:
                raise ErrorCatalogos('recurso_desconocido', 'El recurso no existe.', 404)
            anteriores = _publico(recurso, definicion)
            for campo, valor in normalizados.items():
                setattr(recurso, campo, valor)
            session.flush()
            actualizado = _publico(recurso, definicion)
            cambio_estado = (
                'activo' in normalizados and recurso.activo != anteriores['activo'])
            cambio_datos = any(
                campo in normalizados and actualizado[campo] != anteriores[campo]
                for campo in definicion['campos'])
            if cambio_datos:
                _registrar(session, definicion, definicion['actualizado'], recurso, actor_id)
            if cambio_estado:
                accion = definicion['reactivado'] if recurso.activo else definicion['desactivado']
                _registrar(session, definicion, accion, recurso, actor_id)
            resultado = actualizado
        return resultado
    except ErrorCatalogos:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorCatalogos(
            'almacenamiento_error', 'No se pudo actualizar el catálogo.', 503) from exc
