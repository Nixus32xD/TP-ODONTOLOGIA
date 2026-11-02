# Implementación C-10 — Reprogramación atómica

Estado: Apply en curso. Esta evidencia registra únicamente verificaciones ejecutadas; las pruebas de implementación se completarán por tarea.

## Baseline previo

| Ejecución | Comando | Resultado |
|---|---|---|
| SQLite focal | `..\.venv\Scripts\python.exe -m unittest tests.test_turno_lifecycle_migracion tests.test_turno_ciclo_vida tests.test_consulta_turnos tests.test_api_turno_ciclo_vida tests.test_auditoria -q` desde `backend/` | 38 tests, OK. |
| SQLite + PostgreSQL focal | Mismo comando más `tests.test_postgresql_integracion`, con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test` | 69 tests, OK en 27,85 s. Clúster temporal PostgreSQL 18 aislado. |

El clúster PostgreSQL temporal de C-10 está activo en `127.0.0.1:55432` para las pruebas de Apply; no se utilizó la instancia existente en el puerto 5432. Se detendrá al finalizar las validaciones.

## Evidencia TDD por tarea

### 1.2 — Versión y esquema

- **RED:** las pruebas nuevas detectaron la falta de `turnos.version`, del revisionado Alembic 0009 y de la respuesta fail-closed ante esquema PostgreSQL vigente sin vínculo de agenda; los tests focales reportaron errores/fallos antes de la implementación.
- **GREEN SQLite:** `..\\.venv\\Scripts\\python.exe -m unittest tests.test_turno_lifecycle_migracion tests.test_auth_sqlite_migration tests.test_auth_schema tests.test_postgres_schema tests.test_disponibilidad_migracion tests.test_catalogos_migracion tests.test_auditoria tests.test_api_auth -q` desde `backend/` — 62 tests, OK en 20,944 s. Incluye versión inicial, migración/preservación, auditoría permitida y 503 al faltar la columna.
- **GREEN PostgreSQL:** con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test`, `..\\.venv\\Scripts\\python.exe -m unittest tests.test_postgresql_integracion.IntegracionPostgreSQLTests.test_upgrade_desde_c08_inicializa_version_y_preserva_turno_y_auditoria tests.test_postgresql_integracion.IntegracionPostgreSQLTests.test_validador_postgresql_falla_cerrado_si_version_vigente_no_tiene_vinculo tests.test_postgresql_integracion.IntegracionPostgreSQLTests.test_api_postgresql_falla_cerrado_si_falta_version_de_turno -q` desde `backend/` — 3 tests, OK en 2,016 s. La migración 0009 parte de 0008 y conserva turno/auditoría; el validador/API rechazan fail-closed un esquema incompleto.
- **Compatibilidad:** C-01 mantiene su esquema standalone no versionado; SQLite v8 y PostgreSQL 0009 inicializan versiones migradas en 1. Las restricciones de auditoría aceptan `turno.reprogramado` sin reutilizar el evento de alta.
- **Advertencia:** apareció un `StarletteDeprecationWarning` por `httpx` en TestClient, sin fallos. Una invocación inicial de PostgreSQL contenía un nombre de clase mal tipeado; se corrigió y la corrida final de 3 tests pasó.

### 1.3 — Versión en transiciones

- **Baseline:** `..\\.venv\\Scripts\\python.exe -m unittest tests.test_turno_ciclo_vida tests.test_api_turno_ciclo_vida -q` — 12 tests, OK; PostgreSQL, pruebas focales de serialización y timeout — 2 tests, OK.
- **RED:** dos pruebas SQLite confirmaron que una transición efectiva dejaba `version` en 1 y que cancelar por primera vez tampoco generaba versión 2; la prueba PostgreSQL confirmó que confirmar dejaba la versión en 1. Las fallas fueron previas al cambio productivo.
- **GREEN SQLite:** el mismo comando de módulos de ciclo de vida y API — 14 tests, OK en 3,948 s. Se verificó reservado→confirmado→atendido (versiones 1→2→3) y cancelación repetida sin incremento adicional; las pruebas existentes de permisos, auditoría, atomicidad y timeout también pasaron.
- **GREEN PostgreSQL:** `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test` más `..\\.venv\\Scripts\\python.exe -m unittest tests.test_postgresql_integracion.IntegracionPostgreSQLTests.test_transicion_postgresql_incrementa_version_y_cancelacion_idempotente_no tests.test_postgresql_integracion.IntegracionPostgreSQLTests.test_cancelacion_postgresql_se_serializa_con_alta_concurrente tests.test_postgresql_integracion.IntegracionPostgreSQLTests.test_timeout_de_lock_transicion_postgresql_no_modifica_estado -q` — 3 tests, OK en 0,795 s.
- **Cambio mínimo:** cada transición permitida incrementa `Turno.version` dentro de la misma transacción que persiste estado y auditoría. La cancelación repetida retorna antes de mutar y conserva versión/evento.

### 1.4 — Documentación de esquema

- Se actualizó `backend/README.md`: estados actuales de C-08/C-10, revisión de migración hasta 0009, esquema SQLite v8, inicialización de versiones existentes y compatibilidad C-01 standalone sin `auth_schema_version`/`version`.
- Verificación de consistencia: `..\\.venv\\Scripts\\python.exe -m alembic heads` devuelve `20261102_0009_turn_rescheduling (head)`; `alembic history` confirma 0008→0009.
- Regresión de documentación/contrato: `..\\.venv\\Scripts\\python.exe -m unittest tests.test_turno_lifecycle_migracion tests.test_auth_schema -q` — 9 tests, OK; incluye compatibilidad C-01 y upgrade desde v7 a v8 conservando filas.
- `git diff --check -- backend/README.md openspec/changes/reprogramar-turnos-atomicamente/tasks.md docs/evidencia/implementacion-reprogramacion.md` — limpio (Git informa la conversión esperada LF/CRLF del checkout Windows).

### Hallazgo de fixture PostgreSQL tras la revisión 0009

- Al ampliar el baseline a todo `tests.test_postgresql_integracion`, el test de upgrade repetido y dos tests de revisión restauraban el número Alembic a 0008 aunque el esquema físico ya contenía la columna de 0009. La repetición intentaba crear `turnos.version` de nuevo y las fallas posteriores eran cascada por revisión fuera de sincronía.
- Se actualizaron únicamente los resets de fixtures para restaurar `20261102_0009_turn_rescheduling`. Los tres tests aislados de revisión/upgrade pasaron; luego el módulo completo PostgreSQL pasó **34/34 en 16,459 s**. No se cambió la migración ni se atribuye a un defecto productivo C-10.

### 2.1 — Rechazos y preservación

- **Baseline:** SQLite `tests.test_turno_ciclo_vida`, `test_api_turno_ciclo_vida`, `test_catalogos`, `test_pacientes` y `test_disponibilidad` — **32/32 OK**. El módulo PG inicializó el esquema correctamente, pero destapó la fixture obsoleta descrita arriba; tras corregirla pasó **34/34**.
- **RED:** las pruebas nuevas fallaron al importar la operación aún inexistente `odontologia.reprogramacion.reprogramar_turno` en SQLite y PostgreSQL. Durante la preparación también se corrigió la fixture para que el actor de auditoría opcional no referencie un usuario inexistente.
- **GREEN SQLite:** `..\\.venv\\Scripts\\python.exe -m unittest tests.test_reprogramacion -q` — **8/8 OK**. Cubre versión obsoleta, terminal, paciente inactivo, profesional inactivo, duración distinta, cruce de medianoche local, destino sin horario y bloqueo. Cada rechazo compara la fila completa/version y el conteo del evento `turno.reprogramado` antes/después.
- **GREEN PostgreSQL:** `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test` y `..\\.venv\\Scripts\\python.exe -m unittest tests.test_postgresql_integracion.IntegracionPostgreSQLTests.test_reprogramacion_postgresql_rechazos_preservan_version_y_auditoria -q` — **1/1 OK**, con siete escenarios de rechazo y preservación.
- **Detalle de zona:** el caso PG cruza medianoche local de Mendoza (02:45–03:15 UTC), no medianoche UTC; 23:45 UTC había sido una fixture incorrecta porque aún pertenece al mismo día local.
- **Alcance:** se inició `reprogramar_turno` para que los casos de rechazo pudieran ejecutarse; la operación incluye ahora el camino válido transaccional, lock común, exclusión propia y auditoría. Las tareas 2.2/2.3 deben verificar en RED/GREEN los casos exitosos, conflictos concurrentes y rollback de auditoría; se informará cualquier cobertura adelantada como desviación TDD.

### 2.2 — Operación válida y conflictos

- **SQLite:** `..\\.venv\\Scripts\\python.exe -m unittest tests.test_reprogramacion -q` — **13/13 OK**. Incluye reprogramación válida que conserva paciente/duración/estado e incrementa versión; auditoría registra sólo actor, acción, recurso, ID y resultado. Los rechazos por ocupación profesional/box conservan la fila, versión y cero eventos de reprogramación. También se verifica autoexclusión y que la identidad del paciente no impida una franja con recursos distintos.
- **PostgreSQL:** con DB aislada en 55432, tres pruebas enfocadas — **3/3 OK** para cambio con auditoría, conflicto profesional/box y exclusión del turno propio; en conflictos se compara la asignación/version y el conteo de auditoría previo/posterior.
- **Desviación TDD:** el camino que aplica una reprogramación válida quedó implementado en el mismo ciclo que el validador de rechazos de 2.1, antes de crear las pruebas 2.2. Las pruebas 2.2 se añadieron después y pasaron; no se atribuye un RED anterior para ese camino. El primer intento de auditoría PostgreSQL con actor ficticio falló por la FK real a `usuarios`; se corrigió el fixture para usar una cuenta Administrador creada, sin cambio de producción.

### 2.3 — Concurrencia y rollback de auditoría

- **RED:** se escribieron primero las pruebas focalizadas; el código de reprogramación ya contenía lock/versionado/auditoría desde el bloque 2.1, por lo que no se observó una fase RED para estos comportamientos. No se modificó código productivo para 2.3.
- **SQLite:** `..\\.venv\\Scripts\\python.exe -m unittest tests.test_reprogramacion -q` — **15/15 OK**. Dos hilos con versión 1 producen una confirmación, un `version_desactualizada`, versión final 2 y un único evento. El fallo simulado de auditoría revierte asignación, intervalo y versión.
- **PostgreSQL:** con DB aislada loopback 55432, seis pruebas C-10 — **6/6 OK**; incluye carrera concurrente con misma versión y auditoría única, y fallo de auditoría con rollback de todos los campos.
- **Contrato comprobado:** se reutiliza el lock común de AgendaMutex / `BEGIN IMMEDIATE`; se valida versión bajo ese lock, se actualiza la misma fila y se registra el evento antes del commit. Sólo los éxitos llaman al registro; la auditoría no contiene datos del paciente, destino, horario ni cuerpo.

### 2.4 — Alcance y rechazos documentados

La reprogramación conserva el paciente, duración e identidad del turno; exige estado `reservado`/`confirmado` y versión vigente; valida destino activo, disponibilidad y ocupación con intervalos `[inicio, fin)`, incluyendo excepciones y bloqueos, dentro de una transacción serializada. Los rechazos no crean evento y preservan la versión y los datos originales. El mismo paciente puede mantener otra cita simultánea si usa profesional y box distintos: C-01 sólo excluye por esos recursos. No se consulta ni se asocia prestación; C-06 no persiste `prestacion_id` y cualquier vínculo futuro requiere un change separado.

### 3.1 — API de reprogramación

- **Baseline:** API autenticación, ciclo de vida, documentación/OpenAPI y disponibilidad — **33/33 OK**.
- **RED:** antes de agregar la ruta, cuatro pruebas nuevas fallaron: alta válida, validación de cuerpo estricto, acceso sin sesión/rol y códigos de dominio devolvían 404 porque el endpoint no existía.
- **GREEN:** `..\\.venv\\Scripts\\python.exe -m unittest tests.test_api_reprogramacion -q` — **4/4 OK**. Revisión posterior detectó que la prueba OpenAPI global mantenía una lista cerrada de rutas; se añadió la ruta nueva a la expectativa, sin cambios funcionales adicionales. `..\\.venv\\Scripts\\python.exe -m unittest tests.test_api.ApiTests.test_openapi_y_docs tests.test_api_reprogramacion -q` — **5/5 OK**.
- La ruta `POST /turnos/{turno_id}/reprogramacion` acepta sólo `version`, `inicio`, `fin`, `profesional_id` y `box_id`; Admin y Recepción pueden usarla; requiere sesión, devuelve `version` nueva y datos del turno; el rol Profesional obtiene 403. Se verificaron 404 turno inexistente, 409 versión obsoleta/terminal, 422 contrato inválido y las respuestas OpenAPI.
- Permanece el warning upstream de Starlette/httpx observado en otras pruebas; no afecta resultados.

### 3.2 — Proyección de versión por rol

- **Baseline:** `tests.test_consulta_turnos` + consulta de API por rol — **4/4 OK** antes de exigir `version`.
- **RED:** al agregar expectativas, el servicio y API no incluían `version` en los resultados operativos; dos pruebas fallaron con clave ausente. La proyección Profesional existente seguía limitada a `inicio`, `fin` y `paciente_nombre`.
- **GREEN:** `..\\.venv\\Scripts\\python.exe -m unittest tests.test_consulta_turnos tests.test_api_auth.ApiAutenticacionTests.test_consulta_turnos_paginada_por_personal_y_limitada_al_vinculo_profesional -q` — **4/4 OK**. Administrador y Recepción reciben `version=1`; Profesional conserva el conjunto exacto de tres campos y no recibe `version`.
- Cambio limitado a añadir `version` en la rama operativa del listado; no se alteraron campos de privacidad ni la proyección Profesional.

### 3.3 — README y OpenAPI

- **RED:** el test de contrato descubrió que `RespuestaReprogramacion` no publicaba un ejemplo de respuesta en OpenAPI; faltaba el atributo `examples`.
- **GREEN:** se agregó ejemplo de respuesta versionada al modelo y se verificaron el ejemplo de request estricto, los campos requeridos, la respuesta documentada y su versión positiva. `..\\.venv\\Scripts\\python.exe -m unittest tests.test_api_reprogramacion -q` — **4/4 OK**.
- `backend/README.md` ahora documenta el cuerpo exacto, roles, versión precondición, invariantes de paciente/duración/estado, validación de disponibilidad, errores y recarga/revisión de agenda ante `409 version_desactualizada`. La ruta publica sus ejemplos y respuestas en `/docs` y `/openapi.json`.

### 4.1 — Suites completas

- SQLite: `..\\.venv\\Scripts\\python.exe -m unittest discover -s tests -q` — **271 tests, OK** (83,056 s); PostgreSQL se omitió al no configurar la URL en ese proceso.
- PostgreSQL aislado: mismo comando con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test` — **312 tests, OK** (99,767 s; 0 omitidos). Clúster PostgreSQL temporal 18 en loopback; puerto 5432 quedó fuera de alcance.
- Ambas suites incluyen regresión C-01, migraciones, API, versionado, rechazos, conflictos, concurrencia y rollback de auditoría.

### Seguimiento de revisión — fin local exacto a medianoche

- **RED:** pruebas SQLite y PostgreSQL para una reprogramación 23:30–00:00 local en el tramo 23:00–24:00 fallaron en el guard de fecha, antes de validar el horario.
- **GREEN focal:** se acepta una fecha local posterior sólo cuando el fin es exactamente 00:00; `turno_cabe_en_tramos` comprueba el límite 1440 en el tramo del día inicial. Las pruebas focales verifican que un intervalo que sigue después de 00:00 se rechace. SQLite `tests.test_reprogramacion`: **16/16 OK**; PostgreSQL límite exacto + cruce inválido: **2/2 OK**.
- **Regresión completa tras el cambio de lógica:** SQLite **271 tests OK**; PostgreSQL aislado **312 tests OK**. La prueba no habilita un cruce de medianoche: únicamente permite el fin exacto del tramo C-07 a 24:00.

### 4.2 — Verificación y cierre de Apply

- `..\\.venv\\Scripts\\python.exe -m pip check` — `No broken requirements found.`
- `openspec validate reprogramar-turnos-atomicamente --strict` — `Change 'reprogramar-turnos-atomicamente' is valid`.
- `git diff --check` — código de salida 0, sin errores de whitespace; Git sólo mostró avisos de conversión LF/CRLF del checkout Windows.
- PostgreSQL temporal: `pg_ctl -D C:\\Users\\Oficina\\AppData\\Local\\Temp\\tp_odontologia_c10_pgdata_20261102 status` confirmó el servidor activo antes de detenerlo; `pg_ctl ... stop -m fast` finalizó correctamente y el status posterior indicó `no server running`. El puerto 55432 no tiene listener; la instancia preexistente de 5432 permanece activa, PID 7328.
- C-10 quedó aplicado, validado, archivado y sincronizado localmente en OpenSpec. No se publicó. `docs/discovery/informe-discovery.md` se preservó sin editar durante este Apply.
