"""Verificación de bundles sin modificar el artefacto ni conectarse al servidor."""

import os
from pathlib import Path
import shutil
import subprocess

from odontologia.backup.bundle import _validar_sqlite
from odontologia.backup.errors import ErrorBackup
from odontologia.backup.manifest import ErrorManifiesto, leer_manifiesto
from odontologia.backup.recuentos import contar_tablas_sqlite


_ARCHIVOS_ESPERADOS = {
    'sqlite': {'agenda.sqlite3', 'manifest.json'},
    'postgresql': {'agenda.dump', 'manifest.json'},
}


def verificar_bundle(bundle: str | Path) -> dict[str, object]:
    """Validar estructura, manifiesto, checksum y formato del payload seleccionado."""
    ruta = Path(bundle)
    try:
        if ruta.is_symlink() or not ruta.is_dir():
            raise ErrorBackup('bundle_invalido')
        if any(item.is_symlink() for item in ruta.iterdir()):
            raise ErrorBackup('bundle_invalido')
        manifiesto = leer_manifiesto(ruta / 'manifest.json')
        backend = manifiesto['backend']
        if set(item.name for item in ruta.iterdir()) != _ARCHIVOS_ESPERADOS[backend]:
            raise ErrorBackup('bundle_invalido')
        payload = ruta / manifiesto['payload_name']
        if backend == 'sqlite':
            _validar_sqlite(payload)
            if contar_tablas_sqlite(payload) != manifiesto['table_counts']:
                raise ErrorBackup('recuentos_incompatibles')
        else:
            _validar_archive_postgresql(payload)
        return {
            'verified': True,
            'backend': backend,
            'schema_version': manifiesto['schema_version'],
            'payload_name': manifiesto['payload_name'],
            'payload_size_bytes': manifiesto['payload_size_bytes'],
            'payload_sha256': manifiesto['payload_sha256'],
            'table_counts': manifiesto['table_counts'],
        }
    except ErrorBackup:
        raise
    except ErrorManifiesto as exc:
        raise ErrorBackup('bundle_invalido') from exc
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise ErrorBackup('bundle_invalido') from exc


def _validar_archive_postgresql(payload: Path) -> None:
    pg_restore = shutil.which('pg_restore')
    if not pg_restore:
        raise ErrorBackup('herramienta_ausente')
    entorno = {clave: os.environ[clave] for clave in ('PATH', 'SystemRoot', 'WINDIR')
               if clave in os.environ}
    try:
        resultado = subprocess.run(
            [pg_restore, '--list', str(payload)], check=False, capture_output=True,
            text=True, timeout=60, shell=False, env=entorno,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ErrorBackup('bundle_invalido') from exc
    if resultado.returncode != 0 or not (resultado.stdout or '').strip():
        raise ErrorBackup('bundle_invalido')
