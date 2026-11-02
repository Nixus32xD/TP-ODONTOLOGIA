# Tasks

## 1. Revalidación de nomenclatura y base de pruebas

- [x] 1.1 Comprobar en las fuentes oficiales el estado vigente de ISO 3950 y el subconjunto de códigos HL7 FDI; registrar edición, URL y códigos contrastados en `backend/evidence/C-16-verificacion.md`, usando URL canónica y aclarando que el CodeSystem no es exhaustivo.
- [x] 1.2 Ejecutar y registrar baseline de backend (`.venv/Scripts/python.exe -m unittest discover -s tests -v`, desde `backend/`) y frontend (`npm test`, desde `frontend/`); documentar los 5 skips de integración sin URL y el aislamiento PostgreSQL local previsto en puerto 55432, nombre `*_test`, sin Docker ni Redis.

## 2. Persistencia y migraciones aditivas

- [x] 2.1 Escribir primero pruebas RED para tablas, claves foráneas, restricciones y conservación de versiones/etapas; implementar modelos SQLAlchemy de odontograma y planes y lograr GREEN en SQLite con `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_odontograma_modelos.py" -v` (RED import missing classes; GREEN 5/5).
- [x] 2.2 Escribir prueba RED de upgrade SQLite v9→v10 sobre una copia sintética C-15; agregar migración aditiva preservando filas y lograr GREEN con `python -m unittest discover -s tests -p "test_*migracion*" -v` desde `backend/`.
- [x] 2.3 Escribir pruebas RED de upgrade PostgreSQL desde Alembic 0010 y restricciones/FK/append-only; implementar revisión 0011 y verificar en PostgreSQL aislado de test (localhost, puerto 55432, base `*_test`) con `python -m unittest discover -s tests -p "test_*odontograma*postgresql*" -v` y `alembic upgrade head`.
- [x] 2.4 Documentar las versiones SQLite/PostgreSQL, prerequisitos y migración explícita en `backend/README.md`; verificar que los comandos documentados aplican al menos el upgrade SQLite de una base sintética y que el arranque de FastAPI no migra.

## 3. Odontograma versionado

- [x] 3.1 Escribir pruebas RED de códigos FDI/ISO, dentición primaria/permanente, superficies individuales y compatibilidad anterior/posterior; implementar validación pura, observación opcional <=500 y errores 422, y lograr GREEN más casos límite con `python -m unittest discover -s tests -p "test_*odontograma*" -v`.
- [x] 3.2 Escribir pruebas RED de snapshots completos, secuencia por paciente/profesional, consulta de vigente/historial y corrección append-only; implementar servicio transaccional que conserve versiones previas y lograr GREEN con el mismo patrón unittest.
- [x] 3.3 Agregar rutas FastAPI de consulta y nueva versión, con respuestas y errores documentados en OpenAPI; cubrir escenario válido, entradas inválidas, turno no atendido y aislamiento entre profesionales con `python -m unittest discover -s tests -p "test_api_odontograma*.py" -v`.
- [x] 3.4 Documentar el flujo API y ejemplos exclusivamente sintéticos en `backend/README.md`; verificar que OpenAPI publica los esquemas sin ejemplos de información clínica real.

## 4. Planes manuales

- [x] 4.1 Escribir pruebas RED de alta con etapas ordenadas y prestaciones activas, rechazo de prestaciones ausentes/inactivas, inmutabilidad de etapas y conservación de referencias a prestaciones luego desactivadas; implementar servicio y lograr GREEN con `python -m unittest discover -s tests -p "test_*planes*" -v`.
- [x] 4.2 Escribir pruebas RED de transiciones `propuesto → en_curso → completado/cancelado`, cancelación desde estados no terminales y rechazo 409 de transiciones prohibidas; implementar cambios de estado y verificar que no creen turnos ni precios con el mismo comando unittest.
- [x] 4.3 Agregar rutas de consulta/creación/cambio de estado y pruebas de contrato `python -m unittest discover -s tests -p "test_api_planes*.py" -v`; verificar respuestas públicas y errores sin datos de turnos, precios, consentimiento ni diagnósticos.
- [x] 4.4 Documentar rutas, etapas, estados y ejemplos sintéticos en `backend/README.md`; verificar consistencia con `resource-catalogs` y que no se amplía el contrato de `Prestacion` ni `Turno`.

## 5. Autorización y auditoría clínica

- [x] 5.1 Escribir primero pruebas RED de rol, profesional activo/vigente, vínculo actual y turno propio atendido para cada endpoint; aplicar autorización dentro de la transacción y lograr GREEN con `python -m unittest discover -s tests -p "test_api_*clinica*.py" -v`.
- [x] 5.2 Escribir pruebas RED de lectura/escritura metadata-only, atomicidad con auditoría, rollback ante fallo y respuestas 403 sin contenido para Admin/Recepción; extender eventos y restricciones de auditoría y verificar con `python -m unittest discover -s tests -p "test_*audit*" -v` y las pruebas clínicas.
- [x] 5.3 Revisar cuerpos, respuestas, logs, eventos y ejemplos OpenAPI: confirmar campos acotados, muestras sintéticas, ausencia de logging de contenido clínico y auditoría metadata-only; registrar la inspección y suites focales en `backend/evidence/C-16-verificacion.md`.
- [x] 5.4 TDD de `GET /profesional/atenciones-atendidas?limit&offset`: RED API 404; GREEN servicio/HTTP con rol Profesional, identidad de sesión, campos mínimos, aislamiento entre vínculos, paginación y auditoría metadata-only fail-closed. Verificado en SQLite y PostgreSQL 18 real aislado; C08 no cambia.

## 6. Backup y restore SQLite/PostgreSQL

- [x] 6.1 Escribir prueba RED de versión/whitelist C-16, actualizar manifiesto a SQLite v10/PostgreSQL 0011 y verificar bundle SQLite con snapshot, hallazgo, plan y etapa sintéticos; `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_backup*' -v` — 68 tests OK, 3 skips justificados por host.
- [x] 6.2 Verificar conteos, hash, referencias, rechazo de bundle incompatible, restore a archivo nuevo, filas C-15/C-16 conservadas y fuente intacta; `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_backup_restore*' -v` — 13 tests OK, 1 skip de symlink por permiso Windows.
- [x] 6.3 Verificar bundle/restore PostgreSQL con historia, odontograma versionado, plan y recuentos en cluster local aislado (loopback:55432; origen `*_test`, destino también `*_test`); `ODONTOLOGIA_TEST_DATABASE_URL=... .venv/Scripts/python.exe -m unittest tests.test_backup_odontograma_postgresql_integracion -v` — 1 test real OK con pg_dump/pg_restore 18.
- [x] 6.4 Actualizar `backend/README.md` y `backend/evidence/C-16-verificacion.md` con versiones, comandos y resultados SQLite/PG; revisar que el manifiesto sólo contenga conteos y que restore exija destino distinto de la base activa.

## 7. Vista clínica mínima

- [x] 7.1 Pruebas frontend RED/GREEN para lista paginada de atenciones atendidas propias, carga de historial tras selección, lista vacía sin llamadas clínicas, y ausencia de UI/llamadas C16 para Administrador/Recepción; `npm test -- --run` desde `frontend/` — 55 tests OK.
- [x] 7.2 Cubrir formularios de nomenclatura/superficies, alta de odontograma/plan, cambios de estado y mensaje 422 sin sugerencias clínicas; `npm run build` — TypeScript y Vite OK.
- [x] 7.3 Verificar manualmente con datos sintéticos: Profesional ve la atención atendida, odontograma versión 1 con “sin registros de hallazgo”, controles para agregar versión y plan propuesto; Administrador y Recepción no muestran “Atenciones clínicas”. Tests frontend cubren ausencia de llamadas clínicas para esos roles; no se hizo medición manual de red.

## 8. Integración final

- [x] 8.1 Ejecutar la suite backend completa con PostgreSQL 18 aislado (`.venv/Scripts/python.exe -m unittest discover -s tests -v`: 481 tests OK, 3 skips del host); suite frontend (`npm test -- --run`: 55 tests OK) y build (`npm run build`: OK). La integración PostgreSQL focal C-15/C-16 pasó 5/5, sin cambiar contratos archivados.
- [x] 8.2 Completar `backend/evidence/C-16-verificacion.md` con resultados observados, límites sintéticos y verificación visual manual; `openspec validate gestionar-odontograma-y-plan --strict` OK. La prueba Playwright sigue sin ejecutarse porque falta Chromium; no se afirma medición manual de red.
