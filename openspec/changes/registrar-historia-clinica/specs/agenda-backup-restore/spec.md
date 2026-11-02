# Spec Delta

## ADDED Requirements

### Requirement: Incluir evoluciones clínicas en copias y restauraciones
El sistema SHALL incluir las evoluciones clínicas y sus referencias en cada copia completa de una base con el esquema C-15. El manifiesto SHALL contar la tabla clínica y la restauración SHALL validar su integridad y claves foráneas antes de declarar éxito.

#### Scenario: Backup local conserva evoluciones
- **GIVEN** una base compatible con evoluciones ficticias confirmadas
- **WHEN** se crea un backup local con el flujo existente
- **THEN** el snapshot contiene las evoluciones y el manifiesto incluye el recuento correspondiente, sin exponer valores de las notas

#### Scenario: Restauración conserva referencias clínicas
- **GIVEN** un backup válido con pacientes, turnos atendidos y evoluciones vinculadas
- **WHEN** se restaura a un destino nuevo explícito
- **THEN** la tabla clínica, sus filas y referencias se validan junto con el esquema existente antes de publicar el destino

#### Scenario: Restauración con referencias inválidas
- **GIVEN** un backup de demostración cuyas referencias clínicas no coinciden con paciente, profesional o turno
- **WHEN** se valida o restaura la copia
- **THEN** se rechaza antes de publicar el destino y el artefacto original permanece intacto
