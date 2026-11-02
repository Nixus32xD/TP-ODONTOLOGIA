# patient-management Specification

## Purpose
Permite que el personal autorizado identifique pacientes de la agenda mediante una ficha de contacto mínima y mantenga referencias históricas sin incorporar historia clínica.

## Requirements

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
### Requirement: Consultar fichas de forma paginada
El sistema SHALL permitir a Administrador y Recepción listar pacientes ordenados por ID ascendente y consultar una ficha por ID. La lista SHALL paginarse con límite predeterminado de 50, máximo de 100 y desplazamiento no negativo; incluirá fichas activas e inactivas, identificadas sólo por los campos de la ficha.

#### Scenario: Lista paginada estable
- **GIVEN** una sesión autorizada y pacientes activos e inactivos
- **WHEN** se consulta `GET /pacientes` con parámetros válidos
- **THEN** se devuelve una página ordenada establemente con nombre, teléfono, ID y estado

#### Scenario: Ficha inexistente
- **GIVEN** una sesión autorizada y un ID no registrado
- **WHEN** se consulta `GET /pacientes/{id}`
- **THEN** la API devuelve 404 sin filtrar detalles del almacenamiento

#### Scenario: Paginación fuera de rango
- **GIVEN** límite mayor a 100 o desplazamiento negativo
- **WHEN** se consulta la lista
- **THEN** la API devuelve 422 sin exponer datos

### Requirement: Desactivar y reactivar sin borrar historial
El sistema SHALL permitir sólo a Administrador desactivar o reactivar una ficha mediante baja lógica. Una ficha inactiva SHALL conservarse y seguir visible en consultas; SHALL NOT usarse para nuevos turnos. Sus turnos históricos y referencias SHALL permanecer intactos.

#### Scenario: Baja lógica
- **GIVEN** un Administrador autenticado y una ficha activa
- **WHEN** desactiva el paciente
- **THEN** la ficha queda inactiva y sus turnos existentes continúan asociados

#### Scenario: Rechazar turnos nuevos para ficha inactiva
- **GIVEN** un paciente inactivo con un ID conocido
- **WHEN** se intenta crear un turno nuevo con ese paciente
- **THEN** se devuelve `recurso_inactivo` y no se inserta el turno

#### Scenario: Reactivación
- **GIVEN** un Administrador autenticado y una ficha inactiva
- **WHEN** la reactiva
- **THEN** vuelve a estar disponible para nuevos turnos sin alterar su historial

#### Scenario: Recepción no cambia estado
- **GIVEN** una sesión de Recepción
- **WHEN** intenta desactivar o reactivar una ficha
- **THEN** recibe 403 y el estado se conserva

### Requirement: Rechazar acceso anónimo a pacientes
El sistema SHALL requerir sesión vigente de Administrador o Recepción para todas las operaciones de pacientes y SHALL denegar a otros roles antes de consultar o modificar las fichas.

#### Scenario: Sin sesión
- **GIVEN** una petición sin bearer válido
- **WHEN** consulta o modifica pacientes
- **THEN** recibe 401 y no accede a las fichas

#### Scenario: Rol no habilitado
- **GIVEN** una sesión cuyo rol no es Administrador ni Recepción
- **WHEN** solicita una operación de pacientes
- **THEN** recibe 403 sin leer ni cambiar datos
