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
El sistema SHALL auditar altas de turno confirmadas; creación, cambio de rol y cambio de estado de cuentas; bootstrap del Administrador; y aperturas, cierres y rechazos de sesión.

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
