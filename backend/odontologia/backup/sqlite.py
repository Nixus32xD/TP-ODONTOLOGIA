"""Operaciones de snapshot coherente para SQLite."""

from pathlib import Path
import os
import sqlite3

from odontologia.backup.errors import ErrorBackup
from odontologia.backup.permisos import (
    MODO_ARCHIVO_PRIVADO,
    crear_archivo_exclusivo,
    restringir_modo_posix,
)


def crear_snapshot_sqlite(origen: str | Path, destino: str | Path, *, pages: int = 128,
                          progress=None, sleep: float = 0.01) -> None:
    """Crear en forma exclusiva un snapshot SQLite con la API Online Backup."""
    conexion_origen = None
    conexion_destino = None
    ruta_destino = Path(destino)
    identidad_destino = None
    creado_por_operacion = False
    completado = False
    try:
        ruta_origen = Path(origen).resolve(strict=True)
        destino_resuelto = ruta_destino.resolve(strict=False)
        if not ruta_origen.is_file() or ruta_origen == destino_resuelto:
            raise ErrorBackup('origen_invalido')
        if type(pages) is not int or pages <= 0 or type(sleep) not in (int, float) or sleep < 0:
            raise ErrorBackup('configuracion_invalida')
        if progress is not None and not callable(progress):
            raise ErrorBackup('configuracion_invalida')

        descriptor = crear_archivo_exclusivo(ruta_destino)
        os.close(descriptor)
        creado_por_operacion = True
        identidad_destino = _identidad(ruta_destino)

        uri_origen = ruta_origen.as_uri() + '?mode=ro'
        conexion_origen = sqlite3.connect(uri_origen, uri=True, autocommit=True)
        conexion_origen.execute('PRAGMA query_only=ON')
        if conexion_origen.execute('PRAGMA query_only').fetchone() != (1,):
            raise ErrorBackup('origen_invalido')

        conexion_destino = sqlite3.connect(ruta_destino, autocommit=True)
        conexion_origen.backup(
            conexion_destino, pages=pages, progress=progress, sleep=float(sleep))
        restringir_modo_posix(ruta_destino, MODO_ARCHIVO_PRIVADO)
        completado = True
    except ErrorBackup:
        raise
    except FileExistsError as exc:
        raise ErrorBackup('destino_existente') from exc
    except Exception as exc:
        raise ErrorBackup('operacion_fallida') from exc
    finally:
        if conexion_origen is not None:
            conexion_origen.close()
        if conexion_destino is not None:
            conexion_destino.close()
        if (creado_por_operacion and not completado
                and _identidad(ruta_destino) == identidad_destino):
            ruta_destino.unlink(missing_ok=True)


def _identidad(ruta: Path) -> tuple[int, int] | None:
    try:
        estado = ruta.stat(follow_symlinks=False)
        return estado.st_dev, estado.st_ino
    except OSError:
        return None
