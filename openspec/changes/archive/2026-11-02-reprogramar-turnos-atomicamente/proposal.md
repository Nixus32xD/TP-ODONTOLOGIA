# Proposal

## Why

La agenda ya permite crear turnos, consultar disponibilidad y gestionar estados, pero todavía no ofrece una forma segura de mover un turno existente. Reprogramar como cancelación seguida de un alta separada puede perder el turno original o producir carreras; el cambio necesita una operación atómica con control de versión.

## What Changes

- Agregar `POST /turnos/{id}/reprogramacion` para Administrador y Recepción, limitado a turnos `reservado` o `confirmado`.
- Requerir una versión esperada y rechazar con HTTP 409 cualquier edición obsoleta o nueva asignación en conflicto, sin mutación ni auditoría.
- Cambiar sólo intervalo, profesional y box; conservar paciente, duración y estado actual. Revalidar paciente, recursos activos, horarios, excepciones, bloqueos y ocupación dentro de la misma operación serializada.
- Auditar únicamente la reprogramación confirmada, en la misma transacción que la mutación; si falla la auditoría, revertir todo.
- No introducir exclusión por paciente: se conserva el contrato de C-01 que permite turnos simultáneos de una persona si profesional y box son distintos.
- No asociar prestaciones a turnos en este change. C-06 mantiene su separación de catálogos; no existe una prestación persistida en el turno que C-10 pueda validar.

## Capabilities

### New Capabilities
- `turn-rescheduling`: reprogramar de forma atómica un turno vigente conservando su estado, paciente y duración.

### Modified Capabilities
- `turno-lifecycle`: agregar versión a los turnos y aumentarla en cada transición efectiva de estado.
- `agenda-query`: exponer la versión en la proyección operativa para que Administrador y Recepción puedan enviar una precondición vigente.
- `audit-trail`: registrar la acción metadata-only de reprogramación confirmada junto con la mutación atómica.

## Impact

Afecta el endpoint y servicio de agenda, modelos y migraciones SQLite/PostgreSQL, consultas operativas, auditoría y pruebas de concurrencia. Mantiene intacto el endpoint y contrato standalone de C-01; no agrega un vínculo a prestaciones ni cambia los permisos de Profesional.
