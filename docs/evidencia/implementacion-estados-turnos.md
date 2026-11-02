# Evidencia de implementación C-09 — ciclo de vida de turnos

## Alcance aplicado

Se agregó estado restringido en turnos migrados: `reservado`, `confirmado`, `atendido`, `ausente` y `cancelado`. La migración SQLite v6 y Alembic `20261102_0007_turn_status` asignan `reservado` a las filas previas, preservando sus IDs, referencias e intervalos. Ambas también habilitan la acción metadata-only `turno.estado_actualizado`; SQLite reconstruye la tabla append-only y conserva eventos existentes, mientras PostgreSQL amplía las constraints de acción y combinación.

Sólo `reservado` y `confirmado` ocupan profesional y box. Los estados terminales conservan el historial. Las transiciones son `reservado`→`confirmado`/`cancelado` y `confirmado`→`atendido`/`ausente`/`cancelado`; no se reprograman turnos. Administrador y Recepción usan `POST /turnos/{id}/confirmacion`, `/cancelacion`, `/atencion` y `/ausencia`. Las transiciones devuelven `{id, estado}`; alta migrada devuelve `estado: reservado`. Cancelar de nuevo devuelve 200 sin una segunda mutación auditada. C-01 standalone sin migrar conserva filas sin estado y su exclusión histórica.

Las transiciones toman el mismo lock de agenda que las altas: `BEGIN IMMEDIATE` en SQLite y `AgendaMutex FOR UPDATE` en PostgreSQL. Un timeout de lock responde `agenda_ocupada` y no deja mutaciones parciales. El evento efectivo y el estado se guardan en una transacción; fallo de auditoría revierte ambos.

## Evidencia TDD por tarea

| Task | Pruebas / RED observado | GREEN y triangulación |
| --- | --- | --- |
| 1.1 | La migración SQLite fallaba al esperar v6/columna `estado`; la actualización C-07→0007 en PostgreSQL fallaba al consultar esa columna aún inexistente. | SQLite preserva el turno y rechaza estado fuera de catálogo; PostgreSQL conserva la fila C-07, aplica `reservado`, preserva evento anterior y acepta el nuevo evento de estado. |
| 1.2 | Prueba de C-01 standalone sin migración verifica ausencia de columna/versionado y conflicto original. | Pasa junto con la prueba de alta independiente. |
| 2.1 | Antes de cambiar predicados, los estados terminales causaban conflicto en SQLite y PostgreSQL; `reservado`/`confirmado` sí bloqueaban. | 5 pruebas SQLite y las de integración PG verifican los cinco estados en profesional/box; el historial se conserva. |
| 2.2 | El módulo de pruebas falló al importar el servicio todavía inexistente. | 4 pruebas cubren rutas permitidas, salto inválido, estado terminal y persistencia sin mutación ante rechazo. |
| 2.3 | Cancelar dos veces falló con `transicion_invalida`; el fallo inyectado de auditoría no producía rollback porque todavía no se registraba el evento. La prueba de migración también reprodujo el rechazo de `turno.estado_actualizado` por la constraint anterior. | 6 pruebas del servicio y migración pasan: cancelar repetidamente conserva un único evento, y una falla de auditoría mantiene `reservado`. La migración PG conserva evento histórico y admite la nueva acción. |
| 2.4 | Desviación de secuencia: las pruebas de carrera se agregaron después de implementar el uso del lock, por lo que no se registra un RED previo del mutex. Sí se escribió RED para el límite de timeout: ambos motores devolvían `almacenamiento_error`, no `agenda_ocupada`. | Carreras alta/cancelación pasan en ambos motores. SQLite aplica `busy_timeout`; SQLite y PostgreSQL mapean contención agotada a `agenda_ocupada`, sin cambiar el turno. |
| 3.1 | La nueva prueba HTTP falló porque la respuesta de alta aún no exponía `estado`. | 4 pruebas de API comprueban los cuatro destinos, esquema OpenAPI, respuesta `{id, estado}` y persistencia consultada mediante conexión nueva. |
| 3.2–3.3 | Las pruebas de permisos, turno inexistente, transición inválida e idempotencia se agregaron después de definir las rutas; no se atribuye RED previo para cada caso. | Verifican 401 sin sesión, 200 Recepción, 403 para rol Profesional, 404 inexistente, 409 sin auditoría y cancelación repetida 200 con un solo evento. |
| Hallazgo de revisión A | RED: tres pruebas SQLite fallaron porque horario, excepción y bloqueo trataban terminales como ocupantes; PostgreSQL reprodujo `turnos_afectados`. | 13 pruebas SQLite del módulo y 3 pruebas PG focalizadas pasan: sólo `reservado`/`confirmado` impiden cambios, incluidos los turnos ocupantes pasados. |
| Hallazgo de revisión B | RED: API SQLite respondió 409 y PostgreSQL 500 cuando `turnos.estado` faltaba pese a versión vigente. | API responde 503 `autenticacion_no_configurada` en ambos motores antes de mutar; se verificó que no aparece turno ni evento `turno.creado`. |

## Verificación

Comandos ejecutados desde `backend/` con el entorno Python 3.13 localizado en `%TEMP%\tp-odontologia-c07-review-venv313`:

| Verificación | Resultado |
| --- | --- |
| Baseline SQLite previo a C-09 | 200 tests OK; 1 integración PostgreSQL omitida. |
| Baseline PostgreSQL previo a C-09 | 223/223 tests OK, clúster temporal aislado. |
| `python -m unittest discover -s tests -q` sin URL PostgreSQL | 222 tests OK; 1 integración PostgreSQL omitida. |
| Misma suite con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test` | 251/251 tests OK. |
| `python -m pip check` | `No broken requirements found.` |
| `openspec validate --all --strict` tras Archive | 9 válidos, 0 fallidos. |
| `git diff --check` | Exit code 0; sólo avisos normales LF/CRLF de Windows. |

El servidor PostgreSQL temporal se inició sólo en loopback y puerto 55432, luego se detuvo (`pg_ctl status`: no server running). No se usó la instancia 5432. El aviso de deprecación de `starlette.testclient`/HTTPX permanece y no impide la suite. C-09 quedó archivado localmente; aún no hay commit ni push. La modificación previa de `docs/discovery/informe-discovery.md` se preservó sin editar.

## Pendientes

Apply, sincronización de specs y Archive están completos. Resta el commit local separado; no se hizo push.
