# Proposal

## Why

El consultorio necesita registrar cargos y cobros manuales para consultar saldos sin alterar turnos, prestaciones ni planes clínicos. El change agrega un ledger local verificable con importes exactos y trazabilidad, manteniendo todos los movimientos como demostración sintética.

## What Changes

- Incorporar cargos manuales por paciente, cobros parciales o totales y reversiones parciales o totales append-only.
- Representar ARS en centavos enteros; aceptar importes como texto decimal estricto, sin redondeo, y limitar cada movimiento a ARS 999.999.999,99.
- Impedir sobrepagos y reversiones superiores al importe aún reversible; derivar el saldo del ledger.
- Persistir idempotencia por actor, operación y clave; el mismo comando devuelve su resultado original y una clave con otro payload responde 409.
- Permitir consulta/alta de cargos y registro de cobros a Administrador y Recepción; limitar las reversiones a Administrador.
- Registrar mutación, ledger, idempotencia y auditoría metadata-only en una sola transacción.
- Actualizar migraciones SQLite/PostgreSQL, backup/restore, API, interfaz y pruebas.
- **No** integrar pasarelas de pago, bancos, ARCA, comprobantes fiscales ni cobros automáticos de prestaciones, turnos o planes.

## Capabilities

### New Capabilities
- `financial-ledger`: registro manual e inmutable de cargos, cobros, reversiones e idempotencia monetaria.

### Modified Capabilities
- `audit-trail`: incluir las operaciones del ledger en la lista y escenarios de auditoría, preservando exclusión de importes y contenido.

## Impact

- Backend: API/autorización, nuevo servicio y modelos de ledger/idempotencia, almacenamiento SQLite/PostgreSQL, auditoría y backups.
- Persistencia: nueva revisión SQLite y migración Alembic encadenada a `20261102_0013_patient_self_service`.
- Frontend: vistas internas de cuenta corriente con saldo calculado por el backend.
- Verificación: pruebas unitarias, API, migración, concurrencia, rollback de auditoría, backup/restore SQLite y PostgreSQL, frontend y OpenSpec.
