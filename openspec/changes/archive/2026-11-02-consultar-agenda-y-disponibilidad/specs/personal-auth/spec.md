# Spec Delta

## MODIFIED Requirements

### Requirement: Administrar cuentas del personal
El sistema SHALL permitir a un Administrador autenticado crear y consultar cuentas de Administrador, Recepción y Profesional, y cambiar su rol, estado activo o vínculo profesional. Una cuenta Profesional SHALL vincularse a un único profesional activo; una misma ficha profesional SHALL estar asignada como máximo a una cuenta. Las cuentas Administrador y Recepción SHALL carecer de vínculo profesional. Identificadores SHALL normalizarse con casefold y trim y cumplir el formato ASCII de 3–64 caracteres; contraseñas de 12–128 caracteres SHALL almacenarse sólo como derivación con sal. Respuestas SHALL omitir credenciales, hashes, secretos y tokens. Desactivar una cuenta, cambiar su rol o cambiar su vínculo profesional SHALL revocar sus sesiones.

#### Scenario: Recepción no administra cuentas
- **GIVEN** una sesión válida con rol Recepción
- **WHEN** intenta listar, crear o cambiar una cuenta
- **THEN** recibe 403 y no se modifica el almacenamiento

#### Scenario: Alta de cuenta permitida
- **GIVEN** un Administrador autenticado y un identificador no utilizado
- **WHEN** crea una cuenta Administrador o Recepción con contraseña válida
- **THEN** la cuenta queda persistida y la respuesta omite credenciales y secretos

#### Scenario: Alta de cuenta Profesional vinculada
- **GIVEN** un Administrador autenticado y un profesional activo sin cuenta vinculada
- **WHEN** crea una cuenta con rol Profesional y su ID profesional
- **THEN** la cuenta queda vinculada a ese profesional y la respuesta omite credenciales y secretos

#### Scenario: Asignación profesional inválida o duplicada
- **GIVEN** una cuenta Profesional con ID inexistente/inactivo, una cuenta de otro rol con ID profesional o un profesional ya vinculado
- **WHEN** se intenta crear o cambiar el vínculo de la cuenta
- **THEN** se rechaza con 404/409/422 según corresponda y no se cambia cuenta, vínculo ni auditoría

#### Scenario: Desactivación revoca sesiones
- **GIVEN** una cuenta con sesiones activas
- **WHEN** un Administrador la desactiva, cambia su rol o reasigna su profesional
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
El sistema SHALL emitir una sesión firmada sólo para una cuenta activa Administrador o Recepción o para una cuenta Profesional activa con vínculo válido a un profesional existente. Las respuestas de autenticación fallida SHALL ser genéricas y no distinguir entre cuenta inexistente, inactiva, vínculo faltante o contraseña incorrecta.

#### Scenario: Inicio de sesión válido
- **GIVEN** una cuenta activa habilitada con contraseña válida
- **WHEN** se inicia sesión
- **THEN** se devuelve un token bearer con expiración limitada y datos mínimos de cuenta, sin exponer la derivación de contraseña

#### Scenario: Credenciales inválidas
- **GIVEN** credenciales incorrectas, cuenta inexistente o inactiva, o vínculo profesional inválido
- **WHEN** se solicita una sesión
- **THEN** se devuelve 401 con el mismo mensaje público y no se crea una sesión utilizable

### Requirement: Aplicar el menor privilegio aprobado
El backend SHALL autorizar cada operación según el rol actual de la cuenta. El Administrador puede gestionar las operaciones disponibles y las cuentas; Recepción puede operar la agenda y datos permitidos pero no administrar cuentas; Profesional sólo puede consultar turnos y opciones de disponibilidad de su propio profesional vinculado y no puede crear, cambiar, cancelar ni administrar datos.

#### Scenario: Recepción crea un turno
- **GIVEN** una sesión vigente de Recepción
- **WHEN** solicita un turno válido
- **THEN** la API ejecuta el contrato de alta C-01

#### Scenario: Profesional sin alcance de agenda
- **GIVEN** una sesión vigente de Profesional vinculada a profesional-A
- **WHEN** consulta turnos u opciones de disponibilidad de profesional-A
- **THEN** sólo se evalúa el profesional vinculado y no se expone información de otros calendarios

#### Scenario: Profesional no realiza operaciones de escritura
- **GIVEN** una sesión vigente de Profesional
- **WHEN** intenta crear, cancelar, confirmar, marcar atención/ausencia o modificar turnos, catálogos o cuentas
- **THEN** recibe 403 sin cambios ni eventos de mutación

#### Scenario: Administrador tiene acceso autorizado
- **GIVEN** una sesión vigente de Administrador
- **WHEN** usa una operación disponible para el personal
- **THEN** se aplica la operación correspondiente y quedan vigentes sus reglas de dominio
