## ADDED Requirements

### Requirement: Registrar altas de catálogos con metadatos permitidos

El sistema SHALL auditar las altas confirmadas de profesionales, boxes y prestaciones con fecha UTC, actor, acción explícita, tipo e ID opaco del recurso y resultado. SHALL omitir nombres, duración, cuerpos y otros datos del catálogo.

#### Scenario: Auditoría de alta
- **GIVEN** Administrador o Recepción realiza una operación válida sobre un catálogo
- **WHEN** el alta se confirma
- **THEN** queda un evento con actor, ID opaco, acción y tipo permitidos, sin nombre ni datos de prestación

### Requirement: Registrar actualizaciones de catálogos en la misma transacción

El sistema SHALL auditar actualizaciones confirmadas de profesionales, boxes y prestaciones y cambios de estado con metadatos permitidos, sin guardar nombres, duración ni cuerpos. La mutación y el evento SHALL confirmarse en la misma transacción; si el evento no puede guardarse SHALL revertir la operación.

#### Scenario: Auditoría de actualización y cambio de estado
- **GIVEN** Administrador activa o desactiva un registro de catálogo
- **WHEN** confirma el cambio
- **THEN** queda el evento correspondiente con metadatos permitidos y el estado nuevo persiste

#### Scenario: Fallo al almacenar evento
- **GIVEN** una mutación válida de catálogo cuyo evento no puede almacenarse
- **WHEN** se completa la solicitud
- **THEN** se revierte la mutación y la API no informa éxito

#### Scenario: Actualización conserva metadatos
- **GIVEN** una actualización válida de nombre o duración
- **WHEN** se consulta su evento de auditoría
- **THEN** el evento incluye sólo acción, tipo e ID opaco y omite nombre y duración

#### Scenario: Lectura de catálogos
- **GIVEN** un usuario autorizado consulta un catálogo
- **WHEN** la API devuelve resultados
- **THEN** no se crea un evento de mutación
