# Spec Delta

## MODIFIED Requirements

### Requirement: Políticas excluidas de esta porción

El sistema SHALL aceptar duración positiva libre sin asociarla a prestaciones; con C-07 aplicado, cada alta nueva además SHALL caber íntegramente en la disponibilidad local del profesional y del box y no solaparse con bloqueos. Todo turno registrado SHALL ocupar recursos; no hay cancelación ni estados. SHALL permitir el mismo paciente simultáneo si profesional y box difieren, sin compatibilidad adicional ni excepción de sobreturno.

#### Scenario: Cruce de medianoche
- **GIVEN** un turno que comienza un día local y finaliza al siguiente, y horarios que no cruzan medianoche
- **WHEN** se solicita el alta
- **THEN** se rechaza como `fuera_de_disponibilidad`, sin insertar el turno

#### Scenario: Paciente simultáneo con recursos distintos
- **GIVEN** paciente-A tiene turno con profesional-A y box-A
- **WHEN** el mismo paciente solicita el mismo intervalo con profesional-B y box-B libres y disponibles
- **THEN** se acepta; la exclusión del paciente queda expresamente fuera del contrato

## ADDED Requirements

### Requirement: Validar disponibilidad durante el alta de turnos

`POST /turnos` SHALL verificar dentro de la operación serializada que el turno está disponible para profesional y box antes de insertarlo. Un turno fuera de horario o bloqueado SHALL responder HTTP 409 con `fuera_de_disponibilidad` y no alterar la agenda.

#### Scenario: Disponibilidad de ambos recursos
- **GIVEN** un turno íntegro dentro de un tramo disponible de profesional y box, sin bloqueos
- **WHEN** se solicita el alta
- **THEN** la reserva se confirma después de las validaciones restantes de C-01

#### Scenario: Falta de disponibilidad de un recurso
- **GIVEN** el profesional o box carece de un tramo que contenga el turno completo
- **WHEN** se solicita el alta
- **THEN** se devuelve HTTP 409 con `fuera_de_disponibilidad` y no se inserta el turno

#### Scenario: Carrera entre alta y cambio de disponibilidad
- **GIVEN** una reserva y un cambio de horario o bloqueo concurrentes sobre la misma agenda
- **WHEN** ambas operaciones se serializan y completan
- **THEN** sólo se confirma un estado coherente en el que ningún turno queda fuera de disponibilidad
