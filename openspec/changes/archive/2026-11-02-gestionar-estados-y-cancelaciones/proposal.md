# Proposal

## Why

Los turnos hoy no tienen estado y ocupan profesional y box indefinidamente, por lo que recepción no puede cancelar una reserva ni liberar de forma segura la agenda. Este cambio introduce un ciclo de vida explícito necesario para que las consultas de C-08 cuenten sólo ocupaciones vigentes.

## What Changes

- Incorporar estados `reservado`, `confirmado`, `atendido`, `ausente` y `cancelado`, con transiciones limitadas y auditadas.
- Permitir confirmar, cancelar, marcar atención y registrar ausencia mediante operaciones protegidas para Administrador y Recepción.
- Considerar ocupantes sólo `reservado` y `confirmado`; la cancelación libera ambos recursos sin borrar el turno ni su auditoría.
- Hacer idempotente una cancelación repetida: responder 200 con el estado `cancelado`, sin insertar un segundo evento de mutación.
- Migrar las filas existentes a `reservado` sin modificar IDs, intervalos ni referencias. Conservar el contrato standalone C-01 hasta la migración explícita.
- Ampliar el catálogo de auditoría con `turno.estado_actualizado`; la migración SQLite v6 reconstruye la tabla append-only dentro de la misma transacción y conserva sus eventos existentes.
- Serializar las transiciones con las altas de turnos para impedir que una cancelación concurrente y una nueva reserva dejen la agenda inconsistente.
- Dejar fuera la reprogramación (C-10), el acceso de cuentas Profesional y cualquier borrado físico.

## Capabilities

### New Capabilities

- `turno-lifecycle`: estados, transiciones y operaciones protegidas del ciclo de vida de un turno.

### Modified Capabilities

- `alta-turnos`: una alta migrada nace como `reservado` y sólo estados ocupantes participan en las exclusiones; el C-01 standalone no migrado mantiene el contrato histórico.
- `agenda-availability`: los cambios de horarios, excepciones y bloqueos se validan contra turnos ocupantes (`reservado` y `confirmado`); los estados terminales se conservan como historial y no impiden configurar disponibilidad futura.
- `audit-trail`: registrar las transiciones confirmadas con metadatos mínimos y atomicidad.

## Impact

- Backend FastAPI, dominio y persistencia SQLAlchemy/PostgreSQL y SQLite.
- SQLite esquema v6 y revisión Alembic siguiente a C-07; migración no destructiva de turnos existentes.
- Rutas de confirmación, cancelación, atención y ausencia; autorización sólo Administrador/Recepción.
- Auditoría técnica metadata-only con la acción `turno.estado_actualizado`, locks compartidos de agenda y pruebas unitarias, API, migración y concurrencia en ambos motores.
