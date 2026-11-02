# Evidencia C-17 — Recordatorios simulados

## Estado de implementación

Esta evidencia cubre persistencia/migraciones, gestión del consentimiento en API e interfaz, programación e invalidación, worker local simulado de una pasada y backup/restore con SQLite y PostgreSQL. No se contactó a pacientes ni a servicios externos. Todas las filas creadas para probar el esquema son sintéticas.

## Baseline previo

Antes de modificar C-17 se registró el baseline del change:

| Área | Comando | Resultado |
| --- | --- | --- |
| Backend con PostgreSQL local aislado | `.venv/Scripts/python.exe -m unittest discover -s tests -v` | 481 OK; 3 skips por limitaciones del host. |
| Frontend | `npm test -- --run` | 55 OK. |

## SQLite v10 → v11

- RED inicial: la nueva prueba falló porque la base seguía en esquema v10.
- GREEN: `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_recordatorios_migracion.py" -v` — 3 tests OK.
- Regresión de migraciones anteriores: `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_auth_sqlite_migration.py" -v` — 10 tests OK.
- Ejecución del comando de migración documentado: `python -m odontologia.auth.migrar_sqlite` sobre un archivo SQLite temporal recién creado con agenda sintética; resultado `schema=11`, una tabla `recordatorios_outbox`, archivo temporal eliminado.
- Se comprueba que las fichas existentes reciben consentimiento `false`, la outbox parte vacía, y su FK, clave idempotente y restricciones rechazan referencias huérfanas, duplicados y tipos no admitidos.
- Se comprobó que repetir la migración conserva un consentimiento previamente habilitado.
- Un test de arranque usa un fixture sintético v10, inicia FastAPI y confirma que `POST /sesiones` falla cerrado con 503, el esquema continúa en v10 y no se crea `recordatorios_outbox`. El arranque no aplica DDL automáticamente.

## PostgreSQL Alembic 0011 → 0012

- Base de pruebas: PostgreSQL 18 aislado en `127.0.0.1:55432`, base `odontologia_c16_test` (sufijo `_test`); el caso crea y elimina únicamente un schema aleatorio propio. No se usa el puerto 5432.
- Comando desde `backend/`:

  ```powershell
  $env:ODONTOLOGIA_TEST_DATABASE_URL='postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_c16_test'
  .venv\Scripts\python.exe -m unittest tests.test_recordatorios_postgresql_integracion -v
  ```

- Resultado observado: 1 test OK.
- La prueba comienza en `20261102_0011_odontogram_treatment_plans`, aplica `upgrade head` y comprueba la revisión `20261102_0012_appointment_reminders`, consentimiento inicial `false`, columnas del outbox, FK a turnos, unicidad de turno/versión/tipo, tipo permitido y longitud compatible del estado.
- También se ejecutó el comando documentado `.venv/Scripts/python.exe -m alembic upgrade head` con `DATABASE_URL` apuntando a un schema PostgreSQL efímero sintético: resultado `revision=20261102_0012_appointment_reminders`; sólo se eliminó ese schema temporal.
- El primer RED llegó correctamente hasta la revisión 0011 y falló al esperar 0012; el GREEN se confirmó después de agregar la revisión Alembic. Una aserción de longitud detectó y corrigió una diferencia entre modelo y migración antes de volver a obtener PASS.

## Comandos explícitos de migración

- SQLite: ejecutar `.venv/Scripts/python.exe -m odontologia.auth.migrar_sqlite` desde `backend/`, con `ODONTOLOGIA_DB` apuntando a la agenda sintética elegida.
- PostgreSQL: ejecutar `.venv/Scripts/python.exe -m alembic upgrade head` desde `backend/`, con `DATABASE_URL` de la base seleccionada.
- Las migraciones son explícitas; FastAPI valida el esquema existente y no lo migra durante el arranque.
- Se trabajó sin Docker, Redis, HTTP, correo, WhatsApp, teléfonos reales ni otros proveedores externos.

## Consentimiento y permisos

- Servicio: `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_pacientes.py" -v` — 7 tests OK. Se verifican valor inicial falso, habilitación explícita, evento de auditoría sólo metadata-only y rollback si falla el registro.
- API: `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_api_pacientes.py" -v` — 6 tests OK. Administrador y Recepción cambian el valor; Profesional recibe 403. Tipo no booleano y campos adicionales reciben 422. OpenAPI contiene el campo en creación, actualización y respuesta, con default `false`.
- La escritura usa la transacción existente de actualización de pacientes. El evento permitido es `paciente.actualizado` y no agrega valor de consentimiento, teléfono, nombre ni cuerpo al registro.
- UI: `npm test -- --run src/agenda/Agenda.test.tsx` — 23 tests OK; `npm test -- --run` — 10 archivos, 58 tests OK; `npm run build` — TypeScript y Vite OK. Admin/Recepción ven la preferencia y pueden cambiarla; el control queda deshabilitado durante la petición y el estado visible se actualiza sólo al recibir respuesta. Profesional no carga pacientes ni monta el panel.
- No se realizó inspección visual manual de esta sección; su comportamiento se verificó automáticamente con Vitest.

## Programación e invalidación transaccional

- RED de programación: el test con reloj fijo falló antes de añadir el argumento `ahora` y la outbox. GREEN: `.venv/Scripts/python.exe -m unittest tests.test_turno_ciclo_vida -v` — 13 tests OK en SQLite.
- La confirmación programa únicamente con consentimiento y más de 24 horas de margen; se cubren también exactamente 24 horas, menos de 24 horas, turno ya pasado y conversión `America/Argentina/Mendoza`.
- RED de invalidación: antes de integrar los servicios, la cancelación dejaba el recordatorio pendiente y la reprogramación rechazaba el parámetro de reloj. Tras el cambio, `.venv/Scripts/python.exe -m unittest tests.test_turno_ciclo_vida tests.test_reprogramacion -v` — 34 tests OK.
- Al cancelar, los recordatorios pendientes pasan a `invalidado` con evento de auditoría metadata-only. Al reprogramar un turno confirmado se invalida la versión anterior y sólo se crea la nueva si la fecha conserva más de 24 horas; la clave idempotente incluye la versión.
- Se verificaron fallos sintéticos de auditoría en cancelación y reprogramación: el estado del turno, versión y outbox vuelven al estado previo por rollback. Los casos se ejecutaron sobre bases SQLite temporales con datos ficticios.
- Al activar el consentimiento se consideran turnos ya confirmados que conservan más de 24 horas; al retirarlo se invalidan los pendientes. Un fallo al auditar la invalidación revierte tanto consentimiento como outbox.
- Concurrencia/idempotencia: `tests.test_pacientes` — 10 OK en SQLite, dos habilitaciones simultáneas crean una única fila por turno/versión/tipo. `tests.test_recordatorios_postgresql_integracion` — 2 OK en PostgreSQL 18 aislado en `127.0.0.1:55432`, DB `odontologia_c16_test`; la prueba aplica migración, serializa dos habilitaciones y confirma una única fila, luego la retirada invalida ese pendiente.

## Worker local de una pasada

- CLI: `.venv/Scripts/python.exe -m unittest tests.test_recordatorios_cli -v` — 3 OK. Sin `--once`, o con `--limit` inválido (0, negativo, no numérico o mayor de 100), argparse rechaza antes de cargar configuración; el caso no abre ni prepara la base. La invocación válida usa una sola pasada y muestra únicamente `procesados`, `invalidados` y `fallidos`.
- Worker SQLite: `.venv/Scripts/python.exe -m unittest tests.test_recordatorios_worker -v` — 4 OK. Con reloj fijo procesa como máximo el límite, deja intacto el turno y revalida consentimiento, estado, versión y que el turno aún sea futuro; los elementos ya no elegibles se invalidan. Un fallo de auditoría revierte el estado del outbox.
- Worker PostgreSQL 18 aislado: `.venv/Scripts/python.exe -m unittest tests.test_recordatorios_postgresql_integracion -v` — 3 OK en `127.0.0.1:55432`, base `odontologia_c16_test` (`*_test`). La integración valida revisión C-17, procesamiento simulado, auditoría metadata-only y ausencia de nombre/teléfono en sus registros.
- `validar_esquema_autenticacion` requiere C-17 SQLite v11 y PostgreSQL Alembic `20261102_0012_appointment_reminders`. El worker no aplica migraciones. El adaptador sólo actualiza estado local; no abre conexiones externas.
- Canal de simulación: por defecto devuelve éxito sin E/S. El test inyecta fallos sintéticos; se incrementan intentos, sigue pendiente hasta el tercero y luego queda terminal `fallido`. Un fallo de auditoría deja estado e intentos sin cambios. No existe opción CLI para inyectar fallos ni se escriben logs con datos de paciente.
- Documentación: comando y límites agregados al README del backend. Se ejecutó como subprocess el comando real `python -m odontologia.workers.recordatorios_cli --once --limit 10` en un test con SQLite temporal migrado, turno y paciente ficticios. Salida observada: `Recordatorios simulados: procesados=1 invalidados=0 fallidos=0`; el test comprueba que stdout/stderr no contienen el nombre ni el teléfono ficticios. El archivo se elimina con el fixture temporal.

## Backup y restauración del outbox

- El manifiesto soporta SQLite v11 y PostgreSQL `20261102_0012_appointment_reminders`; el recuento incluye `recordatorios_outbox` y el manifiesto no contiene nombres, teléfonos, estados por fila ni claves de idempotencia.
- SQLite: `.venv/Scripts/python.exe -m unittest tests.test_backup_manifest tests.test_backup_sqlite tests.test_backup_restore_sqlite -v` — 24 OK y 1 skip por symlink no disponible en Windows. Una prueba crea filas sintéticas `pendiente`, `procesado_simulado` e `invalidado`, verifica el bundle y restaura a un archivo nuevo; recuento y estados coinciden, la fuente conserva sus bytes y el manifiesto no expone datos de contacto.
- Snapshot SQLite: se normaliza el payload a journal DELETE antes de publicarlo, evitando que el bundle contenga archivos sidecar `-wal`/`-shm` y permitiendo verificación estricta con los dos archivos esperados.
- PostgreSQL: cliente y servidor 18 en `127.0.0.1:55432`, base `odontologia_c16_test` (sufijo `_test`), con schema de integración efímero y destino restore generado con sufijo `_test`. Comando: `$env:ODONTOLOGIA_TEST_DATABASE_URL='postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_c16_test'; $env:PATH='C:\\Program Files\\PostgreSQL\\18\\bin;' + $env:PATH; .venv\\Scripts\\python.exe -m unittest tests.test_backup_recordatorios_postgresql_integracion -v` — 1 OK.
- La integración PG genera bundle `pg_dump`, verifica revisión, outbox y conteos, restaura a base nueva, compara las tres filas y claves sintéticas, confirma que la fuente sigue intacta y borra únicamente el destino de prueba que creó. El manifiesto no contiene el nombre ni teléfono ficticios. PostgreSQL no se usa en puerto 5432 y no se usa Docker.
- `backend/README.md` documenta versiones, whitelist, outbox, recuentos, restricción del manifiesto y comandos/límites de backup/restore. Estas pruebas son locales automatizadas con fixtures; no prueban recuperación humana ni producción.


## Integración final, sincronización y validación

- Suite backend completa desde `backend/`, con PostgreSQL 18 aislado en `127.0.0.1:55432` y `ODONTOLOGIA_TEST_DATABASE_URL` apuntando a `odontologia_c16_test`:
  `.venv/Scripts/python.exe -m unittest discover -s tests -q` — 515 tests OK; 3 skips del host. El resultado se obtuvo después de integrar C-17; las migraciones y pruebas de integración usaron schemas aislados y fixtures ficticios.
- Suite frontend desde `frontend/`: `npm test -- --run` — 10 archivos y 58 tests OK. `npm run build` — TypeScript y Vite terminaron correctamente.
- La integración completa detectó que `REVISION_ESQUEMA_ACTUAL` del acceso PostgreSQL aún apuntaba a 0011. El esquema C-17 migrado a 0012 era rechazado como no vigente y, en una prueba de upgrade repetido, se intentaba reaplicar la columna de consentimiento. Se actualizó la constante a `20261102_0012_appointment_reminders`; el grupo focal relevante quedó en 34 tests OK y luego la suite completa pasó.
- Los tests de migración vigentes se ajustaron para esperar SQLite v11 y Alembic 0012, manteniendo explícitas las fixtures que comprueban los esquemas históricos v10/0011.
- Los deltas se sincronizaron con las specs principales para agenda-backup-restore, audit-trail, patient-management, reception-agenda-ui, turn-rescheduling y turno-lifecycle; se creó `appointment-reminders` con propósito y contratos del worker/outbox.
- Validación final antes de archive: `openspec validate --all --strict` — 19/19 items OK, incluyendo `programar-recordatorios`. El change quedó archivado en `openspec/changes/archive/2026-11-02-programar-recordatorios/`; después del archive, la validación estricta de las 18 specs principales terminó 18/18 OK.


## Corrección C-17: reconsentimiento y generaciones del outbox

- Reproducción RED: un turno confirmado y futuro con opt-in crea generación 1; al retirar consentimiento queda invalidada; al reconsentir, el comportamiento previo devolvía esa fila histórica y no creaba una nueva. El nuevo caso SQLite falló con `['invalidado']` frente a `['invalidado', 'pendiente']`; el caso PostgreSQL aislado falló igual bajo dos actualizaciones concurrentes.
- GREEN: `recordatorios_outbox.generation` es entero positivo; la clave compuesta de unicidad es turno+versión+tipo+generación. Al detectar como última una fila invalidada, el servicio conserva esa fila y crea la siguiente generación con clave idempotente propia. Una generación no invalidada se reutiliza sin duplicar.
- Serialización: actualización de consentimiento sigue usando `BEGIN IMMEDIATE` en SQLite y el mutex PostgreSQL existente. Pruebas concurrentes verifican una sola nueva generación en ambos motores.
- Compatibilidad SQLite v11: la migración explícita detecta un outbox anterior sin `generation`, lo reconstruye transaccionalmente, asigna generación 1 a las filas existentes y conserva IDs, estados, claves y referencias. Test focal: `.venv/Scripts/python.exe -m unittest tests.test_recordatorios_migracion -q` — 4 OK.
- PostgreSQL Alembic 0012 incluye default 1, restricción positiva y unicidad con generación. Los tests comprueban valor inicial, rechazo de generación 0 y aceptación de generaciones distintas para el mismo turno/versión/tipo.
- Backup/restore: no se agrega tabla ni cambia la whitelist; la generación forma parte de la misma tabla outbox. Tests SQLite y PostgreSQL restauran filas de generaciones 1 y 2, estados/recuentos y claves en un destino nuevo.
- Pruebas focales de consentimiento, reprogramación, migraciones, schema y backup SQLite/PostgreSQL: 66 OK.
- Revalidación completa posterior al fix: backend `.venv/Scripts/python.exe -m unittest discover -s tests -q` — 517 OK y 3 skips; frontend `npm test -- --run` — 10 archivos/58 OK; `npm run build` — TypeScript y Vite OK; `openspec validate --all --strict` — 18/18 specs OK.
- La spec principal y el delta archivado `appointment-reminders` describen la generación para reconsentimiento y la concurrencia. La tarea archivada 3.4 registra los tests de ambos motores y la preservación en backup.
