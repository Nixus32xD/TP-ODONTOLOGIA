# Proposal

## Why

La agenda C-01 conserva su contrato sobre SQLite local, mientras que la cátedra fijó PostgreSQL y SQLAlchemy para el sistema. Este change agrega una transición explícita y auditable sin borrar ni migrar datos al iniciar la API.

## What Changes

- Agregar persistencia PostgreSQL con SQLAlchemy y versionado incremental de esquema.
- Proveer una migración manual y transaccional desde una agenda SQLite C-01, preservando recursos, turnos e identificadores.
- Permitir elegir explícitamente SQLite o PostgreSQL; SQLite sigue siendo el valor predeterminado y el contrato C-01 permanece disponible.
- Aplicar las mismas validaciones, errores, exclusión por profesional/box, prioridad, adyacencia y respuesta HTTP en el adaptador PostgreSQL.
- No ejecutar upgrades ni importaciones de datos al importar módulos o iniciar la API.

## Capabilities

### New Capabilities

- `agenda-postgresql`: registro de turnos sobre PostgreSQL con la semántica de C-01 y selección explícita del backend.
- `agenda-migration`: versionado incremental del esquema y traslado explícito, seguro y verificable de una agenda ficticia SQLite a PostgreSQL.

### Modified Capabilities

- None. El contrato C-01 existente y su backend SQLite predeterminado se conservan.

## Impact

- Afecta `backend/odontologia/db/`, configuración, adaptador de agenda, API, Docker Compose y dependencias.
- Incorpora Alembic, SQLAlchemy y psycopg como dependencias del backend.
- La ruta SQLite continúa sin cambiar por defecto; elegir PostgreSQL exige configurar su URL, aplicar el esquema y ejecutar la migración de forma explícita.
- No modifica autenticación, autorización, auditoría, catálogo, horarios, estados, interfaz ni integraciones externas.
