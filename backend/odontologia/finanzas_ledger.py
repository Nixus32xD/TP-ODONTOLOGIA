"""Comandos locales y sintéticos del ledger financiero inmutable."""

from datetime import datetime, timezone
import hashlib
import json
import sqlite3
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.audit import registrar_evento_session
from odontologia.db.models import (
    AgendaMutex, CargoFinanciero, CobroFinanciero, IdempotenciaFinanciera,
    Paciente, ReversionCobro,
)
from odontologia.finanzas import (
    centavos_a_importe_ars, importe_ars_a_centavos, importe_reversible_centavos,
    saldo_centavos,
)


class ErrorFinanzas(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


def _clave(clave: object) -> str:
    if not isinstance(clave, str) or not 1 <= len(clave) <= 128 or clave.strip() != clave:
        raise ErrorFinanzas('entrada_invalida', 'Idempotency-Key no válida.', 422)
    return clave


def _texto(valor: object, maximo: int, nombre: str) -> str:
    if not isinstance(valor, str) or not 1 <= len(valor.strip()) <= maximo:
        raise ErrorFinanzas('entrada_invalida', f'{nombre} no válido.', 422)
    return valor.strip()


def _fingerprint(payload: dict[str, object]) -> str:
    canonico = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canonico.encode('utf-8')).hexdigest()


def _bloquear(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
        return
    if session.scalar(select(AgendaMutex.id).where(
            AgendaMutex.id == 1).with_for_update()) != 1:
        raise ErrorFinanzas('almacenamiento_error', 'El ledger no está disponible.', 503)


def _idempotente(session: Session, *, actor_id: str, operacion: str, clave: str,
                 fingerprint: str) -> dict[str, object] | None:
    fila = session.scalar(select(IdempotenciaFinanciera).where(
        IdempotenciaFinanciera.actor_id == actor_id,
        IdempotenciaFinanciera.operacion == operacion,
        IdempotenciaFinanciera.clave == clave))
    if fila is None:
        return None
    if fila.fingerprint != fingerprint:
        raise ErrorFinanzas('idempotencia_conflictiva', 'La clave ya fue utilizada.', 409)
    return json.loads(fila.respuesta_json)


def _saldo(session: Session, cargo_id: str) -> int:
    cargo = session.get(CargoFinanciero, cargo_id)
    pagos = session.scalars(select(CobroFinanciero.monto_centavos).where(
        CobroFinanciero.cargo_id == cargo_id)).all()
    reversiones = session.scalars(select(ReversionCobro.monto_centavos).join(
        CobroFinanciero, ReversionCobro.cobro_id == CobroFinanciero.id).where(
            CobroFinanciero.cargo_id == cargo_id)).all()
    return saldo_centavos(cargos=[cargo.monto_centavos],
                          cobros=[int(pago) for pago in pagos],
                          reversiones=[int(item) for item in reversiones])


def _guardar_idempotencia(session: Session, *, actor_id: str, operacion: str,
                          clave: str, fingerprint: str, respuesta: dict[str, object]) -> None:
    session.add(IdempotenciaFinanciera(
        id=str(uuid4()), actor_id=actor_id, operacion=operacion, clave=clave,
        fingerprint=fingerprint,
        respuesta_json=json.dumps(respuesta, sort_keys=True, separators=(',', ':')),
        created_at=datetime.now(timezone.utc)))
    session.flush()


def _ejecutar(engine, operacion: str, actor_id: str, clave: str,
              payload: dict[str, object], mutar) -> dict[str, object]:
    fingerprint = _fingerprint(payload)
    try:
        with Session(engine) as session, session.begin():
            _bloquear(session)
            replay = _idempotente(session, actor_id=actor_id, operacion=operacion,
                                  clave=clave, fingerprint=fingerprint)
            if replay is not None:
                return replay
            respuesta, movimiento_id, accion, cargo_id = mutar(session)
            registrar_evento_session(
                session, action=accion, resource_type='finanzas', result='confirmado',
                actor_id=actor_id, resource_id=movimiento_id)
            _guardar_idempotencia(session, actor_id=actor_id, operacion=operacion,
                                  clave=clave, fingerprint=fingerprint, respuesta=respuesta)
            return respuesta
    except ErrorFinanzas:
        raise
    except (SQLAlchemyError, sqlite3.Error, RuntimeError) as exc:
        raise ErrorFinanzas('almacenamiento_error', 'No se pudo confirmar el movimiento.', 503) from exc


def crear_cargo(engine, *, paciente_id: str, actor_id: str, clave: str,
                monto_ars: str, concepto: str) -> dict[str, object]:
    clave = _clave(clave)
    try:
        centavos = importe_ars_a_centavos(monto_ars)
    except ValueError as exc:
        raise ErrorFinanzas('entrada_invalida', 'Importe ARS inválido.', 422) from exc
    concepto = _texto(concepto, 200, 'Concepto')
    payload = {'paciente_id': paciente_id, 'monto_centavos': centavos, 'concepto': concepto}

    def mutar(session):
        paciente = session.get(Paciente, paciente_id)
        if paciente is None:
            raise ErrorFinanzas('paciente_no_encontrado', 'Paciente no encontrado.', 404)
        if not paciente.activo:
            raise ErrorFinanzas('paciente_inactivo', 'La ficha está inactiva.', 409)
        movimiento_id = str(uuid4())
        cargo = CargoFinanciero(id=movimiento_id, paciente_id=paciente_id,
                                monto_centavos=centavos, concepto=concepto,
                                created_at=datetime.now(timezone.utc))
        session.add(cargo)
        session.flush()
        respuesta = {'id': movimiento_id, 'tipo': 'cargo',
                     'monto_ars': centavos_a_importe_ars(centavos),
                     'saldo_ars': centavos_a_importe_ars(_saldo(session, movimiento_id))}
        return respuesta, movimiento_id, 'cargo.creado', movimiento_id

    return _ejecutar(engine, 'cargo', actor_id, clave, payload, mutar)


def registrar_cobro(engine, *, cargo_id: str, actor_id: str, clave: str,
                    monto_ars: str) -> dict[str, object]:
    clave = _clave(clave)
    try:
        centavos = importe_ars_a_centavos(monto_ars)
    except ValueError as exc:
        raise ErrorFinanzas('entrada_invalida', 'Importe ARS inválido.', 422) from exc
    payload = {'cargo_id': cargo_id, 'monto_centavos': centavos}

    def mutar(session):
        cargo = session.get(CargoFinanciero, cargo_id)
        if cargo is None:
            raise ErrorFinanzas('cargo_no_encontrado', 'Cargo no encontrado.', 404)
        saldo = _saldo(session, cargo_id)
        if centavos > saldo:
            raise ErrorFinanzas('saldo_insuficiente', 'El cobro supera el saldo pendiente.', 409)
        movimiento_id = str(uuid4())
        session.add(CobroFinanciero(id=movimiento_id, cargo_id=cargo_id,
                                    monto_centavos=centavos,
                                    created_at=datetime.now(timezone.utc)))
        session.flush()
        respuesta = {'id': movimiento_id, 'tipo': 'cobro',
                     'monto_ars': centavos_a_importe_ars(centavos),
                     'saldo_ars': centavos_a_importe_ars(_saldo(session, cargo_id))}
        return respuesta, movimiento_id, 'cobro.registrado', cargo_id

    return _ejecutar(engine, 'cobro', actor_id, clave, payload, mutar)


def revertir_cobro(engine, *, cobro_id: str, actor_id: str, clave: str,
                   monto_ars: str, motivo: str) -> dict[str, object]:
    clave = _clave(clave)
    try:
        centavos = importe_ars_a_centavos(monto_ars)
    except ValueError as exc:
        raise ErrorFinanzas('entrada_invalida', 'Importe ARS inválido.', 422) from exc
    motivo = _texto(motivo, 500, 'Motivo')
    payload = {'cobro_id': cobro_id, 'monto_centavos': centavos, 'motivo': motivo}

    def mutar(session):
        cobro = session.get(CobroFinanciero, cobro_id)
        if cobro is None:
            raise ErrorFinanzas('cobro_no_encontrado', 'Cobro no encontrado.', 404)
        reversiones = session.scalars(select(ReversionCobro.monto_centavos).where(
            ReversionCobro.cobro_id == cobro_id)).all()
        restante = importe_reversible_centavos(cobro.monto_centavos, reversiones)
        if centavos > restante:
            raise ErrorFinanzas('reversion_excesiva', 'La reversión supera el cobro neto.', 409)
        movimiento_id = str(uuid4())
        session.add(ReversionCobro(id=movimiento_id, cobro_id=cobro_id,
                                   monto_centavos=centavos, motivo=motivo,
                                   created_at=datetime.now(timezone.utc)))
        session.flush()
        cargo_id = session.get(CobroFinanciero, cobro_id).cargo_id
        respuesta = {'id': movimiento_id, 'tipo': 'reversion',
                     'monto_ars': centavos_a_importe_ars(centavos),
                     'saldo_ars': centavos_a_importe_ars(_saldo(session, cargo_id))}
        return respuesta, movimiento_id, 'cobro.revertido', cargo_id

    return _ejecutar(engine, 'reversion', actor_id, clave, payload, mutar)


def consultar_cuenta(engine, *, paciente_id: str, actor_id: str) -> dict[str, object]:
    try:
        with Session(engine) as session, session.begin():
            _bloquear(session)
            if session.get(Paciente, paciente_id) is None:
                raise ErrorFinanzas('paciente_no_encontrado', 'Paciente no encontrado.', 404)
            cargos = session.scalars(select(CargoFinanciero).where(
                CargoFinanciero.paciente_id == paciente_id).order_by(
                    CargoFinanciero.created_at, CargoFinanciero.id)).all()
            items = []
            saldo_total = 0
            for cargo in cargos:
                saldo = _saldo(session, cargo.id)
                saldo_total += saldo
                items.append({'id': cargo.id, 'tipo': 'cargo',
                              'monto_ars': centavos_a_importe_ars(cargo.monto_centavos),
                              'concepto': cargo.concepto,
                              'created_at': cargo.created_at.isoformat()})
                cobros = session.scalars(select(CobroFinanciero).where(
                    CobroFinanciero.cargo_id == cargo.id).order_by(
                        CobroFinanciero.created_at, CobroFinanciero.id)).all()
                for cobro in cobros:
                    items.append({'id': cobro.id, 'tipo': 'cobro',
                                  'monto_ars': centavos_a_importe_ars(cobro.monto_centavos),
                                  'created_at': cobro.created_at.isoformat()})
                    reversales = session.scalars(select(ReversionCobro).where(
                        ReversionCobro.cobro_id == cobro.id).order_by(
                            ReversionCobro.created_at, ReversionCobro.id)).all()
                    items.extend({'id': item.id, 'tipo': 'reversion',
                                  'monto_ars': centavos_a_importe_ars(item.monto_centavos),
                                  'motivo': item.motivo,
                                  'created_at': item.created_at.isoformat()}
                                 for item in reversales)
            items.sort(key=lambda item: (item['created_at'], item['id']))
            registrar_evento_session(session, action='finanzas.consultadas',
                                     resource_type='finanzas', result='confirmado',
                                     actor_id=actor_id)
            return {'items': items, 'saldo_ars': centavos_a_importe_ars(saldo_total)}
    except ErrorFinanzas:
        raise
    except (SQLAlchemyError, sqlite3.Error, RuntimeError) as exc:
        raise ErrorFinanzas('almacenamiento_error', 'No se pudo consultar la cuenta.', 503) from exc
