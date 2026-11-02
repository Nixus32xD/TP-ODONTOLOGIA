## ADDED Requirements

### Requirement: Las nuevas altas requieren profesional y box activos

El sistema SHALL rechazar un alta con `recurso_inactivo` cuando el profesional o box existe pero está desactivado. SHALL conservar la detección de referencias desconocidas de C-01 antes de evaluar estado, no insertar el turno rechazado y dejar intactos los turnos históricos.

#### Scenario: Profesional inactivo
- **GIVEN** una agenda con paciente activo, un profesional inactivo y un box activo
- **WHEN** se intenta crear un turno para ese profesional
- **THEN** se informa `recurso_inactivo` para `profesional` y no se registra el turno

#### Scenario: Box inactivo
- **GIVEN** una agenda con paciente activo, profesional activo y box inactivo
- **WHEN** se intenta crear un turno en ese box
- **THEN** se informa `recurso_inactivo` para `box` y no se registra el turno

#### Scenario: Recurso desconocido conserva su resultado
- **GIVEN** un ID de profesional o box ausente del catálogo
- **WHEN** se solicita un turno
- **THEN** se informa `recurso_desconocido` conforme a C-01, no `recurso_inactivo`

#### Scenario: Desactivación no altera historial
- **GIVEN** un turno existente asociado a un profesional o box que se desactiva
- **WHEN** se consulta posteriormente el almacenamiento
- **THEN** el turno y sus referencias se conservan sin modificación
