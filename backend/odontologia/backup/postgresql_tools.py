"""Detección segura de clientes PostgreSQL requeridos por los adapters."""

import re
import shutil
import subprocess


class ErrorHerramientasPostgresql(Exception):
    """Error estable sin URL, credenciales ni salida cruda del proceso."""

    def __init__(self, codigo: str):
        self.codigo = codigo
        mensajes = {
            'herramienta_ausente': 'Falta pg_dump o pg_restore en PATH.',
            'herramienta_invalida': 'No se pudo verificar la versión de los clientes PostgreSQL.',
            'version_incompatible': 'Las versiones de pg_dump/pg_restore no coinciden con el servidor.',
            'servidor_no_disponible': 'No se pudo consultar la versión del servidor PostgreSQL.',
        }
        super().__init__(mensajes[codigo])


_VERSION = re.compile(r'PostgreSQL\)\s+(\d+)(?:\.|\s|$)')


def detectar_herramientas_postgresql(server_version_num: int) -> dict[str, object]:
    """Detectar ambos clientes y exigir que su major coincida con el servidor."""
    server_version_num = _normalizar_server_version(server_version_num)
    rutas = {}
    for nombre in ('pg_dump', 'pg_restore'):
        ruta = shutil.which(nombre)
        if not ruta:
            raise ErrorHerramientasPostgresql('herramienta_ausente')
        rutas[nombre] = ruta

    try:
        versiones = {}
        for nombre, ruta in rutas.items():
            resultado = subprocess.run(
                [ruta, '--version'], check=False, capture_output=True, text=True,
                timeout=5, shell=False,
            )
            if resultado.returncode != 0:
                raise ErrorHerramientasPostgresql('herramienta_invalida')
            coincidencia = _VERSION.search(resultado.stdout or '')
            if coincidencia is None:
                raise ErrorHerramientasPostgresql('herramienta_invalida')
            versiones[nombre] = int(coincidencia.group(1))
    except ErrorHerramientasPostgresql:
        raise
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError) as exc:
        raise ErrorHerramientasPostgresql('herramienta_invalida') from exc

    major_servidor = server_version_num // 10000
    validar_major_postgresql(
        server_version_num, versiones['pg_dump'], versiones['pg_restore'])
    if versiones['pg_dump'] != major_servidor:
        raise ErrorHerramientasPostgresql('version_incompatible')
    return {
        'pg_dump': rutas['pg_dump'],
        'pg_restore': rutas['pg_restore'],
        'server_major': major_servidor,
        'pg_dump_major': versiones['pg_dump'],
        'pg_restore_major': versiones['pg_restore'],
    }


def validar_major_postgresql(server_version_num: int, dump_major: int,
                             restore_major: int) -> int:
    """Validar tipos y majors sin ejecutar procesos ni aceptar entradas tipo shell."""
    server_version_num = _normalizar_server_version(server_version_num)
    if (type(dump_major) is not int or dump_major < 10
            or type(restore_major) is not int or restore_major < 10):
        raise ErrorHerramientasPostgresql('version_incompatible')
    major_servidor = server_version_num // 10000
    if dump_major != major_servidor or restore_major != major_servidor:
        raise ErrorHerramientasPostgresql('version_incompatible')
    return major_servidor


def _normalizar_server_version(valor) -> int:
    if type(valor) is str and valor.isascii() and valor.isdecimal():
        valor = int(valor)
    if type(valor) is not int or valor < 100000:
        raise ErrorHerramientasPostgresql('version_incompatible')
    return valor


def validar_runtime_postgresql(engine) -> dict[str, object]:
    """Consultar el servidor y validar clientes antes de crear cualquier salida."""
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    try:
        with engine.connect() as conexion:
            version = conexion.execute(text('SHOW server_version_num')).scalar_one()
    except SQLAlchemyError as exc:
        raise ErrorHerramientasPostgresql('servidor_no_disponible') from exc
    return detectar_herramientas_postgresql(version)
