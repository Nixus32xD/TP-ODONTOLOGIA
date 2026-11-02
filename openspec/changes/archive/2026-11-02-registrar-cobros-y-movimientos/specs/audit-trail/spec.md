# Spec Delta

## MODIFIED Requirements

### Requirement: Operaciones incluidas en auditoría
El sistema SHALL auditar altas de turno confirmadas y reprogramaciones confirmadas; creación, cambio de rol y cambio de estado de cuentas; bootstrap del Administrador; aperturas, cierres y rechazos de sesión; cambios de consentimiento de recordatorios; y programación, invalidación, procesamiento y fallos sintéticos del outbox; y altas de cargos, cobros y reversiones monetarias.

#### Scenario: Cuenta actualizada
- **GIVEN** un Administrador crea una cuenta o cambia su rol o estado
- **WHEN** la operación se confirma
- **THEN** queda un evento de la acción con actor y recurso de cuenta, sin datos personales ni credenciales

#### Scenario: Inicio y cierre de sesión
- **GIVEN** una sesión se abre o se cierra correctamente
- **WHEN** termina la operación
- **THEN** queda un evento con actor y acción, sin JWT, secreto ni identificador de sesión reutilizable

#### Scenario: Bootstrap inicial
- **GIVEN** se crea el primer Administrador
- **WHEN** se confirma el bootstrap
- **THEN** queda un evento con actor nulo y recurso de cuenta, sin nombre ni credenciales

#### Scenario: Reprogramación confirmada
- **GIVEN** Administrador o Recepción reprograma un turno y confirma la transacción
- **WHEN** se registra el evento `turno.reprogramado`
- **THEN** contiene actor, recurso `turno`, ID opaco y resultado `confirmado`, sin paciente, recursos, intervalo ni cuerpo

#### Scenario: Cambio de consentimiento
- **GIVEN** Administrador o Recepción cambia la preferencia de recordatorios de un paciente
- **WHEN** la mutación se confirma
- **THEN** queda un evento metadata-only con actor, acción, recurso e ID opaco, sin nombre, teléfono ni valor del consentimiento

#### Scenario: Procesamiento simulado del outbox
- **GIVEN** el worker programa, invalida, procesa o marca un fallo sintético de un recordatorio
- **WHEN** la operación y su evento terminan
- **THEN** se registran sólo actor cuando corresponda, acción, tipo e ID opaco del recurso y resultado, sin teléfono, nombre, mensaje ni contenido clínico

#### Scenario: Fallo al auditar el outbox
- **GIVEN** una operación del outbox cuya auditoría no puede persistirse
- **WHEN** termina la transacción
- **THEN** se revierten el cambio de estado del recordatorio y el evento, sin cambiar ni borrar el turno

#### Scenario: Movimiento monetario auditado sin contenido financiero
- **GIVEN** Administrador o Recepción confirma un cargo o cobro, o Administrador confirma una reversión
- **WHEN** se registra su evento de auditoría
- **THEN** incluye actor, acción, recurso opaco y resultado, y omite importe, moneda, concepto, paciente y motivo

#### Scenario: Rechazo o rollback de movimiento monetario
- **GIVEN** un comando monetario inválido, repetido de forma idempotente o cuya auditoría falla
- **WHEN** finaliza la operación
- **THEN** no se registra evento de éxito nuevo y ningún movimiento parcial queda persistido
