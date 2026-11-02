# agenda-availability Specification

## MODIFIED Requirements

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
