# Tasks

## 1. Baseline y migraciones

- [x] 1.1 Ejecutar y registrar baseline de suites backend, frontend, build y OpenSpec; adjuntar comandos y conteos reales en `backend/evidence/C-18-verificacion.md` antes de cambios.
- [x] 1.2 Escribir pruebas RED de upgrade SQLite v11→v12 y PostgreSQL Alembic 0012→0013, preservación de cuentas/turnos, vínculo único `paciente_id`, tabla idempotente y whitelist de backup; luego implementar migraciones y ejecutar pruebas focales en SQLite y PostgreSQL aislado puerto 55432.

## 2. Cuenta y sesión de paciente

- [x] 2.1 Escribir pruebas RED para crear cuenta de paciente sólo por Administrador, ficha activa no vinculada, credenciales omitidas, unicidad y revocación al cambiar estado/vínculo; implementar servicios/endpoints y ejecutar pruebas de cuentas.
- [x] 2.2 Escribir pruebas RED para login, principal y sesión vigente con `paciente_id` autenticado, vínculos inválidos y rechazo genérico; implementar autenticación con el nuevo rol y ejecutar pruebas de sesión existentes y nuevas.

## 3. Disponibilidad opaca y reservas

- [x] 3.1 Escribir pruebas RED de franjas sintéticas de 30 minutos con disponibilidad conjunta, horizonte local máximo de 31 días y sólo inicio/fin; implementar consulta opaca sin agenda identificada y ejecutar pruebas de disponibilidad.
- [x] 3.2 Escribir pruebas RED de reserva serializada desde `inicio` únicamente, asignación interna de profesional/box, uso de C-01/C-08 y conflicto concurrente; implementar alta de autoservicio y ejecutar pruebas SQLite/PostgreSQL.
- [x] 3.3 Escribir pruebas RED de máximo tres turnos futuros activos, borde de 24 horas y protección contra `paciente_id` aportado por cliente; implementar validaciones y ejecutar pruebas de reglas.

## 4. Consulta, idempotencia y propiedad

- [x] 4.1 Escribir pruebas RED para `GET /mis-turnos` limitado al principal y esquema mínimo, además de consultas ajenas/desconocidas con el mismo 404; implementar proyecciones y ejecutar pruebas de API.
- [x] 4.2 Escribir pruebas RED de `Idempotency-Key` persistida para reserva/cancelación/reprogramación, repetición idéntica, payload distinto y concurrencia; implementar tabla/servicio de resultados transaccionales y ejecutar pruebas SQLite/PostgreSQL.

## 5. Cancelación, reprogramación y auditoría

- [x] 5.1 Escribir pruebas RED de cancelación propia sólo `reservado`/`confirmado` con anticipación exacta de 24 horas, invalidación de recordatorio C-17 y 404 indistinguible; implementar comando usando actor paciente y ejecutar pruebas focales.
- [x] 5.2 Escribir pruebas RED de reprogramación propia con versión vigente, paciente/duración/estado conservados, nueva franja revalidada y recordatorios recalculados; implementar comando transaccional y ejecutar pruebas SQLite/PostgreSQL.
- [x] 5.3 Escribir pruebas RED de auditoría metadata-only para lecturas/escrituras/denegaciones, rollback ante falla y ausencia de PII/horarios; implementar catálogo de acciones y verificar eventos serializados.

## 6. API y portal

- [x] 6.1 Escribir pruebas RED de autenticación por rol para todas las rutas del portal, cuerpos extraños, validación de fecha/clave/versiones y respuestas mínimas; implementar esquemas/rutas FastAPI y ejecutar pruebas de API/OpenAPI.
- [x] 6.2 Escribir pruebas RED del portal autenticado: login sintético, consulta de turnos/disponibilidad, reserva, cancelación y reprogramación; implementar vistas React por rol y ejecutar tests frontend/build.

## 7. Compatibilidad, evidencia y cierre

- [x] 7.1 Escribir y ejecutar pruebas de backup/restore SQLite y PostgreSQL que preserven vínculos y claves idempotentes; actualizar versiones/whitelists y documentar límites de datos sintéticos en evidencia.
- [x] 7.2 Ejecutar suite backend completa con PostgreSQL aislado puerto 55432, suite frontend, build y `openspec validate habilitar-reserva-del-paciente --strict`; corregir fallas introducidas y registrar resultados exactos en la evidencia.
- [x] 7.3 Verificar OpenAPI y walkthrough visual local con cuentas y turnos ficticios; completar README/evidencia con pasos reproducibles y pendientes reales antes de sincronizar specs.

## Correcciones de revisión posteriores al archive

- [x] 8.1 Agregar replay idempotente SQLite/PostgreSQL tras vencer la franja u horizonte, conservando fingerprint canónico, 409 por payload conflictivo y 404 por titularidad; validar RED/GREEN focal.
- [x] 8.2 Mantener en frontend la clave por operación+objetivo+payload durante errores ambiguos, cambiarla al cambiar comando/payload y limpiarla tras éxito; validar RED/GREEN y regresión frontend.

## Workflow follow-up

- Sincronizar deltas con las specs principales y validar todas las specs en modo estricto.
- Archivar C-18 sólo después de que todas las tareas verificables estén completas y el estado final sea válido.
