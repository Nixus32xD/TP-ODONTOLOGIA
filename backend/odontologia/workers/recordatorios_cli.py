"""CLI explícita de una pasada para recordatorios locales simulados."""
import argparse
import sys


def _limite(valor: str) -> int:
    try:
        limite = int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('debe ser un entero entre 1 y 100') from exc
    if not 1 <= limite <= 100:
        raise argparse.ArgumentTypeError('debe estar entre 1 y 100')
    return limite


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='python -m odontologia.workers.recordatorios_cli',
        description='Procesar una pasada local de recordatorios simulados.',
    )
    parser.add_argument('--once', action='store_true', required=True,
                        help='ejecutar una única pasada y terminar')
    parser.add_argument('--limit', type=_limite, default=100,
                        help='máximo de filas por pasada (1–100; default: 100)')
    return parser


def main(argv: list[str] | None = None) -> int:
    argumentos = crear_parser().parse_args(argv)
    try:
        from odontologia.core.config import cargar_configuracion
        from odontologia.auth.almacenamiento import (
            crear_engine_autenticacion, validar_esquema_autenticacion,
            validar_ruta_sqlite_existente,
        )
        from odontologia.workers.recordatorios import procesar_recordatorios

        configuracion = cargar_configuracion()
        if configuracion.persistencia == 'sqlite':
            validar_ruta_sqlite_existente(configuracion.odontologia_db)
        engine = crear_engine_autenticacion(
            configuracion.persistencia, configuracion.database_url,
            configuracion.odontologia_db if configuracion.persistencia == 'sqlite' else None)
        try:
            validar_esquema_autenticacion(
                engine, configuracion.persistencia,
                configuracion.odontologia_db if configuracion.persistencia == 'sqlite' else None)
            resultado = procesar_recordatorios(engine, limite=argumentos.limit)
        finally:
            engine.dispose()
        print('Recordatorios simulados: '
              f"procesados={resultado['procesados']} "
              f"invalidados={resultado['invalidados']} fallidos={resultado['fallidos']}")
        return 0
    except Exception:
        print('ejecucion_fallida: No se pudo completar la pasada simulada.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
