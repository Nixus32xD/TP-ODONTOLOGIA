"""Lectura y migración explícita de agendas C-01 SQLite."""

from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from sqlalchemy import Engine, func, insert, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.db.models import AgendaMutex, Box, Paciente, Prestacion, Profesional, Turno
from odontologia.db.postgresql import REVISION_ESQUEMA_ACTUAL, codigo_error_postgresql


class ErrorMigracion(Exception):
    """Error público, estable y sin detalles sensibles del motor o la ruta."""

    def __init__(self, codigo: str):
        self.codigo = codigo
        mensajes = {
            'fuente_invalida': 'La agenda SQLite de origen no es válida para C-01.',
            'conflicto_profesional': 'La agenda SQLite contiene turnos solapados por profesional.',
            'conflicto_box': 'La agenda SQLite contiene turnos solapados por box.',
            'destino_no_vacio': 'El destino PostgreSQL ya contiene datos de agenda.',
            'destino_no_preparado': 'El destino PostgreSQL no tiene el esquema vigente.',
            'destino_error': 'No se pudo completar la migración en PostgreSQL.',
            'configuracion_invalida': 'La migración requiere seleccionar PostgreSQL y configurar DATABASE_URL.',
        }
        super().__init__(mensajes[codigo])


@dataclass(frozen=True)
class TurnoSQLite:
    id: int
    paciente_id: str
    profesional_id: str
    box_id: str
    inicio_minuto: int
    fin_minuto: int


@dataclass(frozen=True)
class AgendaSQLite:
    pacientes: tuple[str, ...]
    profesionales: tuple[str, ...]
    boxes: tuple[str, ...]
    turnos: tuple[TurnoSQLite, ...]


@dataclass(frozen=True)
class ResumenMigracion:
    pacientes: int
    profesionales: int
    boxes: int
    turnos: int


_COLUMNAS = {
    'pacientes': {'id': ('TEXT', 0)},
    'profesionales': {'id': ('TEXT', 0)},
    'boxes': {'id': ('TEXT', 0)},
    'turnos': {
        'id': ('INTEGER', 0),
        'paciente_id': ('TEXT', 1),
        'profesional_id': ('TEXT', 1),
        'box_id': ('TEXT', 1),
        'inicio_minuto': ('INTEGER', 1),
        'fin_minuto': ('INTEGER', 1),
    },
}
_REFERENCIAS = {
    ('paciente_id', 'pacientes', 'id'),
    ('profesional_id', 'profesionales', 'id'),
    ('box_id', 'boxes', 'id'),
}


def _validar_esquema(conexion: sqlite3.Connection) -> None:
    tablas = {fila[0] for fila in conexion.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    if tablas != set(_COLUMNAS) or conexion.execute('PRAGMA user_version').fetchone() != (0,):
        raise ErrorMigracion('fuente_invalida')

    for tabla, esperadas in _COLUMNAS.items():
        columnas = {
            nombre: (tipo.upper(), not_null, pk)
            for _, nombre, tipo, not_null, _, pk in conexion.execute(f'PRAGMA table_info({tabla})')
        }
        if set(columnas) != set(esperadas):
            raise ErrorMigracion('fuente_invalida')
        for nombre, (tipo, not_null) in esperadas.items():
            tipo_real, requerido, _ = columnas[nombre]
            if tipo_real != tipo or requerido != not_null:
                raise ErrorMigracion('fuente_invalida')
        if tabla != 'turnos' and columnas['id'][2] != 1:
            raise ErrorMigracion('fuente_invalida')
        if tabla == 'turnos' and columnas['id'][2] != 1:
            raise ErrorMigracion('fuente_invalida')

    referencias = {
        (fila[3], fila[2], fila[4])
        for fila in conexion.execute('PRAGMA foreign_key_list(turnos)')
    }
    if referencias != _REFERENCIAS:
        raise ErrorMigracion('fuente_invalida')

    sql_turnos = conexion.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='turnos'").fetchone()
    sql_normalizado = re.sub(r'\s+', ' ', sql_turnos[0].lower()) if sql_turnos else ''
    if 'check (inicio_minuto < fin_minuto)' not in sql_normalizado:
        raise ErrorMigracion('fuente_invalida')

    indices = {fila[1] for fila in conexion.execute('PRAGMA index_list(turnos)')}
    if not {'turnos_profesional', 'turnos_box'} <= indices:
        raise ErrorMigracion('fuente_invalida')
    columnas_indices = {
        nombre: tuple(fila[2] for fila in conexion.execute(f'PRAGMA index_info({nombre})'))
        for nombre in ('turnos_profesional', 'turnos_box')
    }
    if (columnas_indices['turnos_profesional'] != ('profesional_id', 'inicio_minuto')
            or columnas_indices['turnos_box'] != ('box_id', 'inicio_minuto')):
        raise ErrorMigracion('fuente_invalida')


def _hay_solapamiento(turnos: tuple[TurnoSQLite, ...], campo_recurso: str) -> bool:
    por_recurso: dict[str, list[tuple[int, int]]] = {}
    for turno in turnos:
        recurso = getattr(turno, campo_recurso)
        por_recurso.setdefault(recurso, []).append((turno.inicio_minuto, turno.fin_minuto))

    for intervalos in por_recurso.values():
        fin_maximo = None
        for inicio, fin in sorted(intervalos):
            if fin_maximo is not None and inicio < fin_maximo:
                return True
            fin_maximo = fin if fin_maximo is None else max(fin_maximo, fin)
    return False


def leer_agenda_sqlite(ruta: str | Path) -> AgendaSQLite:
    """Validar una agenda C-01 y leerla en modo sólo lectura."""
    conexion = None
    try:
        uri = Path(ruta).resolve().as_uri() + '?mode=ro'
        conexion = sqlite3.connect(uri, uri=True)
        conexion.execute('PRAGMA query_only=ON')
        conexion.execute('PRAGMA foreign_keys=ON')
        conexion.execute('BEGIN')
        if conexion.execute('PRAGMA integrity_check').fetchone() != ('ok',):
            raise ErrorMigracion('fuente_invalida')
        if conexion.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ErrorMigracion('fuente_invalida')
        _validar_esquema(conexion)

        catalogos = {}
        for tabla in ('pacientes', 'profesionales', 'boxes'):
            ids = tuple(fila[0] for fila in conexion.execute(f'SELECT id FROM {tabla} ORDER BY id'))
            if any(not isinstance(item, str) or not item or len(item) > 64
                   or item.strip() != item for item in ids):
                raise ErrorMigracion('fuente_invalida')
            catalogos[tabla] = ids

        filas = conexion.execute(
            'SELECT id, paciente_id, profesional_id, box_id, inicio_minuto, fin_minuto '
            'FROM turnos ORDER BY id').fetchall()
        turnos = []
        for fila in filas:
            if (type(fila[0]) is not int or fila[0] <= 0
                    or type(fila[4]) is not int or type(fila[5]) is not int
                    or fila[4] >= fila[5]
                    or fila[1] not in catalogos['pacientes']
                    or fila[2] not in catalogos['profesionales']
                    or fila[3] not in catalogos['boxes']):
                raise ErrorMigracion('fuente_invalida')
            turnos.append(TurnoSQLite(*fila))

        turnos_validos = tuple(turnos)
        if _hay_solapamiento(turnos_validos, 'profesional_id'):
            raise ErrorMigracion('conflicto_profesional')
        if _hay_solapamiento(turnos_validos, 'box_id'):
            raise ErrorMigracion('conflicto_box')

        return AgendaSQLite(
            catalogos['pacientes'], catalogos['profesionales'], catalogos['boxes'], turnos_validos)
    except ErrorMigracion:
        raise
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise ErrorMigracion('fuente_invalida') from exc
    finally:
        if conexion is not None:
            conexion.close()


def migrar_agenda_sqlite(engine: Engine, ruta: str | Path) -> ResumenMigracion:
    """Importar una fuente validada a una agenda PostgreSQL vigente y vacía."""
    agenda = leer_agenda_sqlite(ruta)
    try:
        with Session(engine) as session, session.begin():
            revision = session.execute(text('SELECT version_num FROM alembic_version')).scalar_one_or_none()
            mutex = session.scalar(select(AgendaMutex.id).where(AgendaMutex.id == 1).with_for_update())
            if revision != REVISION_ESQUEMA_ACTUAL or mutex != 1:
                raise ErrorMigracion('destino_no_preparado')

            if any(session.scalar(select(func.count()).select_from(modelo))
                   for modelo in (Paciente, Profesional, Box, Prestacion, Turno)):
                raise ErrorMigracion('destino_no_vacio')

            if agenda.pacientes:
                session.execute(insert(Paciente), [
                    {
                        'id': item,
                        'nombre': f'Paciente de demostración {item}',
                        'telefono': None,
                        'activo': True,
                    }
                    for item in agenda.pacientes
                ])
            if agenda.profesionales:
                session.execute(insert(Profesional), [{
                    'id': item, 'nombre': f'Profesional de demostración {item}', 'activo': True,
                } for item in agenda.profesionales])
            if agenda.boxes:
                session.execute(insert(Box), [{
                    'id': item, 'nombre': f'Box de demostración {item}', 'activo': True,
                } for item in agenda.boxes])
            if agenda.turnos:
                session.execute(insert(Turno), [
                    {
                        'id': item.id,
                        'paciente_id': item.paciente_id,
                        'profesional_id': item.profesional_id,
                        'box_id': item.box_id,
                        'inicio_minuto': item.inicio_minuto,
                        'fin_minuto': item.fin_minuto,
                    }
                    for item in agenda.turnos
                ])
            session.execute(text(
                "SELECT setval(pg_get_serial_sequence('turnos', 'id'), "
                "COALESCE(MAX(id), 1), COUNT(*) > 0) FROM turnos"))
    except ErrorMigracion:
        raise
    except SQLAlchemyError as exc:
        raise ErrorMigracion('destino_error') from exc

    return ResumenMigracion(
        len(agenda.pacientes), len(agenda.profesionales), len(agenda.boxes), len(agenda.turnos))
