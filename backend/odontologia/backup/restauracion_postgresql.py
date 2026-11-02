"""Restauración PostgreSQL aislada con base staging y destino nuevo."""

import re
from pathlib import Path
import subprocess
from uuid import uuid4

from odontologia.backup.errors import ErrorBackup
from odontologia.backup.postgresql import _entorno
from odontologia.backup.postgresql_tools import ErrorHerramientasPostgresql, validar_runtime_postgresql
from odontologia.backup.recuentos import contar_tablas_postgresql
from odontologia.backup.verificacion import verificar_bundle


_NOMBRE_DB = re.compile(r'[a-z_][a-z0-9_]{0,62}\Z')


def restaurar_bundle_postgresql(engine, bundle: str | Path, destino: str) -> dict[str, object]:
    """Restaurar un archive en una DB aleatoria y renombrarla sólo tras validación."""
    nombre_destino = _validar_nombre_destino(engine, destino)
    manifiesto = verificar_bundle(bundle)
    if manifiesto['backend'] != 'postgresql':
        raise ErrorBackup('bundle_invalido')
    ruta_payload = Path(bundle) / manifiesto['payload_name']
    try:
        herramientas = validar_runtime_postgresql(engine)
        motor_admin = _crear_engine_mantenimiento(engine)
    except ErrorHerramientasPostgresql as exc:
        raise ErrorBackup(exc.codigo) from exc
    except Exception as exc:
        raise ErrorBackup('servidor_no_disponible') from exc

    nombre_staging: str | None = None
    publicado = False
    try:
        _validar_cluster_destino(motor_admin, nombre_destino)
        nombre_staging = _crear_base_staging(motor_admin)
        _ejecutar_restore(engine, herramientas, ruta_payload, nombre_staging)
        recuentos = _validar_base_restaurada(engine, nombre_staging, manifiesto)
        _renombrar_base(motor_admin, nombre_staging, nombre_destino)
        publicado = True
        return {
            'restored': True,
            'backend': 'postgresql',
            'schema_version': manifiesto['schema_version'],
            'table_counts': recuentos,
        }
    except ErrorBackup:
        raise
    except (OSError, subprocess.SubprocessError, ValueError, TypeError) as exc:
        raise ErrorBackup('operacion_fallida') from exc
    finally:
        if nombre_staging is not None and not publicado:
            _eliminar_base_staging(motor_admin, nombre_staging)
        motor_admin.dispose()


def _validar_nombre_destino(engine, nombre: str) -> str:
    if not isinstance(nombre, str) or not _NOMBRE_DB.fullmatch(nombre):
        raise ErrorBackup('ruta_invalida')
    if nombre == engine.url.database:
        raise ErrorBackup('agenda_activa')
    return nombre


def _crear_engine_mantenimiento(engine):
    from sqlalchemy import create_engine

    url = engine.url.set(database='postgres')
    return create_engine(url, isolation_level='AUTOCOMMIT', pool_pre_ping=True)


def _validar_cluster_destino(motor_admin, nombre_destino: str) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    try:
        with motor_admin.connect() as conexion:
            existe = conexion.execute(
                text('SELECT 1 FROM pg_database WHERE datname = :database_name'),
                {'database_name': nombre_destino},
            ).scalar_one_or_none()
            if existe is not None:
                raise ErrorBackup('destino_existente')
            puede_crear = conexion.execute(text(
                'SELECT rolcreatedb FROM pg_roles WHERE rolname = current_user')).scalar_one_or_none()
    except ErrorBackup:
        raise
    except SQLAlchemyError as exc:
        raise ErrorBackup('servidor_no_disponible') from exc
    if puede_crear is not True:
        raise ErrorBackup('permiso_insuficiente')


def _crear_base_staging(motor_admin) -> str:
    from sqlalchemy.exc import SQLAlchemyError

    nombre = f'c12_restore_{uuid4().hex}'
    try:
        with motor_admin.connect() as conexion:
            conexion.exec_driver_sql(f'CREATE DATABASE "{nombre}"')
    except SQLAlchemyError as exc:
        raise ErrorBackup('permiso_insuficiente') from exc
    return nombre


def _ejecutar_restore(engine, herramientas: dict[str, object], payload: Path,
                      nombre_staging: str) -> None:
    comando = [
        str(herramientas['pg_restore']), '--exit-on-error', '--no-password',
        f'--dbname={nombre_staging}', str(payload),
    ]
    try:
        resultado = subprocess.run(
            comando, check=False, capture_output=True, text=True, timeout=600,
            shell=False, env=_entorno(engine),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ErrorBackup('operacion_fallida') from exc
    if resultado.returncode != 0:
        raise ErrorBackup('operacion_fallida')


def _validar_base_restaurada(engine, nombre_staging: str,
                             manifiesto: dict[str, object]) -> dict[str, int]:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError

    motor_staging = create_engine(engine.url.set(database=nombre_staging), pool_pre_ping=True)
    try:
        with motor_staging.connect() as conexion:
            revision = conexion.execute(
                text('SELECT version_num FROM alembic_version')).scalar_one_or_none()
            if revision != manifiesto['schema_version']:
                raise ErrorBackup('esquema_incompatible')
            recuentos = contar_tablas_postgresql(conexion)
            constraints_no_validadas = conexion.execute(text(
                "SELECT count(*) FROM pg_constraint WHERE contype='f' AND NOT convalidated"
            )).scalar_one()
            if constraints_no_validadas:
                raise ErrorBackup('referencias_invalidas')
        if recuentos != manifiesto['table_counts']:
            raise ErrorBackup('recuentos_incompatibles')
        return recuentos
    except ErrorBackup:
        raise
    except SQLAlchemyError as exc:
        raise ErrorBackup('bundle_invalido') from exc
    finally:
        motor_staging.dispose()


def _renombrar_base(motor_admin, nombre_staging: str, nombre_destino: str) -> None:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    try:
        with motor_admin.connect() as conexion:
            existe = conexion.execute(
                text('SELECT 1 FROM pg_database WHERE datname = :database_name'),
                {'database_name': nombre_destino},
            ).scalar_one_or_none()
            if existe is not None:
                raise ErrorBackup('destino_existente')
            conexion.exec_driver_sql(
                f'ALTER DATABASE "{nombre_staging}" RENAME TO "{nombre_destino}"')
    except ErrorBackup:
        raise
    except SQLAlchemyError as exc:
        raise ErrorBackup('operacion_fallida') from exc


def _eliminar_base_staging(motor_admin, nombre_staging: str) -> None:
    from sqlalchemy.exc import SQLAlchemyError

    try:
        with motor_admin.connect() as conexion:
            conexion.exec_driver_sql(f'DROP DATABASE IF EXISTS "{nombre_staging}"')
    except SQLAlchemyError as exc:
        raise ErrorBackup('limpieza_incompleta') from exc
