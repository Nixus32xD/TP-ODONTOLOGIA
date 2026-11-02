# Proposal

## Why

El proyecto necesita una forma repetible de ejecutar la agenda completa en un entorno aislado antes de considerar cualquier despliegue. Hoy la configuración Compose es local y de desarrollo, y todavía no demuestra arranque, migraciones ni recuperación integrados.

## What Changes

- Definir un paquete ejecutable para una sola clínica en red local controlada, con datos exclusivamente ficticios; este change no habilita publicación ni acceso público.
- Establecer contratos explícitos de configuración, persistencia, secretos, inicio, parada, migración, readiness, smoke y recuperación, incluyendo evidencias y rollback.
- Resolver la discrepancia actual: Compose selecciona PostgreSQL pero también establece `ODONTOLOGIA_DB`, mientras el entrypoint inicializa SQLite si esa ruta no existe.
- Mantener Redis como servicio preparado para cambios futuros; C-14 no implementa ni afirma un worker de recordatorios, que pertenece a C-17.
- Condicionar la aplicación y verificación integrada a completar la tarea 8.1 de C-12 y disponer de un engine Docker real. C-12 está en 20/21 y sigue activo, sin Archive.
- Tratar los cambios de configuración de despliegue como governance ALTO: revisar la propuesta antes de editar Dockerfiles, Compose, secretos o configuración operativa.

## Capabilities

### New Capabilities

- `controlled-deployment`: contrato para empaquetar y operar la agenda en un entorno aislado de una clínica, con configuración explícita, datos ficticios y recuperación verificable.

### Modified Capabilities

Ninguna. La API ya define readiness y los changes existentes especifican persistencia, migración y backup; C-14 coordina su operación sin cambiar esos contratos.

## Impact

- Paquete y documentación: `docker-compose.yml`, `backend/Dockerfile`, `backend/docker-entrypoint.sh`, `frontend/Dockerfile`, variables de entorno y guía raíz.
- Servicios previstos: FastAPI, PostgreSQL, frontend y Redis preparado para C-17. No se incluyen credenciales en el repositorio ni se habilitan puertos públicos.
- Validación futura: builds de ambas imágenes, inicio y readiness, migraciones explícitas, smoke de recepción con datos ficticios, y restauración seguida de una escritura de prueba. Estas verificaciones requieren Docker real y no están acreditadas todavía.
- Antes de aplicar, resolver el build Docker pendiente de C-12; antes de cerrar C-14, ejecutar y documentar la integración en un engine disponible. La validación estructural de esta propuesta OpenSpec no sustituye esas pruebas.
