# Spec Delta

## MODIFIED Requirements

### Requirement: Errores HTTP del dominio
El adaptador SHALL mapear entrada_invalida a 422, recurso_desconocido a 404, conflictos de recursos a 409, agenda_ocupada a 503 y almacenamiento_error a 500 mediante JSON con codigo, campo y mensaje público. SHALL conservar reglas, prioridad profesional/box, rollback y ausencia de reintentos del dominio.

#### Scenario: Conflictos HTTP independientes
- **GIVEN** un turno ocupa profesional-A y box-A
- **WHEN** se solicita igual intervalo cambiando sólo box o sólo profesional
- **THEN** responde 409 con el conflicto correspondiente y conserva un único registro

#### Scenario: Fallo o contención HTTP
- **GIVEN** agenda ausente, corrupta o bloqueada más allá del timeout
- **WHEN** se solicita alta válida
- **THEN** responde 500 almacenamiento_error o 503 agenda_ocupada, sin éxito ficticio ni fuga de rutas

#### Scenario: Fallo al almacenar auditoría del turno
- **GIVEN** el alta del turno es válida pero falla la escritura de su evento de auditoría
- **WHEN** se solicita `POST /turnos`
- **THEN** responde 500 almacenamiento_error y la transacción revierte tanto el turno como el evento
