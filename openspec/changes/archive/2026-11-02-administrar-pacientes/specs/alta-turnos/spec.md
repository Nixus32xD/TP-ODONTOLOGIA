# Spec Delta

## ADDED Requirements

### Requirement: Los turnos nuevos requieren un paciente activo
El sistema SHALL rechazar un alta con `recurso_inactivo` cuando el ID del paciente existe pero su ficha está desactivada. SHALL conservar la prioridad de validación de C-01 para recursos desconocidos y no modificar turnos históricos.

#### Scenario: Paciente inactivo conocido
- **GIVEN** una agenda preparada con una ficha inactiva y recursos profesionales/box válidos
- **WHEN** Administrador o Recepción intenta registrar un turno para esa ficha
- **THEN** el sistema informa `recurso_inactivo` para `paciente` y no inserta ningún turno

#### Scenario: Paciente activo conocido
- **GIVEN** una agenda preparada con una ficha activa y recursos libres
- **WHEN** Administrador o Recepción registra un turno válido
- **THEN** se aplican sin cambios las validaciones y exclusiones del contrato C-01

#### Scenario: Historial de paciente desactivado
- **GIVEN** un turno existente asociado a un paciente que luego fue desactivado
- **WHEN** el personal consulta el turno mediante una capacidad posterior
- **THEN** la referencia al paciente y el turno histórico se conservan
