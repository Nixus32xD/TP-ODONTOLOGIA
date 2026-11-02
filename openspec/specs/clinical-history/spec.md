# clinical-history Specification

## Purpose
Permite registrar y consultar evoluciones clínicas de demostración vinculadas a atenciones finalizadas, con acceso restringido por profesional y trazabilidad que conserva los registros originales.

## Requirements

### Requirement: Mantener evoluciones separadas de la ficha de paciente
El sistema SHALL persistir las evoluciones clínicas en registros separados de la ficha mínima del paciente, vinculando cada una a un paciente, un profesional y un turno atendido. SHALL NOT ampliar la ficha de contacto con campos clínicos.

#### Scenario: Evolución vinculada a una atención
- **GIVEN** una evolución clínica registrada válidamente para un turno atendido
- **WHEN** se consulta la ficha mínima del paciente
- **THEN** la ficha conserva sólo sus campos de contacto y no incluye contenido clínico

### Requirement: Consultar sólo evoluciones de atenciones propias
El sistema SHALL exponer `GET /pacientes/{paciente_id}/historia` sólo para una cuenta Profesional activa vinculada al profesional que atendió al paciente. La respuesta SHALL incluir únicamente evoluciones ligadas a turnos `atendido` del mismo paciente y profesional, ordenadas por creación e ID, con paginación de límite predeterminado 50 y máximo 100.

#### Scenario: Profesional consulta su historia autorizada
- **GIVEN** un Profesional activo y vinculado que tiene al menos un turno atendido para el paciente
- **WHEN** consulta su historia con parámetros válidos
- **THEN** recibe sólo sus evoluciones de turnos atendidos de ese paciente, sin datos de contacto ni contenido de otros profesionales

#### Scenario: Profesional sin atención previa
- **GIVEN** un Profesional que no tiene un turno atendido para el paciente solicitado
- **WHEN** consulta la historia
- **THEN** recibe 404 sin revelar si existen fichas o evoluciones de otros profesionales

### Requirement: Registrar notas narrativas acotadas
El sistema SHALL permitir a un Profesional activo crear una evolución narrativa no vacía de hasta 5000 caracteres, asociada al paciente, al profesional de su cuenta y a un turno `atendido` de ambos. La operación SHALL rechazar campos clínicos estructurados, adjuntos y referencias a turnos de otra persona.

#### Scenario: Alta válida de evolución
- **GIVEN** un Profesional activo vinculado y un turno atendido cuyo paciente y profesional coinciden
- **WHEN** registra una nota narrativa válida
- **THEN** se crea una evolución inmutable con ID y fecha generados por el sistema, sin alterar el turno ni la ficha de paciente

#### Scenario: Nota vacía, excesiva o con campos no admitidos
- **GIVEN** una nota vacía, de más de 5000 caracteres o una solicitud con diagnósticos estructurados, receta o adjuntos
- **WHEN** el Profesional intenta registrar la evolución
- **THEN** se rechaza con 422 sin guardar evolución ni modificar otros datos

#### Scenario: Turno incompatible
- **GIVEN** un turno inexistente, no atendido o asociado a otro paciente o profesional
- **WHEN** se intenta registrar una evolución para ese turno
- **THEN** se rechaza con error genérico de recurso no disponible sin guardar contenido clínico

### Requirement: Corregir evoluciones mediante entradas append-only
El sistema SHALL permitir corregir una evolución propia sólo mediante una nueva evolución que referencia la original y contiene la nota corregida. El original y las correcciones previas SHALL permanecer inmutables y consultables; SHALL NOT existir edición ni borrado ordinario de evoluciones.

#### Scenario: Corrección preserva el registro original
- **GIVEN** una evolución propia vinculada a un turno atendido
- **WHEN** su autor registra una corrección válida
- **THEN** se agrega una nueva entrada con referencia a la original y ambas permanecen disponibles en orden cronológico

#### Scenario: Corrección ajena o referencia inválida
- **GIVEN** una evolución inexistente, de otro profesional o no accesible a la cuenta actual
- **WHEN** se intenta corregirla
- **THEN** se rechaza sin revelar su contenido ni modificar registros existentes

### Requirement: Conservar evoluciones sin purga automática
El sistema SHALL conservar las evoluciones clínicas confirmadas y sus correcciones sin purga automática durante esta demostración. Las migraciones y reinicios normales SHALL NOT borrar ni alterar su contenido.

#### Scenario: Reinicio y migración conservan la historia
- **GIVEN** una base con evoluciones ficticias confirmadas
- **WHEN** la aplicación se reinicia o ejecuta una migración compatible
- **THEN** las evoluciones originales y corregidas permanecen disponibles e inmutables

### Requirement: Limitar el uso a datos ficticios de demostración
La implementación de esta capacidad SHALL documentar y demostrar únicamente con pacientes y notas ficticios; SHALL NOT enviar contenido clínico a servicios externos ni presentarse como preparada para uso productivo.

#### Scenario: Demostración local con datos sintéticos
- **GIVEN** una demostración de historia clínica
- **WHEN** se prepara y ejecuta con los datos de ejemplo del proyecto
- **THEN** todos los pacientes y contenidos clínicos son sintéticos y la documentación declara el alcance local demostrativo
