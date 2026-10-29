"""Configuración por variables de entorno para el stack de la cátedra.

Sólo lee valores; no abre conexiones ni crea bases de datos al importar.
C-01 sigue usando ODONTOLOGIA_DB (SQLite). DATABASE_URL, REDIS_URL y JWT_*
se consumirán cuando C-02, C-03 y C-17 se propongan e implementen.
"""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Configuracion:
    odontologia_db: str
    database_url: str | None
    redis_url: str | None
    jwt_algoritmo: str
    jwt_minutos_expiracion: int


def cargar_configuracion() -> Configuracion:
    """Leer la configuración del entorno sin valores secretos por defecto."""
    return Configuracion(
        odontologia_db=os.environ.get('ODONTOLOGIA_DB', 'agenda.sqlite3'),
        database_url=os.environ.get('DATABASE_URL'),
        redis_url=os.environ.get('REDIS_URL'),
        jwt_algoritmo=os.environ.get('JWT_ALGORITMO', 'HS256'),
        jwt_minutos_expiracion=int(os.environ.get('JWT_MINUTOS_EXPIRACION', '30')),
    )
