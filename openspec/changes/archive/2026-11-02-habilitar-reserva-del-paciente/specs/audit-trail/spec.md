# Spec Delta

## ADDED Requirements

### Requirement: Auditar el autoservicio del paciente sin datos de la solicitud
El sistema SHALL auditar las lecturas y mutaciones del portal con actor paciente, acción, tipo, ID opaco y resultado; los eventos SHALL omitir nombre, teléfono, horarios, profesional, box, cuerpo y contenido clínico.

#### Scenario: Lectura de lista o disponibilidad
- **GIVEN** un paciente autenticado que consulta turnos propios o franjas disponibles
- **WHEN** el sistema confirma la lectura
- **THEN** registra un evento metadata-only antes de devolver datos

#### Scenario: Reserva, cancelación o reprogramación
- **GIVEN** un comando válido del paciente
- **WHEN** confirma su mutación
- **THEN** turno, clave idempotente, cambios de recordatorio y evento de auditoría se confirman en una transacción

#### Scenario: Falla de auditoría
- **GIVEN** una lectura o mutación del portal cuya auditoría no puede persistirse
- **WHEN** termina la solicitud
- **THEN** la lectura no entrega datos y la mutación revierte todos sus cambios

#### Scenario: Solicitud denegada
- **GIVEN** una operación del portal denegada por rol, titularidad o elegibilidad
- **WHEN** la denegación se registra
- **THEN** el evento omite el ID de paciente, el horario y el cuerpo de solicitud
