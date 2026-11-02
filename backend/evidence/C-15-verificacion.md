# C-15 — Registro de verificación

## Alcance revisado

La historia clínica mínima usa exclusivamente fixtures sintéticos. Se documentaron tres endpoints: consulta paginada, alta de evolución y corrección append-only. Las notas tienen un máximo de 5000 caracteres. Sólo el Profesional activo vinculado puede acceder a una ficha con turno propio atendido; Recepción y Administrador no reciben contenido clínico. Las lecturas y escrituras usan auditoría metadata-only y fallan cerradas si el evento no se registra. Las copias incorporan la nueva tabla y sus recuentos sin exponer texto clínico en el manifiesto.

La documentación local está en `backend/README.md`. No requiere Docker, Redis ni servicios externos para la demo SQLite. No usar datos personales reales; el change no acredita aptitud productiva o clínica.

## Comprobaciones ejecutadas

Desde `backend/`:

- Con `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/c15_review_test` y clientes PostgreSQL 18 en `PATH`, `.venv/Scripts/python.exe -m unittest discover -s tests` — 424 tests, OK; 3 omitidos.
- `test_clinical_history_postgresql_integracion.py` — 2 pruebas reales pasaron: migración Alembic 0010, FK/CHECK, trigger append-only, creación de bundle `pg_dump` y restauración `pg_restore` en una base nueva con la evolución sintética, auditoría y recuentos preservados.
- `test_postgresql_integracion.py` — 41 pruebas, OK contra PostgreSQL 18.6 en loopback:55432.
- `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_backup*.py'` — 65 tests, OK; 3 omitidos.
- La prueba `test_openapi_y_docs` se actualizó porque el contrato OpenAPI ahora incluye los tres endpoints C-15; pasó individualmente y en la suite completa.

Desde la raíz:

- `openspec validate registrar-historia-clinica --strict` — válido.
- El plan de Apply tiene 15 tareas completadas. La verificación real de PostgreSQL C-15 quedó registrada en 6.2 y 6.3.

## Alcance y limpieza de PostgreSQL

La verificación usó exclusivamente un clúster temporal PostgreSQL 18.6 en `127.0.0.1:55432` y la base `c15_review_test`; no se conectó al servicio del puerto 5432. El restore creó una base final única `c15_restore_<uuid>`, validó datos y conteos y la eliminó al terminar. Los schemas C-15 propios de las pruebas también se eliminaron.

La suite de integración inicial reveló que dos pruebas antiguas restauraban manualmente `alembic_version` a C-10 (0009), ahora obsoleto. Se actualizaron para restaurar `REVISION_ESQUEMA_ACTUAL` (0010); después, la suite PG completa pasó. El harness de integración C-15 desactiva la carga del logging del ini de Alembic y verifica que `uvicorn.error` quede habilitado, evitando contaminación de las pruebas posteriores.
