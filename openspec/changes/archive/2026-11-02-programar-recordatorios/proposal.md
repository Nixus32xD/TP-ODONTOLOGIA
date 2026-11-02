# Proposal

## Why

El consultorio necesita representar si una persona autorizó recibir recordatorios y demostrar el flujo sin enviar comunicaciones reales. C-17 agrega una cola local verificable para turnos confirmados, con consentimiento revocable, reglas temporales explícitas y procesamiento simulado acotado.

## What Changes

- Agregar a la ficha de paciente el consentimiento para recordatorios, inicialmente desactivado, gestionado por Administrador o Recepción y auditado sin guardar datos personales en eventos.
- Programar recordatorios simulados 24 horas antes de turnos confirmados futuros, sólo con consentimiento y cuando todavía se cumpla el plazo; usar `America/Argentina/Mendoza` para la regla temporal.
- Persistir un outbox idempotente en SQLite y PostgreSQL; invalidar recordatorios pendientes al cancelar, reprogramar o retirar consentimiento y crear una nueva versión sólo si la cita continúa siendo elegible.
- Procesar trabajo únicamente por ejecución local explícita de una pasada (`--once`), con revalidación de consentimiento, estado, versión y fecha; acotar y registrar reintentos sintéticos sin afirmar entrega externa.
- Incluir el outbox en migraciones y backup/restore. El canal es una simulación local que no usa HTTP, correo, WhatsApp, Redis, Docker ni datos reales.

## Capabilities

### New Capabilities
- `appointment-reminders`: consentimiento, programación, outbox idempotente, invalidación y ejecución local simulada de recordatorios.

### Modified Capabilities
- `patient-management`: consentimiento desactivado por defecto, consulta y gestión por Administrador/Recepción.
- `turno-lifecycle`: crear recordatorio al confirmar elegiblemente e invalidar al cancelar, en la misma transacción.
- `turn-rescheduling`: invalidar versión pendiente y evaluar programación para el turno reprogramado.
- `agenda-backup-restore`: conservar la tabla outbox y validar su integridad en copias/restauraciones.
- `audit-trail`: registrar cambios de consentimiento y operaciones del outbox sólo con metadatos.
- `reception-agenda-ui`: permitir que Administrador y Recepción consulten y actualicen el consentimiento desde la gestión de pacientes.

## Impact

Impacta modelos y migraciones SQLite/Alembic, operaciones de ficha de paciente, transiciones y reprogramación de turnos, auditoría, manifiesto/restore de backups, API, UI de pacientes, un comando local de ejecución y pruebas/evidencia. Se mantienen el backend FastAPI, SQLite y PostgreSQL; no se agrega un proveedor ni una dependencia de cola.
