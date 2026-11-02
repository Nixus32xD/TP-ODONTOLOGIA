# Spec Delta

## MODIFIED Requirements

### Requirement: Aplicar el menor privilegio aprobado
El backend SHALL autorizar cada operación según el rol actual de la cuenta. El Administrador puede gestionar las operaciones disponibles y las cuentas, pero no leer contenido clínico; Recepción puede operar la agenda y datos permitidos pero no administrar cuentas ni leer contenido clínico; Profesional sólo puede consultar turnos y opciones de disponibilidad de su propio profesional vinculado y no puede crear, cambiar, cancelar ni administrar turnos, catálogos, pacientes o cuentas. Como excepción, un Profesional activo SHALL poder consultar y registrar evoluciones únicamente para pacientes con turnos `atendido` de su profesional vinculado, según `clinical-history`.

#### Scenario: Recepción crea un turno
- **GIVEN** una sesión vigente de Recepción
- **WHEN** solicita un turno válido
- **THEN** la API ejecuta el contrato de alta C-01

#### Scenario: Profesional sin alcance de agenda
- **GIVEN** una sesión vigente de Profesional vinculada a profesional-A
- **WHEN** consulta turnos u opciones de disponibilidad de profesional-A
- **THEN** sólo se evalúa el profesional vinculado y no se expone información de otros calendarios

#### Scenario: Profesional no realiza operaciones de escritura
- **GIVEN** una sesión vigente de Profesional
- **WHEN** intenta crear, cancelar, confirmar, marcar atención/ausencia o modificar turnos, catálogos, pacientes o cuentas, fuera de la excepción clínica explícita
- **THEN** recibe 403 sin cambios ni eventos de mutación

#### Scenario: Profesional opera clínica sólo en sus atenciones
- **GIVEN** una sesión vigente de Profesional vinculada a profesional-A
- **WHEN** consulta o registra una evolución para un turno `atendido` de profesional-A
- **THEN** la operación se autoriza sólo bajo las reglas de `clinical-history` y no amplía permisos sobre la agenda

#### Scenario: Administrador o Recepción no acceden al contenido clínico
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** intenta consultar, registrar o corregir una evolución
- **THEN** recibe 403 sin obtener contenido clínico ni modificarlo

#### Scenario: Administrador tiene acceso autorizado
- **GIVEN** una sesión vigente de Administrador
- **WHEN** usa una operación disponible para el personal que no expone contenido clínico
- **THEN** se aplica la operación correspondiente y quedan vigentes sus reglas de dominio
