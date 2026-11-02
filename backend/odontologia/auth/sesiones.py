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
from odontologia.db.models import AgendaMutex, Sesion, Usuario


_EMISOR = 'odontologia-local'
_TTL_PREDETERMINADO = 30 * 60


class ErrorSesiones(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int = 401):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


def _ahora(ahora: int | None) -> int:
    return int(time.time()) if ahora is None else int(ahora)


def _bloquear_sqlite(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
    else:
        session.scalar(select(AgendaMutex.id).where(AgendaMutex.id == 1).with_for_update())


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
               ahora: int | None = None) -> str:
    instante = _ahora(ahora)
    try:
        clave = validar_secreto_jwt(secreto)
        nombre = normalizar_identificador(identificador)
        validar_password(password)
    except ValueError as exc:
        raise ErrorSesiones('credenciales_invalidas', 'Identificador o contraseña inválidos.', 401) from exc
    if not isinstance(duracion_segundos, int) or not 60 <= duracion_segundos <= 24 * 60 * 60:
        raise ErrorSesiones('autenticacion_no_configurada', 'La autenticación no está configurada.', 503)

    try:
        with Session(engine) as session, session.begin():
            _bloquear_sqlite(session)
            usuario = session.scalar(select(Usuario).where(Usuario.identificador == nombre))
            if usuario is None:
                # Igualar aproximadamente el coste de scrypt y evitar enumeración temporal.
                hashlib.scrypt(password.encode('utf-8'), salt=b'auth-dummy-salt-01',
                               n=1 << 14, r=8, p=1, dklen=64)
                raise ErrorSesiones('credenciales_invalidas', 'Identificador o contraseña inválidos.', 401)
            if not verificar_password(password, usuario.password_hash) or not usuario.activo:
                raise ErrorSesiones('credenciales_invalidas', 'Identificador o contraseña inválidos.', 401)
            sesion_id = str(uuid4())
            jti = str(uuid4())
            expira = instante + duracion_segundos
            session.add(Sesion(id=sesion_id, usuario_id=usuario.id, jti=jti,
                               expira_en=expira, creado_en=instante))
            session.flush()
            payload = {'iss': _EMISOR, 'sub': usuario.id, 'sid': sesion_id,
                       'jti': jti, 'rol': usuario.rol, 'iat': instante, 'exp': expira}
        return jwt.encode(payload, clave, algorithm='HS256')
    except ErrorSesiones:
        raise
    except SQLAlchemyError as exc:
        raise ErrorSesiones('almacenamiento_error', 'No se pudo validar la sesión.', 503) from exc


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
                    or usuario.rol != payload['rol']):
                raise ErrorSesiones('token_invalido', 'La sesión no es válida.', 401)
            return {'usuario_id': usuario.id, 'identificador': usuario.identificador,
                    'rol': usuario.rol, 'sesion_id': registro.id,
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
            session.execute(update(Sesion).where(
                Sesion.id == identidad['sesion_id'], Sesion.revocada_en.is_(None)
            ).values(revocada_en=instante))
    except SQLAlchemyError as exc:
        raise ErrorSesiones('almacenamiento_error', 'No se pudo cerrar la sesión.', 503) from exc
