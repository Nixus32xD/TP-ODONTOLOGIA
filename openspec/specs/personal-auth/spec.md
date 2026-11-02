# personal-auth Specification

## Purpose

Permitir que el personal autorizado ingrese al sistema, administre las cuentas de trabajo y opere según permisos comprobados en el backend.

## Requirements

### Requirement: Crear la primera cuenta administradora de forma local
El sistema SHALL permitir crear el primer Administrador sólo mediante una operación local explícita que solicite la contraseña sin mostrarla. SHALL rechazar el bootstrap si ya existe un Administrador y SHALL NOT incluir cuentas, contraseñas ni secretos predeterminados.

#### Scenario: Bootstrap inicial válido
- **GIVEN** el esquema de autenticación está migrado y no existe una cuenta Administrador
- **WHEN** un operador ejecuta el comando local e ingresa credenciales válidas
- **THEN** se crea una cuenta Administrador y la contraseña no aparece en pantalla, salida ni logs

#### Scenario: Administrador activo ya existente
- **GIVEN** ya existe una cuenta Administrador activa
- **WHEN** se ejecuta el comando de bootstrap
- **THEN** se rechaza sin modificar usuarios ni sesiones existentes

### Requirement: Administrar cuentas del personal
El sistema SHALL permitir a un Administrador autenticado crear y consultar cuentas de Administrador y Recepción, y cambiar su rol o estado activo. Identificadores SHALL normalizarse con casefold y trim y cumplir el formato ASCII de 3–64 caracteres; contraseñas de 12–128 caracteres SHALL almacenarse sólo como derivación con sal. Respuestas SHALL omitir credenciales, hashes, secretos y tokens. Desactivar una cuenta o cambiar su rol SHALL revocar sus sesiones.

#### Scenario: Recepción no administra cuentas
- **GIVEN** una sesión válida con rol Recepción
- **WHEN** intenta listar, crear o cambiar una cuenta
- **THEN** recibe 403 y no se modifica el almacenamiento

#### Scenario: Alta de cuenta permitida
- **GIVEN** un Administrador autenticado y un identificador no utilizado
- **WHEN** crea una cuenta Administrador o Recepción con contraseña válida
- **THEN** la cuenta queda persistida y la respuesta omite credenciales y secretos

#### Scenario: Desactivación revoca sesiones
- **GIVEN** una cuenta con sesiones activas
- **WHEN** un Administrador la desactiva o cambia su rol
- **THEN** sus sesiones previas dejan de autorizar peticiones

#### Scenario: Identificador o contraseña fuera de política
- **GIVEN** un identificador con formato inválido o una contraseña menor a 12 o mayor a 128 caracteres
- **WHEN** un Administrador intenta crear una cuenta
- **THEN** recibe 422 sin guardar la cuenta ni mostrar la contraseña
#### Scenario: Identificador duplicado
- **GIVEN** ya existe una cuenta con el identificador normalizado
- **WHEN** se intenta crear otra con el mismo identificador
- **THEN** se rechaza sin revelar datos de la cuenta existente

### Requirement: Iniciar sesiones sólo con credenciales válidas
El sistema SHALL emitir una sesión firmada sólo para una cuenta activa Administrador o Recepción con credenciales válidas. Las respuestas de autenticación fallida SHALL ser genéricas y no distinguir entre cuenta inexistente, inactiva o contraseña incorrecta.

#### Scenario: Inicio de sesión válido
- **GIVEN** una cuenta activa con contraseña válida
- **WHEN** se inicia sesión
- **THEN** se devuelve un token bearer con expiración limitada y datos mínimos de cuenta, sin exponer la derivación de contraseña

#### Scenario: Credenciales inválidas
- **GIVEN** credenciales incorrectas, cuenta inexistente o inactiva
- **WHEN** se solicita una sesión
- **THEN** se devuelve 401 con el mismo mensaje público y no se crea una sesión utilizable

### Requirement: Consultar y revocar la sesión actual
El sistema SHALL permitir a una cuenta autenticada consultar su identidad y rol actuales y revocar su propia sesión. La revocación SHALL invalidar el token inmediatamente, incluso antes de su expiración firmada.

#### Scenario: Sesión vigente
- **GIVEN** un token asociado a una sesión no revocada y una cuenta activa
- **WHEN** se consulta la sesión actual
- **THEN** se devuelve sólo el identificador, rol y expiración de la cuenta

#### Scenario: Cierre de sesión
- **GIVEN** una sesión vigente
- **WHEN** la cuenta cierra su sesión
- **THEN** el token queda revocado y una repetición de la petición protegida recibe 401

#### Scenario: Token expirado, revocado o manipulado
- **GIVEN** un token expirado, revocado, malformado o con firma inválida
- **WHEN** se consulta una ruta protegida
- **THEN** recibe 401 y no se ejecuta la operación

### Requirement: Aplicar el menor privilegio aprobado
El backend SHALL autorizar cada operación según el rol de la cuenta. El Administrador puede gestionar las operaciones disponibles y las cuentas; Recepción puede crear turnos pero no administrar cuentas; las cuentas de Profesional no se habilitan hasta un change posterior que defina su agenda propia.

#### Scenario: Recepción crea un turno
- **GIVEN** una sesión vigente de Recepción
- **WHEN** solicita un turno válido
- **THEN** la API ejecuta el contrato de alta C-01

#### Scenario: Profesional sin alcance de agenda
- **GIVEN** una identidad asociada a Profesional
- **WHEN** intenta iniciar sesión o acceder a una operación del sistema
- **THEN** no obtiene acceso hasta que otro change habilite explícitamente su agenda

#### Scenario: Administrador tiene acceso autorizado
- **GIVEN** una sesión vigente de Administrador
- **WHEN** usa una operación disponible para el personal
- **THEN** se aplica la operación correspondiente y quedan vigentes sus reglas de dominio

### Requirement: Fallar cerrado ante configuración de seguridad incompleta
El sistema SHALL requerir un secreto de firma local no versionado con longitud mínima de 32 bytes y una sesión persistida vigente para autorizar peticiones. Si falta configuración, almacenamiento o esquema, SHALL rechazar la operación sin saltarse autenticación ni crear el esquema automáticamente.

#### Scenario: Secreto ausente o débil
- **GIVEN** JWT_SECRETO está ausente o no alcanza la longitud mínima
- **WHEN** se solicita una operación de autenticación o protegida
- **THEN** devuelve 503 antes de acceder al dominio y GET /health sigue disponible

#### Scenario: Almacenamiento de sesión inaccesible
- **GIVEN** no puede confirmarse la vigencia de una sesión persistida
- **WHEN** se solicita una operación protegida
- **THEN** se falla de forma segura sin ejecutar la operación ni emitir éxito
