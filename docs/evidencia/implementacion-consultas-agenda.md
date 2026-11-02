# Evidencia de implementación C-08 — consultas de agenda y disponibilidad

Fecha: 2026-11-02. Apply implementado y validado; C-08 aún no se archivó ni comiteó. Esta evidencia separa pruebas automatizadas de revisión humana y aceptación académica.

## Contratos implementados

- `GET /turnos` exige `desde` y `hasta` con offset explícito, consulta el intervalo semiabierto de hasta 31 días, ordena por inicio e ID, permite filtros por profesional/box/estado y paginación de 1 a 100.
- Administrador y Recepción reciben datos operativos sin teléfono. Profesional consulta únicamente el ID vinculado y recibe inicio, fin y nombre del paciente.
- Administrador asigna una ficha profesional activa a una sola cuenta. SQLite v7 y PostgreSQL Alembic `20261102_0008_professional_accounts` conservan las cuentas existentes sin vínculo. Cambiar rol o vínculo revoca sesiones; JWT e identidad comparan el ID asociado con el dato actual.
- `GET /disponibilidad` propone candidatos cada 15 minutos en `America/Argentina/Mendoza`, ajustados por horarios y excepciones C-07, recursos activos, bloqueos y ocupación C-09. No crea turnos ni auditoría; `POST /turnos` sigue validando dentro de su transacción.
- Profesional no puede escribir turnos ni operar catálogos/cuentas. Las consultas C-08 no habilitan reprogramación ni borrado físico y C-01 standalone conserva su compatibilidad.

## Evidencia TDD

| Tarea | RED observado | GREEN y triangulación |
|---|---|---|
| 1.1 | No aplica: baseline previa a cambios. | SQLite 222 tests OK, 1 PostgreSQL omitido; PostgreSQL aislado 251/251 OK. |
| 1.2–1.3 | Migración/validación fallaron al faltar el vínculo y seguir en revisión previa. | SQLite v6→v7 y Alembic 0007→0008 preservan usuarios, sesiones/eventos; casos FK, único, CHECK y columna faltante verificados. Regresión de migraciones: 26/26. |
| 2.1 | Alta Profesional falló inicialmente por argumento `profesional_id` no admitido. | `tests.test_usuarios_profesional` verifica alta activa, inexistente/inactiva, incompatibilidad y duplicación: 3/3. |
| 2.2 | `actualizar_usuario` no admitía el vínculo; cambiar rol a Profesional sin vínculo terminaba en 503 por CHECK en lugar de 422. La API rechazaba el campo adicional. | `test_api_auth`, `test_usuarios_profesional`, `test_auth_usuarios`: 17/17; asignación/reasignación/retirada, revocación de sesiones, unicidad, último Administrador y endpoints PATCH/POST. |
| 2.3 | JWT/sesión no incluían vínculo y la prueba mostró que Profesional podía crear turno (201). | `test_auth_sesiones` + `test_api_auth`: 13/13; claim e identidad comparados, vínculo faltante/cambiado rechazado, creación devuelve 403 sin insertar. |
| 3.1–3.2 | El import de servicio faltaba y luego la ruta GET respondía 405. | Servicio paginado `test_consulta_turnos`: 3/3; API y servicio: 12/12, rango/filtros, 403/404/422, proyección y no auditoría. |
| 4.1–4.2 | Faltaba el servicio de sugerencias; la API aún no tenía ruta y el servicio no aceptaba scoping de Profesional. | `test_consulta_disponibilidad`: 5/5, casos de turnos reservados/confirmados, terminales, bloqueos, excepciones, recursos inactivos, entrada inválida, vínculo ajeno y fin exacto a medianoche. `test_api_auth` + servicios existentes de C-07: 25/25, con no mutación/auditoría y OpenAPI. |

La suite C-01 de OpenAPI falló inicialmente porque esperaba el conjunto de rutas anterior. Se actualizó la expectativa para `GET /turnos` y `GET /disponibilidad`; el test específico pasó. La primera suite PostgreSQL completa encontró fixtures que restauraban Alembic a 0007 después de simular revisión inválida; se actualizaron para restaurar 0008, y la suite completa volvió a ejecutarse en verde.

Una revisión posterior reportó que el candidato local `23:45–00:00` podía quedar excluido. Se agregó y ejecutó primero una prueba con horario de ambos recursos `23:45–24:00` y duración de 15 minutos; pasó antes de cualquier cambio de producción. El helper C-07 ya contempla fin exactamente a las 00:00 del día siguiente. La revisión reveló cobertura faltante, no un defecto reproducible; se conserva el comportamiento actual y se documenta el caso límite.

## Validación final

Ejecutado desde `backend/` con el entorno temporal Python 3.13. El aviso deprecado de `starlette.testclient`/HTTPX se muestra pero no impide las pruebas.

| Comando | Resultado |
|---|---|
| `python -m unittest discover -s tests -q` sin URL PG | 244 tests, OK; 1 prueba de integración PostgreSQL omitida por diseño. |
| Suite completa con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_test` | 275/275 tests OK; migraciones desde cero hasta Alembic 0008 incluidas. |
| `python -m pip check` | `No broken requirements found.` |
| `openspec validate --all --strict` | 10/10 items válidos, 0 fallidos. |
| `git diff --check` | Sin errores de whitespace. |

PostgreSQL temporal se ejecutó en loopback `127.0.0.1:55432`, puerto distinto del servicio local 5432. Tras incorporar el test de límite exacto a medianoche, se repitieron ambas suites completas; el servicio se detuvo después de las pruebas, `pg_ctl status` informó `no server running` y no quedó listener en 55432. No hubo push, publicación, commit ni Archive. El informe Discovery preexistente se preservó.

## Límite de evidencia

Las pruebas y el OpenAPI acreditan el contrato automatizado del backend. No acreditan revisión humana del código, prueba visual de Swagger, aceptación docente ni uso con datos reales.
