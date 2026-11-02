# Proposal

## Why

Profesionales y boxes hoy sólo existen como IDs de seed sin administración ni estado, y el dominio no ofrece un catálogo de prestaciones. C-06 permite mantener esos recursos ficticios y sus referencias de forma explícita, sin cambiar retroactivamente el alta de turnos de C-01.

## What Changes

- Añadir catálogos autenticados y paginados de profesionales, boxes y prestaciones; habilitar alta, consulta por ID, listado y actualización.
- Incorporar nombre y estado activo en profesionales y boxes, y nombre, duración positiva en minutos y estado activo en prestaciones.
- Permitir sólo a Administrador desactivar o reactivar registros; conservar turnos históricos y rechazar nuevas altas que referencien profesionales o boxes inactivos.
- Auditar las mutaciones de catálogos con metadatos permitidos dentro de la misma transacción; mantener la consulta de auditoría paginada sólo para Administrador.
- Mantener prestaciones como catálogo independiente: C-01 no exige ni recibe una prestación, no calcula su duración y no agrega compatibilidad profesional-box ni profesional-prestación.

## Capabilities

### New Capabilities
- `resource-catalogs`: administración de profesionales, boxes y prestaciones ficticios.

### Modified Capabilities
- `alta-turnos`: las altas nuevas rechazan profesionales o boxes conocidos pero inactivos y conservan C-01 para el resto.
- `audit-trail`: incorpora eventos de mutación de catálogos con la política existente de metadatos, atomicidad, retención y lectura.

## Impact

- API FastAPI, validación y persistencia SQLite/PostgreSQL; migración SQLite y nueva revisión Alembic.
- Matriz de permisos, lista de eventos de auditoría, tests, OpenAPI, documentación del backend y evidencia del cambio.
- Sin dependencias nuevas, integraciones externas, datos reales ni cambios a la forma o duración libre de `POST /turnos` de C-01.
