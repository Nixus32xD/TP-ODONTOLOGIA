# agenda-availability Specification

## Purpose

Define disponibilidad recurrente y excepcional para profesionales y boxes, y bloqueos temporales que limiten nuevas reservas sin modificar turnos existentes.

## Requirements

### Requirement: Administrar horarios semanales por profesional y box

El sistema SHALL permitir a Administrador y Recepción consultar y reemplazar el horario semanal de un profesional o box. La configuración SHALL incluir cero o más tramos por día ISO (lunes 1 a domingo 7), con horas locales `HH:MM` y fin posterior al inicio.

#### Scenario: Varios tramos en un día
- **GIVEN** una sesión autorizada y un profesional o box conocido
- **WHEN** se configura más de un tramo no solapado en un mismo día
- **THEN** todos los tramos quedan guardados y se devuelven en la consulta del horario

#### Scenario: Día cerrado o recurso sin horario
- **GIVEN** un horario semanal guardado sin tramos para un día, o un recurso sin configuración semanal
- **WHEN** se consulta su disponibilidad para ese día
- **THEN** se considera cerrado

#### Scenario: API requiere el esquema completo de C-07
- **GIVEN** una API configurada con SQLite v5 o PostgreSQL Alembic 0006 cuya versión figura vigente pero falta alguna tabla de disponibilidad
- **WHEN** una persona autenticada intenta una operación protegida
- **THEN** el sistema falla cerrado con HTTP 503 y no modifica turnos, agenda ni auditoría

#### Scenario: Servicio standalone mantiene C-01 antes de migrar
- **GIVEN** una base SQLite creada por C-01 sin `auth_schema_version`
- **WHEN** se invoca directamente el servicio standalone de alta
- **THEN** se conserva el contrato C-01; al migrar explícitamente a v5, las reservas nuevas requieren configurar los dos recursos

### Requirement: Validar tramos locales sin cruce de medianoche

El sistema SHALL aceptar sólo horas locales válidas y tramos cuyo fin sea posterior al inicio. Los tramos no SHALL cruzar medianoche ni solaparse entre sí; sí SHALL permitir adyacencia. La zona local SHALL ser `America/Argentina/Mendoza`.

#### Scenario: Tramo inválido o solapado
- **GIVEN** un tramo mal formado, vacío/invertido, nocturno o solapado con otro del mismo día
- **WHEN** se crea o reemplaza el horario
- **THEN** la API devuelve 422 y conserva la configuración previa

#### Scenario: Tramos adyacentes
- **GIVEN** dos tramos del mismo día donde el primero termina cuando comienza el segundo
- **WHEN** se reemplaza el horario semanal
- **THEN** ambos se aceptan sin fusionar sus valores

### Requirement: Administrar excepciones por fecha

El sistema SHALL permitir a Administrador y Recepción crear, consultar, reemplazar y eliminar una excepción fechada para un profesional o box. Una excepción SHALL reemplazar el horario semanal completo de ese recurso para esa fecha; una lista vacía SHALL indicar cierre.

#### Scenario: Excepción reemplaza la recurrencia
- **GIVEN** una excepción con uno o más tramos para la fecha local del recurso
- **WHEN** se consulta disponibilidad en esa fecha
- **THEN** se usan sólo los tramos de la excepción y no los del día semanal

#### Scenario: Excepción vacía o eliminada
- **GIVEN** una excepción vacía o existente
- **WHEN** se consulta la fecha con excepción vacía, o se elimina la excepción
- **THEN** el recurso está cerrado en el primer caso y vuelve a aplicar el horario semanal en el segundo

### Requirement: Administrar bloqueos por recurso

El sistema SHALL permitir a Administrador y Recepción crear, listar y eliminar bloqueos que pertenezcan exactamente a un profesional o a un box. Cada bloqueo SHALL tener un intervalo positivo con instantes ISO 8601 que incluyan offset; su comparación SHALL usar UTC.

#### Scenario: Bloqueo de un recurso
- **GIVEN** un bloqueo válido con exactamente un profesional o un box
- **WHEN** se crea y luego se lista
- **THEN** se devuelve y conserva su ID opaco, recurso e instantes normalizados a UTC

#### Scenario: Recurso del bloqueo inválido
- **GIVEN** un bloqueo sin recurso, con ambos recursos o con referencia desconocida
- **WHEN** se intenta crear
- **THEN** la API rechaza la solicitud como 422 o 404 y no guarda el bloqueo

### Requirement: Limitar nuevas altas a la disponibilidad conjunta

El sistema SHALL aceptar un turno nuevo sólo si su intervalo completo cabe dentro de un tramo vigente del profesional y un tramo vigente del box, y no se solapa con un bloqueo de ninguno. La evaluación SHALL convertir los instantes del turno a la zona local configurada y usar la excepción fechada cuando exista.

#### Scenario: Turno dentro de ambos horarios
- **GIVEN** un turno cuyo intervalo local cabe íntegramente en un tramo abierto de ambos recursos y no tiene bloqueos
- **WHEN** se solicita el alta
- **THEN** se aplican las validaciones de C-01 y el turno puede confirmarse

#### Scenario: Fuera de horario o no cabe en un solo tramo
- **GIVEN** un turno fuera del horario de cualquiera de sus recursos, o que abarca más de un tramo
- **WHEN** se solicita el alta
- **THEN** se rechaza con HTTP 409 y código `fuera_de_disponibilidad`, sin insertar el turno

#### Scenario: Turno cruza medianoche
- **GIVEN** un turno que comienza un día local y termina al siguiente
- **WHEN** se solicita el alta
- **THEN** se rechaza con `fuera_de_disponibilidad` porque ningún tramo permitido cruza medianoche

#### Scenario: Turno solapa un bloqueo
- **GIVEN** un bloqueo activo sobre el profesional o box solicitado
- **WHEN** el turno se solapa con ese intervalo
- **THEN** se rechaza con HTTP 409 y `fuera_de_disponibilidad`, sin insertar el turno

### Requirement: Validar cambios de agenda contra turnos existentes

El sistema SHALL validar horarios y excepciones del recurso contra turnos `reservado` o `confirmado`, sin filtrar por fecha ni reloj. Si alguno queda fuera de disponibilidad, SHALL rechazar el cambio con HTTP 409 `turnos_afectados` y conservar configuración, auditoría y turnos. Los terminales SHALL conservarse como historial y no impedir cambios. Una configuración compatible SHALL poder guardarse aunque el otro recurso de un turno C-01 migrado no tenga horario.

#### Scenario: Horario o excepción afecta un turno ya registrado
- **GIVEN** un turno `reservado` o `confirmado` que quedaría fuera del horario del recurso
- **WHEN** se guarda el horario semanal, se reemplaza una excepción o se elimina una excepción
- **THEN** se rechaza con 409 y se conserva la versión anterior y el historial

#### Scenario: Turno terminal no impide cambiar horario o excepción
- **GIVEN** un turno `atendido`, `ausente` o `cancelado` asociado al recurso
- **WHEN** se reemplaza un horario semanal o se cierra su excepción para ese intervalo
- **THEN** se guarda la configuración nueva y el turno terminal permanece sin cambios

#### Scenario: Turno pasado incompatible
- **GIVEN** un turno `reservado` o `confirmado` de una fecha pasada y una modificación que lo volvería incompatible
- **WHEN** se intenta guardar la modificación
- **THEN** se rechaza con 409 y permanecen intactos el turno y la configuración
### Requirement: Evitar que un bloqueo nuevo interseque turnos

Un bloqueo nuevo SHALL ser rechazado si se solapa directamente con un turno `reservado` o `confirmado` del recurso objetivo, incluso si el turno es pasado. Los turnos terminales SHALL seguir conservados, pero no impedir la creación del bloqueo. Eliminar un bloqueo SHALL permitirse porque sólo amplía disponibilidad. Toda mutación SHALL guardar juntos los datos y la auditoría o revertir ambos.

#### Scenario: Bloqueo afecta un turno
- **GIVEN** un bloqueo que se solaparía con un turno `reservado` o `confirmado`, incluso pasado
- **WHEN** se intenta crearlo
- **THEN** se rechaza con 409 y no se guarda ni el bloqueo ni un evento de mutación

#### Scenario: Bloqueo sobre un turno terminal
- **GIVEN** un turno `atendido`, `ausente` o `cancelado` asociado al recurso
- **WHEN** se crea un bloqueo que se solapa con su intervalo
- **THEN** se guarda el bloqueo y el turno permanece conservado sin cambios

#### Scenario: Bloqueo compatible y auditoría atómica
- **GIVEN** un bloqueo que no se solapa con turnos ocupantes y una auditoría disponible
- **WHEN** se crea
- **THEN** bloqueo y evento se confirman juntos; si falla auditoría, ambos revierten
