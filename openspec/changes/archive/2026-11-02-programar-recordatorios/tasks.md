# Tasks

## 1. Baseline y persistencia

- [x] 1.1 Capturar baseline antes de cambios: backend con PostgreSQL aislado `.venv/Scripts/python.exe -m unittest discover -s tests -v` (481 OK, 3 skips del host) y frontend `npm test -- --run` (55 OK).
- [x] 1.2 Escribir prueba RED para upgrade SQLite v10→v11: consentimiento existente queda falso, outbox vacío, constraints y FK válidas; implementar migración/modelos y verificar `python -m unittest discover -s tests -p "test_recordatorios_migracion.py" -v` y `python -m unittest discover -s tests -p "test_auth_sqlite_migration.py" -v` (2/2 y 10/10).
- [x] 1.3 Escribir prueba RED de Alembic 0011→0012 en PostgreSQL aislado `127.0.0.1:55432`, DB `*_test`; verificar upgrade, valor default false, unicidad, FK, tipo y columnas contra PostgreSQL 18 con `ODONTOLOGIA_TEST_DATABASE_URL=... .venv/Scripts/python.exe -m unittest tests.test_recordatorios_postgresql_integracion -v` (1 test OK; las pruebas se aíslan en schema efímero y eliminan sólo ese schema).
- [x] 1.4 Actualizar README y `backend/evidence/C-17-verificacion.md` con versiones y migración explícita SQLite/PostgreSQL; ejecutar ambos comandos de migración sobre fixtures sintéticos y comprobar en test de arranque que FastAPI no migra (C17 v1.2 SQLite y Alembic `20261102_0012_appointment_reminders` verificados).

## 2. Consentimiento de pacientes

- [x] 2.1 Escribir RED para `acepta_recordatorios=false` por defecto y cambio explícito por Administrador/Recepción; implementar API/servicio con auditoría metadata-only en la misma transacción y verificar rollback ante falla con `python -m unittest discover -s tests -p "test_api_pacientes.py" -v` (5 OK) y `python -m unittest discover -s tests -p "test_pacientes.py" -v` (7 OK).
- [x] 2.2 Escribir RED de UI para crear/editar el consentimiento desde la ficha, ocultarlo a Profesional y reflejar sólo respuestas confirmadas; implementar React y verificar `npm test -- --run src/agenda/Agenda.test.tsx` (23 OK) y suite completa `npm test -- --run` (10 archivos, 58 OK).
- [x] 2.3 Documentar el campo y permisos en README/evidencia; verificar OpenAPI y errores de campo inválido, campos adicionales y rol denegado con `python -m unittest discover -s tests -p "test_api_pacientes.py" -v` (6 OK).

## 3. Programación e invalidación transaccional

- [x] 3.1 Escribir RED con reloj fijo para confirmación y consentimiento habilitado: >24 h encola, exactamente 24 h o menos y turnos ya pasados no encolan; implementar cálculo con instante Mendoza y verificar SQLite con `python -m unittest discover -s tests -p "test_turno_ciclo_vida.py" -v` (13 OK). La confirmación y outbox/auditoría se escriben en la misma transacción; fallo de auditoría deja el turno reservado y sin fila.
- [x] 3.2 Escribir RED para cancelar e invalidar pendientes y para reprogramar la versión anterior/crear sólo una nueva clave elegible; integrar con los servicios existentes y verificar atomicidad/rollback de auditoría u outbox con `.venv/Scripts/python.exe -m unittest tests.test_turno_ciclo_vida tests.test_reprogramacion -v` (34 OK; SQLite).
- [x] 3.3 Cubrir consentimiento retirado y habilitado con turnos ya confirmados, concurrencia serializada e idempotencia turno+versión+tipo; verificar SQLite con `.venv/Scripts/python.exe -m unittest tests.test_pacientes -v` (10 OK) y PostgreSQL aislado `127.0.0.1:55432`, DB `odontologia_c16_test`, con `.venv/Scripts/python.exe -m unittest tests.test_recordatorios_postgresql_integracion -v` (2 OK).

- [x] 3.4 Cubrir reconsentimiento tras invalidación: preservar generación histórica, crear la siguiente con clave turno+versión+tipo+generación y serializar dos opt-ins concurrentes. Validación: test SQLite de ciclo de vida, integración PostgreSQL y migración SQLite de outbox v11 existente; bundles SQLite/PG conservan generation.

## 4. Worker local simulado

- [x] 4.1 Escribir RED para CLI que exige `--once`, valida `--limit` de 1–100 y falla antes de abrir DB si faltan flags; implementar una pasada local y comprobar salida únicamente con conteos mediante `.venv/Scripts/python.exe -m unittest tests.test_recordatorios_cli -v` (3 OK).
- [x] 4.2 Escribir RED para revalidar consentimiento, estado, versión, vencimiento y futuro del turno; implementar worker idempotente que procese como máximo el límite y verificar escenario elegible, consentimiento retirado, cancelado, versión cambiada y turno ya iniciado con SQLite `.venv/Scripts/python.exe -m unittest tests.test_recordatorios_worker -v` (4 OK) y PostgreSQL aislado `.venv/Scripts/python.exe -m unittest tests.test_recordatorios_postgresql_integracion -v` (3 OK).
- [x] 4.3 Escribir RED de fallos sintéticos, máximo tres intentos, estados terminales, auditoría fail-closed y ausencia de teléfono/nombre/mensaje en logs/salida; implementar el canal local inyectable sólo para tests y verificar retries (6 OK), estado terminal, rollback de auditoría (worker SQLite), salida sólo con conteos (CLI 3 OK) y auditoría sin datos personales (PG C-17 3 OK).
- [x] 4.4 Documentar comando `--once`, límite, resultados `simulado` y restricciones locales en `backend/README.md`/evidencia; ejecutar el proceso CLI real en un subprocess sobre SQLite temporal sintético (`tests.test_recordatorios_cli`, 4 OK). Salida capturada: `Recordatorios simulados: procesados=1 invalidados=0 fallidos=0`; sin nombre ni teléfono.

## 5. Backup y restauración

- [x] 5.1 Escribir RED para whitelist/recuentos SQLite, esquema v11, restore a archivo nuevo y conservación de pendientes, procesados e invalidados sin PII; implementar C-17 en manifiesto/conteos/validador y verificar `python -m unittest tests.test_backup_manifest tests.test_backup_sqlite tests.test_backup_restore_sqlite -v` (24 OK; 1 skip del host).
- [x] 5.2 Escribir RED de bundle/restore PostgreSQL con outbox y recuentos en destino nuevo sintético; implementar revisión 0012 y tabla permitida; verificar PostgreSQL 18 aislado en `127.0.0.1:55432`, DB `odontologia_c16_test`, con cliente 18 (`PATH=C:\Program Files\PostgreSQL\18\bin`) y `python -m unittest tests.test_backup_recordatorios_postgresql_integracion -v` (1 OK).
- [x] 5.3 Actualizar README/evidencia con esquema, tabla de outbox, conteos y límites; pruebas SQLite y PG comparan recuentos/estados en destino distinto, conservan la fuente y comprueban que los manifiestos no contengan datos personales.

## 6. Integración final y OpenSpec

- [x] 6.1 Ejecutar suite backend completa con PostgreSQL aislado (515 OK, 3 skips), suite frontend (10 archivos/58 OK) y build TypeScript/Vite OK; corregir la revisión PostgreSQL vigente a Alembic 0012 y ajustar expectativas de esquema actual sin alterar fixtures históricas. Evidencia completa en `backend/evidence/C-17-verificacion.md`.
- [x] 6.2 Sincronizar los siete deltas con las specs principales, validar idempotencia del outbox en SQLite/PostgreSQL y ejecutar `openspec validate --all --strict` — 19/19 items OK.

## Workflow follow-up

- Sync y Archive del change después de que todas las tareas estén verificadas; no incluye commit ni push.
