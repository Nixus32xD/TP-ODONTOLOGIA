# Evidencia técnica C-06 — Catálogos de recursos

Fecha: 2026-11-02. Datos y nombres de prueba exclusivamente ficticios. Esta evidencia registra validación automatizada local; no acredita revisión docente ni prueba visual de producción.

## Alcance verificado

- Catálogos paginados de profesionales, boxes y prestaciones, con alta, consulta por ID y actualización.
- Administrador y Recepción crean, consultan y editan datos descriptivos; sólo Administrador modifica el estado activo.
- SQLite v4 y Alembic `20261102_0005_resource_catalogs` conservan turnos e IDs seed y asignan nombres demostrativos estables a profesionales y boxes.
- La duración de prestación es un entero positivo en minutos hasta 2.147.483.647. C-01 no recibe `prestacion_id`, no calcula la duración del turno y no impone compatibilidades.
- Nuevos turnos rechazan pacientes, profesionales y boxes inactivos. Las referencias desconocidas se detectan antes de evaluar estados y los turnos previos se conservan.
- Los eventos de catálogo guardan sólo fecha, actor, acción, tipo, ID opaco y resultado. Si falla la auditoría, la transacción revierte la mutación.

## Evidencia TDD

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1 | `backend/tests/test_catalogos.py` | Servicio | Suite previa C-06: 159/159 | `ModuleNotFoundError: odontologia.catalogos` | CRUD de los tres catálogos y validaciones en verde | IDs seed, paginación, estado lógico, 404, longitudes y duración | Validación y sesión transaccional compartidas por tipo |
| 1.2 | `backend/tests/test_catalogos_migracion.py` | Esquema/migración | Suite previa C-06: 159/159 | Versión SQLite 3 en vez de 4 y ausencia de tabla/modelo `prestaciones` | 2/2 pruebas de esquema/migración; suite focal relacionada 30/30 | Preserva IDs/turnos, verifica nombres de seed y ausencia de `prestacion_id` | Migraciones aditivas; downgrade destructivo bloqueado |
| 1.3 | `backend/tests/test_catalogos.py` | Servicio | Suite previa C-06: 159/159 | Import del servicio nuevo ausente | CRUD y límites en verde | Casos válido, inválido, límite, baja/reactivación idempotente y desconocido | Servicio común con reglas de campos explícitas |
| 1.4 | KB y README | Documentación | Revisión del contenido previo | N/A: tarea documental | Modelos y reglas contrastados con contratos OpenAPI | Ejemplos ficticios; prestaciones separadas del turno | N/A |
| 2.1 | `backend/tests/test_api_catalogos.py`, `backend/tests/test_api.py` | API/OpenAPI | Suite previa C-06: 159/159 | Rutas nuevas respondían 404 antes de exponerlas | Rutas, validación, permisos, paginación y OpenAPI en verde | Tres recursos, estados Admin-only, anonimato, inputs extra y turno C-01 sin prestación | Modelos HTTP estrictos y errores consistentes |
| 2.2 | `backend/tests/test_catalogos.py`, `backend/tests/test_auditoria.py`, `backend/tests/test_postgresql_integracion.py` | Servicio/esquema/integración | Suite previa C-06: 159/159 | Evento C-06 rechazado por no pertenecer a la matriz cerrada | Auditoría SQLite y PostgreSQL en la suite final | Altas, ediciones, baja/reactivación, metadatos y rollback por fallo | Matriz sincronizada entre helper, DDL y modelo Alembic |
| 2.3 | `backend/tests/test_api_catalogos.py`, README y esta evidencia | Documentación/OpenAPI | Suite previa C-06: 159/159 | La aserción OpenAPI existente falló al detectar rutas nuevas no documentadas en su lista esperada | Rutas, límites de campos y ausencia de `prestacion_id` verificados | Ejemplos y versión de esquema coherentes entre API, KB y README | N/A |
| 3.1 | `backend/tests/test_api_catalogos.py`, `backend/tests/test_postgresql_integracion.py` | Integración SQLite/PostgreSQL | Suite previa C-06: 159/159 | Alta SQLite aceptada (201) con profesional inactivo; no daba el 409 esperado | Casos de profesional/box inactivos pasan en ambos motores | Referencia desconocida gana a estado inactivo; ningún turno rechazado se inserta; historial se conserva | Validación separada: existencia de todas las referencias y luego estados |
| 3.2 | Suite completa, `pip check`, OpenSpec y diff | Validación | Baseline previo: 159 tests | La suite SQLite detectó una aserción de privacidad frágil que confundía dígitos del UUID con duración | SQLite: 155 tests, 154 OK y 1 integración PostgreSQL omitida por no configurar DB; PostgreSQL aislado: 173/173 OK | Integración y concurrencia incluidas en PostgreSQL aislado | `pip check` sin dependencias rotas; OpenSpec 7/7; `git diff --check` limpio |

## Comandos ejecutados

- SQLite: `backend\.venv\Scripts\python.exe -m unittest discover -s tests -q` — 155 tests, 154 OK, 1 PostgreSQL omitido al no configurar `ODONTOLOGIA_TEST_DATABASE_URL`.
- PostgreSQL aislado: `backend\.venv\Scripts\python.exe -m unittest discover -s tests -q` con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test` — 173 tests, OK, 0 omitidos.
- Dependencias: `backend\.venv\Scripts\python.exe -m pip check` — `No broken requirements found.`
- OpenSpec: `openspec validate --all --strict` — 7 pasados, 0 fallidos.
- Diff: `git diff --check` — sin errores de whitespace; Git sólo advirtió conversión LF/CRLF del checkout Windows.

El PostgreSQL de prueba se ejecutó en un clúster temporal aislado y quedó detenido. El servicio local habitual no se modificó. El change sigue abierto en OpenSpec: no se archivó, comiteó ni publicó.
