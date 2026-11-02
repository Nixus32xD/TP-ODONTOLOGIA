# Spec Delta

## MODIFIED Requirements

### Requirement: Confirmar la reprogramación y su auditoría conjuntamente
El sistema SHALL actualizar asignación, versión, evento `turno.reprogramado` y outbox en una transacción. El evento SHALL incluir sólo actor, acción, recurso `turno`, ID opaco y resultado; SHALL omitir paciente, recursos, intervalo y cuerpo. SHALL invalidar pendientes de la versión anterior y programar para la nueva sólo con turno confirmado, consentimiento y más de 24 horas. Cualquier fallo de auditoría u outbox SHALL revertir la operación.

#### Scenario: Auditoría confirma sólo una reprogramación exitosa
- **GIVEN** una asignación válida y auditoría disponible
- **WHEN** la transacción de reprogramación confirma
- **THEN** se guarda un evento metadata-only con el ID del turno y se devuelve éxito

#### Scenario: Fallo de auditoría conserva la asignación previa
- **GIVEN** una reprogramación válida cuya auditoría falla al persistirse
- **WHEN** termina la operación
- **THEN** se revierte asignación y versión, no queda evento y la API no informa éxito

#### Scenario: Reprogramación invalida la versión anterior
- **GIVEN** un turno confirmado con recordatorio pendiente y consentimiento vigente
- **WHEN** Administrador o Recepción confirma una reprogramación válida
- **THEN** el recordatorio anterior se invalida y se agrega a lo sumo uno para la nueva versión si conserva el plazo de 24 horas

#### Scenario: Fallo del outbox revierte la reprogramación
- **GIVEN** una reprogramación elegible cuya actualización de recordatorios no puede persistirse
- **WHEN** termina la operación
- **THEN** se revierte la asignación, la versión y la auditoría, y no se informa éxito
