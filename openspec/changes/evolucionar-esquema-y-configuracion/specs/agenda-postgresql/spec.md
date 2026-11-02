# Spec Delta

## Purpose

Permitir que el sistema de turnos use PostgreSQL de forma optativa y explícita, manteniendo la semántica de C-01 y evitando que una configuración incompleta o un esquema no preparado provoquen escrituras implícitas.

## ADDED Requirements

### Requirement: Selección explícita de PostgreSQL
El sistema SHALL usar SQLite cuando no se configure otro backend. Sólo SHALL usar PostgreSQL cuando la configuración lo indique expresamente y proporcione una URL válida; SHALL NOT inferir el backend por la presencia de variables, crear esquemas, migrar datos ni conectarse al importar módulos o crear la app.

#### Scenario: Configuración predeterminada compatible
- **GIVEN** la configuración no selecciona un backend PostgreSQL
- **WHEN** se crea la aplicación y se registra un turno
- **THEN** se conserva el uso de SQLite y el contrato de C-01

#### Scenario: PostgreSQL seleccionado sin URL
- **GIVEN** la configuración selecciona PostgreSQL pero no provee una URL válida
- **WHEN** se carga la configuración
- **THEN** se rechaza explícitamente y no se cambia a SQLite como alternativa

#### Scenario: App creada sin mutar la base
- **GIVEN** PostgreSQL está seleccionado y su esquema aún no está preparado
- **WHEN** se importan módulos o se crea la app
- **THEN** no se crea ni modifica ninguna tabla y no se migra ningún dato

### Requirement: Alta PostgreSQL compatible con C-01
Cuando PostgreSQL está seleccionado, el alta SHALL conservar identificadores, fechas UTC a minuto exacto, intervalo semiabierto, errores públicos, prioridad profesional/box y persistencia confirmada definidos por C-01.

#### Scenario: Alta persiste con identificador positivo
- **GIVEN** un esquema PostgreSQL vigente con referencias ficticias y recursos libres
- **WHEN** se solicita un turno válido mediante la API
- **THEN** se devuelve 201 con ID positivo, las referencias exactas e instantes UTC, y se conserva la fila al abrir otra conexión

#### Scenario: Conflicto conserva la prioridad y el estado
- **GIVEN** un profesional y un box están ocupados en el intervalo solicitado
- **WHEN** se intenta registrar otro turno con ambos recursos
- **THEN** se devuelve `conflicto_profesional` antes que `conflicto_box` y no se inserta ninguna fila

#### Scenario: Esquema no preparado
- **GIVEN** PostgreSQL está seleccionado pero no tiene el esquema vigente
- **WHEN** se solicita un alta
- **THEN** se informa `almacenamiento_error` sin crear el esquema ni cambiar de backend

### Requirement: Exclusión transaccional de PostgreSQL
La operación SHALL serializar las comprobaciones y el alta dentro de una transacción PostgreSQL compartida, impidiendo que escritores concurrentes confirmen solapamientos del mismo profesional o box.

#### Scenario: Dos escritores compiten por profesional
- **GIVEN** dos procesos usan la misma agenda PostgreSQL y solicitan intervalos solapados del mismo profesional con boxes diferentes
- **WHEN** ambos completan la espera configurada
- **THEN** sólo uno confirma y el otro recibe `conflicto_profesional`

#### Scenario: Dos escritores compiten por box
- **GIVEN** dos procesos usan la misma agenda PostgreSQL y solicitan intervalos solapados del mismo box con profesionales diferentes
- **WHEN** ambos completan la espera configurada
- **THEN** sólo uno confirma y el otro recibe `conflicto_box`

#### Scenario: Bloqueo agotado y recuperación
- **GIVEN** otro escritor retiene la serialización más allá del timeout
- **WHEN** se solicita un alta y luego se repite tras liberar el bloqueo
- **THEN** la primera operación informa `agenda_ocupada` sin insertar y la segunda puede completarse

#### Scenario: Recursos independientes y adyacencia
- **GIVEN** los recursos del turno previo son distintos o el nuevo intervalo es adyacente
- **WHEN** se registra un nuevo turno PostgreSQL
- **THEN** el alta se acepta conforme a la regla `[inicio, fin)` de C-01

### Requirement: Rollback ante errores de PostgreSQL
El sistema SHALL confirmar el turno sólo tras completar la transacción y SHALL revertir escrituras pendientes ante fallos controlados. Los errores de PostgreSQL SHALL mapearse a códigos públicos estables sin exponer consultas, credenciales, rutas o detalles internos.

#### Scenario: Fallo antes del commit
- **GIVEN** una operación que falla después de insertar y antes de confirmar
- **WHEN** termina la petición
- **THEN** la nueva conexión no observa el turno y la API informa `almacenamiento_error`

#### Scenario: Repetición de un alta confirmada
- **GIVEN** un turno ya confirmado en PostgreSQL
- **WHEN** se repite exactamente la solicitud con los mismos recursos e intervalo
- **THEN** se informa el conflicto definido por C-01 y no se devuelve un resultado idempotente
