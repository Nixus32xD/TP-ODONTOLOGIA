# Tasks

## 1. Persistencia de auditoría

- [x] 1.1 Agregar pruebas RED para crear y consultar eventos de metadatos en SQLite, incluyendo rechazo de campos sensibles; verificar primero la falla y luego la implementación con `python -m unittest`.
- [x] 1.2 Implementar tabla/índices y migración explícita SQLite append-only; comprobar persistencia y que app/import no migra implícitamente.
- [x] 1.3 Extender DDL PostgreSQL y pruebas de esquema para auditoría; ejecutar pruebas de integración en PostgreSQL aislado por loopback `127.0.0.1:55432`.
- [x] 1.4 Implementar lector paginado con orden `(created_at, id)` descendente y DTO allowlist; probar límites, empate temporal, offset y ausencia de payload.

## 2. Escrituras atómicas

- [x] 2.1 Agregar pruebas RED de atomicidad de turnos SQLite/PostgreSQL: falla del audit revierte el turno y la API responde `500 almacenamiento_error`.
- [x] 2.2 Integrar evento de alta en la transacción existente de turnos para ambos backends; validar conflictos C-01 y rollback.
- [x] 2.3 Agregar pruebas RED para bootstrap, alta/cambio de cuenta y revocación de sesión, login correcto y logout; validar actor/recurso y ausencia de credenciales.
- [x] 2.4 Integrar eventos de cuentas y sesiones dentro de su transacción; comprobar con fallas inyectadas que mutación, revocación y evento confirman o revierten juntos.
- [x] 2.5 Agregar pruebas RED para login rechazado: evento genérico sin actor ni identificador intentado; fallo de escritura da 503 sin revelar existencia de cuenta.
- [x] 2.6 Implementar auditoría fail-closed de login rechazado y validar que distintas causas devuelven mismo 401 y evento indistinguible.

## 3. API y documentación

- [x] 3.1 Agregar pruebas RED de `GET /auditoria`: Admin recibe página segura; Recepción recibe 403; sin sesión recibe 401; parámetros inválidos se rechazan.
- [x] 3.2 Implementar ruta, modelos OpenAPI y paginación default 50 / máximo 100; validar respuestas y códigos HTTP.
- [x] 3.3 Documentar esquema, comandos de migración, política de datos y ejemplos de consulta en README/KB; ejecutar los comandos documentados en un entorno temporal.

## 4. Integración y evidencia

- [x] 4.1 Ejecutar toda la suite con SQLite y PostgreSQL aislado; verificar C-01 y RBAC C-03, regresiones y guardas para que jamás se conecte al puerto 5432.
- [x] 4.2 Actualizar CHANGES, KB03/08/09 y bitácora/evidencia, mantener AGENTS.md y CLAUDE.md idénticos y dejar informe Discovery intacto; validar OpenSpec en modo estricto y revisar diff.

## Workflow follow-up

- Sincronizar y archivar C-04 después de la revisión del responsable del repositorio.
