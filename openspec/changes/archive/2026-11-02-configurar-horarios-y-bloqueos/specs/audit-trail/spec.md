## ADDED Requirements

### Requirement: Auditar mutaciones de disponibilidad con metadatos mínimos

El sistema SHALL auditar altas, reemplazos y eliminaciones confirmados de horarios, excepciones y bloqueos con actor, acción permitida, tipo de recurso, ID opaco y resultado. SHALL omitir fechas, intervalos, tramos y cuerpos. Cada mutación y evento SHALL confirmarse en la misma transacción; ante falla se SHALL revertir ambos.

#### Scenario: Auditoría de horario, excepción o bloqueo
- **GIVEN** Administrador o Recepción modifica una configuración válida
- **WHEN** la operación se confirma
- **THEN** existe su evento metadata-only y la configuración coincide con la operación

#### Scenario: Fallo de auditoría
- **GIVEN** una mutación de disponibilidad válida cuyo evento falla al escribirse
- **WHEN** termina la solicitud
- **THEN** la API no informa éxito y la configuración previa permanece intacta

#### Scenario: Cambio rechazado por turnos existentes
- **GIVEN** un cambio que produciría `turnos_afectados`
- **WHEN** la operación se rechaza con HTTP 409
- **THEN** no se crea un evento de mutación ni se cambia la configuración

#### Scenario: Lectura de configuración
- **GIVEN** un usuario autorizado consulta un horario, excepción o bloqueo
- **WHEN** recibe el resultado
- **THEN** la consulta no genera un evento de mutación
