"""Migraciones explícitas del esquema de autenticación para SQLite."""
from pathlib import Path
import sqlite3


VERSION_ESQUEMA_AUTENTICACION = 2


def _migrar_auditoria(conexion: sqlite3.Connection) -> None:
    conexion.execute('''
        CREATE TABLE eventos_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT CHECK (id > 0),
            created_at TEXT NOT NULL,
            actor_id TEXT REFERENCES usuarios(id) ON DELETE RESTRICT,
            action TEXT NOT NULL CHECK (action IN (
                'turno.creado', 'cuenta.bootstrap', 'cuenta.creada',
                'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada',
                'sesion.rechazada')),
            resource_type TEXT NOT NULL CHECK (resource_type IN ('turno', 'cuenta', 'sesion')),
            resource_id TEXT,
            result TEXT NOT NULL CHECK (result IN ('confirmado', 'rechazado')),
            CHECK (
                (action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR
                (action = 'cuenta.bootstrap' AND resource_type = 'cuenta' AND result = 'confirmado') OR
                (action = 'cuenta.creada' AND resource_type = 'cuenta' AND result = 'confirmado') OR
                (action = 'cuenta.actualizada' AND resource_type = 'cuenta' AND result = 'confirmado') OR
                (action = 'sesion.iniciada' AND resource_type = 'sesion' AND result = 'confirmado') OR
                (action = 'sesion.cerrada' AND resource_type = 'sesion' AND result = 'confirmado') OR
                (action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado')
            ),
            CHECK (action != 'sesion.rechazada' OR (actor_id IS NULL AND resource_id IS NULL))
        )
    ''')
    conexion.execute(
        'CREATE INDEX ix_eventos_auditoria_fecha_id ON eventos_auditoria(created_at, id)')
    conexion.execute('''CREATE TRIGGER eventos_auditoria_no_update
        BEFORE UPDATE ON eventos_auditoria BEGIN
        SELECT RAISE(ABORT, 'eventos_auditoria es append-only'); END''')
    conexion.execute('''CREATE TRIGGER eventos_auditoria_no_delete
        BEFORE DELETE ON eventos_auditoria BEGIN
        SELECT RAISE(ABORT, 'eventos_auditoria es append-only'); END''')


class MigracionAutenticacionError(RuntimeError):
    """Error público y genérico al preparar el almacenamiento de autenticación."""


def _abrir_existente(ruta_db: str | Path) -> sqlite3.Connection:
    ruta = Path(ruta_db)
    if not ruta.is_file():
        raise MigracionAutenticacionError('La agenda SQLite no existe o no es accesible.')
    try:
        return sqlite3.connect(
            f'{ruta.resolve().as_uri()}?mode=rw', uri=True, isolation_level=None,
            timeout=5.0,
        )
    except (OSError, sqlite3.Error, ValueError) as exc:
        raise MigracionAutenticacionError(
            'No se pudo abrir la agenda SQLite existente.') from exc


def migrar_sqlite(ruta_db: str | Path) -> None:
    """Agregar el esquema de autenticación sólo por invocación local explícita."""
    conexion = _abrir_existente(ruta_db)
    try:
        conexion.execute('PRAGMA foreign_keys=ON')
        if conexion.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
            raise MigracionAutenticacionError('No se pudieron activar las claves foráneas.')
        conexion.execute('BEGIN IMMEDIATE')
        tablas = {fila[0] for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        requeridas = {'pacientes', 'profesionales', 'boxes', 'turnos'}
        if not requeridas <= tablas:
            raise MigracionAutenticacionError('La base no contiene un esquema de agenda compatible.')

        if 'auth_schema_version' in tablas:
            version = conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone()
            if version == (1,):
                if not {'usuarios', 'sesiones'} <= tablas:
                    raise MigracionAutenticacionError('El esquema de autenticación está incompleto.')
                _migrar_auditoria(conexion)
                conexion.execute('UPDATE auth_schema_version SET version=2')
                conexion.execute('COMMIT')
                return
            if version != (VERSION_ESQUEMA_AUTENTICACION,):
                raise MigracionAutenticacionError('La versión de autenticación no es compatible.')
            if not {'usuarios', 'sesiones', 'eventos_auditoria'} <= tablas:
                raise MigracionAutenticacionError('El esquema de autenticación está incompleto.')
            conexion.execute('COMMIT')
            return

        if {'usuarios', 'sesiones'} & tablas:
            raise MigracionAutenticacionError('El esquema de autenticación existente no está versionado.')

        conexion.execute('CREATE TABLE auth_schema_version (version INTEGER NOT NULL)')
        conexion.execute('INSERT INTO auth_schema_version(version) VALUES (?)',
                         (VERSION_ESQUEMA_AUTENTICACION,))
        conexion.execute('''
            CREATE TABLE usuarios (
                id TEXT PRIMARY KEY,
                identificador TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL CHECK (rol IN ('administrador', 'recepcion')),
                activo INTEGER NOT NULL CHECK (activo IN (0, 1))
            )
        ''')
        conexion.execute('''
            CREATE TABLE sesiones (
                id TEXT PRIMARY KEY,
                usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                jti TEXT NOT NULL UNIQUE,
                expira_en INTEGER NOT NULL,
                revocada_en INTEGER,
                creado_en INTEGER NOT NULL
            )
        ''')
        conexion.execute('CREATE INDEX ix_sesiones_usuario_id ON sesiones(usuario_id)')
        _migrar_auditoria(conexion)
        conexion.execute('UPDATE auth_schema_version SET version=2')
        conexion.execute('COMMIT')
    except MigracionAutenticacionError:
        if conexion.in_transaction:
            conexion.execute('ROLLBACK')
        raise
    except (OSError, sqlite3.Error, ValueError) as exc:
        if conexion.in_transaction:
            conexion.execute('ROLLBACK')
        raise MigracionAutenticacionError('No se pudo migrar la agenda SQLite.') from exc
    finally:
        conexion.close()
