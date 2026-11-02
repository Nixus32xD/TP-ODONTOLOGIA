# Tasks

## 1. Configuración explícita de documentación

- [x] 1.1 Agregar pruebas para `ODONTOLOGIA_ENTORNO=desarrollo`, `produccion`, ausente y desconocido; comprobar los estados de `/docs`, `/redoc` y `/openapi.json` y actualizar la configuración FastAPI para que sólo desarrollo explícito los habilite.
- [x] 1.2 Documentar los valores admitidos y el modo local de desarrollo en la configuración/guía existente; verificar que el ejemplo local habilite Swagger explícitamente y que el valor predeterminado no exponga el esquema.

## 2. Correlación, logging permitido y errores internos

- [x] 2.1 Escribir pruebas para `X-Request-ID` UUID válido, ausente, inválido y excesivo; implementar validación/generación UUID y comprobar que todas las respuestas, incluidas las de error, devuelvan el identificador canónico.
- [x] 2.2 Escribir pruebas que inspeccionen los eventos emitidos para solicitudes válidas, no autorizadas y con datos sensibles; implementar el log estructurado con sólo ID, método, plantilla, estado, duración y código estable, y verificar que no incluya ruta cruda, query, body, headers, IP, token, excepción ni stack trace.
- [x] 2.3 Escribir una prueba de excepción no controlada con un secreto centinela; implementar el handler HTTP 500 genérico y la configuración de logging necesaria, y verificar que la respuesta y logs no revelen el secreto ni detalles internos.

## 3. Limitación temporal de inicio de sesión

- [x] 3.1 Escribir pruebas para cinco fallos, sexto intento con 429 y `Retry-After`, expiración de ventana, limpieza tras login correcto y separación por origen/cuenta normalizada; implementar el control en memoria usando sólo peer address y hash de cuenta, y verificar todos esos casos.
- [x] 3.2 Añadir pruebas de límites de memoria, headers reenviados no confiables y fallos de validación/DB no contabilizados; implementar expiración y capacidad acotada de buckets sin bloqueo permanente y documentar que el control sólo coordina el proceso actual.
- [x] 3.3 Agregar una prueba sincronizada de seis logins concurrentes y verificar que sólo cinco llegan a verificar credenciales; reservar espacios atómicamente, contar sólo fallos de credenciales y liberar espacios en éxito o error de DB sin fugas.

## 4. Readiness y errores de operaciones locales

- [x] 4.1 Escribir pruebas para `/ready` con DB disponible/no disponible y para `/health` con DB ausente; implementar el probe de sólo lectura `SELECT 1` y verificar 200/503 estables, que no ejecute DDL y que no cree un archivo SQLite faltante.
- [x] 4.2 Escribir pruebas para errores de backup/restauración con datos sensibles centinela; preservar la salida no-cero y emitir un código estable, verificando que salida y logs no expongan secretos, URL, rutas privadas ni detalle de excepción.

## 5. Regresión e integración

- [x] 5.1 Ejecutar las pruebas backend enfocadas y la suite completa; confirmar que siguen vigentes contratos JWT/sesión, revocación, RBAC, límites de rangos/paginación, `/health` y comportamiento frontend de token sólo en memoria, y corregir cualquier regresión de este change.
- [x] 5.2 Revisar la configuración local y la documentación resultante con valores explícitos; verificar que no se agregaron dependencias de telemetría/rate limiting ni configuración que confíe en `X-Forwarded-*`.
