"""Dominio de turnos ficticios, independiente del adaptador HTTP y proveedores."""

from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
import sqlite3
import math


class ErrorAgenda(Exception):
    """Error público estable, independiente de los detalles de SQLite."""

    def __init__(self, codigo: str, campo: str | None = None):
        self.codigo = codigo
        self.campo = campo
        mensajes = {
            'entrada_invalida': 'La entrada no cumple el contrato.',
            'recurso_desconocido': 'El recurso no está registrado en la agenda ficticia.',
            'conflicto_profesional': 'El profesional ya está ocupado en ese intervalo.',
            'conflicto_box': 'El box ya está ocupado en ese intervalo.',
            'agenda_ocupada': 'La agenda está ocupada por otro escritor.',
            'almacenamiento_error': 'No se pudo completar la operación de almacenamiento.',
            'agenda_existente': 'La agenda ya existe y no se sobrescribió.',
        }
        mensaje = mensajes[codigo]
        super().__init__(f'{mensaje} Campo: {campo}.' if campo else mensaje)


@dataclass(frozen=True)
class Turno:
    id: int
    paciente_id: str
    profesional_id: str
    box_id: str
    inicio: datetime
    fin: datetime


def _minutos(fecha: datetime) -> int:
    delta = fecha - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return delta.days * 1440 + delta.seconds // 60


def _fecha_utc(fecha: datetime, campo: str) -> datetime:
    if not isinstance(fecha, datetime):
        raise ErrorAgenda('entrada_invalida', campo)
    try:
        if fecha.utcoffset() is None or fecha.second or fecha.microsecond:
            raise ErrorAgenda('entrada_invalida', campo)
        normalizada = fecha.astimezone(timezone.utc)
        if normalizada.second or normalizada.microsecond:
            raise ErrorAgenda('entrada_invalida', campo)
        return normalizada
    except (TypeError, ValueError, OverflowError) as exc:
        raise ErrorAgenda('entrada_invalida', campo) from exc


def _cerrar(conexion: sqlite3.Connection | None) -> None:
    """Revertir lo pendiente y cerrar sin reemplazar un error primario."""
    if conexion is None:
        return
    try:
        if conexion.in_transaction:
            conexion.execute('ROLLBACK')
    except sqlite3.Error:
        pass  # La operación original ya rechazó el alta; cerrar igualmente.
    finally:
        try:
            conexion.close()
        except sqlite3.Error:
            pass  # No ocultar la causa original con un fallo de limpieza.


def inicializar_agenda(ruta_db: str | Path) -> None:
    """Crear sólo un archivo nuevo con catálogos exclusivamente ficticios."""
    conexion = None
    try:
        ruta = Path(ruta_db)
        with ruta.open('xb'):
            pass
        conexion = sqlite3.connect(ruta, autocommit=True)
        conexion.execute('PRAGMA foreign_keys=ON')
        conexion.executescript('''
            BEGIN IMMEDIATE;
            CREATE TABLE pacientes (id TEXT PRIMARY KEY);
            CREATE TABLE profesionales (id TEXT PRIMARY KEY);
            CREATE TABLE boxes (id TEXT PRIMARY KEY);
            CREATE TABLE turnos (
                id INTEGER PRIMARY KEY,
                paciente_id TEXT NOT NULL REFERENCES pacientes(id),
                profesional_id TEXT NOT NULL REFERENCES profesionales(id),
                box_id TEXT NOT NULL REFERENCES boxes(id),
                inicio_minuto INTEGER NOT NULL,
                fin_minuto INTEGER NOT NULL,
                CHECK (inicio_minuto < fin_minuto)
            );
            CREATE INDEX turnos_profesional ON turnos(profesional_id, inicio_minuto);
            CREATE INDEX turnos_box ON turnos(box_id, inicio_minuto);
            INSERT INTO pacientes VALUES ('paciente-A'), ('paciente-B');
            INSERT INTO profesionales VALUES ('profesional-A'), ('profesional-B');
            INSERT INTO boxes VALUES ('box-A'), ('box-B');
            COMMIT;
        ''')
    except FileExistsError as exc:
        raise ErrorAgenda('agenda_existente') from exc
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise ErrorAgenda('almacenamiento_error') from exc
    finally:
        _cerrar(conexion)


def crear_turno(ruta_db: str | Path, *, paciente_id: str, profesional_id: str,
                box_id: str, inicio: datetime, fin: datetime,
                timeout_segundos: float = 5.0) -> Turno:
    """Registrar una ocupación ficticia en una agenda local existente."""
    recursos = [('paciente', paciente_id, 'pacientes'),
                ('profesional', profesional_id, 'profesionales'), ('box', box_id, 'boxes')]
    for campo, identificador, _ in recursos:
        if (not isinstance(identificador, str) or not identificador
                or len(identificador) > 64 or identificador.strip() != identificador):
            raise ErrorAgenda('entrada_invalida', campo)
    inicio_utc = _fecha_utc(inicio, 'inicio')
    fin_utc = _fecha_utc(fin, 'fin')
    if inicio_utc >= fin_utc:
        raise ErrorAgenda('entrada_invalida', 'intervalo')
    try:
        valido = (type(timeout_segundos) in (int, float)
                  and math.isfinite(timeout_segundos) and timeout_segundos > 0)
    except OverflowError:
        valido = False
    if not valido:
        raise ErrorAgenda('entrada_invalida', 'timeout')
    inicio_minuto, fin_minuto = _minutos(inicio_utc), _minutos(fin_utc)
    conexion = None
    try:
        conexion = sqlite3.connect(Path(ruta_db).resolve().as_uri() + '?mode=rw',
                                   uri=True, autocommit=True, timeout=timeout_segundos)
        conexion.execute('PRAGMA foreign_keys=ON')
        if conexion.execute('PRAGMA foreign_keys').fetchone() != (1,):
            raise ErrorAgenda('almacenamiento_error')
        conexion.execute('BEGIN IMMEDIATE')
        for campo, identificador, tabla in recursos:
            if conexion.execute(f'SELECT 1 FROM {tabla} WHERE id=?', (identificador,)).fetchone() is None:
                raise ErrorAgenda('recurso_desconocido', campo)
        for campo, identificador in [('profesional', profesional_id), ('box', box_id)]:
            if conexion.execute(
                    f'SELECT 1 FROM turnos WHERE {campo}_id=? '
                    'AND inicio_minuto < ? AND fin_minuto > ? LIMIT 1',
                    (identificador, fin_minuto, inicio_minuto)).fetchone() is not None:
                raise ErrorAgenda(f'conflicto_{campo}', campo)
        cursor = conexion.execute(
            'INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, fin_minuto) '
            'VALUES (?, ?, ?, ?, ?)',
            (paciente_id, profesional_id, box_id, inicio_minuto, fin_minuto))
        conexion.execute('COMMIT')
        return Turno(cursor.lastrowid, paciente_id, profesional_id, box_id, inicio_utc, fin_utc)
    except (OSError, ValueError, sqlite3.Error) as exc:
        codigo_sqlite = getattr(exc, 'sqlite_errorcode', 0) & 0xff
        codigo = 'agenda_ocupada' if codigo_sqlite in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) else 'almacenamiento_error'
        raise ErrorAgenda(codigo) from exc
    finally:
        _cerrar(conexion)
