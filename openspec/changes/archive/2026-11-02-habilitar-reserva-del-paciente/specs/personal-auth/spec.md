# Spec Delta

## ADDED Requirements

### Requirement: Provisionar cuentas sintéticas de paciente
Sólo un Administrador SHALL crear una cuenta `paciente` vinculada a una ficha activa no vinculada previamente. El aprovisionamiento será local y ficticio, aplicará la política vigente de credenciales y no enviará activaciones ni verificaciones externas.

#### Scenario: Administrador crea cuenta vinculada
- **GIVEN** un Administrador autenticado y una ficha activa sin cuenta vinculada
- **WHEN** crea una cuenta de paciente con credenciales válidas
- **THEN** la cuenta queda vinculada de forma única y la respuesta omite credenciales, hashes, secretos y tokens

#### Scenario: Actor no administrador o vínculo inválido
- **GIVEN** un actor distinto de Administrador, una ficha inexistente/inactiva o ya vinculada
- **WHEN** intenta crear la cuenta
- **THEN** recibe 403, 404 o 409 según corresponda y no se crea ni audita una cuenta parcial

#### Scenario: Sin activación externa ni autorregistro
- **GIVEN** la aplicación local de demostración
- **WHEN** no hay una cuenta de paciente previamente provisionada
- **THEN** no existe registro público, envío de activación ni verificación por email, SMS u otro proveedor

## MODIFIED Requirements

### Requirement: Revocar sesiones ante cambios de cuenta
Desactivar una cuenta, cambiar su rol o cambiar su vínculo profesional o de paciente SHALL revocar sus sesiones activas.

#### Scenario: Desactivación revoca sesiones
- **GIVEN** una cuenta con sesiones activas
- **WHEN** un Administrador la desactiva, cambia su rol o reasigna su profesional
- **THEN** sus sesiones previas dejan de autorizar peticiones

#### Scenario: Cambio de vínculo de paciente revoca sesiones
- **GIVEN** una cuenta de paciente con una sesión activa
- **WHEN** un Administrador desactiva la cuenta, cambia su rol o modifica su ficha vinculada
- **THEN** la sesión anterior deja de autorizar operaciones protegidas

### Requirement: Iniciar sesiones sólo con credenciales válidas
El sistema SHALL emitir una sesión firmada sólo para una cuenta activa Administrador o Recepción, para una cuenta Profesional activa con vínculo válido a un profesional existente, o para una cuenta `paciente` activa con vínculo válido y único a una ficha activa. Las respuestas de autenticación fallida SHALL ser genéricas y no distinguir entre cuenta inexistente, inactiva, vínculo faltante o contraseña incorrecta.

#### Scenario: Inicio de sesión válido
- **GIVEN** una cuenta activa habilitada con contraseña válida
- **WHEN** se inicia sesión
- **THEN** se devuelve un token bearer con expiración limitada y datos mínimos de cuenta, sin exponer la derivación de contraseña

#### Scenario: Credenciales inválidas
- **GIVEN** credenciales incorrectas, cuenta inexistente o inactiva, o vínculo profesional o de paciente inválido
- **WHEN** se solicita una sesión
- **THEN** se devuelve 401 con el mismo mensaje público y no se crea una sesión utilizable
