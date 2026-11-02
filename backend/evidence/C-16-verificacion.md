# C-16 — Evidencia de verificación

## Alcance de la evidencia

Esta evidencia corresponde a la preparación e implementación local de C-16. Todo dato funcional de prueba debe ser sintético. No acredita uso clínico, consenso odontológico ni preparación productiva.

## Consulta de nomenclatura oficial

Consulta documental realizada el 2026-11-02:

- [ISO 3950:2016 — Dentistry: designation system for teeth and areas of the oral cavity](https://www.iso.org/standard/68292.html): la ficha oficial muestra la edición 4, publicada en marzo de 2016, y afirma que fue revisada/confirmada en 2022 y permanece vigente. También muestra el estado `90.92 — to be revised` (2025-09-25) y una publicación de reemplazo `ISO/AWI 3950` en desarrollo. La ficha describe la designación de dientes o áreas de cavidad oral con dos dígitos. Aplicar sólo como referencia de nomenclatura y volver a comprobar su estado al implementar.
- [HL7 Terminology — FDI surface CodeSystem](https://terminology.hl7.org/en/CodeSystem-FDI-surface.html): la URL canónica resuelve a la publicación consultada de HL7 Terminology. La página presenta los códigos individuales `M`, `O`, `I`, `D`, `B`, `V`, `L` junto con códigos compuestos `MO`, `DO`, `DI`, `MOD`, y describe su contenido como una selección (“a smattering”). C-16 usa únicamente los siete códigos individuales autorizados como subconjunto explícito; no afirma exhaustividad ni consenso clínico. Las reglas de compatibilidad anterior/posterior son reglas técnicas propuestas para validar entradas, no recomendaciones odontológicas.

## Baseline previo a cambios de implementación

| Área | Comando y entorno | Resultado observado |
| --- | --- | --- |
| Backend | Desde `backend/`: `.venv/Scripts/python.exe -m unittest discover -s tests -v` (Python 3.13.5 del entorno del proyecto) | 381 tests, OK; 5 skipped porque no estaba definida `ODONTOLOGIA_TEST_DATABASE_URL`; 64.719 s. |
| Frontend | Desde `frontend/`: `npm test` (Vitest 4.1.12) | 9 archivos, 50 tests, OK; 6.01 s. |

El primer intento con `python` del `PATH` apuntó a Python 3.10 global, no al entorno del proyecto, y no sirve como baseline: carece de SQLAlchemy y esa versión no admite el argumento `sqlite3.connect(autocommit=...)` que ya utiliza el backend. Para la suite del proyecto se usa explícitamente `.venv/Scripts/python.exe`.

La suite inicial no ejecutó integración PostgreSQL porque no había URL de test configurada. Para C-16 se creó un cluster local temporal propio en `%TEMP%\TP_ODONTOLOGIA_C16_PG_20261102`, con PostgreSQL 18 en `127.0.0.1:55432` y base `odontologia_c16_test`; el puerto `5432` no se usó y no se usó Docker ni Redis.

## Migraciones PostgreSQL C-16

- Prueba focal: desde `backend/`, con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_c16_test`, `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_odontograma_postgresql_integracion.py" -v` — 1 test, OK.
- La prueba crea un esquema aislado, migra primero hasta Alembic `20261102_0010_clinical_history`, luego ejecuta `upgrade head` y verifica que llega a `20261102_0011_odontogram_treatment_plans`.
- Se insertaron datos sintéticos para comprobar FK de paciente/profesional/prestación, restricción de superficie, append-only para hallazgos y etapas, y aceptación/rechazo de combinaciones de auditoría. Los intentos inválidos fallaron y el dato válido persistió.
- La instancia temporal quedó activa para la continuación del trabajo. Esta comprobación es una integración local aislada; no sustituye pruebas de despliegue o producción.

## Validación de nomenclatura

- Prueba focal `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_odontograma_validacion.py" -v` — 7 tests, OK.
- Se aceptan códigos de pieza de dentición permanente y primaria con forma exacta de dos dígitos, superficies individuales HL7 seleccionadas, y observaciones de hasta 500 caracteres. Se rechazan piezas fuera del rango propuesto, superficies repetidas/desconocidas/incompatibles, observaciones inválidas y entradas adicionales que no estén en el contrato.
- Una lista vacía representa un snapshot completo sin registros de hallazgo; no implica normalidad. La etiqueta de presentación debe ser literalmente “sin registros de hallazgo” y el historial append-only conserva las versiones anteriores.

## Servicio de snapshots y autorización

- Prueba focal `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_odontograma_servicio.py" -v` — 5 tests, OK; baseline de auditoría `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_auditoria.py" -v` — 19 tests, OK.
- Se verificó la secuencia de snapshots por paciente/profesional, consulta histórica ordenada, aislamiento por vínculo y atención atendida, denegación a Administrador y fallo cerrado/rollback si falla la auditoría.
- La serialización reusa el bloqueo clínico existente (`BEGIN IMMEDIATE` en SQLite y mutex de agenda en PostgreSQL); cada operación registra sólo metadata.

## API HTTP de odontograma

- Prueba focal `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_api_odontograma.py" -v` — 11 tests, OK.
- `GET` y `POST /pacientes/{paciente_id}/odontograma` se publican en OpenAPI. Se verificó creación/lectura, 422 sin mutación para entrada inválida, 401 anónimo, 403 para Administrador/Recepción y 404 si no hay atención propia atendida.
- Dos profesionales con atenciones propias sobre el mismo paciente ven flujos de versiones separados: uno no recibe el odontograma del otro.
- El ejemplo OpenAPI se inspeccionó mediante la prueba focal y usa sólo pieza/códigos y texto sintéticos, sin campos diagnósticos. La guía de API está en `backend/README.md`.

## Planes manuales

- Prueba focal `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_planes_tratamiento.py" -v` — 6 tests, OK.
- Se verificó orden estable de etapas, referencias sólo a prestaciones activas al crear, rechazo atómico ante referencia ausente/inactiva y conservación del vínculo histórico si una prestación luego se desactiva.
- Un plan no contiene precio ni `turno_id`; se exige profesional vinculado y una atención atendida propia.
- Las transiciones comprobadas son `propuesto → en_curso → completado`, cancelación desde `propuesto` y `en_curso`, y rechazo 409 desde terminales o ante transiciones fuera del flujo. Se confirmó que no se crean turnos al cambiar estado.
- API focal `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_api_planes.py" -v` — 4 tests, OK. Rutas, estados, errores y respuestas OpenAPI se comprobaron con IDs sintéticos; los cuerpos no agregan precio, turno, consentimiento ni diagnóstico.
- Regresión del catálogo `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_catalogos.py" -v` — 6 tests, OK. No se modificó el contrato ni el modelo de `Prestacion`.

## Autorización clínica y auditoría

- Pruebas focales `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_api_odontograma.py" -v` — 11 tests, OK; `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_api_planes.py" -v` — 9 tests, OK.
- Se comprobaron roles, cuenta activa, Profesional activo y vínculo vigente, atención propia `atendido` en lectura/escritura/cambio de estado, denegación sin contenido y aislamiento entre profesionales. Ante un vínculo cambiado, el token previo se invalida; una cuenta desactivada devuelve 401 y un Profesional desactivado no accede al contenido.
- Pruebas de auditoría existentes `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_auditoria.py" -v` — 19 tests, OK. Las pruebas C-16 verifican payload y metadata-only para eventos de lecturas/altas, además de falla 503/rollback si el registro no confirma.
- Migración SQLite C-16 `.venv/Scripts/python.exe -m unittest discover -s tests -p "test_odontograma_migracion.py" -v` — 3 tests, OK; inserción de evento clínico válido y rechazo de combinación acción/recurso inválida. La integración PostgreSQL focal también verifica ambas restricciones.

## Bundle y restauración SQLite/PostgreSQL

- Esquema y whitelist: la prueba RED `test_schema_c16_incluye_tablas_clinicas_y_revision_actual` detectó que el manifiesto todavía declaraba SQLite v9; se actualizó la versión admitida a SQLite v10 y PostgreSQL `20261102_0011_odontogram_treatment_plans`, y se agregaron las cuatro tablas de C-16 a ambas listas de conteo.
- SQLite: `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_backup*' -v` — 68 tests, OK; 3 skips (dos comprobaciones POSIX y symlink no permitido por Windows). `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_backup_restore*' -v` — 13 tests, OK; un skip de symlink (WinError 1314). El fixture crea hallazgo, snapshot, plan y etapa sintéticos; verifica recuentos y filas en el archivo restaurado, una nueva conexión, manifiesto sin textos clínicos, y bytes de origen/bundle sin cambios.
- PostgreSQL real: con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_c16_test` y PostgreSQL 18 `bin` en `PATH`, `.venv/Scripts/python.exe -m unittest tests.test_backup_odontograma_postgresql_integracion -v` — 1 test, OK. Creó bundle con `pg_dump`, restauró con `pg_restore` a una base nueva `c16_restore_<id>_test` y comprobó versiones, hallazgos, plan, etapa y todos los recuentos. El manifiesto no contiene observación clínica ni nombre de prestación.
- La verificación se hizo en un esquema y una base temporales sintéticos en el cluster aislado `127.0.0.1:55432`; no se conectó al puerto 5432, ni se usaron datos reales, Docker o Redis. El caso PostgreSQL de C-16 deja su destino con sufijo `_test` y lo elimina al terminar. No se probó recuperación humana ni producción.
- README actualizado a los esquemas vigentes, tablas/cantidades incluidas y resultados del bundle/restore. No se ejecuta restore sobre la base activa; SQLite rechaza alias del origen y PostgreSQL exige nombre destino distinto y libre.

## Revisión de exposición de contenido clínico

- Inspección de `odontologia/api.py`, `odontologia/odontograma.py` y `odontologia/audit.py`: las solicitudes aceptan sólo pieza, superficies y observación acotada; las respuestas clínicas se limitan a Profesionales autenticados según los controles del servicio. Los ejemplos OpenAPI usan contenido sintético y la política de auditoría registra acción/recurso/resultado/fecha sin copiar hallazgos, observaciones, pacientes ni prestaciones.
- Búsqueda estática en los tres módulos no encontró `print`, `logger` ni `logging` que registren cuerpos o contenido clínico. Los endpoints tienen `response_model` explícitos. La guía de ejecución local usa `--no-access-log`; la prueba API compara eventos de auditoría frente a un texto marcador y confirma que no se guarda el texto.
- Verificaciones focales: `test_auditoria.py` (19 tests), `test_api_odontograma.py` (11) y `test_api_planes.py` (9), OK. El contenido clínico aparece en la respuesta sólo para el Profesional autorizado; Administrador/Recepción reciben denegación sin cuerpo clínico. `hallazgos=[]` se presenta como “sin registros de hallazgo”, no como normalidad.

## Vista React y verificación disponible

- La interfaz Profesional consulta la página de atenciones atendidas propias y sólo carga odontograma/planes tras seleccionar una. Permite navegar páginas, leer historial completo, agregar una versión, crear planes manuales y ejecutar transiciones operativas. Administrador/Recepción no montan el componente clínico.
- `npm test -- --run` desde `frontend/` — 10 archivos, 55 tests OK. Los nuevos tests verifican el orden de llamadas, selección, versiones y el literal “sin registros de hallazgo”, ausencia de llamadas clínicas con lista vacía y otros roles, cuerpo POST para pieza/superficies, error 422, alta de plan y transición `en_curso`.
- `npm run build` desde `frontend/` — TypeScript y Vite OK.
- Verificación visual manual en IAB con el demo sintético: al iniciar sesión como Profesional se mostró la atención atendida; tras seleccionarla aparecieron el odontograma vigente versión 1, la etiqueta literal “sin registros de hallazgo”, el formulario para agregar una nueva versión y el plan `plan-e2e` en estado `propuesto`. Administrador y Recepción no mostraron la sección “Atenciones clínicas”. No se afirma haber inspeccionado manualmente las solicitudes de red; los tests frontend cubren que esos roles no disparan llamadas clínicas.
- La prueba Playwright `npx playwright test e2e/recepcion.spec.ts -g 'Profesional selecciona una atención sintética'` no pudo abrir Chromium porque falta el ejecutable `chromium_headless_shell`; no se instaló software adicional. La automatización E2E queda pendiente, aunque la inspección visual manual indicada arriba sí se realizó.

## Integración final C-16

- Backend completo con PostgreSQL 18 configurado mediante `ODONTOLOGIA_TEST_DATABASE_URL` hacia `127.0.0.1:55432/odontologia_c16_test`: `.venv/Scripts/python.exe -m unittest discover -s tests -v` — 481 tests OK, 3 skips por limitaciones del host (permisos POSIX/symlink). Tiempo observado: 110.986 s.
- Integración focal C-15/C-16: `tests.test_clinical_history_postgresql_integracion`, `tests.test_odontograma_postgresql_integracion` y `tests.test_backup_odontograma_postgresql_integracion` — 5 tests OK. La migración C-15 se comprueba en schema aislado hasta 0010; C-16 verifica upgrade a 0011, aislamiento/auditoría y restore real PostgreSQL.
- Frontend: `npm test -- --run` — 10 archivos, 55 tests OK; `npm run build` — TypeScript y Vite OK.
- `openspec validate gestionar-odontograma-y-plan --strict` — válido.
- La inspección visual manual de UI de 7.3 se completó con datos sintéticos según lo documentado arriba. Sigue pendiente ejecutar Playwright con Chromium disponible; esto no invalida la inspección visual manual ni implica una medición manual de red.

