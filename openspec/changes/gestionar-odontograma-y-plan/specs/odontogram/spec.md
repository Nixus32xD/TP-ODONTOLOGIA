# Spec Delta

## Purpose

Permite registrar y consultar odontogramas sintéticos por paciente, con códigos de piezas y superficies explícitos y un historial versionado que conserva cada observación sin inferir diagnósticos.

## ADDED Requirements

### Requirement: Registrar hallazgos por pieza y superficie
El sistema SHALL permitir guardar hallazgos sintéticos como códigos de pieza ISO 3950 de dos dígitos, una o más superficies individuales admitidas y una observación opcional de hasta 500 caracteres. SHALL NOT inferir diagnósticos, tratamientos ni recomendaciones a partir de estos datos.

#### Scenario: Registrar un hallazgo válido
- **GIVEN** una persona Profesional autorizada y una pieza con superficies compatibles
- **WHEN** registra un hallazgo con códigos y observación válidos
- **THEN** el sistema persiste y devuelve el hallazgo sin crear diagnóstico ni recomendación

#### Scenario: Rechazar pieza o superficie inválida
- **GIVEN** un código de pieza fuera de las denticiones admitidas, una superficie desconocida, repetida o incompatible con pieza anterior/posterior, o una observación superior a 500 caracteres
- **WHEN** se intenta guardar el hallazgo
- **THEN** la API devuelve 422 y no altera el odontograma

#### Scenario: Aceptar ambas denticiones
- **GIVEN** una pieza permanente válida o una pieza primaria válida según la notación FDI de dos dígitos
- **WHEN** se registra un hallazgo sintético compatible
- **THEN** el sistema acepta la pieza y conserva exactamente su código

### Requirement: Versionar el odontograma sin sobrescribir observaciones
El sistema SHALL guardar cada estado completo del odontograma como una nueva versión inmutable, con versión, profesional responsable y fecha generados por el sistema. La corrección SHALL crear otra versión; el sistema SHALL NOT editar ni borrar versiones previas mediante operaciones ordinarias.

#### Scenario: Consultar versiones históricas
- **GIVEN** un paciente con dos o más versiones de odontograma
- **WHEN** el Profesional autorizado consulta el odontograma
- **THEN** recibe la versión vigente y el historial en orden de versión, con sus hallazgos previos preservados

#### Scenario: Corregir un odontograma
- **GIVEN** una versión vigente con un hallazgo que debe corregirse
- **WHEN** el Profesional registra una nueva versión corregida
- **THEN** la nueva versión pasa a ser vigente y la anterior permanece inmutable y consultable

### Requirement: Restringir el odontograma a atención profesional propia
El sistema SHALL permitir consultar o registrar el odontograma sólo a un Profesional activo vinculado que tenga un turno `atendido` propio para el paciente. Administrador y Recepción SHALL NOT recibir contenido del odontograma.

#### Scenario: Profesional consulta o registra con atención propia
- **GIVEN** un Profesional activo vinculado y un turno atendido propio para el paciente
- **WHEN** consulta o registra una versión de odontograma
- **THEN** accede sólo al odontograma de ese paciente y profesional

#### Scenario: Sin atención propia o rol no habilitado
- **GIVEN** el Profesional no tiene una atención propia para el paciente, o la sesión pertenece a Administrador o Recepción
- **WHEN** intenta consultar o escribir el odontograma
- **THEN** recibe una respuesta genérica de denegación y no obtiene ni modifica contenido clínico

### Requirement: Auditar operaciones del odontograma sin datos clínicos
El sistema SHALL registrar lecturas y escrituras del odontograma con metadatos mínimos, sin nota, observación, nombre de paciente ni detalle de hallazgos. La auditoría SHALL confirmarse en la misma transacción que la operación y SHALL fallar cerrada si no puede registrarse.

#### Scenario: Lectura y escritura auditadas
- **GIVEN** una consulta o cambio autorizado del odontograma
- **WHEN** la operación termina
- **THEN** el evento de auditoría contiene actor, acción, tipo/referencia técnica del recurso, resultado y fecha, sin contenido odontológico

#### Scenario: Auditoría no disponible
- **GIVEN** el almacenamiento de auditoría no puede confirmar el evento
- **WHEN** se consulta o modifica un odontograma
- **THEN** la operación no informa éxito y cualquier escritura se revierte
