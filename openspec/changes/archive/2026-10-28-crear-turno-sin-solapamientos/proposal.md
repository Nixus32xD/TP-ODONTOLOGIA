# Proposal

## Why

Recepción necesita registrar turnos sin ocupar simultáneamente al mismo profesional o box. Elijo esta única funcionalidad del MVP porque sus dos reglas confirmadas permiten demostrar un caso feliz, conflictos independientes y bordes temporales mediante pruebas; no requiere historia clínica, pagos ni una interfaz completa.

La propuesta inicial fue implementada. El usuario corrigió expresamente el stack a FastAPI y autorizó continuar exclusivamente C-01, commit y push tras validar. Esto no acredita lectura personal del spec.

## What Changes

- Proponer una operación de alta expuesta mediante FastAPI local con datos ficticios y validación explícita.
- Proponer intervalos `[inicio, fin)`, adyacencia permitida y fechas con offset explícito y precisión de minutos; comparar y persistir instantes en UTC.
- Rechazar conflictos de profesional y box por separado, sin registrar un turno rechazado; si ambos conflictos existen, informar primero profesional.
- Conservar turnos en SQLite local, coordinando consulta e inserción dentro de una transacción de escritura para el mismo archivo.
- Preparar bootstrap ficticio y pruebas unitarias, de persistencia y de competencia entre procesos como tareas del mismo change.
- Mantener fuera cancelación/reprogramación, disponibilidad clínica, WhatsApp, pagos, historia clínica, auth, UI y servicios externos.

## Capabilities

### New Capabilities

- `alta-turnos`: alta validada y persistente con exclusión de profesional y box, bordes temporales y resultados de error observables.

### Modified Capabilities

Ninguna. El inventario `openspec list --specs --json` está vacío; no existen contratos de producto que migrar.

## Impact

El producto contiene odontologia/, tests/ y demo. Python 3.12+, FastAPI, Pydantic y Uvicorn exponen POST /turnos, GET /health y OpenAPI. El adaptador reutiliza crear_turno sin duplicar reglas o transacciones SQLite. Dependencias fijadas y entorno virtual local; HTTPX sólo para pruebas. No cambia el PDF de Discovery.

La garantía se limitará a llamadas que usen esta operación, conexiones independientes y el mismo archivo SQLite en un disco local; no se extiende a escrituras SQL externas, archivos distintos, red o varios equipos.
