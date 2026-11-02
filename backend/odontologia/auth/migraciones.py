"""Migraciones explícitas del esquema de autenticación para SQLite."""
from pathlib import Path
import sqlite3


VERSION_ESQUEMA_AUTENTICACION = 3


def _migrar_auditoria(conexion: sqlite3.Connection) -> None:
    conexion.execute('''
        CREATE TABLE eventos_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT CHECK (id > 0),
            created_at TEXT NOT NULL,
            actor_id TEXT REFERENCES usuarios(id) ON DELETE RESTRICT,
            action TEXT NOT NULL CHECK (action IN (
                'turno.creado', 'paciente.creado', 'paciente.actualizado',
                'paciente.desactivado', 'paciente.reactivado',
                'cuenta.bootstrap', 'cuenta.creada',
                'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada',
                'sesion.rechazada')),
            resource_type TEXT NOT NULL CHECK (resource_type IN ('turno', 'paciente', 'cuenta', 'sesion')),
            resource_id TEXT,
            result TEXT NOT NULL CHECK (result IN ('confirmado', 'rechazado')),
            CHECK (
                (action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR
                (action = 'paciente.creado' AND resource_type = 'paciente' AND result = 'confirmado') OR
                (action = 'paciente.actualizado' AND resource_type = 'paciente' AND result = 'confirmado') OR
                (action = 'paciente.desactivado' AND resource_type = 'paciente' AND result = 'confirmado') OR
                (action = 'paciente.reactivado' AND resource_type = 'paciente' AND result = 'confirmado') OR
                (action = 'cuenta.bootstrap' AND resource_type = 'cuenta' AND result = 'confirmado') OR
                (action = 'cuenta.creada' AND resource_type = 'cuenta' AND result = 'confirmado') OR
                (action = 'cuenta.actualizada' AND resource_type = 'cuenta' AND result = 'confirmado') OR
                (action = 'sesion.iniciada' AND resource_type = 'sesion' AND result = 'confirmado') OR
                (action = 'sesion.cerrada' AND resource_type = 'sesion' AND result = 'confirmado') OR
                (action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado')
            ),
            CHECK (resource_type != 'sesion' OR resource_id IS NULL),
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


def _migrar_fichas_pacientes(conexion: sqlite3.Connection) -> None:
    columnas = {fila[1] for fila in conexion.execute('PRAGMA table_info(pacientes)')}
    if columnas == {'id'}:
        conexion.execute("ALTER TABLE pacientes ADD COLUMN nombre TEXT NOT NULL DEFAULT ''")
        conexion.execute('ALTER TABLE pacientes ADD COLUMN telefono TEXT')
        conexion.execute(
            'ALTER TABLE pacientes ADD COLUMN activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))')
        conexion.execute(
            "UPDATE pacientes SET nombre='Paciente de demostración ' || id WHERE nombre='' ")
    elif columnas != {'id', 'nombre', 'telefono', 'activo'}:
        raise MigracionAutenticacionError('El esquema de pacientes no es compatible.')
    conexion.execute('''CREATE TRIGGER IF NOT EXISTS pacientes_validar_insert
        BEFORE INSERT ON pacientes BEGIN
        SELECT CASE WHEN length(NEW.nombre) NOT BETWEEN 1 AND 120
            THEN RAISE(ABORT, 'nombre de paciente inválido') END;
        SELECT CASE WHEN NEW.telefono IS NOT NULL AND length(NEW.telefono) > 32
            THEN RAISE(ABORT, 'teléfono de paciente inválido') END;
        END''')
    conexion.execute('''CREATE TRIGGER IF NOT EXISTS pacientes_validar_update
        BEFORE UPDATE OF nombre, telefono ON pacientes BEGIN
        SELECT CASE WHEN length(NEW.nombre) NOT BETWEEN 1 AND 120
            THEN RAISE(ABORT, 'nombre de paciente inválido') END;
        SELECT CASE WHEN NEW.telefono IS NOT NULL AND length(NEW.telefono) > 32
            THEN RAISE(ABORT, 'teléfono de paciente inválido') END;
        END''')


def _actualizar_auditoria_pacientes(conexion: sqlite3.Connection) -> None:
    triggers = {'eventos_auditoria_no_update', 'eventos_auditoria_no_delete'}
    existentes = {fila[0] for fila in conexion.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'")}
    for trigger in triggers & existentes:
        conexion.execute(f'DROP TRIGGER {trigger}')
    conexion.execute('DROP INDEX IF EXISTS ix_eventos_auditoria_fecha_id')
    conexion.execute('ALTER TABLE eventos_auditoria RENAME TO eventos_auditoria_v2')
    _migrar_auditoria(conexion)
    conexion.execute('''
        INSERT INTO eventos_auditoria
            (id, created_at, actor_id, action, resource_type, resource_id, result)
        SELECT id, created_at, actor_id, action, resource_type, resource_id, result
        FROM eventos_auditoria_v2
    ''')
    conexion.execute('DROP TABLE eventos_auditoria_v2')


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
                tablas.add('eventos_auditoria')
                version = (2,)
            if version not in ((2,), (VERSION_ESQUEMA_AUTENTICACION,)):
                raise MigracionAutenticacionError('La versión de autenticación no es compatible.')
            if not {'usuarios', 'sesiones', 'eventos_auditoria'} <= tablas:
                raise MigracionAutenticacionError('El esquema de autenticación está incompleto.')
            _migrar_fichas_pacientes(conexion)
            if version == (2,):
                _actualizar_auditoria_pacientes(conexion)
                conexion.execute('UPDATE auth_schema_version SET version=3')
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
        _migrar_fichas_pacientes(conexion)
        conexion.execute('UPDATE auth_schema_version SET version=3')
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
