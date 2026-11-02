# Spec Delta

## ADDED Requirements

### Requirement: Auditar transiciones de estado de turnos
El sistema SHALL auditar cada transición confirmada de estado con actor, acción `turno.estado_actualizado`, tipo de recurso `turno`, ID opaco y resultado `confirmado`. El evento SHALL omitir referencias de paciente, profesional y box, intervalo y cuerpo; mutación y evento SHALL confirmarse en la misma transacción. Las migraciones SHALL ampliar el catálogo de acciones preservando los eventos previos y las protecciones append-only.

#### Scenario: Transición confirmada
- **GIVEN** una transición válida de estado solicitada por Administrador o Recepción
- **WHEN** la mutación se confirma
- **THEN** se guarda un evento metadata-only para el turno y se conserva el nuevo estado

#### Scenario: Fallo al guardar evento
- **GIVEN** una transición válida cuyo evento no puede persistirse
- **WHEN** termina la solicitud
- **THEN** se revierten la transición y su evento, y la API no informa éxito

#### Scenario: Repetición idempotente de cancelación
- **GIVEN** un turno ya cancelado
- **WHEN** se repite la cancelación
- **THEN** se devuelve el estado actual sin agregar otro evento de mutación

#### Scenario: Transición inválida o denegada
- **GIVEN** una transición inválida o una solicitud sin autorización
- **WHEN** se rechaza la operación
- **THEN** no se genera un evento de transición ni se modifica el turno
