# Proposal

## Why

Recepción necesita registrar turnos sin ocupar simultáneamente al mismo profesional o box. Elijo esta única funcionalidad del MVP porque sus dos reglas confirmadas permiten demostrar un caso feliz, conflictos independientes y bordes temporales mediante pruebas; no requiere historia clínica, pagos ni una interfaz completa.

Esta es una propuesta técnica preparada por el agente a pedido del usuario. No acredita revisión humana del spec ni autoriza comenzar Apply en esta misma petición.

## What Changes

- Proponer una operación local de alta con datos ficticios y validación explícita.
- Proponer intervalos `[inicio, fin)`, adyacencia permitida y fechas con offset explícito y precisión de minutos; comparar y persistir instantes en UTC.
- Rechazar conflictos de profesional y box por separado, sin registrar un turno rechazado; si ambos conflictos existen, informar primero profesional.
- Conservar turnos en SQLite local, coordinando consulta e inserción dentro de una transacción de escritura para el mismo archivo.
- Preparar bootstrap ficticio y pruebas unitarias, de persistencia y de competencia entre procesos como tareas del mismo change.
- Mantener fuera cancelación/reprogramación, disponibilidad clínica, WhatsApp, pagos, historia clínica, auth, UI, servidor y servicios externos.

## Capabilities

### New Capabilities

- `alta-turnos`: alta validada y persistente con exclusión de profesional y box, bordes temporales y resultados de error observables.

### Modified Capabilities

Ninguna. El inventario `openspec list --specs --json` está vacío; no existen contratos de producto que migrar.

## Impact

Se propone añadir un módulo `odontologia/`, pruebas `tests/` y una demo local con datos ficticios; todavía no se crean. Runtime propuesto: Python 3.12 o superior con `sqlite3` y `unittest` de la biblioteca estándar. No hay API de red ni dependencias externas de producto. El renderer y el PDF de Discovery permanecen fuera de este change.

La garantía se limitará a llamadas que usen esta operación, conexiones independientes y el mismo archivo SQLite en un disco local; no se extiende a escrituras SQL externas, archivos distintos, red o varios equipos.
