# Spec Delta

## Purpose

Proporciona señales locales y seguras para correlacionar solicitudes, distinguir liveness de readiness y diagnosticar fallos sin exponer datos de pacientes, credenciales o detalles internos.

## ADDED Requirements

### Requirement: Correlacionar solicitudes con identificadores de petición
Cada respuesta HTTP SHALL incluir `X-Request-ID` con un UUID. El sistema SHALL aceptar un identificador entrante sólo si es un UUID válido; en otro caso SHALL generar uno nuevo. El identificador SHALL NOT conceder acceso ni alterar autorización.

#### Scenario: Identificador entrante válido
- **GIVEN** una petición con `X-Request-ID` UUID válido
- **WHEN** el servidor responde
- **THEN** devuelve el mismo UUID canónico en `X-Request-ID` y lo utiliza para correlacionar el evento operativo

#### Scenario: Identificador entrante inválido o ausente
- **GIVEN** una petición sin `X-Request-ID` o con un valor inválido o excesivo
- **WHEN** el servidor responde
- **THEN** genera un UUID nuevo y no refleja el valor inválido recibido

### Requirement: Registrar eventos HTTP con una lista permitida de campos
El sistema SHALL registrar método, plantilla de ruta, estado, duración, código estable e identificador de petición. SHALL NOT registrar ruta cruda, parámetros de consulta, cuerpo, headers, dirección IP, bearer, credenciales, secreto, excepción ni stack trace.

#### Scenario: Solicitud protegida
- **GIVEN** una petición válida, fallida o no autorizada
- **WHEN** finaliza su respuesta
- **THEN** el evento operativo contiene sólo los campos permitidos y la ruta usa su plantilla sin valores de parámetros

#### Scenario: Valor sensible enviado en la petición
- **GIVEN** una contraseña, bearer o dato de paciente en el cuerpo o en una cabecera
- **WHEN** la solicitud genera un evento operativo
- **THEN** esos valores y el contenido crudo no aparecen en el evento

### Requirement: Devolver errores internos seguros y correlacionables
Ante una excepción inesperada, el sistema SHALL responder HTTP 500 con un código y mensaje públicos estables, sin excepción, consulta, ruta local ni stack trace. SHALL incluir el `X-Request-ID` de la respuesta.

#### Scenario: Fallo interno inesperado
- **GIVEN** una ruta que produce una excepción no controlada
- **WHEN** el servidor procesa la respuesta
- **THEN** devuelve 500 genérico, incluye un UUID en `X-Request-ID` y no revela el detalle interno en cuerpo o logs

### Requirement: Separar readiness de liveness y dar señales locales de fallo
`GET /ready` SHALL comprobar sólo conectividad de lectura a la base seleccionada, sin DDL, migración ni creación de archivos. SHALL responder 200 cuando la consulta simple funciona y 503 con código estable cuando no. Los fallos de operaciones locales de backup SHALL conservar un resultado no-cero y código estable sin revelar secretos o rutas.

#### Scenario: Liveness con base indisponible
- **GIVEN** la base de agenda no existe o no responde
- **WHEN** se consulta `GET /health`
- **THEN** mantiene HTTP 200 e informa liveness sin crear la base ni afirmar readiness

#### Scenario: Readiness disponible
- **GIVEN** la base seleccionada acepta una consulta de lectura
- **WHEN** se consulta `GET /ready`
- **THEN** responde 200 con estado ready sin mutar datos ni esquema

#### Scenario: Readiness no disponible
- **GIVEN** la base no puede abrirse o ejecutar la consulta
- **WHEN** se consulta `GET /ready`
- **THEN** responde 503 con un código estable, no revela URL o credenciales y no ejecuta DDL

#### Scenario: Fallo de backup local
- **GIVEN** una operación explícita de backup o restauración falla
- **WHEN** termina la operación CLI
- **THEN** devuelve salida no-cero con código estable sin mostrar secreto, URL de base ni detalle privado del proceso
