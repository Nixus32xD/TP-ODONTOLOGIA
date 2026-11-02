"""Comando local de migración explícita del esquema de autenticación SQLite."""
import sys

from odontologia.auth.migraciones import MigracionAutenticacionError, migrar_sqlite
from odontologia.core.config import cargar_configuracion


def main() -> int:
    if len(sys.argv) != 1:
        print('Este comando no acepta argumentos.')
        return 2
    try:
        config = cargar_configuracion()
        if config.persistencia != 'sqlite':
            print('Migración no aplicada: este comando requiere SQLite.')
            return 1
        migrar_sqlite(config.odontologia_db)
        print('Migración de autenticación aplicada.')
        return 0
    except (ValueError, MigracionAutenticacionError):
        print('Migración no aplicada: verifique que exista una agenda SQLite C-01 compatible.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
