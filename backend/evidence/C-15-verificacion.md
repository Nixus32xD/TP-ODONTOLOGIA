# C-15 — Registro de verificación

## Alcance revisado

La historia clínica mínima usa exclusivamente fixtures sintéticos. Se documentaron tres endpoints: consulta paginada, alta de evolución y corrección append-only. Las notas tienen un máximo de 5000 caracteres. Sólo el Profesional activo vinculado puede acceder a una ficha con turno propio atendido; Recepción y Administrador no reciben contenido clínico. Las lecturas y escrituras usan auditoría metadata-only y fallan cerradas si el evento no se registra. Las copias incorporan la nueva tabla y sus recuentos sin exponer texto clínico en el manifiesto.

La documentación local está en `backend/README.md`. No requiere Docker, Redis ni servicios externos para la demo SQLite. No usar datos personales reales; el change no acredita aptitud productiva o clínica.

## Comprobaciones ejecutadas

Desde `backend/`:

- `.venv/Scripts/python.exe -m unittest discover -s tests` — 381 tests, OK; 4 omitidos por guardas de PostgreSQL.
- `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_backup*.py'` — 65 tests, OK; 3 omitidos.
- La prueba `test_openapi_y_docs` se actualizó porque el contrato OpenAPI ahora incluye los tres endpoints C-15; pasó individualmente y en la suite completa.

Desde la raíz:

- `openspec validate registrar-historia-clinica --strict` — válido.
- El plan de Apply tiene 15 tareas: 13 completadas y 2 pendientes de integración PostgreSQL real (6.2 y 6.3). Por eso no se declara C-15 completamente verificado ni listo para archivar.

## Límite de PostgreSQL en esta verificación

No estaban disponibles `initdb`, `pg_ctl` ni `psql`; no se instaló ni se inició ningún servicio. Pasaron la verificación estructural/encadenamiento de Alembic y la generación offline de SQL. Las pruebas de integración PostgreSQL se omitieron por falta de `ODONTOLOGIA_TEST_DATABASE_URL`; las pruebas de backup/restore PostgreSQL usan mocks. No se aplicó `20261102_0010_clinical_history` contra un servidor ni se probó su trigger/constraints en ejecución. Tampoco se creó ni restauró un bundle C-15 en PostgreSQL. El respaldo y restauración SQLite sí se verificaron con bases temporales. Las pruebas omitidas y los mocks no cuentan como integración PostgreSQL.

Pendientes OpenSpec:

- **6.2:** aplicar la migración en un PostgreSQL de prueba aislado y comprobar tabla, relaciones, restricciones, trigger append-only e integración sin skip.
- **6.3:** crear y restaurar un backup C-15 en un PostgreSQL de prueba aislado, usando datos ficticios y verificando recuentos y relaciones.
