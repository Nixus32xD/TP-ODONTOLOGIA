# Proposal

## Why

Recepción hoy puede registrar y gestionar turnos, pero no consultar una agenda acotada ni obtener opciones libres calculadas con horarios, bloqueos y estados vigentes. C-08 agrega consultas de sólo lectura para operar la agenda y habilita al Profesional con acceso estrictamente limitado a su propio calendario.

## What Changes

- Incorporar `GET /turnos` con rango obligatorio de fechas-hora con offset, máximo de 31 días, filtros opcionales y paginación predeterminada de 50, máxima de 100.
- Administrador y Recepción consultan los turnos permitidos en todos los recursos. Profesional consulta únicamente los turnos de su vínculo de profesional, sin poder delegar otro ID; su respuesta contiene sólo horario y nombre del paciente, sin teléfono.
- Permitir al Administrador asignar a cada cuenta Profesional un vínculo único a un profesional activo al crearla o cambiarla; el esquema y las sesiones fallan cerrados si el vínculo no es válido. No se habilitan acciones de escritura al Profesional.
- Incorporar `GET /disponibilidad` para una fecha local de Mendoza, profesional, box y duración positiva. Ofrece inicios cada 15 minutos que caben en los horarios/excepciones de C-07, respetan recursos activos, bloqueos y ocupación de C-09.
- Las opciones de disponibilidad son orientativas: `POST /turnos` conserva su validación serializada y vuelve a comprobar las reglas antes de confirmar.
- Mantener C-08 como consulta pura: sin altas, cambios de estado, cancelación ni reprogramación.

## Capabilities

### New Capabilities

- `agenda-query`: consulta paginada de turnos, límites de visibilidad por rol y sugerencias de horarios disponibles.

### Modified Capabilities

- `personal-auth`: permitir cuentas de Profesional con vínculo único a un profesional activo y autenticación de sólo lectura, sin acceso a recursos de otros profesionales.

## Impact

- FastAPI, módulos de consulta, filtros y modelos de respuesta; reutilización de C-07 y C-09 para disponibilidad.
- SQLite v7 y PostgreSQL Alembic 0008 para vínculo único de cuenta a profesional y rol Profesional; migración preserva cuentas, sesiones y auditoría existentes.
- Validación de identidad/sesión y administración de cuentas; OpenAPI y documentación local.
- Pruebas SQLite y PostgreSQL aislado para filtros, límites, privacidad por rol, vínculos, recursos inactivos, bloqueos y cambios concurrentes con altas.
