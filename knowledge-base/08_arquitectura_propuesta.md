# Arquitectura propuesta

## Estado y objetivo

Arquitectura de C-01 aplicada al autorizar continuar: Python 3.12+, SQLite local y biblioteca estándar, sin framework, servidor, ORM ni capas adicionales. Ver [diseño](../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md) y [evidencia](../docs/evidencia/implementacion-turnos.md).

**Actualización 2026-10-29:** C-01 se expone con FastAPI (DD-08) y, por corrección de la cátedra, el repositorio adopta el stack Python/FastAPI/JWT/SQLAlchemy/PostgreSQL/Redis/Docker para el backend y React/TypeScript/Vite para el frontend (DD-09). La descripción anterior corresponde al contrato inicial de C-01.

## Responsabilidades y directorios

Desde la corrección de la cátedra (2026-10-29) el código se separa en `backend/` y `frontend/`. C-01 se movió sin cambios de contrato.

| Ruta | Responsabilidad | Change |
| --- | --- | --- |
| [backend/odontologia/agenda.py](../backend/odontologia/agenda.py) | Tipos, bootstrap, validación, transacción y alta | C-01 |
| [backend/odontologia/api.py](../backend/odontologia/api.py) | Adaptador FastAPI: POST /turnos, GET /health | C-01 |
| [backend/odontologia/__init__.py](../backend/odontologia/__init__.py) | Exportaciones de API de módulo | C-01 |
| [backend/odontologia/demo.py](../backend/odontologia/demo.py) | Demo temporal sin red | C-01 |
| [backend/odontologia/core/config.py](../backend/odontologia/core/config.py) | Lectura de variables de entorno del stack | Base |
| `backend/odontologia/db/` | SQLAlchemy + PostgreSQL (estructura) | C-02 |
| `backend/odontologia/auth/` | JWT (estructura) | C-03 |
| `backend/odontologia/workers/` | Cola de recordatorios en Redis (estructura) | C-17 |
| [backend/tests/](../backend/tests/) | 53 tests: dominio, concurrencia, demo y HTTP | C-01 |
| [frontend/](../frontend/README.md) | React + TypeScript + Vite; consume la API vía `/api` | C-11 |
| [docker-compose.yml](../docker-compose.yml) | Servicios db, redis, backend y frontend en loopback | C-02 / C-14 |

La UI no decide conflictos ni valida reglas de negocio por su cuenta: muestra lo que devuelve el backend.

## Seguridad y datos

IDs ficticios; sin datos clínicos, secretos, login/RBAC ni promesa de producción. El alta no crea archivos ausentes. Inicialización exclusiva de archivo nuevo, sin reemplazo de contenido existente. Ninguna integración externa.

## Persistencia, concurrencia y errores

Validar forma, fechas y timeout antes de abrir. Abrir archivo existente rw, activar/comprobar FK, BEGIN IMMEDIATE, validar referencias, consultar profesional y box, insertar, COMMIT y retornar. Conexión propia por operación. Revertir lo pendiente y cerrar sin reemplazar el error original.

Un escritor por archivo serializa control y registro. BUSY/LOCKED produce agenda_ocupada; otros fallos almacenamiento_error. Sin reintentos automáticos ni reconciliación de IO catastrófico/exactamente-una-vez. Garantía sólo mismo archivo local y escritores vía módulo; no varios equipos, red compartida, archivos distintos o SQL directo externo.

## Variables de entorno

C-01: `ODONTOLOGIA_DB` (ruta de la agenda SQLite); timeout numérico 5s por defecto. Stack de la cátedra, todavía sin uso en C-01: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRETO`, `JWT_ALGORITMO` y `JWT_MINUTOS_EXPIRACION`, leídas por `core/config.py`. Los valores reales van en `.env` (no versionado); `.env.example` sólo trae marcadores.

## Validación ejecutada

53 tests unittest, incluidos 10 tests HTTP con TestClient sin red externa. Tres carreras por profesional y tres por box, más recursos diferentes; se verifican PIDs, resultados, exitcodes y filas. Contención mantenida, rollback por trigger SQLite real, recuperación y demo con temporales propios. No se asume N: local: DB en TEMP del sistema.

Comprobaciones que ya pasaban al añadirse están registradas sin fabricar RED. Archive confirmado el 2026-10-28; las evidencias humanas y la aceptación académica se acreditan por separado.
