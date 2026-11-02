# Arquitectura aplicada y evolución propuesta

## Estado y objetivo

Arquitectura inicial de C-01: Python 3.12+, SQLite local y módulo de dominio pequeño. Sobre esa base, C-02 añade PostgreSQL optativo y migraciones explícitas; C-03 añade JWT, sesiones revocables y autorización; está archivado. C-04 añade la tabla `eventos_auditoria` append-only en SQLite y PostgreSQL, inserta eventos en la misma transacción de cada cambio, y ofrece consulta paginada exclusiva de Administrador. Está validado localmente y pendiente de Archive. Ver [evidencia](../docs/evidencia/implementacion-turnos.md).

**Actualización 2026-11-02 — alcance vigente:** C-01 se expone con FastAPI; C-02/C-03 usan SQLAlchemy, PostgreSQL optativo y JWT. El stack completo indicado por la cátedra (incluidos Redis y Docker) se conserva como antecedente de DD-09; esta entrega se arma y demuestra mediante changes, pruebas y demo local, sin Redis, Docker ni despliegue.

## Responsabilidades y directorios

Desde la corrección de la cátedra (2026-10-29) el código se separa en `backend/` y `frontend/`. C-01 se movió sin cambios de contrato.

| Ruta | Responsabilidad | Change |
| --- | --- | --- |
| [backend/odontologia/agenda.py](../backend/odontologia/agenda.py) | Tipos, bootstrap, validación, transacción y alta | C-01 |
| [backend/odontologia/api.py](../backend/odontologia/api.py) | Alta, consultas paginadas y disponibilidad orientativa | C-01 / C-03 / C-08 |
| [backend/odontologia/__init__.py](../backend/odontologia/__init__.py) | Exportaciones de API de módulo | C-01 |
| [backend/odontologia/demo.py](../backend/odontologia/demo.py) | Demo temporal sin red | C-01 |
| [backend/odontologia/core/config.py](../backend/odontologia/core/config.py) | Lectura de variables de entorno del stack | Base |
| `backend/odontologia/db/` | SQLAlchemy + PostgreSQL optativo, migración de C-01 | C-02 / C-03 |
| `backend/odontologia/auth/` | JWT HS256, scrypt, sesiones revocables y RBAC | C-03 |
| Outbox PostgreSQL y worker local simulado | Alternativa propuesta para recordatorios sin cola externa; no implementada | C-17 |
| [backend/tests/](../backend/tests/) | Regresión SQLite y PostgreSQL aislado por change | C-01–C-09 |
| [frontend/](../frontend/README.md) | React + TypeScript + Vite; consume la API vía `/api` | C-11 |
| Configuración de contenedores | No forma parte del flujo de entrega ni se verifica | Opcional/diferido |

## Alcance vigente

La entrega es revisable desde `CHANGES.md`, OpenSpec, código, pruebas y evidencia. No exige iniciar servicios ni publicar una aplicación. PostgreSQL se usa en pruebas aisladas. C-14 despliegue se difiere; C-17 podrá persistir recordatorios/outbox en PostgreSQL con canal simulado. Redis sólo podrá reconsiderarse como alternativa futura si surge una necesidad concreta.

La UI no decide conflictos ni valida reglas de negocio por su cuenta: muestra lo que devuelve el backend.

## Seguridad y datos

Sólo IDs ficticios; sin datos clínicos reales ni promesa de producción. C-08 mantiene JWT y aplica menor privilegio: Administrador administra cuentas y operaciones disponibles; Recepción opera agenda; Profesional lee sólo su vínculo, sin teléfono ni escrituras. El vínculo único y el claim se comparan con la base en cada validación. No hay cuentas predeterminadas ni secretos versionados. El esquema se migra explícitamente; la API y `/health` no crean DB ni ejecutan DDL. Ninguna integración externa.

## Persistencia, concurrencia y errores

El dominio C-01 conserva sus reglas y errores. En SQLite, turnos y cuentas usan almacenamiento local con claves foráneas y transacciones; C-03 migra explícitamente tablas de usuario/sesión sobre una agenda ya existente. En PostgreSQL, Alembic aplica en orden C-01 y C-03, y las escrituras serializan por mutex transaccional. La autorización valida el JWT y consulta cada sesión persistida antes de operar; cambiar rol, desactivar usuario o cerrar sesión revoca el token.

Un escritor por archivo serializa control y registro. BUSY/LOCKED produce agenda_ocupada; otros fallos almacenamiento_error. Sin reintentos automáticos ni reconciliación de IO catastrófico/exactamente-una-vez. Garantía sólo mismo archivo local y escritores vía módulo; no varios equipos, red compartida, archivos distintos o SQL directo externo.

## Variables de entorno

C-01 usa `ODONTOLOGIA_DB` (SQLite por defecto); timeout numérico 5s. C-02/C-03 permiten `ODONTOLOGIA_PERSISTENCIA=postgresql` con `DATABASE_URL`. C-03 usa `JWT_SECRETO` (mínimo 32 bytes aleatorios, fuera del repositorio), `JWT_ALGORITMO=HS256` y `JWT_MINUTOS_EXPIRACION`. Los valores locales van en `.env` no versionado; `.env.example` trae marcadores rechazados por la validación.

## Validación ejecutada

Verificación vigente registrada en [evidencia técnica](../docs/evidencia/implementacion-turnos.md): 111 tests en SQLite y 121 al añadir pruebas de PostgreSQL temporal aislado, incluidos autenticación, roles, sesiones revocables, migraciones y concurrencia. Pruebas con datos ficticios y almacenamiento temporal; no acreditan operación clínica, despliegue ni aceptación docente.

## C-08 — consulta de agenda y disponibilidad (Apply)

SQLite v7 y PostgreSQL Alembic 0008 añaden el vínculo único entre cuenta Profesional y ficha; no modifican el contrato de alta standalone C-01. `GET /turnos` y `GET /disponibilidad` son consultas de sólo lectura. La disponibilidad propone candidatos cada 15 minutos en Mendoza, usa horarios y excepciones C-07 y excluye bloqueos y ocupantes C-09; la operación de alta mantiene su revalidación serializada. La especificación y pruebas dirigidas pasan; la regresión completa de ambos motores y el cierre de OpenSpec quedan pendientes de verificación final. C-08 todavía no se archivó.

Archive de C-01 confirmado el 2026-10-28. C-02–C-07 y C-09 están archivados localmente. Las evidencias humanas y la aceptación académica se acreditan por separado.
