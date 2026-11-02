# Spec Delta

## MODIFIED Requirements

### Requirement: Políticas excluidas de esta porción
El sistema SHALL aceptar duración positiva libre, sin asociarla a prestaciones. Con C-07, cada alta SHALL caber en la disponibilidad del profesional y del box y no solaparse con bloqueos. Con C-09, sólo `reservado` y `confirmado` SHALL ocupar recursos; los estados terminales liberan sus intervalos sin borrar la fila. El mismo paciente SHALL poder tener turnos simultáneos si profesional y box difieren, sin compatibilidad adicional ni sobreturnos.

#### Scenario: Cruce de medianoche
- **GIVEN** un turno que comienza un día local y finaliza al siguiente, y horarios que no cruzan medianoche
- **WHEN** se solicita el alta
- **THEN** se rechaza como `fuera_de_disponibilidad`, sin insertar el turno

#### Scenario: Paciente simultáneo con recursos distintos
- **GIVEN** paciente-A tiene turno con profesional-A y box-A
- **WHEN** el mismo paciente solicita el mismo intervalo con profesional-B y box-B libres y disponibles
- **THEN** se acepta; la exclusión del paciente queda expresamente fuera del contrato
