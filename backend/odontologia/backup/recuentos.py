"""Recuentos agregados de las tablas vigentes, sin leer valores de filas."""

import sqlite3
from pathlib import Path

from odontologia.backup.errors import ErrorBackup
from odontologia.backup.manifest import TABLAS_ESQUEMA_ACTUAL


def contar_tablas_sqlite(ruta: str | Path) -> dict[str, int]:
    uri = Path(ruta).resolve(strict=True).as_uri() + '?mode=ro'
    conexion = sqlite3.connect(uri, uri=True, autocommit=True)
    try:
        tablas = {fila[0] for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if tablas != TABLAS_ESQUEMA_ACTUAL['sqlite']:
            raise ErrorBackup('esquema_incompatible')
        return _contar_sqlite(conexion, tablas)
    except ErrorBackup:
        raise
    except (OSError, sqlite3.Error, ValueError) as exc:
        raise ErrorBackup('integridad_invalida') from exc
    finally:
        conexion.close()


def _contar_sqlite(conexion, tablas: set[str]) -> dict[str, int]:
    recuentos = {}
    for nombre in sorted(tablas):
        nombre_escapado = nombre.replace('"', '""')
        recuentos[nombre] = conexion.execute(
            f'SELECT count(*) FROM "{nombre_escapado}"').fetchone()[0]
    return recuentos


def contar_tablas_postgresql(conexion) -> dict[str, int]:
    from sqlalchemy import text

    filas = conexion.execute(text(
        'SELECT tablename FROM pg_tables WHERE schemaname = current_schema() '
        'ORDER BY tablename')).scalars().all()
    tablas = set(filas)
    if tablas != TABLAS_ESQUEMA_ACTUAL['postgresql']:
        raise ErrorBackup('esquema_incompatible')
    recuentos = {}
    for nombre in sorted(tablas):
        nombre_escapado = nombre.replace('"', '""')
        recuentos[nombre] = conexion.execute(
            text(f'SELECT count(*) FROM "{nombre_escapado}"')).scalar_one()
    return recuentos
