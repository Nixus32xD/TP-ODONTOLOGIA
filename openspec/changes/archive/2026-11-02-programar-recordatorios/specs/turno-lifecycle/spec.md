# Spec Delta

## MODIFIED Requirements

### Requirement: Exponer operaciones de ciclo de vida protegidas
Administrador y Recepción SHALL usar `POST /turnos/{id}/confirmacion`, `/cancelacion`, `/atencion` y `/ausencia`; las operaciones SHALL devolver HTTP 200 con ID y estado, y un turno inexistente SHALL responder 404. Profesional SHALL permanecer sin acceso. Confirmar SHALL programar recordatorio sólo con consentimiento y más de 24 horas; cancelar SHALL invalidar los pendientes en la misma transacción.

#### Scenario: Personal autorizado transiciona un turno
- **GIVEN** una sesión válida de Administrador o Recepción y una transición permitida
- **WHEN** se llama el endpoint correspondiente
- **THEN** responde 200 con el estado actualizado

#### Scenario: Sesión o rol no autorizado
- **GIVEN** una solicitud sin sesión válida o con rol no autorizado
- **WHEN** intenta una operación de ciclo de vida
- **THEN** responde 401 o 403 sin cambiar el turno ni crear un evento de mutación

#### Scenario: Turno inexistente
- **GIVEN** un identificador de turno que no existe
- **WHEN** se solicita una transición
- **THEN** responde 404 sin crear un evento

#### Scenario: Confirmación programa sólo si es elegible
- **GIVEN** un turno reservado, consentimiento vigente y más de 24 horas hasta su inicio
- **WHEN** Administrador o Recepción confirma el turno
- **THEN** el cambio de estado, su auditoría y un recordatorio pendiente para el vencimiento de 24 horas se confirman conjuntamente

#### Scenario: Cancelación invalida el recordatorio pendiente
- **GIVEN** un turno confirmado con un recordatorio pendiente
- **WHEN** Administrador o Recepción cancela el turno
- **THEN** el estado, la auditoría y la invalidación del recordatorio se confirman en la misma transacción
