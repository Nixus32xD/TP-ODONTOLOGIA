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
        version_esperada = 7
        validar_version = lambda version: version == version_esperada
        consulta_tablas = text(
            "SELECT name FROM sqlite_master WHERE type='table' "
            'AND name IN (\'horarios_semanales\', \'excepciones_horario\', '
            '\'tramos_excepcion\', \'bloqueos_agenda\')')
        consulta_estado_turno = text('PRAGMA table_info(turnos)')
        consulta_vinculo_profesional = text('PRAGMA table_info(usuarios)')
    elif persistencia == 'postgresql':
        consulta = text('SELECT version_num FROM alembic_version')
        version_esperada = '20261102_0008_professional_accounts'
        validar_version = lambda version: version == version_esperada
        consulta_tablas = text(
            'SELECT table_name FROM information_schema.tables '
            'WHERE table_schema = current_schema() AND table_name IN '
            "('horarios_semanales', 'excepciones_horario', 'tramos_excepcion', 'bloqueos_agenda')")
        consulta_estado_turno = text(
            'SELECT column_name FROM information_schema.columns '
            "WHERE table_schema = current_schema() AND table_name = 'turnos' "
            "AND column_name = 'estado'")
        consulta_vinculo_profesional = text(
            'SELECT column_name FROM information_schema.columns '
            "WHERE table_schema = current_schema() AND table_name = 'usuarios' "
            "AND column_name = 'profesional_id'")
    else:
        raise RuntimeError('Backend de autenticación desconocido.')
    try:
        with engine.connect() as conexion:
            version = conexion.execute(consulta).scalar_one_or_none()
            tablas = set(conexion.execute(consulta_tablas).scalars())
            if persistencia == 'sqlite':
                columnas_turnos = {fila[1] for fila in conexion.execute(consulta_estado_turno)}
                columnas_usuarios = {
                    fila[1] for fila in conexion.execute(consulta_vinculo_profesional)}
            else:
                columnas_turnos = set(conexion.execute(consulta_estado_turno).scalars())
                columnas_usuarios = set(
                    conexion.execute(consulta_vinculo_profesional).scalars())
        if not validar_version(version):
            raise RuntimeError('La versión del esquema de autenticación no está migrada.')
        if len(tablas) != 4:
            raise RuntimeError('El esquema de disponibilidad no está preparado.')
        if 'estado' not in columnas_turnos:
            raise RuntimeError('La columna de estado de turnos no está preparada.')
        if 'profesional_id' not in columnas_usuarios:
            raise RuntimeError('La columna de vínculo profesional no está preparada.')
    except SQLAlchemyError as exc:
        raise RuntimeError('El esquema de autenticación no está preparado.') from exc
