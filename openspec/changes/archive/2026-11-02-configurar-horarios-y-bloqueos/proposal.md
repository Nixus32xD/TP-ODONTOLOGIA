# Proposal

## Why

El alta de turnos de C-01 controla solapamientos, pero aún permite cualquier horario porque la agenda no tiene disponibilidad configurada. C-07 incorpora horarios y bloqueos locales para que sólo se registren turnos completamente dentro de la disponibilidad del profesional y del box, preservando los turnos ya existentes.

## What Changes

- Agregar horarios semanales separados por profesional y box, con varios tramos diarios, zona `America/Argentina/Mendoza` y sin tramos que crucen medianoche.
- Agregar excepciones por fecha y bloqueos temporales; Administrador y Recepción podrán administrarlos.
- Restringir sólo las nuevas altas de C-01: un turno debe quedar íntegro dentro de un tramo disponible para ambos recursos y no solaparse con un bloqueo.
- Rechazar con HTTP 409 cualquier cambio de horario, excepción o bloqueo incompatible con un turno ya registrado, sea pasado o futuro; conservar la configuración anterior y el historial completo.
- Validar los turnos asociados al recurso que se modifica, de modo que, tras migrar turnos C-01, se pueda abrir progresivamente primero la agenda del profesional y luego la del box; las altas nuevas requieren ambos recursos abiertos.
- Registrar las mutaciones de horarios, excepciones y bloqueos con la política de auditoría metadata-only y transacción atómica existente.
- Mantener el sistema local, sin feriados automáticos, proveedores externos ni interfaz gráfica.
- Exigir SQLite v5 o Alembic 0006 para la API; los turnos en un esquema migrado sin horarios quedan cerrados. El servicio standalone C-01 sobre una base antigua sin esquema de autenticación mantiene su contrato previo hasta que se migre explícitamente.

## Capabilities

### New Capabilities
- `agenda-availability`: configuración semanal, excepciones fechadas, bloqueos y validación de disponibilidad.

### Modified Capabilities
- `alta-turnos`: exigir disponibilidad para el profesional y el box al crear un turno, sin cambiar el cuerpo, formato UTC ni exclusiones C-01.
- `audit-trail`: incorporar auditoría de cambios a horarios, excepciones y bloqueos.

## Impact

- Dominio de agenda y API FastAPI, persistencia SQLite y PostgreSQL, pruebas, migraciones y OpenAPI.
- Nueva migración SQLite esperada a versión 5 y revisión Alembic esperada `20261102_0006_agenda_availability`, después de la revisión real `20261102_0005_resource_catalogs`.
- Sin cambios de UI ni integraciones externas. Se fija `tzdata` para que el identificador IANA funcione también en Windows; el sistema requiere configurar disponibilidad antes de volver a registrar turnos nuevos.
