# resource-catalogs Specification

## Purpose

Administrar los catálogos ficticios de profesionales, boxes y prestaciones sin eliminar referencias históricas ni alterar el contrato de alta de turnos.

## ADDED Requirements

### Requirement: Administrar profesionales y boxes

El sistema SHALL permitir a Administrador y Recepción crear y actualizar profesionales y boxes. Cada registro SHALL tener un ID opaco generado por el sistema, un nombre obligatorio de 1 a 120 caracteres y estado activo. La API SHALL rechazar campos adicionales y entradas inválidas sin modificar el almacenamiento.

#### Scenario: Alta válida de los tres tipos de catálogo
- **GIVEN** una sesión vigente de Administrador o Recepción y datos ficticios válidos
- **WHEN** se crea un profesional o un box
- **THEN** se guarda activo con ID generado y se devuelve sólo el modelo público del recurso

#### Scenario: Nombre inválido o campos extra
- **GIVEN** una operación de profesional o box con nombre ausente, vacío, superior a 120 caracteres o un campo no definido
- **WHEN** se crea o actualiza el registro
- **THEN** la API devuelve 422 sin persistir cambios

### Requirement: Administrar prestaciones

El sistema SHALL permitir a Administrador y Recepción crear y actualizar prestaciones ficticias con ID opaco generado por el sistema, nombre obligatorio de 1 a 120 caracteres, duración entera positiva en minutos y estado activo. SHALL NOT inferir ni redondear la duración y SHALL rechazar campos adicionales.

#### Scenario: Alta válida de prestación
- **GIVEN** una sesión vigente de Administrador o Recepción y nombre y duración válidos
- **WHEN** se crea una prestación
- **THEN** se guarda activa con ID generado y se devuelve sólo el modelo público

#### Scenario: Duración inválida
- **GIVEN** una prestación nueva o existente
- **WHEN** se envía una duración ausente, cero, negativa, fraccionaria, booleana o de tipo incorrecto
- **THEN** la API devuelve 422 y no crea ni modifica la prestación

#### Scenario: Campo adicional
- **GIVEN** una solicitud de prestación con un campo no definido
- **WHEN** se crea o actualiza el registro
- **THEN** la API devuelve 422 sin persistir cambios

### Requirement: Consultar catálogos de forma paginada

El sistema SHALL exponer `GET /profesionales`, `GET /boxes` y `GET /prestaciones`, ordenados por ID ascendente, con límite predeterminado 50, máximo 100 y desplazamiento no negativo. SHALL exponer `GET /{recurso}/{id}` para consultar un registro por ID. Las listas SHALL incluir registros activos e inactivos e indicar el estado. Administrador y Recepción SHALL ser los únicos roles con acceso.

#### Scenario: Listado paginado
- **GIVEN** una sesión de Administrador o Recepción y registros activos e inactivos
- **WHEN** consulta uno de los catálogos con parámetros válidos
- **THEN** recibe una página estable ordenada por ID con los campos públicos y el estado

#### Scenario: Registro inexistente o paginación inválida
- **GIVEN** un ID inexistente, límite mayor a 100 o desplazamiento negativo
- **WHEN** consulta el registro o catálogo
- **THEN** la API devuelve 404 para el ID o 422 para la paginación sin revelar detalles internos

### Requirement: Desactivar y reactivar catálogos mediante baja lógica

El sistema SHALL permitir únicamente a Administrador cambiar el estado activo de profesionales, boxes y prestaciones mediante `PATCH /{recurso}/{id}`. Desactivar SHALL conservar la fila, su ID y referencias históricas; activar SHALL permitir su uso posterior según los requisitos del dominio. La operación SHALL ser idempotente respecto del estado solicitado y SHALL NOT borrar registros.

#### Scenario: Administrador cambia estado
- **GIVEN** un Administrador autenticado y un registro de catálogo
- **WHEN** activa o desactiva el registro
- **THEN** el estado se actualiza sin borrar ni renumerar el recurso

#### Scenario: Recepción intenta cambiar estado
- **GIVEN** una sesión válida de Recepción
- **WHEN** solicita desactivar o reactivar un catálogo
- **THEN** recibe 403 y el estado no cambia

#### Scenario: Recurso con referencias a turnos existentes
- **GIVEN** un profesional o box referenciado por turnos históricos
- **WHEN** un Administrador lo desactiva
- **THEN** el registro y los turnos previos permanecen consultables y asociados

### Requirement: Autorizar acceso a catálogos

El sistema SHALL requerir sesión vigente de Administrador o Recepción para todas las rutas de catálogos y SHALL denegar la operación antes de leer o modificar esos registros ante sesión ausente o rol no autorizado.

#### Scenario: Solicitud sin sesión o rol no habilitado
- **GIVEN** una ruta de catálogo
- **WHEN** se solicita sin sesión vigente o con un rol distinto de Administrador/Recepción
- **THEN** la API devuelve 401 o 403 respectivamente y no accede al catálogo

### Requirement: Mantener prestaciones independientes de turnos

El catálogo de prestaciones SHALL mantenerse separado del registro de turnos. C-06 SHALL NOT agregar una referencia obligatoria u opcional de prestación a `POST /turnos`, ni calcular o limitar el intervalo del turno según la duración de una prestación, ni imponer compatibilidad entre profesionales, boxes y prestaciones.

#### Scenario: Alta C-01 sin prestación
- **GIVEN** una sesión autorizada, paciente activo y profesional/box activos con disponibilidad en el intervalo
- **WHEN** se solicita un turno conforme al cuerpo vigente de C-01 sin campo de prestación
- **THEN** se procesa con la duración recibida y validaciones existentes sin consultar el catálogo de prestaciones

#### Scenario: Prestación sin asociaciones
- **GIVEN** una prestación activa y profesionales o boxes activos
- **WHEN** se administra cualquiera de esos registros
- **THEN** no se crea asociación ni regla de compatibilidad implícita
