"""Configuración de entorno; leerla no abre conexiones ni muta bases."""
from dataclasses import dataclass
import os
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Configuracion:
    persistencia: str
    odontologia_db: str
    database_url: str | None
    redis_url: str | None
    jwt_secreto: str | None
    jwt_algoritmo: str
    jwt_minutos_expiracion: int


def cargar_configuracion() -> Configuracion:
    persistencia = os.environ.get('ODONTOLOGIA_PERSISTENCIA', 'sqlite')
    if persistencia not in {'sqlite', 'postgresql'}:
        raise ValueError('ODONTOLOGIA_PERSISTENCIA debe ser sqlite o postgresql.')

    database_url = os.environ.get('DATABASE_URL')
    if persistencia == 'postgresql':
        partes_url = urlsplit(database_url or '')
        if (not database_url or partes_url.scheme != 'postgresql+psycopg'
                or not partes_url.path.strip('/')):
            raise ValueError(
                'DATABASE_URL debe ser una URL postgresql+psycopg válida cuando '
                'ODONTOLOGIA_PERSISTENCIA=postgresql.')

    return Configuracion(
        persistencia=persistencia,
        odontologia_db=os.environ.get('ODONTOLOGIA_DB', 'agenda.sqlite3'),
        database_url=database_url,
        redis_url=os.environ.get('REDIS_URL'),
        jwt_secreto=os.environ.get('JWT_SECRETO'),
        jwt_algoritmo=os.environ.get('JWT_ALGORITMO', 'HS256'),
        jwt_minutos_expiracion=int(os.environ.get('JWT_MINUTOS_EXPIRACION', '30')),
    )
