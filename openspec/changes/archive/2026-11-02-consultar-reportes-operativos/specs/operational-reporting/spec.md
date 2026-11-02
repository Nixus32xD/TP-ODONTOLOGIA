# Spec Delta

## Purpose

Proporciona reportes diarios agregados de agenda y movimientos financieros para revisar la operación local del consultorio. Los reportes conservan los límites de privacidad, permisos y exactitud de C-08, C-09 y C-19.

## ADDED Requirements

### Requirement: Validar rangos locales de reportes
La API SHALL aceptar rangos de fechas locales ISO `YYYY-MM-DD` semiabiertos `[desde, hasta)` en `America/Argentina/Mendoza`, con `desde < hasta` y como máximo 31 días. Los errores SHALL responder 422 sin filtrar resultados.

#### Scenario: Rango válido de hasta 31 días
- **GIVEN** un rango local canónico con inicio anterior al fin y hasta 31 días
- **WHEN** se consulta un reporte
- **THEN** incluye sólo fechas desde `desde` inclusive hasta `hasta` exclusiva

#### Scenario: Rango inválido o excesivo
- **GIVEN** fechas ausentes, no canónicas, invertidas o separadas por más de 31 días
- **WHEN** se solicita un reporte JSON o CSV
- **THEN** responde 422 y no devuelve filas agregadas

### Requirement: Resumir agenda por estado y capacidad real
La API SHALL agrupar los turnos por fecha local programada y estado, separando conteos y minutos planificados de `reservado`, `confirmado`, `atendido`, `ausente` y `cancelado`. SHALL calcular capacidad por fecha y recurso desde horarios y excepciones vigentes menos bloqueos, sin contar terminales como ocupación; la ocupación SHALL ser nula cuando la capacidad sea cero.

#### Scenario: Estados no se mezclan
- **GIVEN** turnos de varios estados con inicio local dentro del rango
- **WHEN** Administrador o Recepción consulta el reporte de agenda
- **THEN** cada estado tiene su conteo/minutos; sólo `reservado` y `confirmado` contribuyen a minutos ocupados y `atendido` se informa aparte como duración planificada

#### Scenario: Ocupación sobre disponibilidad vigente
- **GIVEN** horarios semanales, una excepción fechada, bloqueos y turnos vigentes
- **WHEN** se calcula la capacidad diaria de un profesional o box
- **THEN** la excepción reemplaza el horario semanal de esa fecha, los bloqueos descuentan su intersección y la ocupación se expresa sobre esos minutos disponibles

#### Scenario: Recurso cerrado o sin disponibilidad
- **GIVEN** un recurso sin tramos abiertos para una fecha o con todos los minutos bloqueados
- **WHEN** se consulta la capacidad
- **THEN** informa cero minutos disponibles y ocupación nula, sin división por cero

#### Scenario: Turno terminal conservado como actividad
- **GIVEN** turnos `atendido`, `ausente` o `cancelado` cuya fecha programada cae dentro del rango
- **WHEN** se genera el reporte
- **THEN** cada uno sólo aparece en su estado y no ocupa capacidad disponible

### Requirement: Resumir el ledger por fecha de movimiento
La API SHALL agrupar cargos, cobros y reversiones por la fecha local de su `created_at`, informar sus importes y cantidades por separado, calcular neto como cobros menos reversiones y mostrar saldo de apertura/cierre exacto derivado del ledger C-19.

#### Scenario: Reversiones parciales y neto diario
- **GIVEN** cargos, cobros y una o más reversiones parciales con `created_at` dentro del rango
- **WHEN** Administrador consulta el reporte financiero
- **THEN** se muestran cargos, cobros y reversiones por separado y neto diario igual a cobros menos reversiones, con centavos exactos

#### Scenario: Saldo al cierre del rango
- **GIVEN** movimientos anteriores a `desde` y movimientos durante el rango
- **WHEN** Administrador consulta el reporte financiero
- **THEN** el saldo de apertura incluye movimientos anteriores a `desde` y cada saldo de cierre incluye todos los cargos menos cobros más reversiones anteriores al límite local exclusivo de ese cierre

#### Scenario: Sin movimientos
- **GIVEN** un rango sin movimientos financieros
- **WHEN** Administrador consulta el reporte
- **THEN** las cantidades e importes del período son cero y se conserva el saldo acumulado de apertura como saldo de cierre

### Requirement: Restringir reportes por rol y datos
La API SHALL permitir reportes de agenda a Administrador y Recepción, y reportes financieros sólo a Administrador. Los reportes SHALL contener agregados sin pacientes, nombres, teléfonos, cuentas, conceptos, motivos, texto clínico ni identificadores personales.

#### Scenario: Permisos de agenda
- **GIVEN** sesión válida de Administrador o Recepción
- **WHEN** solicita el reporte de agenda
- **THEN** recibe los agregados autorizados sin filas ni identificadores de pacientes

#### Scenario: Permisos financieros
- **GIVEN** sesión válida de Administrador
- **WHEN** solicita el reporte financiero
- **THEN** recibe únicamente los totales agregados del ledger

#### Scenario: Rechazo por rol
- **GIVEN** sesión de Profesional o Paciente, o sesión ausente
- **WHEN** solicita un reporte sin permiso
- **THEN** recibe 403 o 401 y no obtiene resultados ni descarga

### Requirement: Mantener equivalencia JSON y CSV seguro
Cada reporte SHALL ofrecer JSON y CSV UTF-8 determinista desde el mismo resultado agregado, con encabezados y orden estables. CSV SHALL usar filas agregadas, escapar campos y neutralizar valores textuales que puedan iniciar una fórmula de hoja de cálculo.

#### Scenario: CSV coincide con JSON
- **GIVEN** una consulta válida de reporte
- **WHEN** se solicita su versión JSON y CSV con el mismo rango
- **THEN** ambos contienen los mismos valores, agregaciones, precisión monetaria y orden lógico

#### Scenario: CSV protege celdas y no contiene datos excluidos
- **GIVEN** IDs de recursos o texto almacenado que comienza con `=`, `+`, `-` o `@`
- **WHEN** se descarga el CSV
- **THEN** el contenido se neutraliza como texto, mantiene UTF-8 y no incluye conceptos, motivos, nombres, teléfonos o datos clínicos
