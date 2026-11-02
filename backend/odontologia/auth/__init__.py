"""Autenticación JWT de personal implementada por C-03.

Las rutas protegidas validan sesiones revocables y la matriz aprobada:
Administrador gestiona cuentas y operaciones disponibles; Recepción crea
turnos; Profesional no accede hasta que C-08 defina su agenda. Las claves se
configuran localmente y no se versionan. C-03 está validado; Archive pendiente.
"""
