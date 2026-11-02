# Design

## Context

Ver `proposal.md` para la motivación y `specs/` para contratos. C-01 usa SQLite y FastAPI; C-02 permite PostgreSQL optativo con SQLAlchemy/Alembic. La app no debe conectarse ni migrar al importarse o crearse. La matriz de roles fue aprobada: Administrador administra cuentas y usa las operaciones disponibles; Recepción crea turnos; Profesional no accede hasta C-08.

## Goals / Non-Goals

**Goals:**
- Aplicar autenticación y autorización en el backend, tanto con SQLite predeterminado como PostgreSQL optativo.
- Habilitar revocación inmediata de una sesión ya emitida.
- Mantener secretos fuera del repositorio, defaults cerrados y rutas públicas limitadas a liveness/documentación local.
- Migrar el esquema de usuarios de forma explícita, sin modificar agendas durante importación o creación de la app.

**Non-Goals:**
- Habilitar acceso del Profesional, pacientes, portal, proveedor externo de identidad, MFA, refresh tokens, rate limiting o despliegue público.
- Cifrar datos en reposo, mantener un registro de auditoría inmutable o proveer recuperación automática de contraseñas; pertenecen a changes posteriores.

## Decisions

### Almacenamiento y migraciones explícitas

Agregar modelos de cuentas y sesiones a la metadata SQLAlchemy y una revisión Alembic sobre C-02 para PostgreSQL. SQLite recibe una migración versionada separada y explícita. Ambas requieren que el esquema C-01/C-02 ya exista y fallan si encuentran tablas incompatibles. Importar módulos, crear la app y consultar `/health` no ejecutan DDL. Bootstrap del administrador ocurre sólo después de migrar.

**Alternativa:** crear tablas al primer login simplifica desarrollo, pero daría privilegios DDL a la API y ocultaría instalaciones incompletas; se descarta.

### Derivación de contraseñas

Usar identificadores ASCII normalizados con `casefold`, longitud 3–64 y caracteres `[a-z0-9._-]`. Aceptar contraseñas de 12–128 caracteres. Usar `hashlib.scrypt` de la biblioteca estándar con sal aleatoria única y parámetros/versionado guardados junto al hash. Comparar de forma constante y ejecutar una derivación ficticia al consultar un usuario inexistente para reducir enumeración por tiempo. No guardar ni registrar contraseñas. No se agregan dependencias de hashing.

**Alternativa:** texto plano o SHA-256 rápido no resiste un volcado de la tabla; no se permiten.

### Tokens y revocación

Emitir JWT HS256 con `PyJWT`, sujeto `user_id`, sesión/JTI aleatoria, rol y expiración de 30 minutos. Exigir `JWT_SECRETO` aleatorio local de al menos 32 bytes y rechazar el marcador de `.env.example`. No permitir algoritmo arbitrario. Persistir JTI, usuario, expiración y revocación. Cada ruta protegida verifica firma/expiración y vuelve a consultar sesión y estado/rol actuales; logout, desactivación y cambio de rol invalidan el acceso inmediatamente.

**Alternativa:** aceptar sólo firma/expiración evita lecturas de sesión, pero no permite revocación inmediata; se descarta.

### Roles y rutas

Representar sólo roles `administrador` y `recepcion` habilitados. Profesional no se provisiona ni inicia sesión hasta C-08; esto evita conceder un token sin operaciones permitidas. `POST /turnos` admite ambos roles; `GET /usuarios`, `POST /usuarios` y `PATCH /usuarios/{id}` sólo Administrador. Recepción puede consultar y cerrar su propia sesión. `/health` permanece público y no consulta DB; `/sesiones` sólo acepta credenciales, y el resto usa Bearer.

El bootstrap es `python -m odontologia.auth.bootstrap_admin`: requiere DB/esquema explícitos, solicita identificador y contraseña con entrada oculta y se niega si ya hay Administrador. No recibe contraseñas como argumentos ni ofrece valor predeterminado.

**Alternativa:** crear un usuario conocido dentro del seed facilitaría la demo, pero filtraría credenciales repetibles; se descarta.

### Configuración y fallas

La app puede iniciar y responder liveness sin `JWT_SECRETO`; todas las rutas protegidas/autenticadas responden 503 `autenticacion_no_configurada` antes de tocar la agenda. La presencia de esquema ausente/incompatible tampoco activa fallback ni DDL. `401` cubre credencial/token inválido o revocado; `403` es sólo identidad válida sin permiso. Mensajes públicos genéricos; detalles técnicos no se devuelven ni loguean.

**Alternativa:** fallar el proceso completo por falta de secreto haría inaccesible `/health`; el cierre por ruta conserva liveness sin abrir operaciones.

## Risks / Trade-offs

- **[Riesgo]** Validar cada sesión en DB añade una lectura por petición. → Aceptarlo para revocación inmediata y el tamaño de este consultorio.
- **[Riesgo]** Usar token bearer sobre HTTP fuera de loopback expondría credenciales. → Mantener el servicio local; TLS y despliegue son gates de C-14 y C-13.
- **[Riesgo]** Perder `JWT_SECRETO` invalida sesiones emitidas. → No persistir claves en el repo; regenerar secreto requiere que usuarios vuelvan a iniciar sesión.
- **[Riesgo]** La migración puede fallar en una DB ya usada. → No alterar tablas existentes silenciosamente; probar migraciones sobre copias temporales en SQLite y PostgreSQL.
- **[Riesgo]** Un administrador puede desactivar su propia última cuenta. → El backend rechaza desactivar/degradar al último Administrador activo.

## Migration Plan

1. Respaldar una copia de trabajo de la agenda ficticia; no usar datos reales.
2. Para SQLite, ejecutar la migración explícita; para PostgreSQL, `alembic upgrade head`. No arrancar la API como sustituto.
3. Configurar `JWT_SECRETO` fuera del repo y ejecutar el bootstrap local una sola vez.
4. Verificar acceso por rol, alta con `Authorization: Bearer`, revocación y errores 401/403.
5. Para rollback, conservar la copia previa y no borrar cuentas ni sesiones por acción del sistema. Esta migración agrega sólo tablas y no tiene downgrade destructivo.
