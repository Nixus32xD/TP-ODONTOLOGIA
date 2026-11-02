# Spec Delta

## MODIFIED Requirements

### Requirement: Restringir la historia clínica al Profesional responsable
Un Profesional activo SHALL consultar, registrar y corregir evoluciones, consultar y versionar odontogramas, y consultar y registrar planes sólo para pacientes con turno `atendido` propio. Administrador y Recepción SHALL NOT consultar ni modificar contenido clínico. Las capacidades clínicas SHALL aplicar sus reglas de propiedad, estado y auditoría.

#### Scenario: Profesional opera clínica sólo en sus atenciones
- **GIVEN** una sesión vigente de Profesional vinculada a profesional-A
- **WHEN** consulta o registra una evolución, odontograma o plan para un turno `atendido` de profesional-A
- **THEN** la operación se autoriza sólo bajo las reglas de cada capacidad clínica y no amplía permisos sobre la agenda

#### Scenario: Administrador o Recepción no acceden al contenido clínico
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** intenta consultar, registrar o corregir una evolución, consultar o versionar un odontograma, o consultar o cambiar un plan
- **THEN** recibe 403 sin obtener contenido clínico ni modificarlo
