# reception-agenda-ui Specification

## Purpose
Ofrece al personal una interfaz web accesible para consultar y operar la agenda del consultorio. La interfaz usa contratos existentes de autenticación y agenda y presenta como autoritativas las respuestas del servidor.

## Requirements

### Requirement: Iniciar y cerrar sesión sin persistir el bearer en el navegador
La interfaz SHALL autenticar al personal con `POST /sesiones`, consultar su identidad vigente y conservar el token sólo en memoria. SHALL ofrecer cierre de sesión revocable mediante `DELETE /sesiones/actual`.

#### Scenario: Inicio de sesión válido del personal
- **GIVEN** una cuenta activa de Administrador, Recepción o Profesional con credenciales válidas y, para Profesional, vínculo vigente
- **WHEN** se inicia sesión desde la interfaz
- **THEN** se consulta la identidad y se habilita sólo la vista/acciones correspondientes al rol sin escribir el bearer en almacenamiento persistente del navegador

#### Scenario: Cierre de sesión
- **GIVEN** una sesión autenticada
- **WHEN** la persona elige cerrar sesión
- **THEN** la interfaz intenta revocar la sesión, elimina de memoria el token y vuelve a la pantalla de acceso

#### Scenario: Sesión vencida o inválida
- **GIVEN** una petición protegida responde 401
- **WHEN** la interfaz recibe la respuesta
- **THEN** elimina el token en memoria, informa que debe iniciar sesión nuevamente y no presenta la operación como confirmada

### Requirement: Consultar agenda diaria y semanal
La interfaz SHALL consultar `GET /turnos` con intervalos offset-aware y rangos de hasta 31 días, conservar filtros y paginación válidos y representar los campos permitidos para el rol autenticado.

#### Scenario: Agenda diaria de Administrador o Recepción
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** se selecciona un día y se consulta la agenda
- **THEN** la interfaz muestra los turnos devueltos por la API con paciente, profesional, box, estado, horario y versión operativa

#### Scenario: Agenda semanal
- **GIVEN** una sesión autorizada y una semana seleccionada
- **WHEN** se consulta un rango de siete días dentro del límite de C-08
- **THEN** se muestra la respuesta de `GET /turnos` para ese rango sin recalcular ocupación ni conflictos en el frontend

#### Scenario: Profesional consulta su propio calendario
- **GIVEN** una sesión Profesional vinculada a un profesional
- **WHEN** consulta su agenda
- **THEN** sólo se muestra el calendario propio y los campos reducidos devueltos por la API, sin controles de escritura ni filtros hacia otros profesionales

#### Scenario: Profesional no recibe consulta de disponibilidad sin catálogo de boxes autorizado
- **GIVEN** una sesión Profesional vinculada a profesional-A y un catálogo de boxes que sólo está habilitado para Administrador/Recepción
- **WHEN** consulta su agenda desde la interfaz
- **THEN** no se ofrece un formulario de disponibilidad ni se le solicita ingresar manualmente IDs de boxes; conserva la vista de agenda propia de sólo lectura

### Requirement: Presentar disponibilidad al personal operativo como orientación y crear turnos por API
Administrador y Recepción SHALL solicitar opciones a `GET /disponibilidad` y crear turnos únicamente mediante `POST /turnos`, usando la duración explícita elegida en minutos y los recursos seleccionados. SHALL NOT inferir esa duración de una prestación. Profesional SHALL permanecer en consulta de su agenda y no verá el formulario de disponibilidad mientras no disponga de un catálogo de boxes autorizado.

#### Scenario: Alta válida con opción sugerida
- **GIVEN** un paciente, profesional y box seleccionados y una opción consultiva elegida
- **WHEN** se envía el alta a `POST /turnos`
- **THEN** sólo tras una respuesta exitosa se muestra el turno como reservado y se recarga la agenda

#### Scenario: Opción deja de estar disponible
- **GIVEN** una opción devuelta previamente por `GET /disponibilidad` que otra operación ocupó
- **WHEN** el alta recibe un conflicto desde la API
- **THEN** se informa el error recibido, no se crea una fila visual de éxito y se actualiza la disponibilidad/agenda

#### Scenario: Turno creado sin prestación asociada
- **GIVEN** una prestación listada en su catálogo independiente
- **WHEN** se registra un turno desde la interfaz
- **THEN** la solicitud no incluye `prestacion_id` y su duración no se deriva del catálogo

### Requirement: Gestionar estado y reprogramación con el contrato vigente
Administrador y Recepción SHALL crear turnos y usar las cuatro transiciones C-09 (confirmar, cancelar, atención y ausencia), además de reprogramar por C-10. Profesional SHALL permanecer en modo de sólo lectura. La interfaz SHALL enviar la versión consultada al reprogramar y SHALL mostrar sólo cambios confirmados por la API.

#### Scenario: Transición de estado confirmada
- **GIVEN** un turno cuyo estado permite la operación elegida
- **WHEN** Administrador o Recepción confirma, cancela, marca atendido o registra ausencia y la API confirma la transición
- **THEN** la interfaz muestra el estado devuelto y actualiza la agenda

#### Scenario: Profesional no ve controles de escritura
- **GIVEN** una sesión Profesional
- **WHEN** consulta su agenda
- **THEN** la interfaz no muestra alta, confirmación, cancelación, atención, ausencia, reprogramación ni formularios de gestión

#### Scenario: Reprogramación con versión vigente
- **GIVEN** un turno operativo con su versión actual y un destino seleccionado
- **WHEN** se envía la reprogramación a `POST /turnos/{id}/reprogramacion`
- **THEN** se usa la versión vigente y la interfaz presenta el turno actualizado sólo después de una respuesta exitosa

#### Scenario: Conflicto o versión obsoleta
- **GIVEN** un cambio rechazado con HTTP 409
- **WHEN** la API devuelve `conflicto_profesional`, `conflicto_box`, `fuera_de_disponibilidad`, `turnos_afectados` o `version_desactualizada`
- **THEN** se muestra el error del servidor, no se sustituye el turno local y se vuelve a consultar la agenda

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
### Requirement: Comunicar estados de interfaz con controles accesibles
Las vistas SHALL permitir navegación por teclado, mantener foco visible y anunciar estados relevantes de carga, vacío, resultado y error sin depender sólo del color.

#### Scenario: Carga, lista vacía y error de consulta
- **GIVEN** una agenda solicitada, sin resultados o con una respuesta de error
- **WHEN** cambia el estado de la petición
- **THEN** la interfaz comunica cuál estado ocurre, conserva controles navegables y permite reintentar una consulta fallida

#### Scenario: Operación pendiente
- **GIVEN** una solicitud de alta, cambio de estado o reprogramación en curso
- **WHEN** el servidor todavía no respondió
- **THEN** se indica que la operación está pendiente y se impiden envíos duplicados desde ese control
