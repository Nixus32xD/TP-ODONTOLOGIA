# Spec Delta

## ADDED Requirements

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
