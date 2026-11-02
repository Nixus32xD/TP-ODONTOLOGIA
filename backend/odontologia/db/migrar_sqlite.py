"""CLI manual: `python -m odontologia.db.migrar_sqlite`."""

import sys

from odontologia.core.config import cargar_configuracion
from odontologia.db.migracion import ErrorMigracion, migrar_agenda_sqlite
from odontologia.db.postgresql import crear_engine


def main() -> int:
    try:
        configuracion = cargar_configuracion()
        if configuracion.persistencia != 'postgresql' or not configuracion.database_url:
            raise ErrorMigracion('configuracion_invalida')
        engine = crear_engine(configuracion.database_url)
        try:
            resumen = migrar_agenda_sqlite(engine, configuracion.odontologia_db)
        finally:
            engine.dispose()
    except (ErrorMigracion, ValueError) as exc:
        print(f'Error de migración: {exc}', file=sys.stderr)
        return 2

    print(
        'Migración confirmada: '
        f'{resumen.pacientes} pacientes, {resumen.profesionales} profesionales, '
        f'{resumen.boxes} boxes, {resumen.turnos} turnos.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
