# Proposal

## Why

C-01 expone el alta de turnos sin autenticar, y la administración de cuentas no existe. C-02 prepara PostgreSQL; antes de ampliar las operaciones del consultorio hace falta identificar al personal y aplicar permisos en el backend con cierre seguro.

## What Changes

- Incorporar usuarios del personal, sesiones revocables y gestión de cuentas restringida al administrador.
- Exigir credenciales válidas y una sesión activa para operar la API protegida.
- Aplicar la matriz aprobada: Administrador gestiona usuarios y tiene acceso a las operaciones disponibles; Recepción puede crear turnos; Profesional no obtiene acceso a la API hasta definir su agenda en C-08.
- Proteger `POST /turnos` sin cambiar validación, conflictos, persistencia ni errores del dominio C-01.
- Añadir migraciones explícitas para el esquema de autenticación en SQLite y PostgreSQL; no sembrar usuarios ni migrar al importar o crear la aplicación.
- Crear el primer Administrador sólo mediante un comando local interactivo, sin credenciales por defecto ni secretos en argumentos o logs.

## Capabilities

### New Capabilities
- `personal-auth`: autenticación, sesiones revocables, gestión de cuentas del personal y autorización por rol.

### Modified Capabilities
- `alta-turnos`: exigir autorización para `POST /turnos` y actualizar la descripción del contrato HTTP para incluir las rutas de sesión y administración de usuarios.

## Impact

Afecta `backend/odontologia/auth/`, `api.py`, configuración JWT, acceso a SQLite/PostgreSQL, SQLAlchemy/Alembic, el esquema SQLite explícito, pruebas HTTP y documentación. No incluye agenda propia del profesional, portal del paciente, MFA, integración de identidad externa, rate limiting avanzado, despliegue público ni datos personales/clínicos reales.
