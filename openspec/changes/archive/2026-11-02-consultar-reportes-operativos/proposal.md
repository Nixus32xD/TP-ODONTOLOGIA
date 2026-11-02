# Proposal

## Why

Administrador y Recepción necesitan revisar la capacidad utilizada y el ciclo de turnos, y Administración necesita resumir movimientos monetarios del ledger C-19. Los reportes locales agregados dan una vista operativa reproducible sin revelar fichas, pacientes ni datos clínicos.

## What Changes

- Agregar reporte diario de agenda por rango local `[desde, hasta)` acotado a 31 días en `America/Argentina/Mendoza`.
- Separar turnos reservados/confirmados, atendidos, ausentes y cancelados; informar minutos y ocupación contra disponibilidad real de profesionales y boxes, calculada desde horarios, excepciones y bloqueos.
- Agregar reporte diario de cargos, cobros, reversiones, neto y saldo al cierre, reutilizando el ledger exacto de C-19.
- Permitir reportes de agenda a Administrador/Recepción y reportes monetarios sólo a Administrador.
- Exponer JSON y CSV UTF-8 determinista usando la misma consulta; CSV sin PII ni contenido clínico y seguro contra fórmulas.
- Añadir un panel local de filtros/resultados y descargas.
- No agregar recomendaciones de productividad, analítica de pacientes, infraestructura o exportaciones identificables.

## Capabilities

### New Capabilities
- `operational-reporting`: consultas diarias agregadas y exportables de agenda y ledger financiero.

### Modified Capabilities

## Impact

- Backend: módulo de consultas agregadas, endpoints JSON/CSV y dependencias de roles existentes.
- Frontend: vista de reportes en React.
- Dominio: reusar disponibilidad C-07, estados C-09 y ledger C-19; sin cambios en cargos o turnos.
- Verificación: fechas límites/zona, recursos con disponibilidad cero, atribución por fecha programada, cálculos exactos del ledger, permisos y equivalencia entre panel/CSV.
