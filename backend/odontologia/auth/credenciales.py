"""Primitivas locales de credenciales sin guardar ni registrar secretos."""
import hashlib
import hmac
import os
import re


_MIN_PASSWORD = 12
_MAX_PASSWORD = 128
_SCRYPT_N = 1 << 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DERIVED_LENGTH = 64
_IDENTIFICADOR = re.compile(r'^[a-z0-9][a-z0-9._-]{2,63}$')


def validar_password(password: str) -> bool:
    if not isinstance(password, str) or not _MIN_PASSWORD <= len(password) <= _MAX_PASSWORD:
        raise ValueError('La contraseña debe tener entre 12 y 128 caracteres.')
    if not password.strip():
        raise ValueError('La contraseña no puede estar vacía.')
    return True


def normalizar_identificador(identificador: str) -> str:
    if not isinstance(identificador, str):
        raise ValueError('Identificador inválido.')
    normalizado = identificador.strip().casefold()
    if not _IDENTIFICADOR.fullmatch(normalizado):
        raise ValueError('Identificador inválido.')
    return normalizado


def derivar_password(password: str) -> str:
    validar_password(password)
    sal = os.urandom(16)
    derivado = hashlib.scrypt(
        password.encode('utf-8'), salt=sal, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P,
        dklen=_DERIVED_LENGTH,
    )
    return '$'.join((
        'scrypt', 'v1', str(_SCRYPT_N), str(_SCRYPT_R), str(_SCRYPT_P),
        sal.hex(), derivado.hex(),
    ))


def verificar_password(password: str, password_hash: str) -> bool:
    if not isinstance(password, str) or not isinstance(password_hash, str):
        return False
    try:
        algoritmo, version, n, r, p, sal_hex, esperado_hex = password_hash.split('$')
        if (algoritmo, version, int(n), int(r), int(p)) != (
                'scrypt', 'v1', _SCRYPT_N, _SCRYPT_R, _SCRYPT_P):
            return False
        sal = bytes.fromhex(sal_hex)
        esperado = bytes.fromhex(esperado_hex)
        if len(sal) != 16 or len(esperado) != _DERIVED_LENGTH:
            return False
        calculado = hashlib.scrypt(
            password.encode('utf-8'), salt=sal, n=_SCRYPT_N, r=_SCRYPT_R,
            p=_SCRYPT_P, dklen=_DERIVED_LENGTH,
        )
    except (ValueError, TypeError, OverflowError):
        return False
    return hmac.compare_digest(calculado, esperado)
