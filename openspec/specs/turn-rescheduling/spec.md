# turn-rescheduling Specification

## Purpose

Permite mover un turno vigente de manera atómica, manteniendo su identidad, paciente, duración y estado, y validando que la nueva asignación siga siendo operativamente válida.

## Requirements

### Requirement: Reprogramar un turno vigente con control de versión
El sistema SHALL exponer `POST /turnos/{id}/reprogramacion` para Administrador y Recepción. La solicitud SHALL incluir una versión esperada entera positiva, inicio/fin ISO 8601 con offset y profesional/box de destino; SHALL conservar paciente, duración y estado.

#### Scenario: Reprogramación válida conserva el estado y la duración
- **GIVEN** un turno `reservado` o `confirmado`, su versión actual, paciente activo y destinos activos
- **WHEN** Administrador o Recepción solicita un intervalo válido de igual duración, sin cruce de medianoche
- **THEN** responde 200 con el turno reprogramado, versión incrementada en uno, paciente y estado originales y nuevos datos de intervalo/profesional/box

#### Scenario: Reprogramar desde la versión vigente
- **GIVEN** una solicitud con versión esperada distinta de la versión actual del turno
- **WHEN** se procesa la reprogramación
- **THEN** responde 409 `version_desactualizada` y no modifica turno ni auditoría

#### Scenario: Dos reprogramaciones concurrentes con la misma versión
- **GIVEN** dos solicitudes simultáneas para el mismo turno con la misma versión vigente
- **WHEN** ambas se serializan y compiten por confirmar destinos válidos
- **THEN** sólo una actualiza el turno y crea su evento; la otra responde 409 `version_desactualizada` sin mutación ni auditoría

#### Scenario: Versión o intervalo inválidos
- **GIVEN** una versión ausente, no entera o no positiva, una fecha sin offset, precisión distinta del minuto, inicio no anterior al fin o intervalo de distinta duración
- **WHEN** se solicita reprogramar
- **THEN** responde 422 `entrada_invalida` y conserva turno y auditoría

### Requirement: Revalidar la asignación contra la agenda vigente
La operación SHALL validar en una única operación serializada el estado, paciente y destinos activos, horarios, excepciones, bloqueos y ocupación del profesional y box. SHALL usar intervalos `[inicio, fin)` y no imponer exclusión por paciente.

#### Scenario: Conflicto en profesional o box
- **GIVEN** el turno a mover y una nueva franja que solapa otro turno ocupante del profesional o box destino
- **WHEN** se reprograma
- **THEN** responde 409 `conflicto_profesional` o `conflicto_box` según corresponda y no modifica ni el turno original ni la auditoría

#### Scenario: Horario, excepción o bloqueo incompatible
- **GIVEN** una franja destino fuera de horarios/excepciones aplicables o solapada con un bloqueo
- **WHEN** se solicita reprogramar
- **THEN** responde 409 `fuera_de_disponibilidad` y conserva la asignación original sin evento de mutación

#### Scenario: Reprogramar con cruce de medianoche
- **GIVEN** una franja que comienza un día local y termina al día siguiente
- **WHEN** se solicita reprogramar
- **THEN** responde 409 `fuera_de_disponibilidad` y conserva la asignación original sin evento de mutación

#### Scenario: Turno terminal
- **GIVEN** un turno terminal
- **WHEN** se intenta reprogramar
- **THEN** responde 409 `turno_no_reprogramable` y no cambia turno ni auditoría

#### Scenario: Paciente inactivo
- **GIVEN** un turno cuyo paciente fue desactivado después del alta
- **WHEN** se intenta reprogramar
- **THEN** responde 409 `recurso_inactivo` para paciente y no cambia turno ni auditoría

#### Scenario: Destino desconocido o inactivo
- **GIVEN** un profesional o box de destino inexistente o inactivo
- **WHEN** se intenta reprogramar
- **THEN** responde 404 `recurso_desconocido` o 409 `recurso_inactivo` según corresponda y no cambia turno ni auditoría

#### Scenario: Paciente con otro turno simultáneo en recursos distintos
- **GIVEN** el mismo paciente ya tiene un turno en el intervalo de destino con otro profesional y box
- **WHEN** se reprograma usando profesional y box disponibles distintos
- **THEN** no se rechaza por identidad de paciente; se conservan las exclusiones por profesional y box de C-01

### Requirement: Confirmar la reprogramación y su auditoría conjuntamente
El sistema SHALL actualizar asignación, versión, evento `turno.reprogramado` y outbox en una transacción. El evento SHALL incluir sólo actor, acción, recurso `turno`, ID opaco y resultado; SHALL omitir paciente, recursos, intervalo y cuerpo. SHALL invalidar pendientes de la versión anterior y programar para la nueva sólo con turno confirmado, consentimiento y más de 24 horas. Cualquier fallo de auditoría u outbox SHALL revertir la operación.

#### Scenario: Auditoría confirma sólo una reprogramación exitosa
- **GIVEN** una asignación válida y auditoría disponible
- **WHEN** la transacción de reprogramación confirma
- **THEN** se guarda un evento metadata-only con el ID del turno y se devuelve éxito

#### Scenario: Fallo de auditoría conserva la asignación previa
- **GIVEN** una reprogramación válida cuya auditoría falla al persistirse
- **WHEN** termina la operación
- **THEN** se revierte asignación y versión, no queda evento y la API no informa éxito

#### Scenario: Reprogramación invalida la versión anterior
- **GIVEN** un turno confirmado con recordatorio pendiente y consentimiento vigente
- **WHEN** Administrador o Recepción confirma una reprogramación válida
- **THEN** el recordatorio anterior se invalida y se agrega a lo sumo uno para la nueva versión si conserva el plazo de 24 horas

#### Scenario: Fallo del outbox revierte la reprogramación
- **GIVEN** una reprogramación elegible cuya actualización de recordatorios no puede persistirse
- **WHEN** termina la operación
- **THEN** se revierte la asignación, la versión y la auditoría, y no se informa éxito
### Requirement: Restringir el acceso a reprogramaciones
Sólo Administrador y Recepción SHALL reprogramar turnos. Profesional SHALL permanecer sin acceso a esta operación.

#### Scenario: Sesión y rol autorizados
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** solicita una reprogramación válida
- **THEN** la operación aplica las validaciones de dominio y puede confirmar el cambio

#### Scenario: Sesión ausente o rol no autorizado
- **GIVEN** una solicitud sin sesión válida o con rol Profesional
- **WHEN** intenta reprogramar
- **THEN** responde 401 o 403 antes de mutar datos o crear evento

#### Scenario: Turno inexistente
- **GIVEN** un ID que no corresponde a un turno
- **WHEN** Administrador o Recepción solicita reprogramarlo
- **THEN** responde 404 sin mutación ni auditoría

### Requirement: Mantener fuera del alcance la asociación de prestaciones
La operación SHALL conservar la duración del intervalo y SHALL NOT asociar ni validar una prestación, porque los turnos actuales no persisten esa referencia. Un futuro vínculo requiere un change propio.

#### Scenario: Reprogramar un turno sin prestación asociada
- **GIVEN** un turno conforme al modelo vigente, que no contiene `prestacion_id`
- **WHEN** se reprograma con un intervalo de igual duración
- **THEN** no se consulta el catálogo de prestaciones ni se agrega una asociación

### Requirement: Preservar el servicio standalone de C-01
La reprogramación SHALL requerir el esquema migrado de C-10. El servicio standalone SQLite de C-01 SHALL conservar su alta y almacenamiento sin exigir ni crear una versión.

#### Scenario: C-01 standalone no migrado
- **GIVEN** una agenda SQLite standalone que no tiene esquema migrado de C-10
- **WHEN** se usa el alta histórica de C-01
- **THEN** se conserva su contrato sin exigir una columna de versión ni inicializar migraciones implícitamente
