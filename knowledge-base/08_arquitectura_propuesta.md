# Arquitectura propuesta

## Estado y objetivo

Arquitectura de C-01 aplicada al autorizar continuar: Python 3.12+, SQLite local y biblioteca estándar, sin framework, servidor, ORM ni capas adicionales. Ver [diseño](../openspec/changes/crear-turno-sin-solapamientos/design.md) y [evidencia](../docs/evidencia/implementacion-turnos.md).

## Responsabilidades y directorios

| Archivo | Responsabilidad |
| --- | --- |
| [agenda.py](../odontologia/agenda.py) | Tipos, bootstrap, validación, transacción y alta |
| [__init__.py](../odontologia/__init__.py) | Exportaciones de API de módulo |
| [demo.py](../odontologia/demo.py) | Demo temporal sin red |
| [test_agenda.py](../tests/test_agenda.py) | Validación, persistencia, conflictos, bordes, rollback y bloqueo |
| [test_concurrencia.py](../tests/test_concurrencia.py) | Procesos spawn independientes |
| [test_demo.py](../tests/test_demo.py) | CLI, repetición y limpieza |

## Seguridad y datos

IDs ficticios; sin datos clínicos, secretos, login/RBAC ni promesa de producción. El alta no crea archivos ausentes. Inicialización exclusiva de archivo nuevo, sin reemplazo de contenido existente. Ninguna integración externa.

## Persistencia, concurrencia y errores

Validar forma, fechas y timeout antes de abrir. Abrir archivo existente rw, activar/comprobar FK, BEGIN IMMEDIATE, validar referencias, consultar profesional y box, insertar, COMMIT y retornar. Conexión propia por operación. Revertir lo pendiente y cerrar sin reemplazar el error original.

Un escritor por archivo serializa control y registro. BUSY/LOCKED produce agenda_ocupada; otros fallos almacenamiento_error. Sin reintentos automáticos ni reconciliación de IO catastrófico/exactamente-una-vez. Garantía sólo mismo archivo local y escritores vía módulo; no varios equipos, red compartida, archivos distintos o SQL directo externo.

## Variables de entorno

Ninguna de producto. Ruta como argumento, timeout numérico 5s por defecto. Demo maneja su temporal. Sin Docker, hosting, servidor de DB ni pip install.

## Validación ejecutada

53 tests unittest, incluidos 10 tests HTTP con TestClient sin red externa. Tres carreras por profesional y tres por box, más recursos diferentes; se verifican PIDs, resultados, exitcodes y filas. Contención mantenida, rollback por trigger SQLite real, recuperación y demo con temporales propios. No se asume N: local: DB en TEMP del sistema.

Comprobaciones que ya pasaban al añadirse están registradas sin fabricar RED. Archive y evidencias humanas de entrega pendientes.
