## MODIFIED Requirements

### Requirement: Liveness y documentación local
El sistema SHALL exponer `GET /health` con HTTP 200 y estado `ok` independientemente de la disponibilidad de la base de datos, identificándolo como liveness y sin crear archivos ni afirmar readiness. SHALL publicar en `/openapi.json`, `/docs` y `/redoc` los contratos de alta, sesiones y administración de usuarios únicamente cuando `ODONTOLOGIA_ENTORNO` esté configurado explícitamente como `desarrollo`. En producción, o cuando la variable falte o contenga un valor desconocido, SHALL dejar esas rutas no disponibles (HTTP 404). SHALL mantener el servidor limitado a uso local sin proveedores externos ni acceso de pacientes.

#### Scenario: Health sin DB
- **GIVEN** una aplicación configurada con una agenda inexistente
- **WHEN** se consulta `GET /health`
- **THEN** responde HTTP 200 con estado `ok`, no crea archivos ni afirma readiness

#### Scenario: Documentación en desarrollo explícito
- **GIVEN** la aplicación creada con `ODONTOLOGIA_ENTORNO=desarrollo`
- **WHEN** se consultan OpenAPI, Swagger UI y ReDoc
- **THEN** `/openapi.json`, `/docs` y `/redoc` responden HTTP 200 y OpenAPI incluye contratos de turnos, administración y sesiones

#### Scenario: Documentación del único caso de uso
- **GIVEN** la aplicación creada en desarrollo explícito
- **WHEN** se consultan OpenAPI y las páginas de documentación
- **THEN** OpenAPI incluye los contratos de turnos, administración y sesiones, y las páginas responden HTTP 200

#### Scenario: Documentación deshabilitada en producción
- **GIVEN** la aplicación creada con `ODONTOLOGIA_ENTORNO=produccion`
- **WHEN** se consultan `/openapi.json`, `/docs` y `/redoc`
- **THEN** las tres rutas responden HTTP 404 sin publicar el esquema

#### Scenario: Configuración de entorno ausente o desconocida
- **GIVEN** `ODONTOLOGIA_ENTORNO` está ausente o tiene un valor no reconocido
- **WHEN** se crea la aplicación y se consultan las rutas de documentación
- **THEN** la documentación permanece deshabilitada y las rutas responden HTTP 404
