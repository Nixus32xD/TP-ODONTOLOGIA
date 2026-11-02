"""Errores CLI estables del subsistema de backup."""


class ErrorBackup(Exception):
    """Rechazo de backup/restauración sin detalles del motor o credenciales."""

    def __init__(self, codigo: str):
        self.codigo = codigo
        mensajes = {
            'origen_invalido': 'La agenda de origen no existe o no es válida.',
            'destino_existente': 'El destino ya existe y no fue sobrescrito.',
            'configuracion_invalida': 'La configuración de backup no es válida.',
            'operacion_fallida': 'No se pudo completar el backup.',
            'origen_ausente': 'La base de origen no existe.',
            'esquema_incompatible': 'La revisión de esquema del origen no está soportada.',
            'integridad_invalida': 'La base no superó la comprobación de integridad.',
            'referencias_invalidas': 'La base contiene referencias inválidas.',
            'bundle_invalido': 'El bundle generado no superó la validación.',
            'herramienta_ausente': 'Falta pg_dump o pg_restore en PATH.',
            'herramienta_invalida': 'No se pudo verificar la versión de los clientes PostgreSQL.',
            'version_incompatible': 'Las versiones de pg_dump/pg_restore no coinciden con el servidor.',
            'servidor_no_disponible': 'No se pudo consultar la versión del servidor PostgreSQL.',
            'agenda_activa': 'El destino coincide con la agenda activa y no fue modificado.',
            'ruta_invalida': 'La ruta de destino no es válida.',
            'recuentos_incompatibles': 'Los recuentos del bundle no coinciden con sus tablas.',
            'permiso_insuficiente': 'El usuario PostgreSQL no puede crear la base temporal requerida.',
            'limpieza_incompleta': 'No se pudo limpiar la base temporal creada por la restauración.',
        }
        super().__init__(mensajes[codigo])
