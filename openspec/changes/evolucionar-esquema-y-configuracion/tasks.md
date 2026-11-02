# Tasks

## 1. Configuración y dependencias

- [x] 1.1 Añadir versiones fijadas de SQLAlchemy, psycopg y Alembic al set del backend; verificar instalación y `pip check` en el entorno local.
- [x] 1.2 Probar que SQLite sigue siendo el valor predeterminado y que la configuración PostgreSQL requiere selección explícita y URL válida; ejecutar los tests de configuración.

## 2. Esquema PostgreSQL versionado

- [x] 2.1 Crear la revisión inicial con catálogos, turnos, checks, índices y fila singleton; verificado en PostgreSQL aislado con upgrade inicial, inspección vía tests y upgrade repetido conservando datos.

## 3. Alta de turnos PostgreSQL

- [x] 3.1 Implementar operación transaccional PostgreSQL con lock, validaciones y errores equivalentes a C-01; escenarios funcionales, timeout, rollback y multiproceso verificados en PostgreSQL aislado.
- [x] 3.2 Enrutar FastAPI según selección explícita, sin conectar al crear app ni cambiar SQLite por defecto; pruebas de selección y regresión completas.

## 4. Migración SQLite explícita

- [x] 4.1 Implementar lector SQLite de sólo lectura; pruebas de esquema/integridad, archivos incompatibles, solapamientos, adyacencia y snapshot frente a un escritor concurrente.
- [x] 4.2 Implementar importación transaccional a esquema vigente y destino vacío; PostgreSQL confirmó conteos, IDs, secuencia y rollback ante fallo, con fuente ficticia intacta.

## 5. Operación y documentación

- [x] 5.1 Documentar preparación, upgrade, importación, verificación, selección explícita y recuperación; se aclara que volver al SQLite pre-migración no conserva escrituras posteriores sólo en PostgreSQL.

## 6. Verificación de integración

- [x] 6.1 Ejecutar migración y concurrencia contra PostgreSQL 18.6 aislado en 127.0.0.1:55432 / odontologia_test; comprobar conflicto profesional/box, timeout, rollback y no uso de 5432.
- [x] 6.2 Suite completa (89 tests), OpenSpec estricto, pip check y git diff --check ejecutados; SQLite sigue siendo el backend predeterminado y se registran límites de verificación.

## Workflow follow-up

- Archivar C-02 con la skill del proyecto sólo cuando la validación PostgreSQL aislada esté completa y la propuesta/spec sincronice sin errores.
