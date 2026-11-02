# Proposal

## Why

El proyecto ya admite SQLite y PostgreSQL, pero no tiene comandos de copia ni restauración. Hace falta demostrar que una agenda puede copiarse de forma coherente y recuperarse en un destino nuevo sin sobrescribir la agenda activa ni perder el historial de auditoría.

## What Changes

- Agregar comandos locales y manuales para respaldar la base completa del backend seleccionado y restaurarla sólo en un destino nuevo y explícito.
- Incluir un manifiesto verificable con fecha UTC, motor, versión de aplicación y esquema, formato e integridad SHA-256; validar la copia antes de reportarla como utilizable.
- Usar SQLite Online Backup API para obtener una copia coherente durante actividad; para PostgreSQL usar `pg_dump` y `pg_restore` con versiones compatibles y detectar herramientas no disponibles antes de operar.
- Rechazar destinos existentes o que correspondan a la agenda activa; ante archivo corrupto, manifiesto incompatible, fallo de integridad o error de restauración, conservar origen y destino previos sin presentarlos como recuperados.
- Documentar que las copias son sensibles y locales: no incluir `.env` ni secretos JWT, no subirlas automáticamente, no borrar copias por retención automática y no afirmar preparación para producción.
- Verificar con datos ficticios consistencia durante escritura controlada, rechazo de copias corruptas/incompatibles, preservación de destinos ocupados y una restauración seguida de una nueva alta.

## Capabilities

### New Capabilities
- `agenda-backup-restore`: Copia manual, verificación de integridad y restauración segura de una agenda SQLite o PostgreSQL en un destino nuevo.

### Modified Capabilities

## Impact

- Backend: módulo CLI de backup/restore, manejo de archivos SQLite y adaptador PostgreSQL mediante las herramientas cliente; sin endpoints HTTP.
- PostgreSQL: disponibilidad de `pg_dump`/`pg_restore` compatibles debe comprobarse explícitamente en el host de prueba; C-12 no construye ni requiere una imagen de contenedor.
- Documentación: comandos reproducibles, prerrequisitos por motor, límites de sensibilidad y guía de verificación técnica.
- Persistencia: no cambia el esquema de negocio; la versión de aplicación del manifiesto requiere una fuente única del proyecto.
- Fuera de alcance: almacenamiento remoto, copias programadas, retención/purga automática, cifrado gestionado, restauración sobre una base existente, uso de datos reales y afirmaciones de operación productiva.
