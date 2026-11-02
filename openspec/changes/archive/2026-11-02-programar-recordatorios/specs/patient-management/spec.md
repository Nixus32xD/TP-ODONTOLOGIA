# Spec Delta

## MODIFIED Requirements

### Requirement: Administrar fichas mínimas de pacientes
El sistema SHALL permitir a Administrador y Recepción gestionar fichas con nombre obligatorio de hasta 120 caracteres, espacios normalizados y teléfono opcional de 7 a 15 dígitos (`+`, espacios, paréntesis y guiones admitidos; conserva el valor ingresado). `acepta_recordatorios` SHALL iniciar en `false` y cambiar sólo por decisión explícita del personal autorizado. SHALL permitir nombres repetidos y rechazar campos adicionales o datos clínicos.

#### Scenario: Alta ficticia válida
- **GIVEN** una sesión de Administrador o Recepción y un nombre válido con teléfono opcional
- **WHEN** se crea el paciente sin indicar consentimiento de recordatorios
- **THEN** se persiste una ficha activa con un ID generado por el sistema y `acepta_recordatorios=false`

#### Scenario: Nombre y contacto inválidos
- **GIVEN** nombre ausente, vacío, de más de 120 caracteres, o teléfono con longitud/dígitos fuera de rango
- **WHEN** se crea o actualiza una ficha
- **THEN** la API devuelve 422 y no modifica el almacenamiento

#### Scenario: Normalización del nombre y conservación del teléfono
- **GIVEN** una ficha válida con espacios externos o repetidos en el nombre y un teléfono con formato admitido
- **WHEN** el personal crea o actualiza la ficha
- **THEN** el nombre se guarda con espacios normalizados y el teléfono se conserva tal como se ingresó

#### Scenario: Nombres repetidos
- **GIVEN** existe un paciente activo con el mismo nombre
- **WHEN** el personal registra otra ficha válida
- **THEN** se permiten ambos pacientes sin inferir que son la misma persona

#### Scenario: Campos no permitidos
- **GIVEN** una solicitud contiene documento, fecha de nacimiento, historia clínica u otro campo extra
- **WHEN** se crea o actualiza una ficha
- **THEN** la API devuelve 422 sin guardar esos datos

#### Scenario: Actualizar consentimiento de recordatorios
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** actualiza `acepta_recordatorios` a un valor booleano explícito
- **THEN** la preferencia se devuelve en la ficha y el cambio queda auditado sin incluir nombre, teléfono ni cuerpo de solicitud
