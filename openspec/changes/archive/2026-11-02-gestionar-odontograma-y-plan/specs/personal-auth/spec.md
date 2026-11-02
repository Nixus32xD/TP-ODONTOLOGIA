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

## ADDED Requirements

### Requirement: Listar sólo atenciones atendidas propias para selección clínica
El sistema SHALL listar atenciones `atendido` propias para la selección clínica. Usará el Profesional de la sesión, responderá con campos mínimos y SHALL registrar auditoría metadata-only fail-closed.

#### Scenario: Profesional obtiene su página de atenciones atendidas
- **GIVEN** una sesión vigente de un Profesional activo con vínculo actual
- **WHEN** solicita `GET /profesional/atenciones-atendidas?limit=25&offset=0`
- **THEN** recibe sólo sus turnos `atendido` con los campos mínimos y una página vacía si no tiene resultados
- **AND** el sistema registra auditoría metadata-only antes de devolver el resultado

#### Scenario: Rol operativo no obtiene atenciones para seleccionar contenido clínico
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** solicita `GET /profesional/atenciones-atendidas`
- **THEN** recibe 403 y no se ejecuta una consulta de contenido clínico

#### Scenario: Una falla de auditoría impide devolver la lista
- **GIVEN** un Profesional autenticado con atenciones atendidas propias
- **AND** la escritura del evento de auditoría falla
- **WHEN** solicita la lista de atenciones
- **THEN** la operación falla cerrada y no devuelve nombres ni identificadores de pacientes
