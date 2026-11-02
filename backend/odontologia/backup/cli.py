"""Entrada CLI del flujo manual de backup, verificación y restauración."""

import argparse
import sys

from odontologia.backup.bundle import crear_bundle_sqlite
from odontologia.backup.errors import ErrorBackup
from odontologia.backup.postgresql import crear_bundle_postgresql
from odontologia.backup.restauracion_postgresql import restaurar_bundle_postgresql
from odontologia.backup.restauracion_sqlite import restaurar_bundle_sqlite
from odontologia.backup.verificacion import verificar_bundle
from odontologia.core.config import cargar_configuracion


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='python -m odontologia.backup',
        description='Crear, verificar y restaurar copias locales de agenda.',
    )
    acciones = parser.add_subparsers(dest='accion')

    crear = acciones.add_parser('crear', help='crear un bundle nuevo en una ruta local')
    crear.add_argument('bundle', help='directorio nuevo para el bundle')

    verificar = acciones.add_parser('verificar', help='verificar un bundle existente')
    verificar.add_argument('bundle', help='directorio local del bundle')

    restaurar = acciones.add_parser('restaurar', help='restaurar en un destino nuevo')
    restaurar.add_argument('bundle', help='directorio local del bundle')
    restaurar.add_argument('destino', help='ruta SQLite nueva o nombre de base PostgreSQL nuevo')
    return parser


def _mostrar_fallo(exc: ErrorBackup | ValueError) -> None:
    if isinstance(exc, ErrorBackup):
        print(f'{exc.codigo}: {exc}', file=sys.stderr)
        return
    print('operacion_fallida: No se pudo completar la operación.', file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = crear_parser()
    argumentos = parser.parse_args(argv)
    if argumentos.accion is None:
        parser.print_help()
        return 0
    if argumentos.accion == 'crear':
        try:
            configuracion = cargar_configuracion()
            if configuracion.persistencia == 'sqlite':
                resultado = crear_bundle_sqlite(
                    configuracion.odontologia_db, argumentos.bundle)
            else:
                from odontologia.db.postgresql import crear_engine

                engine = crear_engine(configuracion.database_url)
                try:
                    resultado = crear_bundle_postgresql(engine, argumentos.bundle)
                finally:
                    engine.dispose()
            print(f"Copia verificada creada en el destino solicitado ({resultado['backend']}).")
            print(
                'Aviso: el bundle contiene datos sensibles de pacientes, cuentas y auditoría. '
                'Guárdelo fuera del repositorio, limite el acceso y no lo comparta.'
            )
            return 0
        except (ErrorBackup, ValueError) as exc:
            _mostrar_fallo(exc)
            return 2
    if argumentos.accion == 'verificar':
        try:
            resultado = verificar_bundle(argumentos.bundle)
            print(f"Bundle verificado ({resultado['backend']}, esquema {resultado['schema_version']}).")
            return 0
        except (ErrorBackup, ValueError) as exc:
            _mostrar_fallo(exc)
            return 2
    if argumentos.accion == 'restaurar':
        try:
            configuracion = cargar_configuracion()
            bundle = verificar_bundle(argumentos.bundle)
            if bundle['backend'] == 'sqlite':
                resultado = restaurar_bundle_sqlite(
                    argumentos.bundle, argumentos.destino,
                    origen_activo=configuracion.odontologia_db,
                )
            elif configuracion.persistencia == 'postgresql':
                from odontologia.db.postgresql import crear_engine

                engine = crear_engine(configuracion.database_url)
                try:
                    resultado = restaurar_bundle_postgresql(
                        engine, argumentos.bundle, argumentos.destino)
                finally:
                    engine.dispose()
            else:
                raise ErrorBackup('configuracion_invalida')
            print(f"Restauración técnica completada en destino nuevo ({resultado['backend']}).")
            return 0
        except (ErrorBackup, ValueError) as exc:
            _mostrar_fallo(exc)
            return 2
    print('La verificación y restauración todavía no están disponibles.', file=sys.stderr)
    return 2
