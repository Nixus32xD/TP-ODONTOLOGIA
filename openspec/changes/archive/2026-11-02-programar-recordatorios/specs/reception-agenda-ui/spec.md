# Spec Delta

## MODIFIED Requirements

### Requirement: Exponer formularios mínimos sobre catálogos y disponibilidad
La interfaz SHALL permitir usar las rutas existentes para consultar y administrar fichas, catálogos y horarios ya habilitados al rol, incluyendo el consentimiento `acepta_recordatorios` por Administrador o Recepción. SHALL conservar las respuestas y errores de API y SHALL dejar las decisiones de validez al backend.

#### Scenario: Seleccionar o crear paciente
- **GIVEN** una sesión de Administrador o Recepción y el formulario de alta de turno
- **WHEN** se selecciona un paciente activo o se crea una ficha mínima permitida
- **THEN** la selección usa el ID devuelto por la API y no agrega campos de historia clínica

#### Scenario: Gestionar horarios y bloqueos
- **GIVEN** una sesión autorizada y un recurso profesional o box
- **WHEN** se consultan o modifican horario semanal, excepción o bloqueo
- **THEN** la interfaz usa las rutas C-07 existentes y, ante 409 `turnos_afectados`, conserva la configuración mostrada y presenta el rechazo

#### Scenario: Catálogos y permisos
- **GIVEN** una sesión de Recepción o Administrador
- **WHEN** se listan o editan campos permitidos de catálogos
- **THEN** se respetan las acciones habilitadas para el rol y la respuesta del backend, incluida la restricción de estados activos exclusiva de Administrador

#### Scenario: Mostrar y actualizar consentimiento de recordatorios
- **GIVEN** una sesión de Administrador o Recepción que crea o edita una ficha
- **WHEN** consulta o cambia la opción `acepta_recordatorios`
- **THEN** la interfaz muestra el valor confirmado por la API y no afirma que un recordatorio fue enviado

#### Scenario: Profesional no gestiona preferencias de contacto
- **GIVEN** una sesión Profesional
- **WHEN** consulta la interfaz
- **THEN** no ve controles para consultar o modificar consentimiento de recordatorios
