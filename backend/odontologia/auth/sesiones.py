"""Autenticación con JWT HS256 y revocación persistida por sesión."""
import hashlib
import time
from uuid import uuid4

import jwt
from sqlalchemy import select, text, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.auth.credenciales import (
    normalizar_identificador,
    validar_password,
    verificar_password,
)
from odontologia.auth.tokens import validar_secreto_jwt
from odontologia.db.models import AgendaMutex, Profesional, Sesion, Usuario
from odontologia.audit import ErrorAuditoria


_EMISOR = 'odontologia-local'
_TTL_PREDETERMINADO = 30 * 60


class ErrorSesiones(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int = 401,
                 retry_after: int | None = None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado
        self.retry_after = retry_after


def _ahora(ahora: int | None) -> int:
    return int(time.time()) if ahora is None else int(ahora)


def _bloquear_sqlite(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
    else:
        mutex = session.scalar(select(AgendaMutex.id).where(
            AgendaMutex.id == 1).with_for_update())
        if mutex != 1:
            raise ErrorSesiones(
                'almacenamiento_error', 'No se pudo validar la sesión.', 503)


def _registrar_rechazo(engine) -> None:
    from odontologia.audit import registrar_evento_session

    with Session(engine) as session, session.begin():
        _bloquear_sqlite(session)
        registrar_evento_session(
            session, action='sesion.rechazada', resource_type='sesion',
            result='rechazado')


def _token_payload(token: str, secreto: str, ahora: int) -> dict:
    try:
        return jwt.decode(
            token, validar_secreto_jwt(secreto), algorithms=['HS256'],
            issuer=_EMISOR, options={'require': ['iss', 'sub', 'sid', 'jti', 'rol', 'iat', 'exp'],
                                     'verify_exp': False, 'verify_iat': False},
        )
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise ErrorSesiones('token_invalido', 'La sesión no es válida.', 401) from exc


def autenticar(engine, identificador: str, password: str, secreto: str,
               *, duracion_segundos: int = _TTL_PREDETERMINADO,
               ahora: int | None = None, limitador=None,
               origen: str | None = None) -> str:
    instante = _ahora(ahora)
    try:
        clave = validar_secreto_jwt(secreto)
    except ValueError as exc:
        raise ErrorSesiones(
            'autenticacion_no_configurada', 'La autenticación no está configurada.', 503) from exc
    try:
        nombre = normalizar_identificador(identificador)
        validar_password(password)
    except ValueError as exc:
        try:
            _registrar_rechazo(engine)
        except (ErrorAuditoria, SQLAlchemyError) as error:
            raise ErrorSesiones(
                'almacenamiento_error', 'No se pudo validar la sesión.', 503) from error
        raise ErrorSesiones(
            'credenciales_invalidas', 'Identificador o contraseña inválidos.', 401) from None
    if not isinstance(duracion_segundos, int) or not 60 <= duracion_segundos <= 24 * 60 * 60:
        raise ErrorSesiones('autenticacion_no_configurada', 'La autenticación no está configurada.', 503)
    reserva = None
    if limitador is not None and origen is not None:
        reserva, restante = limitador.reservar_intento(origen, nombre)
        if restante is not None:
            raise ErrorSesiones(
                'demasiados_intentos', 'Demasiados intentos. Reintente más tarde.', 429,
                retry_after=restante)

    def liberar_reserva() -> None:
        nonlocal reserva
        if reserva is not None:
            limitador.finalizar_intento(
                origen, nombre, reserva, credenciales_validas=None)
            reserva = None

    rechazado = False
    try:
        with Session(engine) as session, session.begin():
            _bloquear_sqlite(session)
            usuario = session.scalar(select(Usuario).where(Usuario.identificador == nombre))
            if usuario is None:
                # Igualar aproximadamente el coste de scrypt y evitar enumeración temporal.
                hashlib.scrypt(password.encode('utf-8'), salt=b'auth-dummy-salt-01',
                               n=1 << 14, r=8, p=1, dklen=64)
                rechazado = True
            elif not verificar_password(password, usuario.password_hash) or not usuario.activo:
                rechazado = True
            elif usuario.rol == 'profesional' and (
                    usuario.profesional_id is None
                    or session.get(Profesional, usuario.profesional_id) is None):
                rechazado = True
            if rechazado:
                from odontologia.audit import registrar_evento_session

                registrar_evento_session(
                    session, action='sesion.rechazada', resource_type='sesion',
                    result='rechazado')
            else:
                sesion_id = str(uuid4())
                jti = str(uuid4())
                expira = instante + duracion_segundos
                session.add(Sesion(id=sesion_id, usuario_id=usuario.id, jti=jti,
                                   expira_en=expira, creado_en=instante))
                session.flush()
                from odontologia.audit import registrar_evento_session

                registrar_evento_session(
                    session, action='sesion.iniciada', resource_type='sesion',
                    actor_id=usuario.id, result='confirmado')
                payload = {'iss': _EMISOR, 'sub': usuario.id, 'sid': sesion_id,
                           'jti': jti, 'rol': usuario.rol,
                           'profesional_id': usuario.profesional_id,
                           'iat': instante, 'exp': expira}
        if rechazado:
            if reserva is not None:
                limitador.finalizar_intento(
                    origen, nombre, reserva, credenciales_validas=False)
                reserva = None
            raise ErrorSesiones(
                'credenciales_invalidas', 'Identificador o contraseña inválidos.', 401)
        if reserva is not None:
            limitador.finalizar_intento(
                origen, nombre, reserva, credenciales_validas=True)
            reserva = None
        return jwt.encode(payload, clave, algorithm='HS256')
    except ErrorSesiones:
        liberar_reserva()
        raise
    except ErrorAuditoria as exc:
        liberar_reserva()
        raise ErrorSesiones('almacenamiento_error', 'No se pudo validar la sesión.', 503) from exc
    except SQLAlchemyError as exc:
        liberar_reserva()
        raise ErrorSesiones('almacenamiento_error', 'No se pudo validar la sesión.', 503) from exc
    except Exception:
        liberar_reserva()
        raise


def validar_sesion(engine, token: str, secreto: str, *, ahora: int | None = None) -> dict[str, object]:
    instante = _ahora(ahora)
    payload = _token_payload(token, secreto, instante)
    try:
        expira = int(payload['exp'])
        if expira <= instante:
            raise ErrorSesiones('token_invalido', 'La sesión no es válida.', 401)
        with Session(engine) as session:
            registro = session.get(Sesion, payload['sid'])
            usuario = session.get(Usuario, payload['sub'])
            if (registro is None or usuario is None or registro.revocada_en is not None
                    or registro.expira_en <= instante or registro.jti != payload['jti']
                    or registro.usuario_id != usuario.id or not usuario.activo
                    or usuario.rol != payload['rol']
                    or usuario.profesional_id != payload.get('profesional_id')
                    or (usuario.rol == 'profesional' and (
                        usuario.profesional_id is None
                        or session.get(Profesional, usuario.profesional_id) is None))):
                raise ErrorSesiones('token_invalido', 'La sesión no es válida.', 401)
            return {'usuario_id': usuario.id, 'identificador': usuario.identificador,
                    'rol': usuario.rol, 'sesion_id': registro.id,
                    'profesional_id': usuario.profesional_id,
                    'expira_en': registro.expira_en}
    except ErrorSesiones:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ErrorSesiones('token_invalido', 'La sesión no es válida.', 401) from exc
    except SQLAlchemyError as exc:
        raise ErrorSesiones('almacenamiento_error', 'No se pudo validar la sesión.', 503) from exc


def cerrar_sesion(engine, token: str, secreto: str, *, ahora: int | None = None) -> None:
    instante = _ahora(ahora)
    identidad = validar_sesion(engine, token, secreto, ahora=instante)
    try:
        with Session(engine) as session, session.begin():
            _bloquear_sqlite(session)
            resultado = session.execute(update(Sesion).where(
                Sesion.id == identidad['sesion_id'], Sesion.revocada_en.is_(None)
            ).values(revocada_en=instante))
            if resultado.rowcount != 1:
                raise ErrorSesiones('token_invalido', 'La sesión no es válida.', 401)
            from odontologia.audit import registrar_evento_session

            registrar_evento_session(
                session, action='sesion.cerrada', resource_type='sesion',
                actor_id=identidad['usuario_id'], result='confirmado')
    except ErrorSesiones:
        raise
    except ErrorAuditoria as exc:
        raise ErrorSesiones('almacenamiento_error', 'No se pudo cerrar la sesión.', 503) from exc
    except SQLAlchemyError as exc:
        raise ErrorSesiones('almacenamiento_error', 'No se pudo cerrar la sesión.', 503) from exc
