"""Permisos owner-only para bundles cuando el sistema operativo es POSIX."""

import os
from pathlib import Path
import sys
import ctypes
import errno


MODO_DIRECTORIO_PRIVADO = 0o700
MODO_ARCHIVO_PRIVADO = 0o600


def restringir_modo_posix(ruta: str | Path, modo: int) -> None:
    """Aplicar modo POSIX sin modificar ACL heredados en Windows."""
    if os.name == 'posix':
        os.chmod(ruta, modo)


def crear_archivo_exclusivo(ruta: str | Path) -> int:
    """Crear un archivo nuevo; en POSIX nace owner-only antes de cualquier escritura."""
    modo = MODO_ARCHIVO_PRIVADO if os.name == 'posix' else 0o666
    descriptor = os.open(
        ruta,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        modo,
    )
    try:
        if os.name == 'posix':
            os.fchmod(descriptor, MODO_ARCHIVO_PRIVADO)
        return descriptor
    except OSError:
        os.close(descriptor)
        os.unlink(ruta)
        raise


def publicar_directorio_nuevo(origen: str | Path, destino: str | Path) -> None:
    """Renombrar un directorio completo de forma atómica y sin reemplazar."""
    if os.name == 'nt':
        # En Windows os.rename falla si el destino ya existe.
        os.rename(origen, destino)
        return
    if not sys.platform.startswith('linux'):
        raise OSError(errno.ENOTSUP, 'No existe primitiva no-replace disponible', os.fspath(destino))

    biblioteca = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(biblioteca, 'renameat2', None)
    if renameat2 is None:
        raise OSError(errno.ENOTSUP, 'renameat2 no está disponible', os.fspath(destino))
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                          ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    resultado = renameat2(
        -100, os.fsencode(origen), -100, os.fsencode(destino), 1)
    if resultado != 0:
        codigo = ctypes.get_errno()
        if codigo == errno.EEXIST:
            raise FileExistsError(codigo, os.strerror(codigo), os.fspath(destino))
        raise OSError(codigo, os.strerror(codigo), os.fspath(destino))
