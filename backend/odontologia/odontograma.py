"""Validación técnica de nomenclatura para odontogramas sintéticos."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.audit import ErrorAuditoria, registrar_evento_session
from odontologia.historia_clinica import ErrorHistoriaClinica


_SUPERFICIES = frozenset({'M', 'D', 'O', 'I', 'B', 'V', 'L'})
_SUPERFICIES_ANTERIORES = frozenset({'I', 'V'})
_SUPERFICIES_POSTERIORES = frozenset({'O', 'B'})


class ErrorOdontograma(ErrorHistoriaClinica):
    def __init__(self, mensaje: str = 'Los hallazgos del odontograma no son válidos.'):
        super().__init__('entrada_invalida', mensaje, 422)


def _validar_pieza(pieza: object) -> tuple[str, bool]:
    if (not isinstance(pieza, str) or len(pieza) != 2
            or any(caracter not in '0123456789' for caracter in pieza)):
        raise ErrorOdontograma()
    cuadrante, posicion = int(pieza[0]), int(pieza[1])
    if 1 <= cuadrante <= 4:
        valida = 1 <= posicion <= 8
    elif 5 <= cuadrante <= 8:
        valida = 1 <= posicion <= 5
    else:
        valida = False
    if not valida:
        raise ErrorOdontograma()
    return pieza, posicion <= 3


def _validar_observacion(observacion: object) -> str | None:
    if observacion is None:
        return None
    if not isinstance(observacion, str):
        raise ErrorOdontograma()
    observacion = observacion.strip()
    if len(observacion) > 500 or any(
            ord(caracter) < 32 and caracter not in '\n\t' for caracter in observacion):
        raise ErrorOdontograma()
    return observacion or None


def validar_hallazgos(hallazgos: object) -> list[dict[str, str | None]]:
    """Valida códigos individuales y devuelve filas planas para una versión nueva."""
    if not isinstance(hallazgos, list):
        raise ErrorOdontograma()
    normalizados: list[dict[str, str | None]] = []
    vistos: set[tuple[str, str]] = set()
    for hallazgo in hallazgos:
        if (not isinstance(hallazgo, dict)
                or set(hallazgo) - {'pieza_fdi', 'superficies', 'observacion'}
                or not {'pieza_fdi', 'superficies'} <= set(hallazgo)):
            raise ErrorOdontograma()
        pieza, anterior = _validar_pieza(hallazgo.get('pieza_fdi'))
        superficies = hallazgo.get('superficies')
        if not isinstance(superficies, list) or not superficies:
            raise ErrorOdontograma()
        if (any(not isinstance(superficie, str) or superficie not in _SUPERFICIES
                for superficie in superficies) or len(set(superficies)) != len(superficies)):
            raise ErrorOdontograma()
        for superficie in superficies:
            if ((anterior and superficie in _SUPERFICIES_POSTERIORES)
                    or (not anterior and superficie in _SUPERFICIES_ANTERIORES)):
                raise ErrorOdontograma()
            clave = pieza, superficie
            if clave in vistos:
                raise ErrorOdontograma()
            vistos.add(clave)
            normalizados.append({
                'pieza_fdi': pieza,
                'superficie_fdi': superficie,
                'observacion': _validar_observacion(hallazgo.get('observacion')),
            })
    return normalizados


def _validar_paciente_id(valor: object) -> str:
    if not isinstance(valor, str) or not valor or len(valor) > 64 or valor.strip() != valor:
        raise ErrorHistoriaClinica(
            'paciente_desconocido', 'El odontograma no está disponible.', 404)
    return valor


def _publicar_version(version, hallazgos) -> dict[str, object]:
    fecha = version.created_at
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return {
        'id': version.id,
        'paciente_id': version.paciente_id,
        'profesional_id': version.profesional_id,
        'version': version.version,
        'created_at': fecha.astimezone(timezone.utc).isoformat(timespec='microseconds'),
        'hallazgos': [{
            'pieza_fdi': hallazgo.pieza_fdi,
            'superficie_fdi': hallazgo.superficie_fdi,
            'observacion': hallazgo.observacion,
        } for hallazgo in hallazgos],
    }


def _autorizacion_profesional_paciente(session: Session, paciente_id: str, identidad: object):
    from odontologia.db.models import Paciente, Turno
    from odontologia.historia_clinica import _profesional_vigente

    identidad = identidad if isinstance(identidad, dict) else {}
    actor_id = identidad.get('usuario_id')
    actor_id = actor_id if isinstance(actor_id, str) and actor_id else None
    autorizado = _profesional_vigente(session, identidad)
    paciente = session.get(Paciente, paciente_id) if autorizado else None
    turno_id = None
    if autorizado is not None and paciente is not None:
        _usuario, profesional = autorizado
        turno_id = session.scalar(select(Turno.id).where(
            Turno.paciente_id == paciente.id,
            Turno.profesional_id == profesional.id,
            Turno.estado == 'atendido').with_for_update().limit(1))
    return actor_id, autorizado, paciente, turno_id


def _registrar_denegacion(session: Session, actor_id: str | None) -> None:
    registrar_evento_session(
        session, action='odontograma.denegada', resource_type='odontograma',
        result='rechazado', actor_id=actor_id, resource_id=None)


def crear_odontograma(engine, *, paciente_id: object, hallazgos: object,
                       identidad: dict[str, object]) -> dict[str, object]:
    from odontologia.db.models import HallazgoOdontograma, OdontogramaVersion
    from odontologia.historia_clinica import (
        _iniciar_transaccion_clinica,
    )

    paciente_id = _validar_paciente_id(paciente_id)
    hallazgos_validados = validar_hallazgos(hallazgos)
    actor_id = identidad.get('usuario_id') if isinstance(identidad, dict) else None
    actor_id = actor_id if isinstance(actor_id, str) and actor_id else None
    error = None
    resultado = None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            actor_id, autorizado, paciente, turno_id = _autorizacion_profesional_paciente(
                session, paciente_id, identidad)
            if autorizado is None:
                _registrar_denegacion(session, actor_id)
                error = ErrorHistoriaClinica(
                    'permiso_denegado', 'No tiene permiso para acceder al odontograma.', 403)
            elif paciente is None or turno_id is None:
                _registrar_denegacion(session, actor_id)
                error = ErrorHistoriaClinica(
                    'atencion_no_disponible', 'El odontograma no está disponible.', 404)
            else:
                _usuario, profesional = autorizado
                version_actual = session.scalar(select(func.max(
                    OdontogramaVersion.version)).where(
                        OdontogramaVersion.paciente_id == paciente.id,
                        OdontogramaVersion.profesional_id == profesional.id)) or 0
                version = OdontogramaVersion(
                    id=str(uuid4()), paciente_id=paciente.id,
                    profesional_id=profesional.id, version=version_actual + 1,
                    created_at=datetime.now(timezone.utc))
                session.add(version)
                session.flush()
                session.add_all([HallazgoOdontograma(
                    id=str(uuid4()), version_id=version.id,
                    pieza_fdi=hallazgo['pieza_fdi'],
                    superficie_fdi=hallazgo['superficie_fdi'],
                    observacion=hallazgo['observacion']) for hallazgo in hallazgos_validados])
                session.flush()
                registrar_evento_session(
                    session, action='odontograma.version_creada',
                    resource_type='odontograma', result='confirmado', actor_id=actor_id,
                    resource_id=version.id)
                resultado = _publicar_version(version, [
                    HallazgoOdontograma(
                        pieza_fdi=hallazgo['pieza_fdi'],
                        superficie_fdi=hallazgo['superficie_fdi'],
                        observacion=hallazgo['observacion'])
                    for hallazgo in hallazgos_validados])
        if error is not None:
            raise error
        assert resultado is not None
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudo guardar el odontograma.', 503) from exc


def consultar_odontograma(engine, paciente_id: object, *, identidad: dict[str, object]):
    from odontologia.db.models import HallazgoOdontograma, OdontogramaVersion
    from odontologia.historia_clinica import _iniciar_transaccion_clinica

    paciente_id = _validar_paciente_id(paciente_id)
    actor_id = identidad.get('usuario_id') if isinstance(identidad, dict) else None
    actor_id = actor_id if isinstance(actor_id, str) and actor_id else None
    error = None
    resultado = None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            actor_id, autorizado, paciente, turno_id = _autorizacion_profesional_paciente(
                session, paciente_id, identidad)
            if autorizado is None:
                _registrar_denegacion(session, actor_id)
                error = ErrorHistoriaClinica(
                    'permiso_denegado', 'No tiene permiso para acceder al odontograma.', 403)
            elif paciente is None or turno_id is None:
                _registrar_denegacion(session, actor_id)
                error = ErrorHistoriaClinica(
                    'atencion_no_disponible', 'El odontograma no está disponible.', 404)
            else:
                _usuario, profesional = autorizado
                versiones = session.scalars(select(OdontogramaVersion).where(
                    OdontogramaVersion.paciente_id == paciente.id,
                    OdontogramaVersion.profesional_id == profesional.id
                ).order_by(OdontogramaVersion.version, OdontogramaVersion.id)).all()
                items = []
                for version in versiones:
                    hallazgos = session.scalars(select(HallazgoOdontograma).where(
                        HallazgoOdontograma.version_id == version.id
                    ).order_by(
                        HallazgoOdontograma.pieza_fdi,
                        HallazgoOdontograma.superficie_fdi,
                    )).all()
                    items.append(_publicar_version(version, hallazgos))
                registrar_evento_session(
                    session, action='odontograma.consultada',
                    resource_type='odontograma', result='confirmado', actor_id=actor_id,
                    resource_id=paciente.id)
                resultado = {
                    'items': items,
                    'version_vigente': items[-1]['version'] if items else None,
                }
        if error is not None:
            raise error
        assert resultado is not None
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudo consultar el odontograma.', 503) from exc


def listar_atenciones_atendidas(engine, *, identidad: dict[str, object],
                                limit: int = 25, offset: int = 0) -> dict[str, object]:
    """Lista sólo las atenciones atendidas del Profesional autenticado."""
    from odontologia.db.models import Paciente, Turno
    from odontologia.historia_clinica import (
        _iniciar_transaccion_clinica, _profesional_vigente, _validar_pagina,
    )

    _validar_pagina(limit, offset)
    if not isinstance(identidad, dict) or identidad.get('rol') != 'profesional':
        raise ErrorHistoriaClinica(
            'permiso_denegado', 'No tiene permiso para consultar atenciones clínicas.', 403)
    actor_id = identidad.get('usuario_id')
    actor_id = actor_id if isinstance(actor_id, str) and actor_id else None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            autorizado = _profesional_vigente(session, identidad)
            if autorizado is None:
                raise ErrorHistoriaClinica(
                    'permiso_denegado', 'No tiene permiso para consultar atenciones clínicas.', 403)
            _usuario, profesional = autorizado
            filas = session.execute(
                select(Turno, Paciente)
                .join(Paciente, Paciente.id == Turno.paciente_id)
                .where(Turno.profesional_id == profesional.id, Turno.estado == 'atendido')
                .order_by(Turno.inicio_minuto, Turno.id)
                .limit(limit).offset(offset).with_for_update(of=Turno)
            ).all()
            items = [{
                'turno_id': turno.id,
                'paciente_id': paciente.id,
                'paciente_nombre': paciente.nombre,
                'inicio': datetime.fromtimestamp(turno.inicio_minuto * 60, timezone.utc),
                'fin': datetime.fromtimestamp(turno.fin_minuto * 60, timezone.utc),
            } for turno, paciente in filas]
            registrar_evento_session(
                session, action='historia.atenciones_listadas',
                resource_type='historia', result='confirmado', actor_id=actor_id)
            resultado = {'items': items, 'limit': limit, 'offset': offset}
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError, OverflowError, OSError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudieron consultar las atenciones.', 503) from exc


class ErrorPlanTratamiento(ErrorHistoriaClinica):
    def __init__(self, codigo: str, mensaje: str, estado: int):
        super().__init__(codigo, mensaje, estado)


def _validar_prestaciones_ids(prestaciones_ids: object) -> list[str]:
    if (not isinstance(prestaciones_ids, list) or not prestaciones_ids
            or any(not isinstance(item, str) or not item or len(item) > 64
                   or item.strip() != item for item in prestaciones_ids)
            or len(set(prestaciones_ids)) != len(prestaciones_ids)):
        raise ErrorPlanTratamiento(
            'entrada_invalida', 'Las etapas del plan no son válidas.', 422)
    return prestaciones_ids


def _publicar_plan(plan, etapas) -> dict[str, object]:
    fecha = plan.created_at
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return {
        'id': plan.id,
        'paciente_id': plan.paciente_id,
        'profesional_id': plan.profesional_id,
        'estado': plan.estado,
        'created_at': fecha.astimezone(timezone.utc).isoformat(timespec='microseconds'),
        'etapas': [{'orden': etapa.orden, 'prestacion_id': etapa.prestacion_id}
                   for etapa in etapas],
    }


def _registrar_denegacion_plan(session: Session, actor_id: str | None) -> None:
    registrar_evento_session(
        session, action='plan.denegado', resource_type='plan', result='rechazado',
        actor_id=actor_id, resource_id=None)


def crear_plan_tratamiento(engine, *, paciente_id: object, prestaciones_ids: object,
                           identidad: dict[str, object]) -> dict[str, object]:
    from odontologia.db.models import EtapaPlanTratamiento, PlanTratamiento, Prestacion
    from odontologia.historia_clinica import _iniciar_transaccion_clinica

    paciente_id = _validar_paciente_id(paciente_id)
    prestaciones_ids = _validar_prestaciones_ids(prestaciones_ids)
    actor_id = identidad.get('usuario_id') if isinstance(identidad, dict) else None
    actor_id = actor_id if isinstance(actor_id, str) and actor_id else None
    error = None
    resultado = None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            actor_id, autorizado, paciente, turno_id = _autorizacion_profesional_paciente(
                session, paciente_id, identidad)
            if autorizado is None:
                _registrar_denegacion_plan(session, actor_id)
                error = ErrorHistoriaClinica(
                    'permiso_denegado', 'No tiene permiso para acceder a planes.', 403)
            elif paciente is None or turno_id is None:
                _registrar_denegacion_plan(session, actor_id)
                error = ErrorHistoriaClinica(
                    'atencion_no_disponible', 'El plan no está disponible.', 404)
            else:
                prestaciones = session.scalars(select(Prestacion).where(
                    Prestacion.id.in_(prestaciones_ids), Prestacion.activo.is_(True)
                )).all()
                if len(prestaciones) != len(prestaciones_ids):
                    error = ErrorPlanTratamiento(
                        'prestacion_no_disponible',
                        'Una o más prestaciones no están disponibles.', 422)
                else:
                    _usuario, profesional = autorizado
                    plan = PlanTratamiento(
                        id=str(uuid4()), paciente_id=paciente.id,
                        profesional_id=profesional.id, estado='propuesto',
                        created_at=datetime.now(timezone.utc))
                    session.add(plan)
                    session.flush()
                    etapas = [EtapaPlanTratamiento(
                        id=str(uuid4()), plan_id=plan.id,
                        prestacion_id=prestacion_id, orden=orden)
                        for orden, prestacion_id in enumerate(prestaciones_ids, start=1)]
                    session.add_all(etapas)
                    session.flush()
                    registrar_evento_session(
                        session, action='plan.creado', resource_type='plan',
                        result='confirmado', actor_id=actor_id, resource_id=plan.id)
                    resultado = _publicar_plan(plan, etapas)
        if error is not None:
            raise error
        assert resultado is not None
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudo guardar el plan.', 503) from exc


def consultar_planes_tratamiento(engine, paciente_id: object, *, identidad: dict[str, object]):
    from odontologia.db.models import EtapaPlanTratamiento, PlanTratamiento
    from odontologia.historia_clinica import _iniciar_transaccion_clinica

    paciente_id = _validar_paciente_id(paciente_id)
    actor_id = identidad.get('usuario_id') if isinstance(identidad, dict) else None
    actor_id = actor_id if isinstance(actor_id, str) and actor_id else None
    error = None
    resultado = None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            actor_id, autorizado, paciente, turno_id = _autorizacion_profesional_paciente(
                session, paciente_id, identidad)
            if autorizado is None:
                _registrar_denegacion_plan(session, actor_id)
                error = ErrorHistoriaClinica(
                    'permiso_denegado', 'No tiene permiso para acceder a planes.', 403)
            elif paciente is None or turno_id is None:
                _registrar_denegacion_plan(session, actor_id)
                error = ErrorHistoriaClinica(
                    'atencion_no_disponible', 'El plan no está disponible.', 404)
            else:
                _usuario, profesional = autorizado
                planes = session.scalars(select(PlanTratamiento).where(
                    PlanTratamiento.paciente_id == paciente.id,
                    PlanTratamiento.profesional_id == profesional.id
                ).order_by(PlanTratamiento.created_at, PlanTratamiento.id)).all()
                items = []
                for plan in planes:
                    etapas = session.scalars(select(EtapaPlanTratamiento).where(
                        EtapaPlanTratamiento.plan_id == plan.id
                    ).order_by(EtapaPlanTratamiento.orden)).all()
                    items.append(_publicar_plan(plan, etapas))
                registrar_evento_session(
                    session, action='plan.consultado', resource_type='plan',
                    result='confirmado', actor_id=actor_id, resource_id=paciente.id)
                resultado = {'items': items}
        if error is not None:
            raise error
        assert resultado is not None
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudo consultar el plan.', 503) from exc


_TRANSICIONES_PLAN = {
    'propuesto': frozenset({'en_curso', 'cancelado'}),
    'en_curso': frozenset({'completado', 'cancelado'}),
    'completado': frozenset(),
    'cancelado': frozenset(),
}


def cambiar_estado_plan_tratamiento(engine, *, plan_id: object, estado: object,
                                    identidad: dict[str, object]) -> dict[str, object]:
    from odontologia.db.models import EtapaPlanTratamiento, PlanTratamiento
    from odontologia.historia_clinica import _iniciar_transaccion_clinica

    if not isinstance(plan_id, str) or not plan_id or len(plan_id) > 36:
        raise ErrorPlanTratamiento(
            'plan_no_disponible', 'El plan no está disponible.', 404)
    if not isinstance(estado, str):
        raise ErrorPlanTratamiento(
            'entrada_invalida', 'El estado del plan no es válido.', 422)
    actor_id = identidad.get('usuario_id') if isinstance(identidad, dict) else None
    actor_id = actor_id if isinstance(actor_id, str) and actor_id else None
    error = None
    resultado = None
    try:
        with Session(engine) as session, session.begin():
            _iniciar_transaccion_clinica(session)
            plan = session.scalar(select(PlanTratamiento).where(
                PlanTratamiento.id == plan_id).with_for_update())
            if plan is None:
                _registrar_denegacion_plan(session, actor_id)
                error = ErrorPlanTratamiento(
                    'plan_no_disponible', 'El plan no está disponible.', 404)
            else:
                actor_id, autorizado, paciente, turno_id = _autorizacion_profesional_paciente(
                    session, plan.paciente_id, identidad)
                if autorizado is None:
                    _registrar_denegacion_plan(session, actor_id)
                    error = ErrorHistoriaClinica(
                        'permiso_denegado', 'No tiene permiso para cambiar el plan.', 403)
                elif (paciente is None or turno_id is None
                      or autorizado[1].id != plan.profesional_id):
                    _registrar_denegacion_plan(session, actor_id)
                    error = ErrorHistoriaClinica(
                        'atencion_no_disponible', 'El plan no está disponible.', 404)
                elif estado not in _TRANSICIONES_PLAN.get(plan.estado, frozenset()):
                    error = ErrorPlanTratamiento(
                        'transicion_invalida', 'La transición solicitada no está permitida.', 409)
                else:
                    plan.estado = estado
                    session.flush()
                    etapas = session.scalars(select(EtapaPlanTratamiento).where(
                        EtapaPlanTratamiento.plan_id == plan.id
                    ).order_by(EtapaPlanTratamiento.orden)).all()
                    registrar_evento_session(
                        session, action='plan.estado_actualizado', resource_type='plan',
                        result='confirmado', actor_id=actor_id, resource_id=plan.id)
                    resultado = _publicar_plan(plan, etapas)
        if error is not None:
            raise error
        assert resultado is not None
        return resultado
    except ErrorHistoriaClinica:
        raise
    except (ErrorAuditoria, SQLAlchemyError) as exc:
        raise ErrorHistoriaClinica(
            'almacenamiento_error', 'No se pudo actualizar el plan.', 503) from exc
