# treatment-plans Specification

## Purpose

Permite organizar planes sintéticos y manuales por paciente mediante prestaciones del catálogo existente y etapas con estado operativo, sin convertirlos en diagnósticos ni asociarlos automáticamente a turnos.

## Requirements

### Requirement: Crear un plan manual con prestaciones del catálogo
El sistema SHALL permitir a un Profesional autorizado crear un plan para un paciente con una o más etapas ordenadas que referencian prestaciones existentes y activas. El contenido de las etapas SHALL permanecer inmutable después del alta; un plan adicional SHALL registrarse por separado. El plan SHALL mantenerse separado de diagnósticos, precios y turnos.

#### Scenario: Crear plan con prestaciones activas
- **GIVEN** un Profesional autorizado y prestaciones activas del catálogo
- **WHEN** registra un plan manual con etapas ordenadas
- **THEN** el sistema conserva las referencias y el orden sin crear precios ni turnos

#### Scenario: Rechazar prestación desconocida o inactiva
- **GIVEN** una etapa que referencia una prestación inexistente o inactiva
- **WHEN** se intenta crear un plan
- **THEN** la API rechaza la solicitud sin guardar cambios ni eliminar datos existentes

### Requirement: Mantener estados operativos explícitos del plan
Cada plan SHALL iniciar en `propuesto` y permitir las transiciones `propuesto` a `en_curso` o `cancelado`, y `en_curso` a `completado` o `cancelado`. Los estados `completado` y `cancelado` SHALL ser terminales; estos estados describen seguimiento operativo y SHALL NOT afirmar consentimiento del paciente.

#### Scenario: Avanzar un plan por estados permitidos
- **GIVEN** un plan `propuesto` o `en_curso`
- **WHEN** se solicita una transición permitida
- **THEN** se confirma el nuevo estado y queda trazado quién y cuándo lo cambió

#### Scenario: Rechazar transición no permitida
- **GIVEN** un plan en estado terminal o una transición fuera del flujo definido
- **WHEN** se solicita el cambio de estado
- **THEN** la API responde 409 y conserva el estado anterior

### Requirement: Consultar planes sólo en atenciones propias
El sistema SHALL permitir consultar o registrar planes únicamente a un Profesional activo vinculado que tenga un turno `atendido` propio para el paciente. Administrador y Recepción SHALL NOT recibir contenido de planes.

#### Scenario: Profesional opera un plan del paciente atendido
- **GIVEN** un Profesional activo vinculado y una atención propia en estado `atendido` para el paciente
- **WHEN** consulta o registra un plan
- **THEN** opera sólo sobre planes de ese paciente bajo su vínculo profesional

#### Scenario: Rol o vínculo sin autorización
- **GIVEN** Administrador, Recepción o un Profesional sin atención propia para el paciente
- **WHEN** intenta consultar o modificar un plan
- **THEN** recibe una respuesta genérica de denegación sin obtener ni cambiar contenido clínico

### Requirement: Auditar cambios de planes sin contenido clínico
El sistema SHALL auditar lecturas y escrituras de planes con metadatos mínimos, sin nombres de pacientes, observaciones clínicas ni detalle del plan. Los eventos SHALL confirmarse en la misma transacción y la operación SHALL fallar cerrada si no se registra la auditoría.

#### Scenario: Auditar operación de plan
- **GIVEN** una lectura o cambio autorizado del plan
- **WHEN** la operación termina
- **THEN** queda un evento metadata-only de actor, acción, recurso, resultado y fecha

#### Scenario: Auditoría no disponible al guardar
- **GIVEN** no se puede confirmar el evento de auditoría
- **WHEN** se crea o cambia un plan
- **THEN** la transacción se revierte y la API no informa éxito
