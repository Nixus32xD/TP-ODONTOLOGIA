# Proposal

## Why

La API ya valida JWT, sesiones persistidas y permisos por rol, pero conserva documentación HTTP pública en cualquier entorno, no limita intentos de login y carece de preparación separada de liveness, trazas de solicitud y logs seguros. Este change reduce abuso y facilita diagnosticar fallos del demo sin habilitar datos reales ni servicios externos.

## What Changes

- Limitar temporalmente los fallos de inicio de sesión por origen observado y hash del identificador normalizado: cinco fallos en cinco minutos, respuesta 429 con `Retry-After`, recuperación automática y sin bloqueo permanente. No confiar en `X-Forwarded-*`; documentar que el contador vive en el único proceso actual.
- Mantener `/health` como liveness y exponer `/ready` como comprobación de sólo lectura de la base, con 503 estable cuando no esté disponible y sin DDL ni creación de archivos.
- Emitir y propagar `X-Request-ID` UUID validado o generado; registrar únicamente ID, método, plantilla de ruta, estado, duración y código estable. No registrar ruta cruda, query, cuerpo, headers, IP, token, secreto, excepción ni stack trace.
- Devolver errores internos 500 genéricos, correlacionables por el ID de respuesta, y señales locales para fallos de base/backup; no agregar alertas externas.
- Conservar Swagger/OpenAPI en desarrollo y deshabilitar `/docs`, `/redoc` y `/openapi.json` en producción mediante modo explícito que falle cerrado si es inválido. Mantener autorización backend y el bearer sólo en memoria del frontend.
- Confirmar con pruebas que continúan vigentes los límites de rango/paginación y el comportamiento de sesión de C-11; no agregar dependencias externas de rate limiting u observabilidad.

## Capabilities

### New Capabilities
- `operational-observability`: correlación de solicitudes, logs permitidos, errores internos seguros, readiness y señales locales de indisponibilidad.

### Modified Capabilities
- `personal-auth`: añadir limitación temporal de fallos de inicio de sesión.
- `alta-turnos`: condicionar la exposición de OpenAPI/Swagger al entorno, conservando `/health` como liveness público y el uso local.

## Impact

Afecta configuración y middleware FastAPI, autenticación, endpoint de readiness, serialización de errores, logging de Uvicorn, pruebas backend y configuración/documentación del entorno local. No cambia roles ni contratos de turno, no persiste IPs o identificadores de login para limitar intentos, no modifica el almacenamiento de sesiones y no agrega proveedores ni telemetría remota. C-12 continúa pendiente del build Docker; C-13 no afirmará esa validación como realizada ni habilitará uso clínico real.
