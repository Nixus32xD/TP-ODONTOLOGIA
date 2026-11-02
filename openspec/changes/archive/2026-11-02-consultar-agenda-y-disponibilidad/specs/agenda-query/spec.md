# Spec Delta

## Purpose

Permite consultar turnos y opciones de horario con filtros, paginación y visibilidad por rol, reutilizando disponibilidad y estados vigentes sin mutar la agenda.

## ADDED Requirements

### Requirement: Consultar turnos por rango temporal acotado

El sistema SHALL exponer `GET /turnos` con `desde` y `hasta` obligatorios, en formato ISO 8601 con offset explícito. El intervalo SHALL ser semiabierto `[desde, hasta)`, con inicio anterior al fin y duración máxima de 31 días. SHALL aceptar filtros opcionales por profesional, box y estado; SHALL ordenar por inicio e ID y paginar con `limit=50`, máximo 100, y `offset=0` no negativo.

#### Scenario: Consulta paginada y filtrada
- **GIVEN** turnos que intersectan el rango y cumplen los filtros opcionales
- **WHEN** Administrador o Recepción consulta con `desde`, `hasta`, filtros y paginación válidos
- **THEN** recibe sólo los turnos de `[desde, hasta)`, en orden estable, con `limit` y `offset` informados

#### Scenario: Rango temporal inválido o excesivo
- **GIVEN** parámetros sin offset, ausentes, mal formados, con `desde >= hasta` o con más de 31 días entre instantes
- **WHEN** se consulta `GET /turnos`
- **THEN** se responde 422 sin consultar datos de la agenda

#### Scenario: Filtro o paginación inválidos
- **GIVEN** un ID vacío/desconocido o estado fuera del catálogo, un límite fuera de 1–100 o un offset negativo
- **WHEN** se consulta `GET /turnos`
- **THEN** se responde 422 para valor inválido y 404 para recurso filtrado desconocido

### Requirement: Limitar filas y campos visibles según el rol

Administrador y Recepción SHALL poder consultar turnos de todos los profesionales y boxes con sus campos operativos permitidos. Profesional SHALL consultar sólo los turnos del profesional vinculado a su cuenta; su respuesta SHALL incluir únicamente inicio, fin y nombre del paciente, sin teléfono ni campos de otros recursos. Si intenta filtrar por otro profesional SHALL recibir 403.

#### Scenario: Personal consulta agenda operativa
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** consulta un rango con varios profesionales y boxes
- **THEN** sólo se devuelven los turnos coincidentes, sin teléfono del paciente ni credenciales

#### Scenario: Profesional consulta su agenda
- **GIVEN** una sesión de Profesional vinculada a un único profesional
- **WHEN** consulta un rango sin solicitar otro profesional
- **THEN** recibe únicamente turnos asignados a ese profesional y cada fila sólo contiene horarios y nombre del paciente

#### Scenario: Profesional intenta consultar otro calendario
- **GIVEN** una sesión de Profesional vinculada a profesional-A
- **WHEN** solicita un filtro explícito por profesional-B
- **THEN** recibe 403 y no se devuelven turnos de profesional-B

### Requirement: Calcular opciones de disponibilidad consultivas

El sistema SHALL exponer `GET /disponibilidad` para una fecha local `YYYY-MM-DD`, profesional, box y duración entera positiva en minutos. SHALL proponer sólo inicios alineados a incrementos de 15 minutos que caben dentro del día local y de los horarios/excepciones vigentes de ambos recursos.

#### Scenario: Opciones cumplen la disponibilidad conjunta
- **GIVEN** un profesional y box activos con horario o excepción que permite algunos inicios de 15 minutos
- **WHEN** se consulta una fecha y duración válida
- **THEN** se devuelven sólo intervalos completos dentro del horario de ambos recursos y sin bloqueo ni ocupación vigente

### Requirement: Excluir opciones con recursos inactivos u ocupaciones

La consulta SHALL excluir intervalos con profesional o box inactivo, bloqueos o turnos ocupantes `reservado`/`confirmado`.

#### Scenario: Ocupación, bloqueo o recurso inactivo elimina opciones
- **GIVEN** turnos reservados/confirmados, bloqueos o un profesional o box inactivo que impiden ciertos intervalos
- **WHEN** se consultan las opciones
- **THEN** no se proponen los intervalos incompatibles y no se modifican turnos ni auditoría

### Requirement: Mantener la consulta orientativa y sin mutaciones

Las opciones SHALL ser orientativas. La consulta SHALL NOT escribir ni auditar; `POST /turnos` SHALL revalidar dentro de su operación serializada.

#### Scenario: Consulta no reserva una opción
- **GIVEN** una opción libre devuelta por `GET /disponibilidad`
- **WHEN** termina la consulta o luego otra solicitud ocupa ese intervalo
- **THEN** la opción no crea una reserva y el alta posterior vuelve a validar agenda y conflictos

#### Scenario: Entrada inválida o recurso desconocido
- **GIVEN** una fecha local inválida, duración no positiva, formato incorrecto o recurso inexistente
- **WHEN** se consulta `GET /disponibilidad`
- **THEN** se responde 422 para parámetros inválidos o 404 para recurso desconocido sin modificar datos

#### Scenario: Profesional consulta opciones propias
- **GIVEN** una sesión de Profesional vinculada a profesional-A
- **WHEN** consulta disponibilidad para profesional-A
- **THEN** recibe opciones sólo para ese profesional; si indica profesional-B recibe 403
