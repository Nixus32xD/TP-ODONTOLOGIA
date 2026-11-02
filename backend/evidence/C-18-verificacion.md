# Evidencia C-18 — Portal sintético de autoservicio

## Alcance y límites

C-18 incorpora un portal local para cuentas de paciente vinculadas por Administrador a fichas ficticias. No hay autorregistro, verificación, invitaciones ni comunicación externa. La duración de 30 minutos se limita a esta demo; no define la duración general de las prestaciones. Esta evidencia no acredita preparación productiva, uso con pacientes reales ni aceptación docente.

## Baseline previo

Antes de implementar C-18 se registró el siguiente estado:

| Área | Comando | Resultado |
|---|---|---|
| Backend | `.venv/Scripts/python.exe -m unittest discover -s tests -v` | 467 tests OK; 9 skips del host/entorno. |
| Frontend | `npm test -- --reporter=dot` | 10 archivos / 58 tests OK. |
| Build frontend | `npm run build` | TypeScript y Vite OK. |
| OpenSpec | `openspec validate habilitar-reserva-del-paciente --strict` | OK antes de Apply. |

## Persistencia y migraciones

- SQLite sube de v11 a v12: `usuarios.paciente_id` es único y la tabla `idempotencia_portal_paciente` persiste claves por paciente/operación. Las filas previas de cuentas, sesiones, auditoría y turnos se conservan.
- PostgreSQL aplica Alembic `20261102_0012_appointment_reminders` → `20261102_0013_patient_self_service`; constraints preservan acciones de horarios/excepciones/bloqueos además de las nuevas acciones del portal.
- RED/GREEN: las pruebas de upgrade SQLite/PG fallaron antes de agregar vínculo/tabla; una prueba PG adicional reprodujo que el primer ajuste del catálogo de auditoría omitía acciones históricas C-07. Se restauraron esas acciones y sus combinaciones en Alembic/modelo antes de continuar.
- `tests.test_auth_sqlite_migration`, `tests.test_patient_self_service_migration_postgresql_integracion`, `tests.test_postgres_schema`: resultados focales registrados abajo tras la última corrida.

## Cuenta y sesión

El Administrador puede crear cuentas `paciente` sólo para una ficha activa no vinculada. La respuesta no expone hash ni token. La sesión incluye el `paciente_id` vigente; el login falla genéricamente ante vínculos inválidos y la sesión se invalida si el vínculo cambia. Los tests focales `test_auth_sesiones`, `test_usuarios_profesional` y `test_api_auth` se ejecutaron con 32 tests OK.

## API y reglas del portal

- `GET /portal/disponibilidad?fecha=...` entrega sólo `inicio`/`fin` para franjas conjuntas de 30 minutos dentro del horizonte local máximo de 31 días.
- `GET /mis-turnos` deriva el titular del principal y devuelve únicamente id opaco de turno, fechas, estado y versión.
- `POST /mis-turnos`, `/mis-turnos/{id}/cancelacion` y `/mis-turnos/{id}/reprogramacion` usan `Idempotency-Key` persistida; payload distinto devuelve 409. No se acepta `paciente_id` del cuerpo.
- La reserva escoge profesional/box internamente, serializa con el mutex vigente y permite hasta tres turnos futuros activos. Cancelación/reprogramación exigen 24 horas, titularidad, estado y versión válidos.
- El desconocido y el ajeno dan el mismo 404 antes de buscar/retornar idempotencia. Recepción, Administrador y Profesional reciben 403 para el portal.
- Eventos guardan metadatos opacos únicamente. Si falla auditoría, no se devuelve la lectura y se revierte mutación y clave.

Pruebas focales SQLite/API: `tests.test_portal_paciente` y `tests.test_api_portal_paciente` — 15 tests OK. PostgreSQL 18 aislado en `127.0.0.1:55432`, base `odontologia_c16_test` (`*_test`), schemas efímeros propios: migración, operaciones del portal y backup/restore C-18 — 5 tests OK, incluida la concurrencia por franja (una reserva exitosa y una 409) y replay vencido.

## Backup y restore

- SQLite: whitelist y manifiesto actualizados a v12; `tests.test_backup_manifest tests.test_backup_sqlite tests.test_backup_restore_sqlite` — 25 tests OK, 1 skip por symlink no disponible en Windows.
- PostgreSQL: bundle/restore con `pg_dump`/`pg_restore` 18, schema sintético fuente y base destino `_test` nueva. `tests.test_backup_portal_paciente_postgresql_integracion` — 1 test OK; vínculo `usuarios.paciente_id`, clave idempotente y todos los recuentos se conservan. El manifiesto no expone el nombre ni el ID de paciente.
- Se usó el PATH de cliente sólo para el proceso de test: `C:\Program Files\PostgreSQL\18\bin`; no se alteró configuración global. No se usó el puerto 5432 ni Docker.

## Interfaz

La UI acepta el rol `paciente` y presenta un panel separado para consultar turnos, disponibilidad, reservar, cancelar y reprogramar. El rol paciente no monta Agenda, Atenciones Clínicas ni Catálogos. Pruebas frontend focales: `src/auth/session.test.tsx`, `src/App.test.tsx` y `src/pages/PortalPaciente.test.tsx` — 3 archivos / 16 tests OK. `PortalPaciente.test.tsx` verifica cambio de fecha y respuesta tardía, reuso de clave tras timeout ambiguo, clave nueva para otro slot y separación entre reprogramación y cancelación. La suite frontend completa pasó en 11 archivos / 66 tests y el build de TypeScript/Vite terminó correctamente.

Se levantó una demo efímera e independiente con SQLite sintético en `%TEMP%\odontologia-c18-paciente-20261102`, API en `http://127.0.0.1:8280` y Vite en `http://127.0.0.1:5174` (proxy hacia la API en 8280). Se verificaron por HTTP el login de la cuenta sintética, el listado vacío inicial, la disponibilidad mínima y una reserva ficticia que aparece en `GET /mis-turnos`. `/health`, `/openapi.json` y la portada de Vite respondieron 200.

La inspección visual manual posterior de root en una pestaña IAB nueva confirmó login sintético y vista limitada al turno propio. Al cambiar la fecha con el control nativo (04→05 mediante ArrowUp), las opciones mostraron 5 de noviembre y desaparecieron las franjas anteriores del 3/4 de noviembre. No se realizó ni se afirma una nueva reserva durante esa comprobación. Para la prueba automatizada headless, el control se cambió con Playwright `fill`, que sí dispara el `change` de React; el request proxied fue `fecha=2026-11-04` y las opciones resultantes correspondieron al 4 de noviembre.

## Validación final

### Revisión crítica posterior al archive

Se corrigieron dos defectos detectados en revisión independiente:

- El backend ahora parsea y canoniza el payload para fingerprint, comprueba autenticación/titularidad y consulta idempotencia antes de validar vigencia/horizonte para comandos nuevos. Un replay confirmado devuelve su resultado original aunque la fecha haya pasado o exceda el horizonte actual; payload conflictivo sigue dando 409 y una cuenta ajena 404.
- La UI conserva la clave por operación+objetivo+payload ante errores ambiguos, crea otra cuando cambia el comando o payload y la descarta sólo después de completar el comando y actualizar la vista.

RED/GREEN focal: los tests SQLite `test_reserva_replay_no_revalida_vigencia_ni_horizonte` y `test_reprogramacion_replay_vencido_preserva_conflicto_y_verifica_titularidad`, y el test PostgreSQL `test_replays_vencidos_preservan_idempotencia_conflictos_y_titularidad` reprodujeron primero el 422 incorrecto; después pasaron. En frontend, `reutiliza la clave tras una respuesta ambigua...` reprodujo primero una clave distinta al reintentar; luego pasó junto con el caso de cambio de operación.

| Área | Comando | Resultado |
|---|---|---|
| Backend completo | `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_c16_test; .venv/Scripts/python.exe -m unittest discover -s tests -q` | 544 tests OK; 3 skips del entorno, en 138.747 s. |
| Focal portal SQLite/API | `.venv/Scripts/python.exe -m unittest tests.test_portal_paciente tests.test_api_portal_paciente -q` | 15 tests OK. |
| Focal PostgreSQL C-18 | `.venv/Scripts/python.exe -m unittest tests.test_patient_self_service_migration_postgresql_integracion tests.test_portal_paciente_postgresql_integracion tests.test_backup_portal_paciente_postgresql_integracion -q` | 5 tests OK en PostgreSQL 18 aislado, puerto 55432. |
| Frontend completo | `npm test -- --run` | 11 archivos / 66 tests OK. |
| Portal frontend focal | `npm test -- --run src/pages/PortalPaciente.test.tsx` | 6 tests OK. |
| Build | `npm run build` | TypeScript y Vite OK. |
| OpenSpec | `openspec validate --all --strict` | 19 specs válidas; sin cambios activos. |

No se usó Docker, Redis, proveedores externos ni el puerto PostgreSQL 5432. La comprobación visual manual quedó completada por root; la reserva observada era la ficha sintética preexistente en la base efímera.
