# Tasks

## 1. Contrato y persistencia de catálogos

- [x] 1.1 Agregar pruebas fallidas de validación y servicio para CRUD paginado de profesional, box y prestación, duración positiva y estado; comprobar que fallan antes de implementar.
- [x] 1.2 Añadir tablas/campos y migraciones SQLite v4 y Alembic 0005 conservando los IDs seed; verificar migración nueva y actualización desde esquemas anteriores.
- [x] 1.3 Implementar servicios transaccionales para alta, lectura, listado, actualización y estado; hacer pasar triangulación de casos válidos, límites e inválidos.
- [x] 1.4 Documentar modelos y reglas del catálogo en KB y README; comprobar que los ejemplos son sólo ficticios y coherentes con OpenAPI.

## 2. API, permisos y auditoría

- [x] 2.1 Escribir primero pruebas RED de rutas, paginación, 401/403 y restricciones de estado; luego exponer rutas `/profesionales`, `/boxes` y `/prestaciones` y verificar contratos HTTP.
- [x] 2.2 Extender la matriz de auditoría SQLite/PostgreSQL y agregar pruebas RED de atomicidad, metadatos permitidos y rollback por fallo; verificar límites sin almacenar nombres ni duración.
- [x] 2.3 Actualizar la documentación OpenAPI/backend y evidencia del cambio; verificar rutas, ejemplos y que no exista `prestacion_id` en `/turnos`.

## 3. Turnos y regresión

- [x] 3.1 Agregar primero pruebas RED para profesional y box inactivos y referencias desconocidas; ajustar la validación transaccional y verificar error, prioridad y ausencia de inserción.
- [x] 3.2 Ejecutar suite completa en SQLite y PostgreSQL aislado, `pip check`, `openspec validate --all --strict` y `git diff --check`; resolver fallos introducidos por C-06.

## Workflow follow-up

- Archivar el change después de validar, sincronizar las specs y actualizar roadmap y bitácora.
- Crear un commit local separado después de validar el change; no hacer push sin autorización explícita.
