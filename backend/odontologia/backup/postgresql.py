"""Creación de bundles custom PostgreSQL con cliente externo validado."""

import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import mkdtemp

from odontologia.backup.errors import ErrorBackup
from odontologia.backup.manifest import (
    ErrorManifiesto,
    crear_manifiesto,
    guardar_manifiesto,
    leer_manifiesto,
)
from odontologia.backup.postgresql_tools import (
    ErrorHerramientasPostgresql,
    validar_runtime_postgresql,
)
from odontologia.backup.permisos import (
    MODO_ARCHIVO_PRIVADO,
    MODO_DIRECTORIO_PRIVADO,
    crear_archivo_exclusivo,
    publicar_directorio_nuevo,
    restringir_modo_posix,
)
from odontologia.backup.recuentos import contar_tablas_postgresql


_PAYLOAD = 'agenda.dump'
_MANIFIESTO = 'manifest.json'
_REVISION_ACTUAL = '20261102_0013_patient_self_service'


def crear_bundle_postgresql(engine, destino: str | Path) -> dict[str, object]:
    """Crear y validar una copia pg_dump custom en un directorio nuevo."""
    ruta_destino = Path(destino)
    staging: Path | None = None
    destino_publicado: Path | None = None
    identidad_publicada: tuple[int, int] | None = None
    bundle_validado = False
    try:
        if ruta_destino.exists() or ruta_destino.is_symlink():
            raise ErrorBackup('destino_existente')
        # Revisar esquema y clientes antes de crear directorios o archivos de salida.
        _validar_revision(engine)
        herramientas = validar_runtime_postgresql(engine)
        padre = ruta_destino.parent.resolve(strict=True)
        destino_publicado = padre / ruta_destino.name
        if destino_publicado.exists() or destino_publicado.is_symlink():
            raise ErrorBackup('destino_existente')

        staging = Path(mkdtemp(prefix='.tmp-backup-', dir=padre))
        restringir_modo_posix(staging, MODO_DIRECTORIO_PRIVADO)
        payload = staging / _PAYLOAD
        descriptor = crear_archivo_exclusivo(payload)
        os.close(descriptor)
        table_counts = _capturar_snapshot_y_dump(engine, herramientas, payload)
        restringir_modo_posix(payload, MODO_ARCHIVO_PRIVADO)
        _validar_archive(engine, herramientas, payload)
        manifiesto = crear_manifiesto(
            payload, backend='postgresql', schema_version=_REVISION_ACTUAL,
            table_counts=table_counts)
        guardar_manifiesto(manifiesto, staging / _MANIFIESTO)
        leer_manifiesto(staging / _MANIFIESTO, payload)

        try:
            publicar_directorio_nuevo(staging, destino_publicado)
        except FileExistsError as exc:
            raise ErrorBackup('destino_existente') from exc
        identidad_publicada = _identidad(destino_publicado)
        leer_manifiesto(destino_publicado / _MANIFIESTO)
        _validar_archive(engine, herramientas, destino_publicado / _PAYLOAD)
        bundle_validado = True
        return manifiesto
    except ErrorBackup:
        raise
    except ErrorHerramientasPostgresql as exc:
        raise ErrorBackup(exc.codigo) from exc
    except ErrorManifiesto as exc:
        raise ErrorBackup('bundle_invalido') from exc
    except (OSError, subprocess.SubprocessError, ValueError, TypeError) as exc:
        raise ErrorBackup('operacion_fallida') from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        if (destino_publicado is not None and identidad_publicada is not None
                and _identidad(destino_publicado) == identidad_publicada
                and not bundle_validado):
            shutil.rmtree(destino_publicado, ignore_errors=True)


def _validar_revision(engine) -> None:
    from sqlalchemy import text

    try:
        with engine.connect() as conexion:
            revision = conexion.execute(
                text('SELECT version_num FROM alembic_version')).scalar_one()
    except Exception as exc:
        raise ErrorBackup('esquema_incompatible') from exc
    if revision != _REVISION_ACTUAL:
        raise ErrorBackup('esquema_incompatible')


def _entorno(engine) -> dict[str, str]:
    """Armar entorno mínimo para libpq; no heredar JWT u otras credenciales."""
    import os

    url = engine.url
    entorno = {
        clave: os.environ[clave]
        for clave in ('PATH', 'SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'LC_ALL')
        if clave in os.environ
    }
    valores = {
        'PGHOST': url.host,
        'PGPORT': str(url.port) if url.port is not None else None,
        'PGUSER': url.username,
        'PGPASSWORD': url.password,
    }
    for clave_url, clave_pg in (
            ('sslmode', 'PGSSLMODE'), ('sslrootcert', 'PGSSLROOTCERT'),
            ('sslcert', 'PGSSLCERT'), ('sslkey', 'PGSSLKEY'),
            ('connect_timeout', 'PGCONNECT_TIMEOUT'), ('application_name', 'PGAPPNAME'),
            ('options', 'PGOPTIONS')):
        valor = url.query.get(clave_url)
        if isinstance(valor, str):
            valores[clave_pg] = valor
    entorno.update({clave: valor for clave, valor in valores.items() if valor is not None})
    return entorno


def _capturar_snapshot_y_dump(engine, herramientas: dict[str, object],
                              payload: Path) -> dict[str, int]:
    from sqlalchemy import text

    try:
        with engine.connect() as conexion:
            conexion = conexion.execution_options(isolation_level='REPEATABLE READ')
            with conexion.begin():
                revision = conexion.execute(
                    text('SELECT version_num FROM alembic_version')).scalar_one()
                if revision != _REVISION_ACTUAL:
                    raise ErrorBackup('esquema_incompatible')
                table_counts = contar_tablas_postgresql(conexion)
                snapshot_id = conexion.execute(
                    text('SELECT pg_export_snapshot()')).scalar_one()
                if not isinstance(snapshot_id, str) or not re.fullmatch(
                        r'[0-9A-Fa-f-]+', snapshot_id):
                    raise ErrorBackup('operacion_fallida')
                _ejecutar_dump(engine, herramientas, payload, snapshot_id)
                return table_counts
    except ErrorBackup:
        raise
    except Exception as exc:
        raise ErrorBackup('operacion_fallida') from exc


def _ejecutar_dump(engine, herramientas: dict[str, object], payload: Path,
                   snapshot_id: str) -> None:
    comando = [
        str(herramientas['pg_dump']), '--format=custom', '--no-password',
        f'--snapshot={snapshot_id}', '--file', str(payload),
        '--dbname', engine.url.database,
    ]
    try:
        resultado = subprocess.run(
            comando, check=False, capture_output=True, text=True, timeout=300,
            shell=False, env=_entorno(engine),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ErrorBackup('operacion_fallida') from exc
    if resultado.returncode != 0 or not payload.is_file() or payload.stat().st_size == 0:
        raise ErrorBackup('operacion_fallida')


def _validar_archive(engine, herramientas: dict[str, object], payload: Path) -> None:
    comando = [str(herramientas['pg_restore']), '--list', str(payload)]
    try:
        resultado = subprocess.run(
            comando, check=False, capture_output=True, text=True, timeout=60,
            shell=False, env=_entorno(engine),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ErrorBackup('bundle_invalido') from exc
    if resultado.returncode != 0 or not (resultado.stdout or '').strip():
        raise ErrorBackup('bundle_invalido')


def _identidad(ruta: Path) -> tuple[int, int] | None:
    try:
        estado = ruta.stat(follow_symlinks=False)
        return estado.st_dev, estado.st_ino
    except OSError:
        return None
