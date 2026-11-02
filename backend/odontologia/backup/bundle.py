"""Creación validada de bundles SQLite en directorios locales nuevos."""

import os
from pathlib import Path
import shutil
import sqlite3
from tempfile import mkdtemp

from odontologia.backup.errors import ErrorBackup
from odontologia.backup.manifest import (
    ErrorManifiesto,
    ESQUEMAS_SOPORTADOS,
    TABLAS_ESQUEMA_ACTUAL,
    crear_manifiesto,
    guardar_manifiesto,
    leer_manifiesto,
)
from odontologia.backup.permisos import (
    MODO_DIRECTORIO_PRIVADO,
    publicar_directorio_nuevo,
    restringir_modo_posix,
)
from odontologia.backup.recuentos import contar_tablas_sqlite
from odontologia.backup.sqlite import crear_snapshot_sqlite


_PAYLOAD = 'agenda.sqlite3'
_MANIFIESTO = 'manifest.json'


def crear_bundle_sqlite(origen: str | Path, destino: str | Path, *, pages: int = 128,
                        progress=None) -> dict[str, object]:
    """Crear un bundle SQLite completo; rechaza destinos existentes y esquemas viejos."""
    ruta_origen = Path(origen)
    ruta_destino = Path(destino)
    staging: Path | None = None
    destino_propio: tuple[int, int] | None = None
    try:
        if not ruta_origen.exists():
            raise ErrorBackup('origen_ausente')
        _validar_sqlite(ruta_origen)
        if ruta_destino.exists() or ruta_destino.is_symlink():
            raise ErrorBackup('destino_existente')
        padre = ruta_destino.parent.resolve(strict=True)
        destino_resuelto = padre / ruta_destino.name
        if destino_resuelto == ruta_origen.resolve(strict=True):
            raise ErrorBackup('origen_invalido')

        staging = Path(mkdtemp(prefix='.tmp-backup-', dir=padre))
        restringir_modo_posix(staging, MODO_DIRECTORIO_PRIVADO)
        payload = staging / _PAYLOAD
        crear_snapshot_sqlite(ruta_origen, payload, pages=pages, progress=progress)
        _validar_sqlite(payload)
        table_counts = contar_tablas_sqlite(payload)
        manifiesto = crear_manifiesto(
            payload, backend='sqlite', schema_version=ESQUEMAS_SOPORTADOS['sqlite'],
            table_counts=table_counts)
        guardar_manifiesto(manifiesto, staging / _MANIFIESTO)
        # Volver a leer desde el disco antes de hacer visible el bundle.
        leer_manifiesto(staging / _MANIFIESTO, payload)

        try:
            publicar_directorio_nuevo(staging, destino_resuelto)
        except FileExistsError as exc:
            raise ErrorBackup('destino_existente') from exc
        destino_propio = _identidad(destino_resuelto)
        leer_manifiesto(destino_resuelto / _MANIFIESTO)
        _validar_sqlite(destino_resuelto / _PAYLOAD)
        return manifiesto
    except ErrorBackup:
        raise
    except ErrorManifiesto as exc:
        raise ErrorBackup('bundle_invalido') from exc
    except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
        raise ErrorBackup('operacion_fallida') from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        if destino_propio is not None and _identidad(ruta_destino) == destino_propio:
            # Sólo se elimina el directorio que esta operación reservó.
            shutil.rmtree(ruta_destino, ignore_errors=True) if not _bundle_valido(ruta_destino) else None


def _validar_sqlite(ruta: Path) -> None:
    try:
        resolved = ruta.resolve(strict=True)
        uri = resolved.as_uri() + '?mode=ro'
        conexion = sqlite3.connect(uri, uri=True, autocommit=True)
        try:
            resultado = conexion.execute('PRAGMA integrity_check').fetchone()
            if resultado != ('ok',):
                raise ErrorBackup('integridad_invalida')
            if conexion.execute('PRAGMA foreign_key_check').fetchone() is not None:
                raise ErrorBackup('referencias_invalidas')
            tablas = {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'")}
            if tablas != TABLAS_ESQUEMA_ACTUAL['sqlite']:
                raise ErrorBackup('esquema_incompatible')
            if 'auth_schema_version' not in tablas:
                raise ErrorBackup('esquema_incompatible')
            revision = conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone()
            if revision != (10,):
                raise ErrorBackup('esquema_incompatible')
            columnas_turnos = {fila[1] for fila in conexion.execute(
                'PRAGMA table_info(turnos)')}
            if 'version' not in columnas_turnos:
                raise ErrorBackup('esquema_incompatible')
        finally:
            conexion.close()
    except ErrorBackup:
        raise
    except (OSError, sqlite3.Error, ValueError) as exc:
        raise ErrorBackup('integridad_invalida') from exc


def _identidad(ruta: Path) -> tuple[int, int] | None:
    try:
        estado = ruta.stat(follow_symlinks=False)
        return estado.st_dev, estado.st_ino
    except OSError:
        return None


def _bundle_valido(ruta: Path) -> bool:
    try:
        leer_manifiesto(ruta / _MANIFIESTO)
        _validar_sqlite(ruta / _PAYLOAD)
        return True
    except (ErrorManifiesto, ErrorBackup, OSError):
        return False
