"""Construcción de engines de autenticación sin abrir ni preparar bases."""
from pathlib import Path

from sqlalchemy import URL, create_engine, event
from sqlalchemy.pool import NullPool


def crear_engine_autenticacion(persistencia: str, database_url: str | None,
                               ruta_sqlite: str | Path | None):
    if persistencia == 'postgresql':
        if not database_url:
            raise ValueError('DATABASE_URL requerida para autenticación PostgreSQL.')
        from odontologia.db.postgresql import crear_engine

        return crear_engine(database_url)
    if persistencia != 'sqlite' or ruta_sqlite is None:
        raise ValueError('Configuración de persistencia inválida.')

    ruta = Path(ruta_sqlite)
    engine = create_engine(
        URL.create('sqlite', database=str(ruta)),
        connect_args={'timeout': 5.0}, poolclass=NullPool,
    )

    @event.listens_for(engine, 'connect')
    def activar_claves_foraneas(conexion, _registro):
        cursor = conexion.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

    return engine


def validar_ruta_sqlite_existente(ruta_sqlite: str | Path) -> None:
    """Evitar que el driver SQLite cree una DB vacía al ejecutar auth."""
    if not Path(ruta_sqlite).is_file():
        raise RuntimeError('La agenda SQLite no existe o no está disponible.')


def validar_esquema_autenticacion(engine, persistencia: str,
                                  ruta_sqlite: str | Path | None = None) -> None:
    """Comprobar el esquema migrado sin aplicar DDL ni reparar datos."""
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    if persistencia == 'sqlite':
        if ruta_sqlite is None:
            raise RuntimeError('Ruta SQLite requerida.')
        validar_ruta_sqlite_existente(ruta_sqlite)
        consulta = text('SELECT version FROM auth_schema_version')
        version_esperada = 2
        validar_version = lambda version: version == version_esperada
    elif persistencia == 'postgresql':
        consulta = text('SELECT version_num FROM alembic_version')
        version_esperada = '20261101_0003_audit'
        validar_version = lambda version: version == version_esperada
    else:
        raise RuntimeError('Backend de autenticación desconocido.')
    try:
        with engine.connect() as conexion:
            version = conexion.execute(consulta).scalar_one_or_none()
        if not validar_version(version):
            raise RuntimeError('La versión del esquema de autenticación no está migrada.')
    except SQLAlchemyError as exc:
        raise RuntimeError('El esquema de autenticación no está preparado.') from exc
