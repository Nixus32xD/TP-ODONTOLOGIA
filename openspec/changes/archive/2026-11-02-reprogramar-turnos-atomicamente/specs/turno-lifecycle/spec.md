# Spec Delta

## ADDED Requirements

### Requirement: Mantener versión para concurrencia optimista
Cada turno migrado SHALL iniciar con versión positiva `1`. Cada mutación efectiva de datos o estado del turno SHALL incrementarla en uno; una operación idempotente que no modifica el turno SHALL conservarla.

#### Scenario: Migración inicializa versión
- **GIVEN** turnos existentes antes de C-10
- **WHEN** se migra el esquema
- **THEN** cada turno conserva identidad, referencias, intervalo y estado, y recibe versión `1`

#### Scenario: Alta inicia versión
- **GIVEN** una agenda con esquema C-10
- **WHEN** se crea un turno válido
- **THEN** el turno comienza con versión `1`

#### Scenario: Transición de estado incrementa versión
- **GIVEN** un turno vigente con versión `n`
- **WHEN** se confirma una transición de estado permitida
- **THEN** el estado cambia y la versión pasa a `n + 1` en la misma transacción

#### Scenario: Repetir cancelación no modifica versión
- **GIVEN** un turno ya cancelado con versión `n`
- **WHEN** se repite la cancelación idempotente
- **THEN** se devuelve su estado actual y la versión permanece en `n`
