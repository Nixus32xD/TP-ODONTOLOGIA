# Spec Delta

## MODIFIED Requirements

### Requirement: Operaciones incluidas en auditoría
El sistema SHALL auditar altas de turno confirmadas y reprogramaciones confirmadas; creación, cambio de rol y cambio de estado de cuentas; bootstrap del Administrador; y aperturas, cierres y rechazos de sesión.

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
