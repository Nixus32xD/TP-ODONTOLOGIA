# Proposal

## Why

El panel de reportes ya maneja carga y error, pero cuando una consulta exitosa devuelve `dias` vacío no explica el resultado. La persona puede interpretar una pantalla vacía como una falla; el problema afecta más a tecnologías de asistencia. El cambio completa el estado vacío de C-20 sin alterar la API ni sus cálculos.

## What Changes

- Comunicar con texto visible y una región accesible cuando una consulta válida de agenda o finanzas no devuelve días.
- Mostrar el estado vacío por reporte, de modo que un informe vacío no oculte el otro que sí contiene resultados.
- Mantener separado el error de consulta del estado vacío.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `operational-reporting`: el panel comunica estados vacíos accesibles en consultas exitosas sin días.

## Impact

- `frontend/src/pages/Reportes.tsx` y su suite Vitest.
- Delta de OpenSpec para `operational-reporting` y referencia C-21 en `CHANGES.md`.
- Sin cambios en backend, persistencia, permisos, dependencias ni rutas HTTP.
