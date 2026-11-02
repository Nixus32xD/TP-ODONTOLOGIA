"""Probe de conectividad de sólo lectura para readiness."""
import sqlite3
from contextlib import closing
from pathlib import Path

from sqlalchemy import text


def comprobar_conectividad(persistencia: str, ruta_sqlite: str | Path, engine) -> None:
    """Ejecutar exclusivamente SELECT 1 sin crear base ni alterar el esquema."""
    if persistencia == 'sqlite':
        ruta = Path(ruta_sqlite)
        if not ruta.is_file():
            raise OSError('Base SQLite no disponible.')
        with closing(sqlite3.connect(
                f'{ruta.resolve().as_uri()}?mode=ro', uri=True, timeout=1.0)) as conexion:
            if conexion.execute('SELECT 1').fetchone() != (1,):
                raise OSError('Probe SQLite no disponible.')
        return

    if persistencia == 'postgresql':
        with engine.connect() as conexion:
            if conexion.execute(text('SELECT 1')).scalar_one() != 1:
                raise OSError('Probe PostgreSQL no disponible.')
        return

    raise OSError('Persistencia desconocida.')
