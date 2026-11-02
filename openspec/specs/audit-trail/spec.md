# audit-trail Specification

## Purpose

Proporciona trazabilidad verificable de las operaciones administrativas y de agenda sin almacenar datos clínicos, secretos de autenticación ni contenido de solicitudes.

## Requirements

### Requirement: Eventos de auditoría limitados a metadatos
El sistema SHALL registrar eventos inmutables con fecha UTC, acción, recurso, resultado y actor cuando corresponda. Los eventos SHALL omitir cuerpos, nombres, datos clínicos, credenciales, tokens y hashes.

#### Scenario: Alta confirmada de turno
- **GIVEN** Recepción creó un turno confirmado
- **WHEN** se consulta su evento de auditoría
- **THEN** incluye el actor y el identificador del turno, sin referencias de paciente/profesional/box ni datos de la solicitud

#### Scenario: Autenticación rechazada
- **GIVEN** un inicio de sesión fue rechazado
- **WHEN** se registra el evento
- **THEN** informa rechazo genérico con actor y recurso nulos, sin conservar el identificador intentado ni la causa sensible

### Requirement: Mutaciones y auditoría atómicas
El sistema SHALL confirmar cada mutación auditable y su evento en la misma transacción. Si falla el registro de auditoría, SHALL revertir la mutación y no informar éxito.

#### Scenario: Fallo al auditar una mutación
- **GIVEN** una operación válida modifica un turno, cuenta o sesión
- **WHEN** no se puede almacenar su evento
- **THEN** la transacción no confirma ni la mutación ni el evento

#### Scenario: Rechazo de autenticación auditable
- **GIVEN** las credenciales de inicio de sesión no son válidas
- **WHEN** se puede registrar el evento genérico de rechazo
- **THEN** la operación termina con error 401 genérico y el evento queda confirmado

#### Scenario: Auditoría indisponible durante rechazo
- **GIVEN** las credenciales de inicio de sesión no son válidas
- **WHEN** falla el almacenamiento del evento de rechazo
- **THEN** la operación termina con error 503 genérico y no expone si la cuenta existe

### Requirement: Operaciones incluidas en auditoría
El sistema SHALL auditar altas de turno confirmadas y reprogramaciones confirmadas; creación, cambio de rol y cambio de estado de cuentas; bootstrap del Administrador; aperturas, cierres y rechazos de sesión; cambios de consentimiento de recordatorios; y programación, invalidación, procesamiento y fallos sintéticos del outbox; y altas de cargos, cobros y reversiones monetarias.

#### Scenario: Cuenta actualizada
- **GIVEN** un Administrador crea una cuenta o cambia su rol o estado
- **WHEN** la operación se confirma
- **THEN** queda un evento de la acción con actor y recurso de cuenta, sin datos personales ni credenciales

#### Scenario: Inicio y cierre de sesión
- **GIVEN** una sesión se abre o se cierra correctamente
- **WHEN** termina la operación
- **THEN** queda un evento con actor y acción, sin JWT, secreto ni identificador de sesión reutilizable

#### Scenario: Bootstrap inicial
- **GIVEN** se crea el primer Administrador
- **WHEN** se confirma el bootstrap
- **THEN** queda un evento con actor nulo y recurso de cuenta, sin nombre ni credenciales

#### Scenario: Reprogramación confirmada
- **GIVEN** Administrador o Recepción reprograma un turno y confirma la transacción
- **WHEN** se registra el evento `turno.reprogramado`
- **THEN** contiene actor, recurso `turno`, ID opaco y resultado `confirmado`, sin paciente, recursos, intervalo ni cuerpo

#### Scenario: Cambio de consentimiento
- **GIVEN** Administrador o Recepción cambia la preferencia de recordatorios de un paciente
- **WHEN** la mutación se confirma
- **THEN** queda un evento metadata-only con actor, acción, recurso e ID opaco, sin nombre, teléfono ni valor del consentimiento

#### Scenario: Procesamiento simulado del outbox
- **GIVEN** el worker programa, invalida, procesa o marca un fallo sintético de un recordatorio
- **WHEN** la operación y su evento terminan
- **THEN** se registran sólo actor cuando corresponda, acción, tipo e ID opaco del recurso y resultado, sin teléfono, nombre, mensaje ni contenido clínico

#### Scenario: Fallo al auditar el outbox
- **GIVEN** una operación del outbox cuya auditoría no puede persistirse
- **WHEN** termina la transacción
- **THEN** se revierten el cambio de estado del recordatorio y el evento, sin cambiar ni borrar el turno

#### Scenario: Movimiento monetario auditado sin contenido financiero
- **GIVEN** Administrador o Recepción confirma un cargo o cobro, o Administrador confirma una reversión
- **WHEN** se registra su evento de auditoría
- **THEN** incluye actor, acción, recurso opaco y resultado, y omite importe, moneda, concepto, paciente y motivo

#### Scenario: Rechazo o rollback de movimiento monetario
- **GIVEN** un comando monetario inválido, repetido de forma idempotente o cuya auditoría falla
- **WHEN** finaliza la operación
- **THEN** no se registra evento de éxito nuevo y ningún movimiento parcial queda persistido

### Requirement: Consulta de auditoría protegida y paginada
El sistema SHALL exponer una consulta paginada de eventos sólo para Administrador, con límite predeterminado de 50 y máximo de 100, desplazamiento no negativo y orden estable por fecha UTC descendente e identificador descendente.

#### Scenario: Administrador consulta eventos
- **GIVEN** una sesión válida de Administrador
- **WHEN** consulta `GET /auditoria` con parámetros de página válidos
- **THEN** recibe sólo metadatos permitidos ordenados establemente y una página de hasta 100 eventos

#### Scenario: Otro rol o sesión ausente
- **GIVEN** una solicitud sin sesión o con rol distinto de Administrador
- **WHEN** consulta `GET /auditoria`
- **THEN** recibe 401 o 403 y no obtiene eventos

#### Scenario: Parámetros fuera de límite
- **GIVEN** un límite mayor que 100 o desplazamiento negativo
- **WHEN** se consulta `GET /auditoria`
- **THEN** la API rechaza la solicitud como entrada inválida sin filtrar datos

### Requirement: Auditoría append-only sin purga automática
El sistema SHALL impedir la edición y el borrado ordinarios de eventos y SHALL conservarlos sin purga automática durante este demo.

#### Scenario: No existe operación de modificación o borrado
- **GIVEN** un Administrador consulta la API documentada
- **WHEN** intenta modificar o eliminar un evento mediante operaciones ordinarias
- **THEN** no existe una operación disponible que altere la auditoría

#### Scenario: Retención local del demo
- **GIVEN** hay eventos almacenados
- **WHEN** la aplicación se reinicia o se ejecuta una migración normal
- **THEN** los eventos continúan disponibles y no se purgan automáticamente

### Requirement: Auditar mutaciones de pacientes sin guardar la ficha
El sistema SHALL auditar cada alta, actualización, desactivación y reactivación confirmada de paciente con acción, recurso `paciente`, resultado, actor e ID interno opaco. SHALL omitir nombre, teléfono, cuerpo de solicitud y cualquier otro dato de la ficha. Mutación y evento SHALL confirmarse en la misma transacción; un fallo de auditoría SHALL revertir ambos.

#### Scenario: Alta y actualización de paciente
- **GIVEN** una sesión autorizada y datos ficticios válidos
- **WHEN** se crea o actualiza una ficha
- **THEN** queda un evento confirmado con actor e ID del paciente, sin nombre ni teléfono

#### Scenario: Cambio de estado
- **GIVEN** un Administrador modifica el estado activo de una ficha
- **WHEN** la operación se confirma
- **THEN** queda un evento de desactivación o reactivación con metadatos permitidos

#### Scenario: Auditoría indisponible
- **GIVEN** una mutación válida de paciente cuyo evento no puede almacenarse
- **WHEN** finaliza la operación
- **THEN** la ficha conserva su estado previo y la API no informa éxito

#### Scenario: Lectura de ficha
- **GIVEN** una consulta autorizada de pacientes
- **WHEN** se devuelve una ficha
- **THEN** no se genera un evento de mutación y no se incluyen datos de ficha en el registro de auditoría

### Requirement: Registrar altas de catálogos con metadatos permitidos

El sistema SHALL auditar las altas confirmadas de profesionales, boxes y prestaciones con fecha UTC, actor, acción explícita, tipo e ID opaco del recurso y resultado. SHALL omitir nombres, duración, cuerpos y otros datos del catálogo.

#### Scenario: Auditoría de alta
- **GIVEN** Administrador o Recepción realiza una operación válida sobre un catálogo
- **WHEN** el alta se confirma
- **THEN** queda un evento con actor, ID opaco, acción y tipo permitidos, sin nombre ni datos de prestación

### Requirement: Registrar actualizaciones de catálogos en la misma transacción

El sistema SHALL auditar actualizaciones confirmadas de profesionales, boxes y prestaciones y cambios de estado con metadatos permitidos, sin guardar nombres, duración ni cuerpos. La mutación y el evento SHALL confirmarse en la misma transacción; si el evento no puede guardarse SHALL revertir la operación.

#### Scenario: Auditoría de actualización y cambio de estado
- **GIVEN** Administrador activa o desactiva un registro de catálogo
- **WHEN** confirma el cambio
- **THEN** queda el evento correspondiente con metadatos permitidos y el estado nuevo persiste

#### Scenario: Fallo al almacenar evento
- **GIVEN** una mutación válida de catálogo cuyo evento no puede almacenarse
- **WHEN** se completa la solicitud
- **THEN** se revierte la mutación y la API no informa éxito

#### Scenario: Actualización conserva metadatos
- **GIVEN** una actualización válida de nombre o duración
- **WHEN** se consulta su evento de auditoría
- **THEN** el evento incluye sólo acción, tipo e ID opaco y omite nombre y duración

#### Scenario: Lectura de catálogos
- **GIVEN** un usuario autorizado consulta un catálogo
- **WHEN** la API devuelve resultados
- **THEN** no se crea un evento de mutación

### Requirement: Auditar mutaciones de disponibilidad con metadatos mínimos

El sistema SHALL auditar altas, reemplazos y eliminaciones confirmados de horarios, excepciones y bloqueos con actor, acción permitida, tipo de recurso, ID opaco y resultado. SHALL omitir fechas, intervalos, tramos y cuerpos. Cada mutación y evento SHALL confirmarse en la misma transacción; ante falla se SHALL revertir ambos.

#### Scenario: Auditoría de horario, excepción o bloqueo
- **GIVEN** Administrador o Recepción modifica una configuración válida
- **WHEN** la operación se confirma
- **THEN** existe su evento metadata-only y la configuración coincide con la operación

#### Scenario: Fallo de auditoría
- **GIVEN** una mutación de disponibilidad válida cuyo evento falla al escribirse
- **WHEN** termina la solicitud
- **THEN** la API no informa éxito y la configuración previa permanece intacta

#### Scenario: Cambio rechazado por turnos existentes
- **GIVEN** un cambio que produciría `turnos_afectados`
- **WHEN** la operación se rechaza con HTTP 409
- **THEN** no se crea un evento de mutación ni se cambia la configuración

#### Scenario: Lectura de configuración
- **GIVEN** un usuario autorizado consulta un horario, excepción o bloqueo
- **WHEN** recibe el resultado
- **THEN** la consulta no genera un evento de mutación

### Requirement: Auditar transiciones de estado de turnos
El sistema SHALL auditar cada transición confirmada de estado con actor, acción `turno.estado_actualizado`, tipo de recurso `turno`, ID opaco y resultado `confirmado`. El evento SHALL omitir referencias de paciente, profesional y box, intervalo y cuerpo; mutación y evento SHALL confirmarse en la misma transacción. Las migraciones SHALL ampliar el catálogo de acciones preservando los eventos previos y las protecciones append-only.

#### Scenario: Transición confirmada
- **GIVEN** una transición válida de estado solicitada por Administrador o Recepción
- **WHEN** la mutación se confirma
- **THEN** se guarda un evento metadata-only para el turno y se conserva el nuevo estado

#### Scenario: Fallo al guardar evento
- **GIVEN** una transición válida cuyo evento no puede persistirse
- **WHEN** termina la solicitud
- **THEN** se revierten la transición y su evento, y la API no informa éxito

#### Scenario: Repetición idempotente de cancelación
- **GIVEN** un turno ya cancelado
- **WHEN** se repite la cancelación
- **THEN** se devuelve el estado actual sin agregar otro evento de mutación

#### Scenario: Transición inválida o denegada
- **GIVEN** una transición inválida o una solicitud sin autorización
- **WHEN** se rechaza la operación
- **THEN** no se genera un evento de transición ni se modifica el turno

### Requirement: Auditar accesos y mutaciones de historia clínica sin contenido
El sistema SHALL auditar consultas autorizadas y denegadas, altas y correcciones de evoluciones con fecha UTC, actor, acción, tipo de recurso, resultado e ID opaco cuando exista. Los eventos SHALL omitir nombres, notas, datos clínicos, cuerpos de solicitud/respuesta, credenciales y tokens.

#### Scenario: Consulta autorizada
- **GIVEN** un Profesional solicita una historia clínica que puede consultar
- **WHEN** se confirma la lectura
- **THEN** se registra un evento metadata-only con actor, acción, resultado e ID opaco, sin incluir la historia ni nombres

#### Scenario: Consulta denegada
- **GIVEN** una cuenta autenticada intenta acceder a una historia fuera de su alcance
- **WHEN** se deniega la operación
- **THEN** se registra el resultado denegado sin copiar el contenido clínico ni datos de la solicitud

#### Scenario: Alta o corrección confirmada
- **GIVEN** un Profesional registra una evolución o una corrección válida
- **WHEN** la escritura se confirma
- **THEN** queda un evento metadata-only sin guardar la nota narrativa ni nombres

### Requirement: Confirmar lectura clínica y auditoría en forma conjunta
El sistema SHALL confirmar el evento de auditoría de una lectura clínica antes de devolver contenido. Si no puede almacenar el evento, SHALL responder con error de disponibilidad sin revelar contenido.

#### Scenario: Falla la auditoría de lectura
- **GIVEN** una consulta clínica autorizada cuyo evento no puede persistirse
- **WHEN** finaliza la solicitud
- **THEN** la API devuelve error de disponibilidad y no entrega evoluciones

### Requirement: Confirmar escritura clínica y auditoría en una transacción
El sistema SHALL confirmar cada evolución o corrección y su evento de auditoría en la misma transacción. Si falla el evento, SHALL revertir la escritura y no informar éxito.

#### Scenario: Falla la auditoría de escritura
- **GIVEN** una evolución válida cuyo evento de auditoría no puede almacenarse
- **WHEN** termina la solicitud
- **THEN** la evolución no queda persistida y la API no informa éxito

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
