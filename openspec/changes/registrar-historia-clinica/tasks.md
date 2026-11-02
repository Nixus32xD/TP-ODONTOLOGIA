# Tasks

## 1. Persistencia clínica y migraciones

- [x] 1.1 Escribir primero pruebas para tabla, restricciones, relaciones y protección append-only de evoluciones; implementar el modelo separado y verificar con `.venv/Scripts/python.exe -m unittest tests/test_postgres_schema.py tests/test_clinical_history_migration.py`.
- [x] 1.2 Escribir pruebas de migración SQLite desde versión 8 que preserven turnos, pacientes, auditoría y triggers; implementar la migración transaccional a versión 9 y verificar con `.venv/Scripts/python.exe -m unittest tests/test_auth_sqlite_migration.py tests/test_migracion_sqlite.py tests/test_clinical_history_migration.py`.
- [x] 1.3 Agregar la revisión Alembic siguiente a `20261102_0009_turn_rescheduling`; verificar metadatos/encadenamiento con `test_postgres_schema.py` y generar DDL offline con `alembic upgrade head --sql`. La aplicación contra servidor PostgreSQL queda pendiente en 6.2.

## 2. Auditoría clínica metadata-only

- [x] 2.1 Escribir pruebas de normalización para consulta concedida/denegada, alta y corrección, incluyendo omisión de contenido y nombres; ampliar catálogo y funciones de auditoría y verificar con `.venv/Scripts/python.exe -m unittest tests/test_auditoria.py tests/test_postgres_schema.py`.
- [x] 2.2 Escribir pruebas de atomicidad: fallo de auditoría no devuelve lectura clínica ni confirma altas/correcciones; conectar las operaciones a la transacción existente y verificar con `.venv/Scripts/python.exe -m unittest tests/test_clinical_history.py tests/test_api_clinical_history.py`.

## 3. Consulta y alta de evoluciones

- [x] 3.1 Escribir pruebas de autorización por rol activo, vínculo profesional vigente y turno atendido coincidente, incluyendo denegaciones a Recepción y Administrador; implementar el servicio de dominio y verificar con `.venv/Scripts/python.exe -m unittest tests/test_clinical_history.py`.
- [x] 3.2 Escribir pruebas de `GET /pacientes/{paciente_id}/historia`, paginación y proyección limitada; implementar el endpoint sin ampliar ficha ni agenda y verificar con `.venv/Scripts/python.exe -m unittest tests/test_api_clinical_history.py tests/test_api_pacientes.py tests/test_consulta_turnos.py`.
- [x] 3.3 Escribir pruebas de `POST /pacientes/{paciente_id}/evoluciones` para nota vacía, límite de 5000 caracteres, campos extra y referencias inválidas; implementar validación y persistencia y verificar con `.venv/Scripts/python.exe -m unittest tests/test_api_clinical_history.py tests/test_clinical_history.py`.

## 4. Correcciones inmutables

- [x] 4.1 Escribir pruebas de correcciones propias, referencias ajenas/inexistentes y preservación del original; implementar `POST /evoluciones/{evolucion_id}/correcciones` append-only y verificar con `.venv/Scripts/python.exe -m unittest tests/test_clinical_history.py tests/test_api_clinical_history.py`.

## 5. Backup, restauración y alcance de demostración

- [x] 5.1 Actualizar manifiesto, lista de tablas y contratos de recuentos SQLite/PostgreSQL para incluir la tabla clínica sin exponer notas; verificar con `test_backup_manifest.py` y `test_backup_verificacion.py`. La integración PostgreSQL real queda pendiente en 6.3.
- [x] 5.2 Integrar C-15 al flujo C-12 y verificar la conservación/restauración SQLite en destino nuevo con `test_backup_cli.py` y `test_backup_restore_sqlite.py`; las pruebas de contrato PostgreSQL son con mocks. La restauración PostgreSQL real queda pendiente en 6.3.
- [x] 5.3 Documentar fixtures sintéticos, permisos, límites del demo y comando local sin Docker ni servicios externos; comprobar que instrucciones y ejemplos no usan datos reales ni afirman preparación productiva en `backend/README.md` y `backend/evidence/C-15-verificacion.md`.

## 6. Verificación integrada

- [x] 6.1 Ejecutar la suite backend completa y validación OpenSpec estricta; resolver fallos atribuibles al change y verificar desde `backend/` con `..\\.venv\\Scripts\\python.exe -m unittest discover -s tests` (381 tests, OK; 4 omitidos) y desde la raíz con `openspec validate registrar-historia-clinica --strict`.
- [ ] 6.2 Aplicar Alembic hasta `20261102_0010_clinical_history` en PostgreSQL de prueba aislado (loopback, puerto 55432); comprobar creación de tabla, claves foráneas, CHECK y trigger append-only, y ejecutar `test_postgresql_integracion.py` sin skip.
- [ ] 6.3 En un PostgreSQL de prueba aislado y con fixtures sintéticos, crear bundle C-15, verificar manifiesto/recuentos y restaurarlo en base nueva; confirmar nota, relaciones, auditoría y append-only. Ejecutar las pruebas reales de backup/restore PostgreSQL sin mocks; no usar bases ni datos reales.
