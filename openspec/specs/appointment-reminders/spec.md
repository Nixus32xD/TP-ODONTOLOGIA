# Appointment Reminders Specification

## Purpose

Permite programar recordatorios locales y simulados para turnos confirmados, respetando el consentimiento revocable y conservando un historial idempotente sin contactar pacientes ni proveedores externos.

## Requirements

### Requirement: Programar sólo recordatorios con consentimiento y plazo
El sistema SHALL programar un recordatorio simulado 24 horas antes de un turno `confirmado` futuro sólo si el paciente mantiene consentimiento. El instante SHALL calcularse desde el horario del turno en `America/Argentina/Mendoza` y persistirse como instante inequívoco.

#### Scenario: Confirmación con tiempo suficiente y consentimiento
- **GIVEN** un paciente con consentimiento y un turno reservado cuya hora de inicio está a más de 24 horas
- **WHEN** Administrador o Recepción confirma el turno
- **THEN** se crea un recordatorio pendiente para 24 horas antes del inicio, asociado al turno y su versión vigente

#### Scenario: Sin tiempo suficiente para el aviso
- **GIVEN** un turno cuya confirmación ocurre a 24 horas o menos de su inicio
- **WHEN** se confirma el turno aunque el paciente tenga consentimiento
- **THEN** no se crea un recordatorio pendiente

#### Scenario: Consentimiento habilitado para turno confirmado
- **GIVEN** un turno futuro confirmado a más de 24 horas y un paciente que cambia su consentimiento a habilitado
- **WHEN** se confirma el cambio de preferencia
- **THEN** se programa un recordatorio pendiente si todavía se cumple el plazo

### Requirement: Mantener un outbox idempotente sin contenido de contacto
El sistema SHALL conservar los recordatorios en un outbox local persistente para SQLite y PostgreSQL. Cada fila SHALL identificar turno, versión, generación, tipo, vencimiento, estado e intentos, con clave única turno+versión+tipo+generación; SHALL NOT almacenar teléfono, mensaje de contacto ni contenido clínico. Una generación invalidada SHALL permanecer en el historial.

#### Scenario: Repetir programación no duplica filas
- **GIVEN** que ya existe un recordatorio con la misma clave de idempotencia
- **WHEN** se vuelve a evaluar esa misma versión de turno
- **THEN** se conserva una sola fila y su estado procesado o invalidado no se reinicia

#### Scenario: Reconsentir conserva historial y crea una generación nueva
- **GIVEN** un turno confirmado y futuro con un recordatorio de generación 1 invalidado por retirar el consentimiento, todavía con más de 24 horas
- **WHEN** Administrador o Recepción vuelve a habilitar el consentimiento
- **THEN** se conserva la generación 1 invalidada y se crea una sola generación 2 pendiente con una clave de idempotencia distinta

#### Scenario: Reconsentimientos concurrentes no duplican la generación
- **GIVEN** un turno elegible con su última generación invalidada
- **WHEN** dos actualizaciones concurrentes vuelven a habilitar el consentimiento
- **THEN** existe una sola generación nueva pendiente y las generaciones anteriores se conservan

#### Scenario: Persistencia después de reiniciar
- **GIVEN** recordatorios pendientes y procesados en el almacenamiento local
- **WHEN** se cierra y vuelve a abrir la aplicación
- **THEN** se conservan las filas y sus estados sin iniciar un envío automático

### Requirement: Revalidar elegibilidad antes de procesar
El sistema SHALL volver a comprobar consentimiento, estado confirmado, versión y hora del turno antes de simular cada recordatorio pendiente. Sólo procesará avisos vencidos mientras el turno siga siendo futuro y la condición de aviso continúe vigente.

#### Scenario: Recordatorio elegible al procesar
- **GIVEN** un recordatorio vencido cuyo paciente consiente y cuyo turno sigue futuro, confirmado y en la versión vinculada
- **WHEN** se ejecuta el worker
- **THEN** se registra el resultado de canal simulado y el recordatorio queda procesado de forma idempotente

#### Scenario: Datos dejan de ser elegibles
- **GIVEN** un recordatorio cuya fecha ya pasó, el turno dejó de estar confirmado, cambió de versión o el paciente retiró el consentimiento
- **WHEN** el worker lo vuelve a validar
- **THEN** lo marca invalidado sin ejecutar el canal simulado

### Requirement: Invalidar recordatorios por cambios de turno o consentimiento
El sistema SHALL invalidar pendientes al cancelar un turno o retirar el consentimiento. Al reprogramar un turno SHALL invalidar la versión anterior y crear una nueva fila sólo si el turno permanece confirmado, el paciente consiente y queda más de 24 horas.

#### Scenario: Cancelar turno invalida el pendiente
- **GIVEN** un turno confirmado con un recordatorio pendiente
- **WHEN** Administrador o Recepción cancela el turno
- **THEN** el recordatorio queda invalidado en la misma transacción y no puede procesarse

#### Scenario: Reprogramar genera clave para la nueva versión
- **GIVEN** un turno confirmado con un recordatorio pendiente
- **WHEN** Administrador o Recepción reprograma el turno
- **THEN** la versión anterior se invalida y sólo se agrega un recordatorio asociado a la nueva versión si conserva el plazo elegible

#### Scenario: Retirar consentimiento invalida los pendientes
- **GIVEN** un paciente con uno o más recordatorios pendientes
- **WHEN** Administrador o Recepción deshabilita el consentimiento
- **THEN** los pendientes se invalidan junto con el cambio de preferencia

### Requirement: Ejecutar una pasada local acotada y explícita
El sistema SHALL ofrecer un worker local que sólo procese una pasada bajo la opción obligatoria `--once` y un límite positivo acotado por ejecución. El worker SHALL usar exclusivamente un canal simulado y SHALL NOT abrir conexiones de red ni iniciar un daemon.

#### Scenario: Ejecutar una pasada
- **GIVEN** una invocación explícita del worker con `--once` y un límite válido
- **WHEN** existen avisos vencidos y elegibles
- **THEN** se procesan como máximo el límite indicado y la ejecución termina

#### Scenario: Rechazar ejecución sin límite de pasada
- **GIVEN** una invocación del worker que omite `--once` o usa un límite fuera de rango
- **WHEN** se valida la línea de comandos
- **THEN** se rechaza antes de abrir el almacenamiento o procesar recordatorios

### Requirement: Limitar reintentos sintéticos y no afirmar entrega externa
El sistema SHALL limitar los reintentos a un máximo definido y permitir fallos únicamente del canal de simulación. Agotar reintentos SHALL marcar el elemento como fallido. El procesamiento SHALL NOT alterar ni borrar el turno ni declarar entregado un mensaje externo.

#### Scenario: Reintento simulado acotado
- **GIVEN** el canal simulado devuelve un fallo sintético recuperable
- **WHEN** se ejecuta el worker en pasadas posteriores
- **THEN** se incrementan los intentos sin duplicar la clave y se detiene al alcanzar el máximo

#### Scenario: Agotar intentos
- **GIVEN** un recordatorio pendiente que alcanzó el máximo de intentos permitidos
- **WHEN** ocurre otro fallo del canal simulado
- **THEN** queda en estado fallido y no vuelve a procesarse automáticamente

### Requirement: Proteger la privacidad del procesamiento simulado
El sistema SHALL registrar y mostrar sólo resultados técnicos y metadatos opacos del procesamiento. SHALL NOT exponer teléfonos, nombres, texto de contacto ni datos clínicos en salida, auditoría o logs.

#### Scenario: Salida y auditoría no incluyen datos personales
- **GIVEN** un recordatorio de prueba asociado a un paciente sintético con teléfono y un turno clínico
- **WHEN** se consulta la salida del worker y sus eventos de auditoría
- **THEN** sólo se observan estado, conteos, acción y referencias técnicas opacas, sin teléfono, nombre, texto clínico ni mensaje de contacto
