# Spec Delta

## ADDED Requirements

### Requirement: Auditar mutaciones de pacientes sin guardar la ficha
El sistema SHALL auditar cada alta, actualización, desactivación y reactivación confirmada de paciente con acción, recurso `paciente`, resultado, actor e ID interno opaco. SHALL omitir nombre, teléfono, cuerpo de solicitud y cualquier otro dato de la ficha. Mutación y evento SHALL confirmarse en la misma transacción; un fallo de auditoría SHALL revertir ambos.

#### Scenario: Alta y actualización de paciente
- **GIVEN** una sesión autorizada y datos ficticios válidos
- **WHEN** se crea o actualiza una ficha
- **THEN** queda un evento confirmado con actor e ID del paciente, sin nombre ni teléfono

#### Scenario: Cambio de estado
- **GIVEN** un Administrador modifica el estado activo de una ficha
- **WHEN** la operación se confirma
- **THEN** queda un evento de desactivación o reactivación con metadatos permitidos

#### Scenario: Auditoría indisponible
- **GIVEN** una mutación válida de paciente cuyo evento no puede almacenarse
- **WHEN** finaliza la operación
- **THEN** la ficha conserva su estado previo y la API no informa éxito

#### Scenario: Lectura de ficha
- **GIVEN** una consulta autorizada de pacientes
- **WHEN** se devuelve una ficha
- **THEN** no se genera un evento de mutación y no se incluyen datos de ficha en el registro de auditoría
