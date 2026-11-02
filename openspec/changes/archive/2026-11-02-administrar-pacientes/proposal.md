# Proposal

## Why

La agenda sólo identifica pacientes por códigos ficticios, así que Recepción no puede reconocer a quién corresponde un turno. Se necesita una ficha mínima para operar la agenda sin incorporar historia clínica ni datos reales en este demo.

## What Changes

- Agregar nombre visible y teléfono de contacto opcional a cada paciente; conservar los IDs y turnos existentes mediante una migración explícita.
- Incorporar alta, consulta paginada, consulta por ID y actualización de pacientes autenticadas. Administrador y Recepción podrán operar fichas; sólo Administrador podrá desactivar o reactivar.
- Implementar baja lógica: conservar turnos históricos y rechazar nuevas asignaciones a pacientes inactivos.
- Auditar altas, cambios y cambios de estado en la misma transacción, guardando sólo metadatos y el ID interno opaco.
- Limitar datos y pruebas a valores ficticios. No agregar documento, fecha de nacimiento, notas clínicas ni integraciones externas.

## Capabilities

### New Capabilities
- `patient-management`: ficha mínima, permisos, consultas y estado activo de pacientes.

### Modified Capabilities
- `alta-turnos`: las altas futuras rechazan pacientes inactivos sin cambiar la exclusión temporal de C-01.
- `audit-trail`: incorpora eventos de mutación de pacientes manteniendo la política append-only y sin datos personales.
- `personal-auth`: Recepción puede gestionar fichas mínimas de pacientes; las cuentas de Profesional permanecen fuera de acceso.

## Impact

Backend FastAPI, modelos SQLAlchemy, almacenamiento SQLite, migraciones SQLite y Alembic, eventos de auditoría, OpenAPI y suites SQLite/PostgreSQL. No requiere dependencias nuevas ni cambia la agenda SQLite predeterminada.
