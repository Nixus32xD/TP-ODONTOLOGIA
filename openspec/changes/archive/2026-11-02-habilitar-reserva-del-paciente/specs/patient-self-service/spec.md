# Spec Delta

## Purpose

Permitir que pacientes con cuentas sintéticas autenticadas consulten y administren sus propios turnos mediante una interfaz acotada, sin revelar información de otras personas ni contenido clínico.

## ADDED Requirements

### Requirement: Exponer autoservicio sólo al paciente autenticado
La API SHALL derivar el paciente exclusivamente del principal autenticado y SHALL autorizar estas operaciones sólo al rol `paciente` activo con vínculo vigente.

#### Scenario: Personal intenta usar el autoservicio
- **GIVEN** una sesión vigente de Administrador, Recepción o Profesional
- **WHEN** solicita una ruta de autoservicio del paciente
- **THEN** recibe 403 antes de consultar o mutar turnos

#### Scenario: Identidad provista en el cuerpo
- **GIVEN** una sesión vigente de paciente
- **WHEN** incluye `paciente_id` en el cuerpo de una reserva o cambio
- **THEN** la solicitud se rechaza como entrada inválida y no altera datos

### Requirement: Consultar turnos propios con datos mínimos
La API SHALL ofrecer `GET /mis-turnos` con turnos propios y campos mínimos de operación, sin clínica, teléfono, catálogo detallado, agenda identificada ni datos de otros turnos.

#### Scenario: Paciente consulta sus turnos
- **GIVEN** una sesión vigente vinculada a paciente-A
- **WHEN** solicita `GET /mis-turnos`
- **THEN** recibe sólo sus turnos y los campos turno_id, inicio, fin, estado y versión

#### Scenario: Lista sin turnos
- **GIVEN** un paciente autenticado sin turnos
- **WHEN** consulta su lista
- **THEN** recibe una colección vacía

### Requirement: Ocultar turnos desconocidos y ajenos
La API SHALL responder de forma indistinguible con 404 para identificadores de turno inexistentes y ajenos, y SHALL comprobar titularidad antes de evaluar o devolver una respuesta idempotente.

#### Scenario: Identificador ajeno
- **GIVEN** un turno existente de paciente-B y una sesión de paciente-A
- **WHEN** paciente-A intenta consultarlo, cancelarlo o reprogramarlo
- **THEN** recibe el mismo 404 que para un identificador inexistente y no obtiene datos del turno

#### Scenario: Repetición de una operación sobre turno ajeno
- **GIVEN** una clave de idempotencia previamente usada por paciente-A y un ID de turno ajeno
- **WHEN** paciente-A repite una operación con esa clave
- **THEN** se valida titularidad primero y la respuesta es el 404 indistinguible

### Requirement: Mostrar únicamente franjas disponibles mínimas
El sistema SHALL permitir al paciente consultar disponibilidad mediante filtros acotados y SHALL devolver sólo franjas seleccionables, sin identificar profesionales, boxes, pacientes ni turnos existentes.

#### Scenario: Consultar franjas disponibles
- **GIVEN** un paciente autenticado y un rango permitido
- **WHEN** solicita disponibilidad
- **THEN** recibe intervalos seleccionables con inicio y fin, sin agenda identificada ni datos de ocupación

#### Scenario: Filtro fuera de rango
- **GIVEN** un rango inválido o mayor al límite documentado
- **WHEN** consulta disponibilidad
- **THEN** recibe 422 sin ejecutar una consulta sin límite

### Requirement: Reservar una franja disponible con límites
El sistema SHALL reservar una franja disponible para el paciente autenticado en una operación serializada que revalida la disponibilidad y SHALL limitar a tres sus turnos futuros activos (`reservado` o `confirmado`).

#### Scenario: Reserva válida
- **GIVEN** una franja disponible y menos de tres turnos futuros activos del paciente
- **WHEN** reserva la franja
- **THEN** se crea un turno `reservado` asociado al paciente autenticado y se devuelve la representación mínima

#### Scenario: Se alcanza el límite personal
- **GIVEN** el paciente ya tiene tres turnos futuros activos
- **WHEN** intenta reservar otra franja
- **THEN** recibe 409 y no se crea otro turno

#### Scenario: Dos pacientes compiten por la misma franja
- **GIVEN** dos pacientes autenticados solicitan simultáneamente una franja
- **WHEN** se serializan las reservas
- **THEN** sólo una se confirma y la otra recibe 409 sin exponer quién obtuvo el turno

### Requirement: Deduplicar comandos mediante claves persistidas
Cada comando de reserva, cancelación o reprogramación SHALL exigir `Idempotency-Key` y guardar la clave por paciente, operación y fingerprint canónico del payload; una repetición igual devuelve el resultado original y otra distinta responde 409. Tras comprobar autenticación y titularidad, un replay confirmado SHALL resolverse antes de volver a validar vigencia temporal, límite de horizonte o versión que sólo correspondan a una operación nueva.

#### Scenario: Repetir la misma solicitud
- **GIVEN** una solicitud confirmada con clave y payload determinados
- **WHEN** se repite con la misma clave y payload
- **THEN** devuelve el mismo resultado sin duplicar mutaciones ni auditoría

#### Scenario: Reusar clave con otro payload
- **GIVEN** una clave persistida para un paciente y operación
- **WHEN** se reutiliza con un payload diferente
- **THEN** responde 409 sin ejecutar la nueva operación

#### Scenario: Repetir luego de vencer la franja u horizonte
- **GIVEN** un comando confirmado cuyo inicio ya pasó o quedó fuera del horizonte vigente
- **WHEN** el paciente autenticado reintenta con la misma clave y payload canónico
- **THEN** recibe el resultado original sin una segunda mutación ni auditoría duplicada
- **AND** la titularidad de la sesión y, para operaciones sobre turno, la titularidad del turno se comprueban antes del replay

### Requirement: Mantener claves idempotentes durante reintentos del portal
La interfaz SHALL reutilizar una clave idempotente para la misma operación, objetivo y payload mientras su resultado no se haya confirmado; una operación, objetivo o payload diferente SHALL usar una clave diferente. La interfaz SHALL descartar la clave pendiente sólo después de completar con éxito la operación y su actualización de vista.

#### Scenario: Reintento tras respuesta ambigua
- **GIVEN** una operación del portal cuya respuesta no pudo confirmarse por un error de transporte
- **WHEN** el paciente reintenta la misma operación con el mismo objetivo y payload
- **THEN** el cliente envía la misma clave idempotente

#### Scenario: Cambia la operación o el payload
- **GIVEN** una clave pendiente para una operación del portal
- **WHEN** el paciente cambia el objetivo, la operación o el payload
- **THEN** el cliente usa una clave idempotente distinta

#### Scenario: Operación confirmada
- **GIVEN** una operación que termina correctamente y cuya vista se actualiza
- **WHEN** el paciente vuelve a iniciar ese comando
- **THEN** el cliente genera una clave nueva

### Requirement: Aplicar anticipación y estados al cancelar
El paciente SHALL cancelar sólo sus turnos `reservado` o `confirmado` cuyo inicio esté al menos 24 horas adelante en `America/Argentina/Mendoza`; titularidad, elegibilidad y mutación SHALL comprobarse atómicamente.

#### Scenario: Cancelación dentro de plazo
- **GIVEN** un turno propio `reservado` o `confirmado` que inicia en 24 horas o más
- **WHEN** el paciente lo cancela
- **THEN** queda cancelado y los recordatorios pendientes se invalidan en la misma operación

#### Scenario: Cancelación tardía o terminal
- **GIVEN** un turno propio que inicia en menos de 24 horas o está en estado terminal
- **WHEN** el paciente intenta cancelarlo
- **THEN** recibe 409 sin cambiar turno, recordatorios ni auditoría de mutación

### Requirement: Reprogramar un turno propio con versión
El paciente SHALL reprogramar sólo turnos propios `reservado` o `confirmado` con al menos 24 horas de anticipación; la operación SHALL conservar paciente, duración y estado y SHALL exigir versión vigente y disponibilidad revalidada en la misma transacción.

#### Scenario: Reprogramación válida
- **GIVEN** un turno propio elegible y un intervalo alternativo disponible de igual duración
- **WHEN** el paciente envía su versión vigente y destino
- **THEN** el turno cambia de horario, conserva paciente, duración y estado e incrementa la versión
- **AND** se invalidan y recalculan recordatorios usando la elegibilidad vigente

#### Scenario: Versión desactualizada o intervalo ocupado
- **GIVEN** una versión obsoleta o un destino que dejó de estar disponible
- **WHEN** el paciente reprograma
- **THEN** recibe 409 y la asignación anterior permanece intacta

### Requirement: Auditar operaciones del portal sin contenido
Las lecturas de turnos propios/disponibilidad y los comandos SHALL generar eventos metadata-only con actor paciente, acción, tipo e ID opaco y resultado; SHALL omitir datos personales, clínica, horarios y cuerpo. La auditoría SHALL confirmarse antes de devolver lecturas o junto a mutaciones.

#### Scenario: Lectura o mutación autorizada
- **GIVEN** una operación válida del portal
- **WHEN** se confirma su resultado
- **THEN** existe un evento de auditoría sin nombre, teléfono, turno horario, cuerpo ni contenido clínico

#### Scenario: Falla la auditoría
- **GIVEN** que la auditoría no puede persistirse
- **WHEN** se consulta o cambia un turno desde el portal
- **THEN** la lectura no devuelve datos y la mutación revierte turno, clave idempotente y recordatorios

### Requirement: Mantener el portal de demostración sintético
El portal SHALL operar sólo con cuentas y pacientes ficticios creados localmente y SHALL NOT habilitar auto-registro, activación o verificación externa, ni comunicar reservas a terceros.

#### Scenario: Uso del portal local
- **GIVEN** una cuenta de paciente creada por Administrador para la demo
- **WHEN** inicia sesión y administra turnos
- **THEN** el sistema procesa localmente la operación sin iniciar comunicación externa
