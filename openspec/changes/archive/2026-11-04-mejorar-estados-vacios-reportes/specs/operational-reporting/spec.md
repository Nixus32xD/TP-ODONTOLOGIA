# Spec Delta

## ADDED Requirements

### Requirement: Comunicar estados vacíos accesibles en el panel de reportes
El panel SHALL mostrar un mensaje visible y anunciarlo como estado accesible cuando una consulta exitosa de agenda o finanzas no devuelva días. El estado vacío de un reporte SHALL ser independiente del otro y no SHALL reemplazar un error de consulta.

#### Scenario: Agenda sin datos para el rango
- **GIVEN** una sesión de Recepción y una consulta exitosa cuyo reporte de agenda contiene `dias` vacío
- **WHEN** se muestran los resultados
- **THEN** el panel presenta un mensaje de agenda sin datos dentro de una región accesible de estado, sin mostrar tablas vacías

#### Scenario: Finanzas vacías y agenda con actividad
- **GIVEN** una sesión de Administrador, una agenda con días y un reporte financiero exitoso sin días
- **WHEN** se muestran ambos reportes
- **THEN** el panel conserva las tablas de agenda y comunica por separado que finanzas no tiene movimientos para el rango

#### Scenario: Reporte con datos
- **GIVEN** una consulta exitosa con al menos un día de resultados para un reporte
- **WHEN** se muestran sus resultados
- **THEN** el panel presenta las tablas y no muestra para ese reporte el mensaje de estado vacío

#### Scenario: Error de consulta no se presenta como estado vacío
- **GIVEN** una consulta de reportes que falla
- **WHEN** el panel recibe el error
- **THEN** comunica el error como tal y no presenta un mensaje de consulta exitosa sin datos
