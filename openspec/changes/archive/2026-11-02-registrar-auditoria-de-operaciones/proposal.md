# Proposal

## Why

Las operaciones actuales de turnos y autenticación no dejan atribución consultable. El consultorio necesita saber qué acción se confirmó y quién la realizó, y que una mutación no quede registrada sin su evento de auditoría.

## What Changes

- Añadir eventos append-only para altas confirmadas de turnos, creación/cambio de cuentas, bootstrap del Administrador e inicio/cierre de sesión.
- Registrar intentos de autenticación rechazados sin conservar el identificador intentado; nunca guardar contraseñas, hashes, JWT, cuerpos, nombres ni datos clínicos.
- Escribir la mutación y su evento en la misma transacción. Si falla el evento, revertir la mutación; en autenticación rechazada, devolver 401 genérico sólo tras registrar el rechazo, y 503 si la auditoría no está disponible.
- Exponer `GET /auditoria` sólo a Administrador, paginado y ordenado de forma estable. No habilitar edición, borrado ni purga automática en este demo.
- Actualizar `POST /turnos` para devolver `almacenamiento_error` y no persistir el turno cuando falle su evento de auditoría.

## Capabilities

### New Capabilities
- `audit-trail`: registrar y consultar metadatos inmutables de las operaciones aprobadas.

### Modified Capabilities
- `alta-turnos`: incluir el fallo de auditoría en la semántica HTTP de almacenamiento y rollback.

## Impact

Afecta el esquema y las migraciones explícitas SQLite/PostgreSQL, las transacciones de agenda, cuentas y sesiones, la API FastAPI/OpenAPI, pruebas y documentación. No altera las reglas de solapamiento ni la matriz RBAC vigente. El endpoint de consulta queda reservado al Administrador.
