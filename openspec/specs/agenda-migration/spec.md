# agenda-migration Specification

## Purpose

Permitir evolucionar el esquema de la agenda y trasladar datos ficticios existentes entre SQLite y PostgreSQL de forma explícita, versionada y verificable, sin modificar la fuente ni sobrescribir un destino.

## Requirements

### Requirement: Versionado incremental del esquema
El sistema SHALL mantener una versión verificable del esquema PostgreSQL. La aplicación de la versión vigente SHALL ser repetible sin alterar los datos existentes, y una versión desconocida SHALL bloquear cambios de negocio sin intentar reparar o reemplazar tablas automáticamente.

#### Scenario: Aplicación repetida del esquema vigente
- **GIVEN** una base PostgreSQL cuya versión de esquema ya es la actual
- **WHEN** se solicita aplicar las migraciones disponibles
- **THEN** el esquema y los datos existentes permanecen sin cambios

#### Scenario: Versión de esquema desconocida
- **GIVEN** una base PostgreSQL con una revisión no reconocida por esta versión del sistema
- **WHEN** la aplicación intenta registrar un turno
- **THEN** informa `almacenamiento_error` y no modifica la base

### Requirement: Migración explícita SQLite a PostgreSQL
El sistema SHALL ofrecer una operación explícita que lea una agenda C-01 SQLite válida y copie sus pacientes, profesionales, boxes y turnos a un esquema PostgreSQL vigente. La operación SHALL conservar los IDs, referencias e instantes en minutos UTC y SHALL NOT modificar ni eliminar la fuente SQLite.

#### Scenario: Migración válida conserva la agenda
- **GIVEN** una agenda SQLite C-01 válida con recursos ficticios y turnos
- **WHEN** se migra a un destino PostgreSQL preparado y vacío
- **THEN** el destino contiene las mismas filas y los mismos IDs, referencias e intervalos, y la fuente conserva su contenido original

#### Scenario: Destino con datos previos
- **GIVEN** un esquema PostgreSQL que ya contiene datos de agenda
- **WHEN** se solicita una migración SQLite
- **THEN** se rechaza sin cambiar el destino ni la fuente

#### Scenario: Fuente inválida o incompatible
- **GIVEN** una ruta ausente, una agenda ilegible o un esquema SQLite incompatible con C-01
- **WHEN** se solicita una migración
- **THEN** se informa un error público de migración sin crear ni alterar datos del destino o de la fuente

### Requirement: Atomicidad de migración de datos
La importación de una agenda SHALL ser una única transacción PostgreSQL. Ante cualquier fallo antes de confirmar la transacción, el destino SHALL permanecer vacío y la fuente SHALL conservarse intacta.

#### Scenario: Fallo durante la importación
- **GIVEN** una migración que falla después de comenzar a insertar recursos o turnos
- **WHEN** la operación termina
- **THEN** PostgreSQL no conserva ninguna fila importada y SQLite permanece sin cambios

#### Scenario: Repetición después de una migración confirmada
- **GIVEN** un destino que ya recibió una migración confirmada
- **WHEN** se vuelve a ejecutar la migración hacia ese destino
- **THEN** se rechaza por destino no vacío sin duplicar filas ni modificar ninguna de las dos agendas
