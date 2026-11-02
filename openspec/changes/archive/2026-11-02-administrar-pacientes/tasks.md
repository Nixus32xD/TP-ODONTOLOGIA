# Tasks

## 1. Esquema y migraciones

- [x] 1.1 Ejecutar baseline de la suite (130 tests, 1 PostgreSQL omitido); escribir pruebas RED para migración SQLite legacy/v2→v3 y upgrade PostgreSQL desde revisión 0003, comprobar preservación de pacientes/turnos, e implementar columnas y revisión Alembic; verificar pruebas SQLite y PostgreSQL.
- [x] 1.2 Adaptar y verificar la importación C-02 desde SQLite C-01 legacy: asignar nombre ficticio, teléfono nulo y activo verdadero sin modificar la fuente; pasan las pruebas de integración de migración.

## 2. Dominio de pacientes

- [x] 2.1 Agregar pruebas RED para nombre, teléfono, homónimos, paginación, ID desconocido, baja lógica y rollback si falla auditoría; implementar el servicio transaccional mínimo y verificar `tests.test_pacientes` en SQLite.
- [x] 2.2 Extender pruebas del catálogo de auditoría para cuatro acciones de paciente y sus combinaciones válidas/inválidas en SQLite y PostgreSQL; implementar restricciones y normalización de eventos sin aceptar nombre/teléfono, y verificar `tests.test_auditoria` y `tests.test_postgres_schema`.

## 3. Adaptador HTTP y permisos

- [x] 3.1 Escribir pruebas RED para 401, 403, CRUD permitido a Administrador/Recepción, baja sólo Admin, validación estricta, paginación y errores públicos; implementar modelos/rutas FastAPI y verificar `tests.test_api_pacientes` y regresión `tests.test_api_auth`.
- [x] 3.2 Actualizar OpenAPI y `backend/README.md` con campos, roles, migración y uso exclusivamente ficticio; verificar documentación generada, `git diff --check` y que `AGENTS.md`/`CLAUDE.md` permanezcan idénticos.

## 4. Integración con turnos

- [x] 4.1 Escribir pruebas RED para rechazo de altas nuevas de pacientes inactivos en SQLite y PostgreSQL, mantener aceptación para activos y conservar C-01 sin migración automática; implementar el comportamiento y verificar pruebas específicas y regresión completa de agenda.

## 5. Validación integral

- [x] 5.1 Ejecutar toda la suite: SQLite **143 tests, OK (1 PostgreSQL skip)** y PostgreSQL aislado en loopback **159 tests, OK**; `pip check` sin dependencias rotas; `openspec validate --all --strict` pasó 6/6; `git diff --check` sin errores; revisar diff y excluir `docs/discovery/informe-discovery.md`.

## Workflow follow-up

- Archive confirmado por OpenSpec con siete requisitos sincronizados en las specs principales; CHANGES.md, README y las instrucciones ya reflejan C-05 archivado.
- Crear un commit local separado después de la validación; no hacer push sin autorización expresa.
