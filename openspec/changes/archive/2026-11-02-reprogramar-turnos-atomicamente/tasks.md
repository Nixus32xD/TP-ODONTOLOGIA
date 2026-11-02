# Tasks

## 1. Esquema y versionado

- [x] 1.1 Ejecutar el baseline focalizado SQLite y PostgreSQL de migraciones, ciclo de vida, consultas y auditoría; registrar el resultado previo para distinguir regresiones.
- [x] 1.2 Escribir primero pruebas RED para versión inicial, preservación de turnos y esquema incompleto; implementar SQLite v8, revisión Alembic siguiente y validación fail-closed, y verificar migraciones desde v7/0008 en ambos motores.
- [x] 1.3 Escribir primero pruebas RED para incremento de versión en transiciones efectivas y estabilidad ante cancelación idempotente; implementar el incremento transaccional y verificar los casos en SQLite y PostgreSQL.
- [x] 1.4 Actualizar README y evidencia de esquema/versionado con migraciones y compatibilidad C-01; verificar comandos y estructura documentados.

## 2. Operación de dominio atómica

- [x] 2.1 Escribir pruebas RED para versión obsoleta, turno terminal, paciente/recurso inactivo, duración distinta, cruce de medianoche (rechazando si continúa después y aceptando fin exacto 00:00 en tramo C-07 23:00–24:00) y horario/bloqueo incompatible; verificar que los rechazos preserven fila, versión y auditoría.
- [x] 2.2 Agregar y ejecutar pruebas para cambio válido, conflictos por profesional/box y exclusión del propio turno; la operación ya se había implementado durante 2.1, por lo que estas pruebas pasaron sin RED observable (desviación TDD documentada); verificar en SQLite y PostgreSQL.
- [x] 2.3 Agregar y ejecutar pruebas de carrera con dos solicitudes de la misma versión y de fallo de auditoría; la lógica ya se había implementado durante 2.1, por lo que estas pruebas pasaron sin RED observable (desviación TDD documentada); verificar resultado único/409, rollback completo y un evento metadata-only.
- [x] 2.4 Documentar el contrato de transacción y los casos de rechazo en la evidencia de C-10; verificar que quede explícito que prestaciones y exclusión por paciente no se agregan.

## 3. API y consulta operativa

- [x] 3.1 Escribir pruebas RED para solicitud estricta, respuesta, errores 404/409/422, ausencia de sesión y roles; implementar `POST /turnos/{id}/reprogramacion` para Administrador/Recepción y verificar OpenAPI y respuestas HTTP.
- [x] 3.2 Escribir pruebas RED de proyección de versión por rol; incluir `version` sólo en filas operativas de Administrador/Recepción y verificar que Profesional conserva únicamente inicio, fin y nombre del paciente.
- [x] 3.3 Actualizar README y documentación de API con cuerpo, precondición, respuestas y recuperación ante 409; verificar que ejemplos coincidan con los esquemas publicados.

## 4. Integración y cierre técnico

- [x] 4.1 Ejecutar suite completa SQLite y PostgreSQL aislado en loopback distinto de 5432; verificar migración, API, concurrencia, auditoría y regresión C-01.
- [x] 4.2 Ejecutar `pip check`, `openspec validate --change reprogramar-turnos-atomicamente --strict` y `git diff --check`; actualizar bitácora/evidencia con resultados reales y detener PostgreSQL temporal.
