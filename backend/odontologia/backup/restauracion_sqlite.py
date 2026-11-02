"""Restauración local de bundles SQLite a archivos que todavía no existen."""

import os
from pathlib import Path
import shutil
from tempfile import mkdtemp

from odontologia.backup.bundle import _validar_sqlite
from odontologia.backup.errors import ErrorBackup
from odontologia.backup.sqlite import crear_snapshot_sqlite
from odontologia.backup.recuentos import contar_tablas_sqlite
from odontologia.backup.verificacion import verificar_bundle


def validar_destino_restauracion_sqlite(bundle: str | Path, destino: str | Path,
                                         origen_activo: str | Path | None = None) -> Path:
    """Normalizar y rechazar alias, destinos existentes, inválidos o dentro del bundle."""
    ruta_bundle = Path(bundle)
    ruta_destino = Path(destino)
    try:
        bundle_resuelto = ruta_bundle.resolve(strict=True)
        if not bundle_resuelto.is_dir():
            raise ErrorBackup('bundle_invalido')
        padre = ruta_destino.parent.resolve(strict=True)
        if not padre.is_dir() or not ruta_destino.name or ruta_destino.name in {'.', '..'}:
            raise ErrorBackup('ruta_invalida')
        destino_resuelto = padre / ruta_destino.name
        if origen_activo is not None:
            activo_resuelto = Path(origen_activo).resolve(strict=False)
            if destino_resuelto.resolve(strict=False) == activo_resuelto:
                raise ErrorBackup('agenda_activa')
        try:
            destino_resuelto.relative_to(bundle_resuelto)
        except ValueError:
            pass
        else:
            raise ErrorBackup('ruta_invalida')
        if destino_resuelto.exists() or destino_resuelto.is_symlink():
            raise ErrorBackup('destino_existente')
        return destino_resuelto
    except ErrorBackup:
        raise
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        raise ErrorBackup('ruta_invalida') from exc


def restaurar_bundle_sqlite(bundle: str | Path, destino: str | Path, *,
                            origen_activo: str | Path | None = None) -> dict[str, object]:
    """Restaurar un bundle verificado sin reemplazar archivos ni mutar su fuente."""
    ruta_destino = validar_destino_restauracion_sqlite(bundle, destino, origen_activo)
    verificado = verificar_bundle(bundle)
    if verificado['backend'] != 'sqlite':
        raise ErrorBackup('bundle_invalido')

    staging: Path | None = None
    identidad_destino: tuple[int, int] | None = None
    publicado = False
    try:
        staging = Path(mkdtemp(prefix='.tmp-restore-', dir=ruta_destino.parent))
        archivo_staging = staging / 'agenda-restaurada.sqlite3'
        payload = Path(bundle) / 'agenda.sqlite3'
        crear_snapshot_sqlite(payload, archivo_staging)
        _validar_sqlite(archivo_staging)
        recuentos_origen = verificado['table_counts']
        recuentos_restaurados = contar_tablas_sqlite(archivo_staging)
        if recuentos_restaurados != recuentos_origen:
            raise ErrorBackup('bundle_invalido')

        try:
            os.link(archivo_staging, ruta_destino)
        except FileExistsError as exc:
            raise ErrorBackup('destino_existente') from exc
        identidad_destino = _identidad(ruta_destino)
        _validar_sqlite(ruta_destino)
        publicado = True
        return {
            'restored': True,
            'backend': 'sqlite',
            'schema_version': verificado['schema_version'],
            'row_counts': recuentos_restaurados,
        }
    except ErrorBackup:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise ErrorBackup('operacion_fallida') from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        if (not publicado and identidad_destino is not None
                and _identidad(ruta_destino) == identidad_destino):
            ruta_destino.unlink(missing_ok=True)


def _identidad(ruta: Path) -> tuple[int, int] | None:
    try:
        estado = ruta.stat(follow_symlinks=False)
        return estado.st_dev, estado.st_ino
    except OSError:
        return None
