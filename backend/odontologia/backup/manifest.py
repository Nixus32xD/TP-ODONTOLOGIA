"""Formato y verificación estricta del manifiesto de un backup."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from odontologia.backup.permisos import crear_archivo_exclusivo
from odontologia.version import __version__


VERSION_FORMATO = 1
ESQUEMAS_SOPORTADOS = {
    'sqlite': '8',
    'postgresql': '20261102_0009_turn_rescheduling',
}
TABLAS_ESQUEMA_ACTUAL = {
    'sqlite': {
        'auth_schema_version', 'bloqueos_agenda', 'boxes', 'eventos_auditoria',
        'excepciones_horario', 'horarios_semanales', 'pacientes', 'prestaciones',
        'profesionales', 'sesiones', 'tramos_excepcion', 'turnos', 'usuarios',
    },
    'postgresql': {
        'agenda_mutex', 'alembic_version', 'bloqueos_agenda', 'boxes',
        'eventos_auditoria', 'excepciones_horario', 'horarios_semanales',
        'pacientes', 'prestaciones', 'profesionales', 'sesiones',
        'tramos_excepcion', 'turnos', 'usuarios',
    },
}
_CAMPOS = {
    'format_version', 'created_at_utc', 'backend', 'application_version',
    'schema_version', 'payload_name', 'payload_size_bytes', 'payload_sha256',
    'table_counts',
}
_MENSAJES = {
    'payload_invalido': 'El archivo de datos del backup no es válido.',
    'manifiesto_invalido': 'El manifiesto del backup no es válido o no es compatible.',
    'manifiesto_existente': 'El manifiesto ya existe y no fue sobrescrito.',
}


class ErrorManifiesto(Exception):
    """Error público estable de formato, versión o integridad del manifiesto."""

    def __init__(self, codigo: str):
        self.codigo = codigo
        super().__init__(_MENSAJES[codigo])


def _sha256(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b''):
            digest.update(bloque)
    return digest.hexdigest()


def crear_manifiesto(payload: str | Path, *, backend: str, schema_version: str,
                     table_counts: dict[str, int] | None = None,
                     created_at: datetime | None = None) -> dict[str, object]:
    ruta = Path(payload)
    if (backend not in ESQUEMAS_SOPORTADOS
            or schema_version != ESQUEMAS_SOPORTADOS.get(backend)
            or not ruta.is_file()
            or not _recuentos_validos(backend, table_counts)):
        raise ErrorManifiesto('payload_invalido')

    fecha = created_at or datetime.now(timezone.utc)
    if not isinstance(fecha, datetime) or fecha.utcoffset() is None:
        raise ErrorManifiesto('manifiesto_invalido')
    fecha_utc = fecha.astimezone(timezone.utc)
    return {
        'format_version': VERSION_FORMATO,
        'created_at_utc': fecha_utc.isoformat(timespec='seconds'),
        'backend': backend,
        'application_version': __version__,
        'schema_version': schema_version,
        'payload_name': ruta.name,
        'payload_size_bytes': ruta.stat().st_size,
        'payload_sha256': _sha256(ruta),
        'table_counts': dict(sorted(table_counts.items())),
    }


def guardar_manifiesto(manifiesto: dict[str, object], destino: str | Path) -> None:
    ruta = Path(destino)
    try:
        descriptor = crear_archivo_exclusivo(ruta)
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as archivo:
            json.dump(manifiesto, archivo, ensure_ascii=False, sort_keys=True, indent=2)
            archivo.write('\n')
            archivo.flush()
            os.fsync(archivo.fileno())
    except FileExistsError as exc:
        raise ErrorManifiesto('manifiesto_existente') from exc
    except (OSError, TypeError, ValueError) as exc:
        raise ErrorManifiesto('manifiesto_invalido') from exc


def leer_manifiesto(manifiesto: str | Path, payload: str | Path | None = None) -> dict[str, object]:
    ruta_manifiesto = Path(manifiesto)
    try:
        datos = json.loads(ruta_manifiesto.read_text(encoding='utf-8'))
        if (not isinstance(datos, dict) or set(datos) != _CAMPOS
                or type(datos['format_version']) is not int
                or datos['format_version'] != VERSION_FORMATO
                or datos['backend'] not in ESQUEMAS_SOPORTADOS
                or datos['schema_version'] != ESQUEMAS_SOPORTADOS[datos['backend']]
                or datos['application_version'] != __version__
                or not _recuentos_validos(datos['backend'], datos['table_counts'])
                or not isinstance(datos['payload_name'], str)
                or not datos['payload_name']
                or Path(datos['payload_name']).name != datos['payload_name']
                or type(datos['payload_size_bytes']) is not int
                or datos['payload_size_bytes'] < 0
                or not isinstance(datos['payload_sha256'], str)
                or len(datos['payload_sha256']) != 64
                or any(c not in '0123456789abcdef' for c in datos['payload_sha256'])):
            raise ErrorManifiesto('manifiesto_invalido')

        fecha = datetime.fromisoformat(datos['created_at_utc'])
        if fecha.utcoffset() is None or fecha.utcoffset().total_seconds() != 0:
            raise ErrorManifiesto('manifiesto_invalido')

        ruta_payload = Path(payload) if payload is not None else ruta_manifiesto.parent / datos['payload_name']
        if ruta_payload.name != datos['payload_name'] or not ruta_payload.is_file():
            raise ErrorManifiesto('manifiesto_invalido')
        if ruta_payload.stat().st_size != datos['payload_size_bytes']:
            raise ErrorManifiesto('manifiesto_invalido')
        if _sha256(ruta_payload) != datos['payload_sha256']:
            raise ErrorManifiesto('manifiesto_invalido')
        return datos
    except ErrorManifiesto:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ErrorManifiesto('manifiesto_invalido') from exc


def _recuentos_validos(backend: str, table_counts) -> bool:
    if backend not in TABLAS_ESQUEMA_ACTUAL or not isinstance(table_counts, dict):
        return False
    if set(table_counts) != TABLAS_ESQUEMA_ACTUAL[backend]:
        return False
    return all(type(cantidad) is int and cantidad >= 0
               for cantidad in table_counts.values())
