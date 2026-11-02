"""Validación estricta de configuración JWT; emisión se agrega por servicio."""


_ALGORITMO_PERMITIDO = 'HS256'
_MARCADORES = ('cambiar', 'change_me', 'replace_me', 'your-secret')


def validar_secreto_jwt(secreto: str | None, algoritmo: str = _ALGORITMO_PERMITIDO) -> str:
    if not isinstance(secreto, str) or len(secreto.encode('utf-8')) < 32:
        raise ValueError('JWT_SECRETO debe contener al menos 32 bytes aleatorios.')
    if secreto.strip().casefold().startswith(_MARCADORES):
        raise ValueError('JWT_SECRETO no puede ser un marcador de ejemplo.')
    if algoritmo != _ALGORITMO_PERMITIDO:
        raise ValueError('JWT_ALGORITMO debe ser HS256.')
    return secreto
