# Spec Delta

## MODIFIED Requirements

### Requirement: Adaptador FastAPI local
El sistema SHALL exponer `POST /turnos` mediante FastAPI y devolver 201 sólo tras persistir un alta UTC válida. SHALL exigir una sesión bearer vigente de Administrador o Recepción antes de procesar la solicitud. SHALL aceptar el objeto JSON de cinco campos definido por C-01, con IDs string y fechas ISO 8601 con offset y minuto exacto; SHALL rechazar campos extra y timestamps numéricos. SHALL NOT crear ni inicializar la agenda al importar, crear la app o recibir peticiones.
#### Scenario: Alta HTTP persistida
- **GIVEN** agenda preparada, sesión vigente de Administrador o Recepción y cuerpo válido con recursos libres
- **WHEN** se ejecuta POST /turnos
- **THEN** devuelve 201, ID positivo e instantes UTC y existe una sola fila persistida

#### Scenario: JSON inválido o coerción no permitida
- **GIVEN** sesión autorizada y cuerpo ausente, mal formado, no objeto, con campos adicionales, ID numérico o fecha epoch
- **WHEN** se ejecuta POST /turnos
- **THEN** devuelve 422 entrada_invalida sin alta ni detalles internos

#### Scenario: Sesión ausente o inválida
- **GIVEN** falta el token o la sesión es inválida, expirada o revocada
- **WHEN** se ejecuta POST /turnos
- **THEN** devuelve 401 antes de ejecutar el dominio y no persiste un turno

#### Scenario: Rol no autorizado
- **GIVEN** una sesión autenticada sin permiso de crear turnos
- **WHEN** se ejecuta POST /turnos
- **THEN** devuelve 403 sin ejecutar el dominio ni modificar la agenda

### Requirement: Errores HTTP del dominio
El adaptador SHALL mapear entrada_invalida a 422, recurso_desconocido a 404, conflictos de recursos a 409, agenda_ocupada a 503 y almacenamiento_error a 500 mediante JSON con codigo, campo y mensaje público. SHALL conservar reglas, prioridad profesional/box, rollback y ausencia de reintentos del dominio.

#### Scenario: Conflictos HTTP independientes
- **GIVEN** un turno ocupa profesional-A y box-A
- **WHEN** se solicita igual intervalo cambiando sólo box o sólo profesional
- **THEN** responde 409 con el conflicto correspondiente y conserva un único registro

#### Scenario: Fallo o contención HTTP
- **GIVEN** agenda ausente, corrupta o bloqueada más allá del timeout
- **WHEN** se solicita alta válida
- **THEN** responde 500 almacenamiento_error o 503 agenda_ocupada, sin éxito ficticio ni fuga de rutas

### Requirement: Liveness y documentación local
El sistema SHALL exponer GET /health con 200 y status ok independientemente de la DB, identificándolo como liveness. SHALL publicar en /openapi.json, /docs y /redoc los contratos de alta, sesiones y administración de usuarios, con estados y modelos de entrada/salida. SHALL mantener servidor limitado a uso local sin proveedores externos ni acceso de pacientes.

#### Scenario: Health sin DB
- **GIVEN** una app configurada con una agenda que no existe
- **WHEN** se consulta GET /health
- **THEN** devuelve 200 status ok sin crear el archivo ni afirmar readiness de almacenamiento

#### Scenario: Documentación del único caso de uso
- **GIVEN** la aplicación creada
- **WHEN** se consulta OpenAPI y documentación
- **THEN** OpenAPI contiene las operaciones protegidas de turnos y administración, las rutas de sesión, GET /health público y los estados esperados, y las páginas responden 200
