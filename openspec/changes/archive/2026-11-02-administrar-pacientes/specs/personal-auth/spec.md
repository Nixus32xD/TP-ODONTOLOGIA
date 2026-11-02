# Spec Delta

## ADDED Requirements

### Requirement: Permitir a Recepción operar fichas mínimas
El backend SHALL permitir a Recepción crear, listar, consultar y actualizar nombre/teléfono de pacientes. SHALL reservar para Administrador la desactivación y reactivación; ninguna operación SHALL habilitar acceso a cuentas de Profesional ni permitir administrar cuentas del personal.

#### Scenario: Recepción administra datos de contacto
- **GIVEN** una sesión vigente de Recepción
- **WHEN** crea, lista, consulta o actualiza una ficha mínima válida
- **THEN** la operación se autoriza y sus validaciones y auditoría se aplican

#### Scenario: Recepción no cambia el estado
- **GIVEN** una sesión vigente de Recepción
- **WHEN** intenta desactivar o reactivar un paciente
- **THEN** recibe 403 sin modificar la ficha

#### Scenario: Recepción no administra cuentas
- **GIVEN** una sesión vigente de Recepción
- **WHEN** intenta crear o modificar una cuenta de personal
- **THEN** continúa recibiendo 403 y no se modifica la cuenta
