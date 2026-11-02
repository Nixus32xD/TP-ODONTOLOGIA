# alta-turnos Specification

## Purpose
Registrar turnos ficticios de recepción con persistencia local, evitando la ocupación simultánea del mismo profesional o box y haciendo observables los rechazos, bordes temporales y límites de la operación.

## Requirements

### Requirement: Preparación explícita de agenda ficticia
El sistema SHALL permitir preparar una agenda local nueva con dos pacientes, dos profesionales y dos boxes ficticios. SHALL rechazar la preparación sobre una agenda existente con `agenda_existente`, sin sobrescribir su contenido. El alta SHALL exigir una agenda preparada y no crearla implícitamente.

#### Scenario: Agenda nueva
- **GIVEN** una ruta local nueva reservada para la demo
- **WHEN** se prepara la agenda
- **THEN** existen los seis recursos ficticios y no existen turnos

#### Scenario: Preparación repetida
- **GIVEN** una agenda preparada con un turno
- **WHEN** se intenta prepararla nuevamente
- **THEN** se informa `agenda_existente` y se conserva el turno original

#### Scenario: Alta sin agenda
- **GIVEN** una ruta donde no existe agenda
- **WHEN** se solicita un alta
- **THEN** se informa `almacenamiento_error` y no se crea una agenda vacía implícita

### Requirement: Identificación válida de recursos
El sistema SHALL exigir identificadores de paciente, profesional y box como cadenas no vacías de hasta 64 caracteres, sin espacios iniciales o finales. SHALL rechazar datos mal formados con `entrada_invalida`, y referencias ausentes del catálogo ficticio con `recurso_desconocido`, indicando el campo. SHALL evaluar campos en orden paciente, profesional, box.

#### Scenario: Identificadores conocidos
- **GIVEN** identificadores válidos existentes y recursos libres
- **WHEN** se solicita un alta válida
- **THEN** se usan exactamente las referencias recibidas, sin recortarlas ni cambiar mayúsculas

#### Scenario: Referencia desconocida
- **GIVEN** un paciente válido y un profesional no registrado
- **WHEN** se solicita el alta
- **THEN** se informa `recurso_desconocido` para profesional y no se registra ningún turno

#### Scenario: Entrada de identificador inválida
- **GIVEN** paciente vacío, con espacios extremos, de tipo distinto de cadena o de más de 64 caracteres
- **WHEN** se solicita el alta
- **THEN** se informa `entrada_invalida` para paciente sin corregir el valor ni registrar un turno

### Requirement: Fechas explícitas y duración positiva
El sistema SHALL aceptar inicio y fin como fechas-hora con offset explícito, segundos y microsegundos cero e inicio anterior al fin. SHALL comparar instantes en UTC y devolverlos en UTC. SHALL rechazar fechas sin offset, tipos incorrectos, precisión menor a un minuto e intervalos vacíos o invertidos con `entrada_invalida`, sin redondear.

#### Scenario: Offsets equivalentes
- **GIVEN** dos solicitudes que representan 12:00–12:30 UTC como 09:00–09:30 -03:00 y como 12:00–12:30 +00:00
- **WHEN** se registra la primera y se solicita la segunda con el mismo profesional
- **THEN** la primera devuelve sus instantes en UTC y la segunda se rechaza por `conflicto_profesional`, pues ocupa el mismo intervalo

#### Scenario: Intervalo vacío o invertido
- **GIVEN** inicio igual o posterior al fin
- **WHEN** se solicita el alta
- **THEN** se informa `entrada_invalida` para intervalo y no se registra un turno

#### Scenario: Fecha sin offset o precisión inválida
- **GIVEN** una fecha sin offset, un valor de tipo incorrecto o una fecha con segundos o microsegundos distintos de cero
- **WHEN** se solicita el alta
- **THEN** se informa `entrada_invalida` para inicio o fin sin inferir zona horaria ni redondear

### Requirement: Persistencia de un alta válida
Con datos válidos y recursos libres, el sistema SHALL registrar exactamente un turno y devolver un identificador entero positivo, las tres referencias e inicio/fin en UTC. SHALL conservar el turno para conexiones y ejecuciones posteriores que usen la misma agenda, y devolver éxito sólo después de confirmar su almacenamiento.

#### Scenario: Alta en agenda vacía
- **GIVEN** agenda preparada sin turnos y referencias conocidas
- **WHEN** se solicita un intervalo válido
- **THEN** se devuelve un turno y la agenda contiene exactamente ese registro

#### Scenario: Persistencia después de cerrar conexión
- **GIVEN** un alta confirmada
- **WHEN** se cierra la conexión y se abre otra sobre la misma agenda
- **THEN** se conserva el mismo identificador, referencias e instantes

### Requirement: Exclusión del profesional
El sistema SHALL rechazar con `conflicto_profesional` un intervalo que solape uno existente del mismo profesional, aunque use otro box. Dos intervalos solapan cuando inicio existente es menor que fin solicitado y fin existente es mayor que inicio solicitado. El rechazo SHALL conservar los registros previos sin insertar otro turno.

#### Scenario: Superposición parcial por profesional
- **GIVEN** profesional-A en box-A de 09:00 a 09:30 -03:00
- **WHEN** se pide profesional-A en box-B de 09:15 a 09:45 -03:00 del mismo día
- **THEN** se informa `conflicto_profesional` y sigue existiendo un único turno

#### Scenario: Contención por profesional
- **GIVEN** profesional-A ocupado de 09:00 a 10:00 -03:00
- **WHEN** se solicita ese profesional de 09:15 a 09:30 o de 08:30 a 10:30 -03:00
- **THEN** se rechaza por profesional tanto el intervalo contenido como el que contiene al existente

### Requirement: Exclusión del box
El sistema SHALL rechazar con `conflicto_box` un intervalo que solape uno existente del mismo box, aunque cambie el profesional, usando el mismo predicado temporal. SHALL informar primero el conflicto de profesional si ambos recursos presentan conflicto. El rechazo SHALL conservar los turnos previos sin insertar otro.

#### Scenario: Superposición por box con profesional distinto
- **GIVEN** box-A ocupado por profesional-A de 09:00 a 09:30 -03:00
- **WHEN** se solicita profesional-B en box-A de 09:15 a 09:45 -03:00
- **THEN** se informa `conflicto_box` sin registrar el nuevo turno

#### Scenario: Contención por box
- **GIVEN** box-A ocupado de 09:00 a 10:00 -03:00
- **WHEN** otro profesional solicita box-A de 09:15 a 09:30 o de 08:30 a 10:30 -03:00
- **THEN** se rechazan ambas solicitudes por box

#### Scenario: Ambos recursos en conflicto
- **GIVEN** un turno ocupa el profesional y otro ocupa el box solicitados durante el mismo intervalo
- **WHEN** se solicita el alta que entra en conflicto con ambos
- **THEN** se informa `conflicto_profesional` de forma determinista y no se registra el alta

### Requirement: Adyacencia y recursos independientes
El sistema SHALL tratar los intervalos como `[inicio, fin)`, permitiendo empezar exactamente al finalizar otro turno y finalizar exactamente al comenzar otro. SHALL aceptar intervalos superpuestos cuando tanto profesional como box son diferentes.

#### Scenario: Adyacencia posterior
- **GIVEN** los mismos recursos ocupados de 09:00 a 09:30 -03:00
- **WHEN** se solicita de 09:30 a 10:00 -03:00
- **THEN** se registra el segundo turno

#### Scenario: Adyacencia anterior
- **GIVEN** los mismos recursos ocupados de 09:00 a 09:30 -03:00
- **WHEN** se solicita de 08:30 a 09:00 -03:00
- **THEN** se registra el turno anterior

#### Scenario: Superposición de recursos diferentes
- **GIVEN** profesional-A y box-A ocupados de 09:00 a 09:30 -03:00
- **WHEN** profesional-B y box-B solicitan de 09:00 a 09:30 -03:00
- **THEN** se registra el segundo turno

### Requirement: Políticas excluidas de esta porción
El sistema SHALL aceptar duración positiva libre, sin asociarla a prestaciones. Con C-07, cada alta SHALL caber en la disponibilidad del profesional y del box y no solaparse con bloqueos. Con C-09, sólo `reservado` y `confirmado` SHALL ocupar recursos; los estados terminales liberan sus intervalos sin borrar la fila. El mismo paciente SHALL poder tener turnos simultáneos si profesional y box difieren, sin compatibilidad adicional ni sobreturnos.

#### Scenario: Cruce de medianoche
- **GIVEN** un turno que comienza un día local y finaliza al siguiente, y horarios que no cruzan medianoche
- **WHEN** se solicita el alta
- **THEN** se rechaza como `fuera_de_disponibilidad`, sin insertar el turno

#### Scenario: Paciente simultáneo con recursos distintos
- **GIVEN** paciente-A tiene turno con profesional-A y box-A
- **WHEN** el mismo paciente solicita el mismo intervalo con profesional-B y box-B libres y disponibles
- **THEN** se acepta; la exclusión del paciente queda expresamente fuera del contrato
### Requirement: Competencia sobre una agenda compartida local
Para solicitudes simultáneas válidas mediante esta operación sobre la misma agenda en disco local, el sistema SHALL confirmar como máximo una cuando comparten profesional o box e intervalos superpuestos. Una solicitud competidora que obtiene acceso antes del timeout SHALL evaluar los turnos ya confirmados; si el timeout se agota SHALL informar `agenda_ocupada` sin éxito ficticio.

#### Scenario: Dos procesos compiten por profesional
- **GIVEN** dos procesos independientes con acceso a la misma agenda e igual profesional e intervalo, pero boxes distintos
- **WHEN** solicitan altas simultáneas y ambos completan el acceso dentro del timeout
- **THEN** uno confirma y otro recibe `conflicto_profesional`; existe exactamente un nuevo turno

#### Scenario: Dos procesos compiten por box
- **GIVEN** dos procesos independientes con la misma agenda e igual box e intervalo, pero profesionales distintos
- **WHEN** solicitan altas simultáneas y ambos completan el acceso dentro del timeout
- **THEN** uno confirma y otro recibe `conflicto_box`; existe exactamente un nuevo turno

#### Scenario: Contención que agota la espera
- **GIVEN** otro escritor mantiene ocupada la agenda más allá del timeout configurado
- **WHEN** se intenta un alta válida
- **THEN** se informa `agenda_ocupada` sin registrar el turno solicitado

### Requirement: Fallos de almacenamiento y reintentos explícitos
El sistema SHALL informar `almacenamiento_error` ante fallos de lectura o registro distintos de contención, sin devolver éxito ni continuar a insertar después de una validación fallida. Ante un fallo controlado antes del commit SHALL revertir la inserción. El sistema SHALL NOT reintentar automáticamente ni prometer idempotencia o deduplicación de peticiones.

#### Scenario: Fallo controlado antes de confirmar
- **GIVEN** una inserción cuyo almacenamiento falla de forma controlada antes del commit
- **WHEN** la operación termina
- **THEN** informa `almacenamiento_error` y una conexión nueva no observa el turno fallido

#### Scenario: Archivo no accesible
- **GIVEN** una ruta inválida o una agenda que no puede abrirse para la operación
- **WHEN** se solicita un alta
- **THEN** se informa `almacenamiento_error` sin crear una agenda alternativa ni devolver éxito

#### Scenario: Repetición después de éxito
- **GIVEN** una solicitud ya confirmada
- **WHEN** se repite exactamente el alta
- **THEN** se informa `conflicto_profesional`, sin devolver el turno anterior como resultado idempotente

### Requirement: Espera de almacenamiento configurable
El sistema SHALL usar por defecto un timeout de 5 segundos y permitir configurarlo como número finito positivo. SHALL rechazar cero, negativos, valores no finitos, booleanos o tipos no numéricos con `entrada_invalida` para timeout antes de acceder a la agenda. El timeout configura la espera por contención, no un plazo garantizado para toda la operación.

#### Scenario: Timeout positivo
- **GIVEN** una agenda disponible y timeout 0.1 o 5.0 segundos
- **WHEN** se solicita un alta válida
- **THEN** el alta se procesa sin rechazar ese valor de configuración

#### Scenario: Timeout inválido
- **GIVEN** timeout cero, negativo, infinito, NaN, booleano o cadena
- **WHEN** se solicita el alta
- **THEN** se informa `entrada_invalida` para timeout sin acceder a la agenda

### Requirement: Adaptador FastAPI local
El sistema SHALL exponer `POST /turnos` mediante FastAPI y devolver 201 sólo tras persistir un alta UTC válida. SHALL exigir una sesión bearer vigente de Administrador o Recepción antes de procesar la solicitud. SHALL aceptar el objeto JSON de cinco campos definido por C-01, con IDs string y fechas ISO 8601 con offset y minuto exacto; SHALL rechazar campos extra y timestamps numéricos. SHALL NOT crear ni inicializar la agenda al importar, crear la app o recibir peticiones.
#### Scenario: Alta HTTP persistida
- **GIVEN** agenda preparada, sesión vigente de Administrador o Recepción y cuerpo válido con recursos libres
- **WHEN** se ejecuta POST /turnos
- **THEN** devuelve 201, ID positivo e instantes UTC y existe una sola fila persistida

#### Scenario: JSON inválido o coerción no permitida
- **GIVEN** sesión autorizada y cuerpo ausente, mal formado, no objeto, con campos adicionales, ID numérico o fecha epoch
- **WHEN** se ejecuta POST /turnos
- **THEN** devuelve 422 entrada_invalida sin alta ni detalles internos

#### Scenario: Sesión ausente o inválida
- **GIVEN** falta el token o la sesión es inválida, expirada o revocada
- **WHEN** se ejecuta POST /turnos
- **THEN** devuelve 401 antes de ejecutar el dominio y no persiste un turno

#### Scenario: Rol no autorizado
- **GIVEN** una sesión autenticada sin permiso de crear turnos
- **WHEN** se ejecuta POST /turnos
- **THEN** devuelve 403 sin ejecutar el dominio ni modificar la agenda

### Requirement: Errores HTTP del dominio
El adaptador SHALL mapear entrada_invalida a 422, recurso_desconocido a 404, conflictos de recursos a 409, agenda_ocupada a 503 y almacenamiento_error a 500 mediante JSON con codigo, campo y mensaje público. SHALL conservar reglas, prioridad profesional/box, rollback y ausencia de reintentos del dominio.

#### Scenario: Conflictos HTTP independientes
- **GIVEN** un turno ocupa profesional-A y box-A
- **WHEN** se solicita igual intervalo cambiando sólo box o sólo profesional
- **THEN** responde 409 con el conflicto correspondiente y conserva un único registro

#### Scenario: Fallo o contención HTTP
- **GIVEN** agenda ausente, corrupta o bloqueada más allá del timeout
- **WHEN** se solicita alta válida
- **THEN** responde 500 almacenamiento_error o 503 agenda_ocupada, sin éxito ficticio ni fuga de rutas

#### Scenario: Fallo al almacenar auditoría del turno
- **GIVEN** el alta del turno es válida pero falla la escritura de su evento de auditoría
- **WHEN** se solicita `POST /turnos`
- **THEN** responde 500 almacenamiento_error y la transacción revierte tanto el turno como el evento

### Requirement: Liveness y documentación local
El sistema SHALL exponer GET /health con 200 y status ok independientemente de la DB, identificándolo como liveness. SHALL publicar en /openapi.json, /docs y /redoc los contratos de alta, sesiones y administración de usuarios, con estados y modelos de entrada/salida. SHALL mantener servidor limitado a uso local sin proveedores externos ni acceso de pacientes.

#### Scenario: Health sin DB
- **GIVEN** una app configurada con una agenda que no existe
- **WHEN** se consulta GET /health
- **THEN** devuelve 200 status ok sin crear el archivo ni afirmar readiness de almacenamiento

#### Scenario: Documentación del único caso de uso
- **GIVEN** la aplicación creada
- **WHEN** se consulta OpenAPI y documentación
- **THEN** OpenAPI contiene las operaciones protegidas de turnos y administración, las rutas de sesión, GET /health público y los estados esperados, y las páginas responden 200

### Requirement: Los turnos nuevos requieren un paciente activo
El sistema SHALL rechazar un alta con `recurso_inactivo` cuando el ID del paciente existe pero su ficha está desactivada. SHALL conservar la prioridad de validación de C-01 para recursos desconocidos y no modificar turnos históricos.

#### Scenario: Paciente inactivo conocido
- **GIVEN** una agenda preparada con una ficha inactiva y recursos profesionales/box válidos
- **WHEN** Administrador o Recepción intenta registrar un turno para esa ficha
- **THEN** el sistema informa `recurso_inactivo` para `paciente` y no inserta ningún turno

#### Scenario: Paciente activo conocido
- **GIVEN** una agenda preparada con una ficha activa y recursos libres
- **WHEN** Administrador o Recepción registra un turno válido
- **THEN** se aplican sin cambios las validaciones y exclusiones del contrato C-01

#### Scenario: Historial de paciente desactivado
- **GIVEN** un turno existente asociado a un paciente que luego fue desactivado
- **WHEN** el personal consulta el turno mediante una capacidad posterior
- **THEN** la referencia al paciente y el turno histórico se conservan

### Requirement: Las nuevas altas requieren profesional y box activos

El sistema SHALL rechazar un alta con `recurso_inactivo` cuando el profesional o box existe pero está desactivado. SHALL conservar la detección de referencias desconocidas de C-01 antes de evaluar estado, no insertar el turno rechazado y dejar intactos los turnos históricos.

#### Scenario: Profesional inactivo
- **GIVEN** una agenda con paciente activo, un profesional inactivo y un box activo
- **WHEN** se intenta crear un turno para ese profesional
- **THEN** se informa `recurso_inactivo` para `profesional` y no se registra el turno

#### Scenario: Box inactivo
- **GIVEN** una agenda con paciente activo, profesional activo y box inactivo
- **WHEN** se intenta crear un turno en ese box
- **THEN** se informa `recurso_inactivo` para `box` y no se registra el turno

#### Scenario: Recurso desconocido conserva su resultado
- **GIVEN** un ID de profesional o box ausente del catálogo
- **WHEN** se solicita un turno
- **THEN** se informa `recurso_desconocido` conforme a C-01, no `recurso_inactivo`

#### Scenario: Desactivación no altera historial
- **GIVEN** un turno existente asociado a un profesional o box que se desactiva
- **WHEN** se consulta posteriormente el almacenamiento
- **THEN** el turno y sus referencias se conservan sin modificación

### Requirement: Validar disponibilidad durante el alta de turnos

`POST /turnos` SHALL verificar dentro de la operación serializada que el turno está disponible para profesional y box antes de insertarlo. Un turno fuera de horario o bloqueado SHALL responder HTTP 409 con `fuera_de_disponibilidad` y no alterar la agenda.

#### Scenario: Disponibilidad de ambos recursos
- **GIVEN** un turno íntegro dentro de un tramo disponible de profesional y box, sin bloqueos
- **WHEN** se solicita el alta
- **THEN** la reserva se confirma después de las validaciones restantes de C-01

#### Scenario: Falta de disponibilidad de un recurso
- **GIVEN** el profesional o box carece de un tramo que contenga el turno completo
- **WHEN** se solicita el alta
- **THEN** se devuelve HTTP 409 con `fuera_de_disponibilidad` y no se inserta el turno

#### Scenario: Carrera entre alta y cambio de disponibilidad
- **GIVEN** una reserva y un cambio de horario o bloqueo concurrentes sobre la misma agenda
- **WHEN** ambas operaciones se serializan y completan
- **THEN** sólo se confirma un estado coherente en el que ningún turno queda fuera de disponibilidad
