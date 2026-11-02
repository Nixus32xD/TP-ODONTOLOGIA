# turno-lifecycle Specification

## Purpose

Permite que el personal gestione el ciclo de vida de los turnos sin borrar su historial y libera profesional y box cuando el turno deja de ocuparlos.

## Requirements

### Requirement: Crear turnos migrados en estado reservado
Todo turno creado con el esquema de ciclo de vida SHALL comenzar en `reservado`. La migración SHALL asignar `reservado` a cada turno existente sin alterar su ID, referencias ni intervalo.

#### Scenario: Alta después de migrar
- **GIVEN** una agenda con C-09 migrado y recursos disponibles
- **WHEN** se registra un turno válido
- **THEN** queda en estado `reservado` y la respuesta incluye ese estado

#### Scenario: Migración preserva turnos existentes
- **GIVEN** turnos previos a C-09 en una agenda migrada
- **WHEN** se aplica la migración
- **THEN** cada fila conserva sus datos y recibe estado `reservado`

### Requirement: Ocupar recursos sólo en estados vigentes
Los turnos `reservado` y `confirmado` SHALL ocupar sus intervalos de profesional y box. Los turnos `atendido`, `ausente` y `cancelado` SHALL conservarse como historial y no bloquear nuevas altas.

#### Scenario: Estado vigente impide solapamiento
- **GIVEN** un turno `reservado` o `confirmado` que ocupa el profesional o box solicitado
- **WHEN** se intenta una nueva alta superpuesta
- **THEN** se conserva el rechazo de conflicto de C-01

#### Scenario: Estado terminal libera recursos
- **GIVEN** un turno que pasa a `atendido`, `ausente` o `cancelado`
- **WHEN** se solicita un turno superpuesto para sus mismos recursos
- **THEN** se evalúan las demás reglas vigentes y el turno terminal no causa conflicto

### Requirement: Restringir transiciones de estado
El ciclo SHALL permitir `reservado` a `confirmado` o `cancelado`, y `confirmado` a `atendido`, `ausente` o `cancelado`. Los estados `atendido`, `ausente` y `cancelado` SHALL ser terminales.

#### Scenario: Transición permitida
- **GIVEN** un turno en `reservado` o `confirmado`
- **WHEN** se solicita una transición permitida desde su estado actual
- **THEN** se guarda y devuelve el nuevo estado

#### Scenario: Transición no permitida o estado terminal
- **GIVEN** un turno cuya transición no está permitida o ya está en estado terminal
- **WHEN** se solicita cambiarlo a otro estado
- **THEN** se responde HTTP 409 con `transicion_invalida` y se conserva el turno sin nuevo evento de transición

### Requirement: Exponer operaciones de ciclo de vida protegidas
El sistema SHALL permitir a Administrador y Recepción confirmar, cancelar, marcar atendido o registrar ausencia mediante las operaciones `POST /turnos/{id}/confirmacion`, `/cancelacion`, `/atencion` y `/ausencia`. Las operaciones SHALL devolver HTTP 200 con ID y estado resultante; un turno ausente SHALL responder 404 y Profesional SHALL permanecer sin acceso.

#### Scenario: Personal autorizado transiciona un turno
- **GIVEN** una sesión válida de Administrador o Recepción y una transición permitida
- **WHEN** se llama el endpoint correspondiente
- **THEN** responde 200 con el estado actualizado

#### Scenario: Sesión o rol no autorizado
- **GIVEN** una solicitud sin sesión válida o con rol no autorizado
- **WHEN** intenta una operación de ciclo de vida
- **THEN** responde 401 o 403 sin cambiar el turno ni crear un evento de mutación

#### Scenario: Turno inexistente
- **GIVEN** un identificador de turno que no existe
- **WHEN** se solicita una transición
- **THEN** responde 404 sin crear un evento

### Requirement: Hacer idempotente la cancelación repetida
Cancelar un turno ya `cancelado` SHALL devolver HTTP 200 con su estado actual y no SHALL crear otro evento de mutación ni modificar historial.

#### Scenario: Repetir cancelación
- **GIVEN** un turno ya cancelado
- **WHEN** se vuelve a llamar `POST /turnos/{id}/cancelacion`
- **THEN** responde 200 con `cancelado` y permanece un solo evento de cancelación

### Requirement: Serializar transiciones con altas concurrentes
La transición que cambia la ocupación SHALL serializarse con las altas y otras transiciones de la misma agenda. Toda operación confirmada SHALL dejar una ocupación coherente; si hay contención agotada o falla el almacenamiento, SHALL fallar sin éxito ficticio ni mutación parcial.

#### Scenario: Cancelación concurrente con nueva reserva
- **GIVEN** una cancelación y una nueva alta concurrentes que requieren el mismo recurso e intervalo
- **WHEN** ambas operaciones se serializan
- **THEN** la nueva reserva sólo se confirma si al validar la ocupación el turno anterior ya está cancelado

#### Scenario: Auditoría falla durante transición
- **GIVEN** una transición válida cuyo evento no puede guardarse
- **WHEN** termina la operación
- **THEN** se revierte el estado y no se confirma el evento

### Requirement: Conservar contrato standalone de C-01
El servicio standalone C-01 en SQLite sin migración explícita SHALL conservar el contrato histórico: las filas no tienen estado y cada turno registrado ocupa recursos.

#### Scenario: C-01 standalone no migrado
- **GIVEN** una base SQLite de C-01 sin esquema autenticado/versionado de C-09
- **WHEN** se utiliza el servicio standalone sin pasar por la API migrada
- **THEN** se mantienen su resultado y exclusión históricos sin exigir una columna de estado

### Requirement: Validar columna de estado antes de aceptar operaciones migradas
La API SHALL comprobar que `turnos.estado` existe además de validar la versión de esquema vigente. Si falta la columna en SQLite o PostgreSQL, SHALL responder HTTP 503 antes de mutar turnos, agenda o auditoría.

#### Scenario: Falta la columna con versión aparentemente vigente
- **GIVEN** una API cuyo número de versión coincide con la revisión actual, pero a `turnos` le falta `estado`
- **WHEN** una persona autenticada solicita crear o cambiar un turno
- **THEN** la API responde 503 con `autenticacion_no_configurada` y no persiste cambios ni eventos de mutación
