# Design

## Context

`Paciente` hoy sólo contiene un ID ficticio. SQLite es la persistencia predeterminada; PostgreSQL usa SQLAlchemy/Alembic y la revisión `20261101_0003_audit`. La importación de C-02 lee agendas C-01 con esquema legado. Las operaciones de escritura auditables de C-04 usan una transacción común.

## Goals / Non-Goals

**Goals:** mantener un único contrato de pacientes para SQLite y PostgreSQL; conservar IDs y turnos existentes; validar el acceso en el backend; incluir las mutaciones en la política de auditoría.

**Non-Goals:** historia clínica, identificaciones gubernamentales, fecha de nacimiento, notificaciones, importación de datos reales, eliminar físicamente pacientes o cambiar la exclusión temporal de C-01.

## Decisions

- **Campos y normalización:** agregar `nombre` obligatorio (1–120 caracteres Unicode tras recortar extremos y colapsar espacios consecutivos), `telefono` opcional y `activo` booleano. El teléfono admite 7–15 dígitos y sólo `+`, espacios, paréntesis y guiones adicionales; se valida pero conserva su escritura. No se deduplican nombres ni teléfonos: pueden existir homónimos y teléfonos compartidos.
- **Identidad:** preservar los IDs existentes y generar UUID para nuevas fichas. Las migraciones de datos C-01 rellenan un nombre ficticio derivado del ID (`Paciente de demostración <id>`), teléfono nulo y estado activo. La importación de C-02 desde SQLite legado crea esos mismos campos sin escribir en la fuente.
- **Permisos:** Administrador y Recepción crean, leen y actualizan los campos de contacto. Sólo Administrador cambia `activo`; los demás roles no pueden consultar ni modificar fichas.
- **Baja lógica:** `DELETE /pacientes/{id}` desactiva; `PATCH` permite reactivar sólo a Administrador. Las fichas inactivas se incluyen en consultas administrativas y no se pueden usar para nuevos turnos. Las claves foráneas y filas históricas se conservan.
- **Transacciones:** usar `Session` del engine ya configurado para ambos motores. En cada mutación, guardar la ficha y registrar su evento antes del commit. Las lecturas usan páginas acotadas, orden por ID y seleccionan explícitamente los campos de respuesta.
- **Auditoría:** extender el catálogo cerrado de acciones y recursos de C-04 con cuatro pares paciente-acción. El ID UUID cabe en el campo opaco existente; nombre y teléfono no se pasan al módulo de auditoría. La combinación acción/recurso/resultado continúa restringida por la aplicación y por DDL.
- **Esquema:** añadir una revisión Alembic encadenada para PostgreSQL. En SQLite, subir `auth_schema_version` a 3 en la migración explícita ya existente; versionar los campos junto con el esquema de acceso evita que una app sin migrar lea/escriba fichas parcialmente. Las agendas nuevas se crean con el esquema actual; `crear_turno` mantiene soporte para agendas C-01 previas hasta completar migración explícita, sin alterar datos al arrancar.
- **Errores:** conservar el formato público actual; usar 404 para ID inexistente, 409 para duplicidad de ID generada o paciente inactivo al crear turno, 422 para campos inválidos, 401/403 para sesión/rol y 503 cuando no se pueda confirmar el esquema/almacenamiento.

## Risks / Trade-offs

- [La evolución de C-01 SQLite puede afectar una agenda existente] → migración transaccional, explícita, comprobación de versión y pruebas de preservación de IDs/turnos.
- [Una ficha podría exponerse por una nueva ruta] → exigir sesión y comprobar Administrador/Recepción en backend; Probar 401/403 sin acceso a DB.
- [Una mutación puede quedar sin rastro] → escritura de auditoría y ficha dentro de la misma transacción; inyectar fallos de auditoría en SQLite y PostgreSQL.
- [Los datos de contacto son personales aunque el demo use valores ficticios] → no usar datos reales; almacenar sólo nombre y teléfono opcional; no copiar campos de ficha a logs.

## Migration Plan

1. Añadir esquema SQLite v3 y migración Alembic siguiente, ambas sin eliminar tablas o columnas.
2. Para SQLite, ejecutar la migración sólo mediante el comando local explícito; para PostgreSQL, aplicar Alembic hasta `head` antes de usar las rutas.
3. Actualizar importador para leer C-01 legacy en modo sólo lectura y crear pacientes con valores de demostración conservando claves y turnos.
4. No ofrecer downgrade automático que suprima nombres/contactos o revierta el estado; restaurar sólo desde una copia controlada si una migración falla.

## Open Questions

Ninguna decisión del alcance queda pendiente. La etiqueta del nombre de demostración conserva el ID histórico y no pretende ser una identidad real.
