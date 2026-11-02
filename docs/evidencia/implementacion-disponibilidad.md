# Evidencia de implementación C-07 — horarios y bloqueos

Fecha de validación: 2026-11-02. El change continúa activo en OpenSpec; esta evidencia registra Apply, no Archive.

## Alcance realizado

- Horarios semanales por profesional y box, en `America/Argentina/Mendoza`, con varios tramos diarios, sin cruces de medianoche.
- Excepciones por fecha que reemplazan el horario semanal del recurso; una excepción vacía cierra ese día.
- Bloqueos UTC asignados exactamente a un profesional o a un box.
- API autenticada para Administrador y Recepción, paginación de bloqueos y auditoría de metadatos en la misma transacción.
- Reservas nuevas requieren horario vigente de ambos recursos y ausencia de bloqueos.
- Un cambio de horario o excepción se valida contra todos los turnos (pasados y futuros) del recurso que se está editando. Así, una agenda C-01 importada puede configurarse por etapas: primero profesional y luego box. La nueva reserva sigue exigiendo ambos horarios. Los bloqueos que se solapan directamente con turnos existentes se rechazan.
- SQLite v5 sólo activa disponibilidad tras migración explícita; las bases SQLite C-01 standalone sin `auth_schema_version` conservan su comportamiento histórico. La API valida versión y tablas requeridas y falla cerrada con 503 si el esquema declarado está incompleto.

## Pruebas y validaciones

Ejecutadas desde `N:\Nueva carpeta\TP-ODONTOLOGIA\backend` con el Python de `..\.venv`:

| Comando | Resultado |
|---|---|
| `..\.venv\Scripts\python.exe -m unittest discover -s tests -q` (sin `ODONTOLOGIA_TEST_DATABASE_URL`) | 199 tests, OK; 1 integración PostgreSQL omitida por diseño. |
| `$env:ODONTOLOGIA_TEST_DATABASE_URL='postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test'; ..\.venv\Scripts\python.exe -m unittest discover -s tests -q` | 222 tests, OK, contra PostgreSQL temporal aislado. |
| `..\.venv\Scripts\python.exe -m pip check` | `No broken requirements found.` |
| `..\.venv\Scripts\python.exe -c "from zoneinfo import ZoneInfo; print(ZoneInfo('America/Argentina/Mendoza'))"` | Carga IANA confirmada mediante `tzdata`. |
| `openspec validate --all --strict` | 8/8 items válidos, 0 fallidos. |
| `git diff --check` | Sin errores de whitespace. Git mostró advertencias normales de conversión LF/CRLF en el checkout Windows. |

PostgreSQL usó puerto loopback `55432` y base `odontologia_test`; el servicio preexistente en `5432` no se usó. La verificación de apagado del clúster temporal se completó al finalizar (puerto 55432 libre). No se utilizaron servicios externos reales.

## Evidencia TDD por tareas

La secuencia observada se consigna sin atribuir RED/GREEN a pruebas que ya estaban implementadas al retomar el change. Cada fila representa el ciclo verificable disponible en el historial de trabajo de C-07; algunas tareas integradoras reutilizan el lock de agenda existente y por eso validan sus carreras, sin afirmar que el lock original se haya creado mediante RED en esta tarea.

| Task | Pruebas principales | RED/GREEN y triangulación | Refactor / estado |
|---|---|---|---|
| 1.1–1.2 | `test_disponibilidad_migracion.py`, `test_postgres_schema.py`, `test_postgresql_integracion.py` | Las pruebas de versión, tablas/FKs y upgrade de SQLite/PostgreSQL identificaron fallos antes de ajustar DDL/migraciones; luego pasan preservando turnos e IDs. | Validado en ambos motores. |
| 1.3 | `test_disponibilidad_migracion.py` | Prueba de carga IANA y dependencia portable; después carga `America/Argentina/Mendoza` en el entorno Windows. | Pin aplicado a requisitos y lock; pip check limpio. |
| 2.1–2.3 | `test_disponibilidad_servicios.py`, `test_disponibilidad_migracion.py` | Casos válidos, inválidos, límites y CRUD; el historial disponible no permite asegurar que cada operación CRUD haya tenido un test RED separado antes de toda su implementación. | Servicios y modelos verificados en SQLite; README coincide con contratos. |
| 3.1 | `test_api_disponibilidad.py` | Autenticación, roles, cuerpos, errores y paginación cubiertos. Al retomar, varias rutas ya estaban implementadas; no se atribuye RED previo para cada endpoint. | Respuestas y OpenAPI verificadas, incluido `/docs`. |
| 3.2 | `test_api_disponibilidad.py`, `test_disponibilidad_servicios.py`, `test_postgresql_integracion.py` | Casos de auditoría metadata-only y rollback; la prueba del helper de auditoría falló antes de ajustar la matriz exacta y luego pasó. | Atomicidad verificada en SQLite y PostgreSQL. |
| 3.3 | `test_api_disponibilidad.py` | Prueba de ejemplos OpenAPI/JSON falló antes de documentar los esquemas y luego pasó. | `/openapi.json` y `/docs` comprobados. |
| 4.1 | `test_alta_disponibilidad.py` | RED en conversión UTC/local, agendas cerradas, ambos recursos y casos de bloqueo; GREEN y triangulación para excepciones, medianoche, legacy C-01 y concurrencia SQLite. | 12 casos de disponibilidad pasan. |
| 4.2 | `test_disponibilidad_servicios.py`, `test_disponibilidad_migracion.py` | Primero falló permitir cambios incompatibles y la configuración progresiva con turnos importados; implementación valida el recurso objetivo, conservando el contrato 409 para turnos afectados. Se verifican turnos pasados/futuros, rollback y configuración profesional→box. | 9 tests de servicio y prueba de migración progresiva pasan. |
| 4.3 | `test_alta_disponibilidad.py`, `test_postgresql_integracion.py` | Se ejercitan carreras reserva/configuración y los dos órdenes en SQLite, además de `AgendaMutex` en PostgreSQL. El mutex se reutiliza desde C-01; no se presenta su creación como RED de C-07. | Suites completas pasan en ambos motores. |
| 5.1 | Suites completas | SQLite: 199 tests, 1 omitido; PostgreSQL aislado: 222 tests, 0 fallidos. | pip, IANA, OpenSpec strict y diff-check limpios. |

## Límites y estado

La verificación acredita pruebas locales automatizadas y contrato OpenAPI, no una revisión visual completa del producto ni aceptación docente. C-07 no se archivó, no se comiteó y no se publicó. La modificación preexistente de `docs/discovery/informe-discovery.md` se preserva fuera del alcance; no se incorporó a esta evidencia.
