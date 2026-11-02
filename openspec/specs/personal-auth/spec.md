# personal-auth Specification

## Purpose

Permitir que el personal autorizado ingrese al sistema, administre las cuentas de trabajo y opere según permisos comprobados en el backend.

## Requirements

### Requirement: Crear la primera cuenta administradora de forma local
El sistema SHALL permitir crear el primer Administrador sólo mediante una operación local explícita que solicite la contraseña sin mostrarla. SHALL rechazar el bootstrap si ya existe un Administrador y SHALL NOT incluir cuentas, contraseñas ni secretos predeterminados.

#### Scenario: Bootstrap inicial válido
- **GIVEN** el esquema de autenticación está migrado y no existe una cuenta Administrador
- **WHEN** un operador ejecuta el comando local e ingresa credenciales válidas
- **THEN** se crea una cuenta Administrador y la contraseña no aparece en pantalla, salida ni logs

#### Scenario: Administrador activo ya existente
- **GIVEN** ya existe una cuenta Administrador activa
- **WHEN** se ejecuta el comando de bootstrap
- **THEN** se rechaza sin modificar usuarios ni sesiones existentes

### Requirement: Administrar cuentas del personal
El sistema SHALL permitir a un Administrador autenticado crear y consultar cuentas de Administrador, Recepción y Profesional, y cambiar su rol o estado activo.

#### Scenario: Recepción no administra cuentas
- **GIVEN** una sesión válida con rol Recepción
- **WHEN** intenta listar, crear o cambiar una cuenta
- **THEN** recibe 403 y no se modifica el almacenamiento

#### Scenario: Alta de cuenta permitida
- **GIVEN** un Administrador autenticado y un identificador no utilizado
- **WHEN** crea una cuenta Administrador o Recepción con contraseña válida
- **THEN** la cuenta queda persistida y la respuesta omite credenciales y secretos

### Requirement: Vincular cuentas Profesionales con recursos únicos
Una cuenta Profesional SHALL vincularse a un único profesional activo; una ficha SHALL estar asignada como máximo a una cuenta. Las cuentas Administrador y Recepción SHALL carecer de vínculo profesional.

#### Scenario: Alta de cuenta Profesional vinculada
- **GIVEN** un Administrador autenticado y un profesional activo sin cuenta vinculada
- **WHEN** crea una cuenta Profesional y asigna su ID
- **THEN** queda asociada la ficha profesional solicitada

#### Scenario: Asignación profesional inválida o duplicada
- **GIVEN** un ID inexistente/inactivo, un rol incompatible o una ficha ya vinculada
- **WHEN** se intenta crear o cambiar el vínculo
- **THEN** se rechaza con 404/409/422 y no se cambia cuenta, vínculo ni auditoría

### Requirement: Aplicar política de credenciales y respuestas de cuenta
Identificadores SHALL ser únicos tras normalizarse con casefold y trim, y cumplir el formato ASCII de 3–64 caracteres. Contraseñas de 12–128 caracteres SHALL almacenarse sólo como derivación con sal. Respuestas SHALL omitir credenciales, hashes, secretos y tokens.

#### Scenario: Identificador o contraseña fuera de política
- **GIVEN** un identificador con formato inválido o una contraseña menor a 12 o mayor a 128 caracteres
- **WHEN** un Administrador intenta crear una cuenta
- **THEN** recibe 422 sin guardar la cuenta ni mostrar la contraseña

#### Scenario: Identificador duplicado
- **GIVEN** ya existe una cuenta con el identificador normalizado
- **WHEN** se intenta crear otra con el mismo identificador
- **THEN** se rechaza sin revelar datos de la cuenta existente

#### Scenario: Alta de cuenta Profesional omite credenciales
- **GIVEN** un Administrador autenticado y datos válidos de una cuenta Profesional
- **WHEN** crea la cuenta con una ficha profesional activa
- **THEN** la cuenta queda vinculada y la respuesta no contiene contraseña, hash, secreto ni token

### Requirement: Revocar sesiones ante cambios de cuenta
Desactivar una cuenta, cambiar su rol o cambiar su vínculo profesional SHALL revocar sus sesiones activas.

#### Scenario: Desactivación revoca sesiones
- **GIVEN** una cuenta con sesiones activas
- **WHEN** un Administrador la desactiva, cambia su rol o reasigna su profesional
- **THEN** sus sesiones previas dejan de autorizar peticiones

### Requirement: Iniciar sesiones sólo con credenciales válidas
El sistema SHALL emitir una sesión firmada sólo para una cuenta activa Administrador o Recepción o para una cuenta Profesional activa con vínculo válido a un profesional existente. Las respuestas de autenticación fallida SHALL ser genéricas y no distinguir entre cuenta inexistente, inactiva, vínculo faltante o contraseña incorrecta.

#### Scenario: Inicio de sesión válido
- **GIVEN** una cuenta activa habilitada con contraseña válida
- **WHEN** se inicia sesión
- **THEN** se devuelve un token bearer con expiración limitada y datos mínimos de cuenta, sin exponer la derivación de contraseña

#### Scenario: Credenciales inválidas
- **GIVEN** credenciales incorrectas, cuenta inexistente o inactiva, o vínculo profesional inválido
- **WHEN** se solicita una sesión
- **THEN** se devuelve 401 con el mismo mensaje público y no se crea una sesión utilizable

### Requirement: Consultar y revocar la sesión actual
El sistema SHALL permitir a una cuenta autenticada consultar su identidad y rol actuales y revocar su propia sesión. La revocación SHALL invalidar el token inmediatamente, incluso antes de su expiración firmada.

#### Scenario: Sesión vigente
- **GIVEN** un token asociado a una sesión no revocada y una cuenta activa
- **WHEN** se consulta la sesión actual
- **THEN** se devuelve sólo el identificador, rol y expiración de la cuenta

#### Scenario: Cierre de sesión
- **GIVEN** una sesión vigente
- **WHEN** la cuenta cierra su sesión
- **THEN** el token queda revocado y una repetición de la petición protegida recibe 401

#### Scenario: Token expirado, revocado o manipulado
- **GIVEN** un token expirado, revocado, malformado o con firma inválida
- **WHEN** se consulta una ruta protegida
- **THEN** recibe 401 y no se ejecuta la operación

### Requirement: Aplicar el menor privilegio aprobado
El backend SHALL autorizar cada operación según el rol actual de la cuenta. Administrador gestiona las operaciones permitidas; Recepción opera agenda y datos autorizados, pero no administra cuentas. Profesional sólo consulta la agenda de su vínculo y no modifica turnos, catálogos, pacientes ni cuentas.

#### Scenario: Recepción crea un turno
- **GIVEN** una sesión vigente de Recepción
- **WHEN** solicita un turno válido
- **THEN** la API ejecuta el contrato de alta C-01

#### Scenario: Profesional sin alcance de agenda
- **GIVEN** una sesión vigente de Profesional vinculada a profesional-A
- **WHEN** consulta turnos u opciones de disponibilidad de profesional-A
- **THEN** sólo se evalúa el profesional vinculado y no se expone información de otros calendarios

#### Scenario: Profesional no realiza operaciones de escritura
- **GIVEN** una sesión vigente de Profesional
- **WHEN** intenta crear, cancelar, confirmar, marcar atención/ausencia o modificar turnos, catálogos, pacientes o cuentas
- **THEN** recibe 403 sin cambios ni eventos de mutación

#### Scenario: Administrador tiene acceso autorizado
- **GIVEN** una sesión vigente de Administrador
- **WHEN** usa una operación disponible para el personal
- **THEN** se aplica la operación correspondiente y quedan vigentes sus reglas de dominio

### Requirement: Restringir la historia clínica al Profesional responsable
Un Profesional activo SHALL consultar, registrar y corregir evoluciones, consultar y versionar odontogramas, y consultar y registrar planes sólo para pacientes con turno `atendido` propio. Administrador y Recepción SHALL NOT consultar ni modificar contenido clínico. Las capacidades clínicas SHALL aplicar sus reglas de propiedad, estado y auditoría.

#### Scenario: Profesional opera clínica sólo en sus atenciones
- **GIVEN** una sesión vigente de Profesional vinculada a profesional-A
- **WHEN** consulta o registra una evolución, odontograma o plan para un turno `atendido` de profesional-A
- **THEN** la operación se autoriza sólo bajo las reglas de cada capacidad clínica y no amplía permisos sobre la agenda

#### Scenario: Administrador o Recepción no acceden al contenido clínico
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** intenta consultar, registrar o corregir una evolución, consultar o versionar un odontograma, o consultar o cambiar un plan
- **THEN** recibe 403 sin obtener contenido clínico ni modificarlo

### Requirement: Listar sólo atenciones atendidas propias para selección clínica
El sistema SHALL listar atenciones `atendido` propias para la selección clínica. Usará el Profesional de la sesión, responderá con campos mínimos y SHALL registrar auditoría metadata-only fail-closed.

#### Scenario: Profesional obtiene su página de atenciones atendidas
- **GIVEN** una sesión vigente de un Profesional activo con vínculo actual
- **WHEN** solicita `GET /profesional/atenciones-atendidas?limit=25&offset=0`
- **THEN** recibe sólo sus turnos `atendido` con los campos mínimos y una página vacía si no tiene resultados
- **AND** el sistema registra auditoría metadata-only antes de devolver el resultado

#### Scenario: Rol operativo no obtiene atenciones para seleccionar contenido clínico
- **GIVEN** una sesión vigente de Administrador o Recepción
- **WHEN** solicita `GET /profesional/atenciones-atendidas`
- **THEN** recibe 403 y no se ejecuta una consulta de contenido clínico

#### Scenario: Una falla de auditoría impide devolver la lista
- **GIVEN** un Profesional autenticado con atenciones atendidas propias
- **AND** la escritura del evento de auditoría falla
- **WHEN** solicita la lista de atenciones
- **THEN** la operación falla cerrada y no devuelve nombres ni identificadores de pacientes

### Requirement: Fallar cerrado ante configuración de seguridad incompleta
El sistema SHALL requerir un secreto de firma local no versionado con longitud mínima de 32 bytes y una sesión persistida vigente para autorizar peticiones. Si falta configuración, almacenamiento o esquema, SHALL rechazar la operación sin saltarse autenticación ni crear el esquema automáticamente.

#### Scenario: Secreto ausente o débil
- **GIVEN** JWT_SECRETO está ausente o no alcanza la longitud mínima
- **WHEN** se solicita una operación de autenticación o protegida
- **THEN** devuelve 503 antes de acceder al dominio y GET /health sigue disponible

#### Scenario: Almacenamiento de sesión inaccesible
- **GIVEN** no puede confirmarse la vigencia de una sesión persistida
- **WHEN** se solicita una operación protegida
- **THEN** se falla de forma segura sin ejecutar la operación ni emitir éxito

### Requirement: Permitir a Recepción operar fichas mínimas
El backend SHALL permitir a Recepción crear, listar, consultar y actualizar nombre/teléfono de pacientes. SHALL reservar para Administrador la desactivación y reactivación; ninguna operación SHALL habilitar acceso a cuentas de Profesional ni permitir administrar cuentas del personal.

#### Scenario: Recepción administra datos de contacto
- **GIVEN** una sesión vigente de Recepción
- **WHEN** crea, lista, consulta o actualiza una ficha mínima válida
- **THEN** la operación se autoriza y sus validaciones y auditoría se aplican

#### Scenario: Recepción no cambia el estado
- **GIVEN** una sesión vigente de Recepción
- **WHEN** intenta desactivar o reactivar un paciente
- **THEN** recibe 403 sin modificar la ficha

#### Scenario: Recepción no administra cuentas
- **GIVEN** una sesión vigente de Recepción
- **WHEN** intenta crear o modificar una cuenta de personal
- **THEN** continúa recibiendo 403 y no se modifica la cuenta

### Requirement: Limitar intentos fallidos de inicio de sesión
El sistema SHALL limitar en memoria los fallos de autenticación por dirección de origen y hash de cuenta normalizada. Tras cinco fallos en una ventana móvil de cinco minutos, SHALL responder HTTP 429 con `Retry-After` hasta que expire el fallo más antiguo. Un login exitoso SHALL limpiar los fallos confirmados; los contadores SHALL expirar y SHALL NOT producir bloqueos permanentes.

#### Scenario: Se alcanza el límite de fallos
- **GIVEN** cinco intentos fallidos para la misma dirección de origen y cuenta normalizada durante cinco minutos
- **WHEN** llega otro intento para esa combinación antes de expirar la ventana
- **THEN** responde HTTP 429 con `Retry-After` positivo y no verifica credenciales

#### Scenario: Expira el límite temporal
- **GIVEN** una combinación limitada cuyos cinco minutos ya transcurrieron
- **WHEN** llega un nuevo intento
- **THEN** el intento puede verificarse normalmente y no existe un bloqueo permanente

#### Scenario: Inicio de sesión exitoso limpia fallos previos
- **GIVEN** una combinación con fallos previos pero sin un límite activo
- **WHEN** el usuario inicia sesión correctamente
- **THEN** el contador de fallos de esa combinación se limpia

#### Scenario: No se confía en headers de proxy
- **GIVEN** dos peticiones con valores distintos de `X-Forwarded-For` pero la misma dirección de conexión
- **WHEN** ambas fallan al iniciar sesión para la misma cuenta normalizada
- **THEN** se contabilizan bajo la misma dirección de conexión, sin usar el header reenviado

#### Scenario: Estado temporal no persistido
- **GIVEN** ocurre un fallo de autenticación
- **WHEN** se actualiza el control de intentos
- **THEN** no se persiste la IP ni el identificador de cuenta

### Requirement: Reservar capacidad para verificaciones concurrentes
El sistema SHALL reservar atómicamente hasta cinco verificaciones de credenciales activas por dirección de origen y hash de cuenta normalizada antes del trabajo de contraseña. Un intento concurrente adicional SHALL responder 429 con `Retry-After`. Errores de validación o disponibilidad SHALL liberar su reserva sin contar como fallo. Un login exitoso SHALL limpiar fallos confirmados sin descartar otras verificaciones activas.

#### Scenario: Intentos concurrentes limitados antes de verificar
- **GIVEN** seis intentos con la misma dirección de origen y cuenta normalizada llegan mientras se verifican contraseñas
- **WHEN** el límite reserva espacios de verificación
- **THEN** como máximo cinco llegan a la verificación de credenciales y el restante recibe HTTP 429 con `Retry-After`

#### Scenario: Éxito o indisponibilidad libera reservas correctamente
- **GIVEN** existen verificaciones simultáneas para la misma combinación
- **WHEN** una finaliza correctamente o falla por indisponibilidad de la base
- **THEN** el éxito limpia los fallos confirmados conservando otras verificaciones activas, y el error de base libera su espacio sin contar como fallo

#### Scenario: Límite local al proceso
- **GIVEN** la aplicación ejecutada con la configuración de un solo proceso Uvicorn del proyecto
- **WHEN** ocurren fallos de autenticación
- **THEN** el control se aplica en memoria de ese proceso y no afirma coordinación entre múltiples procesos o instancias
