# Spec Delta

## MODIFIED Requirements

### Requirement: Incluir registros clínicos en copias y restauraciones
El sistema SHALL incluir evoluciones clínicas, versiones de odontograma, hallazgos, planes y outbox de recordatorios con sus referencias en cada copia completa de una base con esquema C-15 o posterior. El manifiesto SHALL contar las nuevas tablas sin exponer contenido clínico ni datos de contacto y la restauración SHALL validar integridad y claves foráneas antes de declarar éxito.

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

#### Scenario: Backup y restauración preservan odontogramas y planes
- **GIVEN** una base compatible con versiones de odontograma y planes ficticios confirmados
- **WHEN** se crea un bundle y se restaura en un destino nuevo explícito
- **THEN** el snapshot conserva versiones, hallazgos, etapas, estados y referencias; los recuentos coinciden y el manifiesto no contiene notas ni valores clínicos

#### Scenario: Rechazar referencias clínicas inválidas de C-16
- **GIVEN** un bundle con hallazgos, versiones o etapas que referencian piezas, pacientes, profesionales o prestaciones inexistentes
- **WHEN** se verifica o restaura el bundle
- **THEN** se rechaza antes de publicar el destino y se mantiene intacta la fuente

#### Scenario: Copia y restauración preservan el outbox de recordatorios
- **GIVEN** una base de demostración con recordatorios pendientes, procesados e invalidados asociados a turnos sintéticos
- **WHEN** se crea y restaura una copia completa a un destino nuevo
- **THEN** se conservan las filas, estados, claves de idempotencia y referencias, el recuento coincide y el manifiesto no expone teléfonos ni texto de contacto
