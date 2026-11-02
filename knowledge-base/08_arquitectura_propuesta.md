# Arquitectura aplicada y evolución propuesta

## Estado y objetivo

Arquitectura inicial de C-01: Python 3.12+, SQLite local y módulo de dominio pequeño. Sobre esa base, C-02 añade PostgreSQL optativo y migraciones explícitas; C-03 añade JWT, sesiones revocables y autorización. Ambos cambios están validados localmente y pendientes de Archive. Ver [evidencia](../docs/evidencia/implementacion-turnos.md).

**Actualización 2026-11-01:** C-01 se expone con FastAPI; C-02/C-03 ya usan SQLAlchemy, PostgreSQL optativo y JWT. El repositorio conserva la separación de la cátedra: Python/FastAPI/JWT/SQLAlchemy/PostgreSQL/Redis/Docker para backend y React/TypeScript/Vite para frontend (DD-09). La descripción inicial corresponde al diseño original de C-01.

## Responsabilidades y directorios

Desde la corrección de la cátedra (2026-10-29) el código se separa en `backend/` y `frontend/`. C-01 se movió sin cambios de contrato.

| Ruta | Responsabilidad | Change |
| --- | --- | --- |
| [backend/odontologia/agenda.py](../backend/odontologia/agenda.py) | Tipos, bootstrap, validación, transacción y alta | C-01 |
| [backend/odontologia/api.py](../backend/odontologia/api.py) | Alta protegida, sesiones, administración y liveness | C-01 / C-03 |
| [backend/odontologia/__init__.py](../backend/odontologia/__init__.py) | Exportaciones de API de módulo | C-01 |
| [backend/odontologia/demo.py](../backend/odontologia/demo.py) | Demo temporal sin red | C-01 |
| [backend/odontologia/core/config.py](../backend/odontologia/core/config.py) | Lectura de variables de entorno del stack | Base |
| `backend/odontologia/db/` | SQLAlchemy + PostgreSQL optativo, migración de C-01 | C-02 / C-03 |
| `backend/odontologia/auth/` | JWT HS256, scrypt, sesiones revocables y RBAC | C-03 |
| `backend/odontologia/workers/` | Cola de recordatorios en Redis (estructura) | C-17 |
| [backend/tests/](../backend/tests/) | 111 tests SQLite; 121 con PostgreSQL temporal | C-01 / C-02 / C-03 |
| [frontend/](../frontend/README.md) | React + TypeScript + Vite; consume la API vía `/api` | C-11 |
| [docker-compose.yml](../docker-compose.yml) | Servicios db, redis, backend y frontend en loopback | C-02 / C-14 |

La UI no decide conflictos ni valida reglas de negocio por su cuenta: muestra lo que devuelve el backend.

## Seguridad y datos

Sólo IDs ficticios; sin datos clínicos reales ni promesa de producción. C-03 protege las operaciones con JWT y aplica el menor privilegio aprobado: Administrador gestiona usuarios y operaciones disponibles; Recepción crea turnos; Profesional no accede hasta C-08. No hay cuentas predeterminadas ni secretos versionados. El esquema se migra explícitamente; la API y `/health` no crean DB ni ejecutan DDL. Ninguna integración externa.

## Persistencia, concurrencia y errores

El dominio C-01 conserva sus reglas y errores. En SQLite, turnos y cuentas usan almacenamiento local con claves foráneas y transacciones; C-03 migra explícitamente tablas de usuario/sesión sobre una agenda ya existente. En PostgreSQL, Alembic aplica en orden C-01 y C-03, y las escrituras serializan por mutex transaccional. La autorización valida el JWT y consulta cada sesión persistida antes de operar; cambiar rol, desactivar usuario o cerrar sesión revoca el token.

Un escritor por archivo serializa control y registro. BUSY/LOCKED produce agenda_ocupada; otros fallos almacenamiento_error. Sin reintentos automáticos ni reconciliación de IO catastrófico/exactamente-una-vez. Garantía sólo mismo archivo local y escritores vía módulo; no varios equipos, red compartida, archivos distintos o SQL directo externo.

## Variables de entorno

C-01 usa `ODONTOLOGIA_DB` (SQLite por defecto); timeout numérico 5s. C-02/C-03 permiten `ODONTOLOGIA_PERSISTENCIA=postgresql` con `DATABASE_URL`. C-03 usa `JWT_SECRETO` (mínimo 32 bytes aleatorios, fuera del repositorio), `JWT_ALGORITMO=HS256` y `JWT_MINUTOS_EXPIRACION`. Los valores locales van en `.env` no versionado; `.env.example` trae marcadores rechazados por la validación.

## Validación ejecutada

Verificación vigente registrada en [evidencia técnica](../docs/evidencia/implementacion-turnos.md): 111 tests en SQLite y 121 al añadir pruebas de PostgreSQL temporal aislado, incluidos autenticación, roles, sesiones revocables, migraciones y concurrencia. Pruebas con datos ficticios y almacenamiento temporal; no acreditan operación clínica, despliegue ni aceptación docente.

Archive de C-01 confirmado el 2026-10-28. C-02 y C-03 tienen su Apply validado pero permanecen activos hasta Archive; las evidencias humanas y la aceptación académica se acreditan por separado.
