"""Bootstrap local interactivo del primer Administrador; sin credenciales CLI."""
import getpass
import sys

from odontologia.auth.almacenamiento import (
    crear_engine_autenticacion,
    validar_esquema_autenticacion,
    validar_ruta_sqlite_existente,
)
from odontologia.auth.tokens import validar_secreto_jwt
from odontologia.auth.usuarios import ErrorUsuarios, crear_primer_administrador
from odontologia.core.config import cargar_configuracion


def main() -> int:
    if len(sys.argv) != 1:
        print('Este comando no acepta argumentos.')
        return 2

    engine = None
    try:
        config = cargar_configuracion()
        validar_secreto_jwt(config.jwt_secreto, config.jwt_algoritmo)
        engine = crear_engine_autenticacion(
            config.persistencia, config.database_url, config.odontologia_db)
        if config.persistencia == 'sqlite':
            validar_ruta_sqlite_existente(config.odontologia_db)
        validar_esquema_autenticacion(
            engine, config.persistencia, config.odontologia_db)
        identificador = input('Identificador del administrador: ')
        password = getpass.getpass('Contraseña del administrador: ')
        confirmacion = getpass.getpass('Repetir contraseña: ')
        if password != confirmacion:
            print('Bootstrap no completado: las contraseñas no coinciden.')
            return 1
        crear_primer_administrador(engine, identificador, password)
        print('Administrador creado.')
        return 0
    except (ValueError, RuntimeError, ErrorUsuarios):
        print('Bootstrap no completado: verifique configuración, esquema y credenciales.')
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
