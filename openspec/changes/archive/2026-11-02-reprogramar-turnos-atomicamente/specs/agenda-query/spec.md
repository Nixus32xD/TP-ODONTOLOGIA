# Spec Delta

## ADDED Requirements

### Requirement: Exponer versión para reprogramación operativa
La respuesta operativa de `GET /turnos` para Administrador y Recepción SHALL incluir la versión vigente de cada turno. La proyección de Profesional SHALL seguir limitada a inicio, fin y nombre del paciente, sin exponer la versión ni otros campos.

#### Scenario: Personal obtiene la precondición vigente
- **GIVEN** una sesión de Administrador o Recepción que consulta turnos
- **WHEN** recibe filas operativas
- **THEN** cada fila contiene la versión que debe enviar para reprogramar ese turno

#### Scenario: Profesional conserva proyección reducida
- **GIVEN** una sesión de Profesional vinculada a su agenda
- **WHEN** consulta turnos propios
- **THEN** cada fila sólo expone inicio, fin y nombre del paciente
