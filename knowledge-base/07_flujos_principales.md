# Flujos principales

Flujos conceptuales para especificar; no describen componentes existentes. Las horas son ilustrativas en una misma fecha ficticia, sin elegir representación temporal ni duración por prestación.

## Flujo 1: alta válida

**Disparador:** solicitud de registrar un turno. **Actor:** recepción.

1. Recepción proporciona paciente, profesional, box e intervalo conforme al contrato futuro.
2. La operación de alta valida los datos mínimos y referencias acordadas.
3. La operación consulta ocupaciones que cuenten según la política acordada.
4. Sin conflicto de profesional ni box, registra el turno y devuelve un resultado comprensible.
5. La prueba observa los datos del resultado y el efecto del alta según el almacenamiento elegido.

**Ejemplo candidato:** agenda vacía, profesional-A y box-A, 09:00–09:30 → alta exitosa.

**Casos de error:** datos inválidos → rechazo explícito; fallo del mecanismo de registro → error sin afirmar éxito. El contrato de fallos y ausencia de efectos parciales debe concretarse en diseño.

## Flujo 2: conflicto de profesional

**Disparador:** solicitud incompatible con profesional ocupado. **Actor:** recepción.

1. Existe un turno de profesional-A y box-A, 09:00–09:30.
2. Se solicita profesional-A y box-B, 09:15–09:45.
3. El control encuentra conflicto del profesional y rechaza la solicitud, aunque el box sea distinto.
4. El resultado explica el conflicto según el contrato de errores por acordar.

**Confirmado:** rechazar por profesional. **Pendiente:** semántica temporal exacta y forma de verificar que no se registró el rechazo.

**Casos de error/borde candidatos:** turno nuevo contenido dentro del existente; turno que lo contiene; recursos diferentes con intervalos iguales. Requieren especificación y pruebas separadas.

## Flujo 3: conflicto de box

**Disparador:** solicitud incompatible con box ocupado. **Actor:** recepción.

1. Existe profesional-A y box-A, 09:00–09:30.
2. Se solicita profesional-B y box-A, 09:15–09:45.
3. El control encuentra conflicto del box y rechaza, aunque el profesional sea distinto.
4. El resultado explica el recurso ocupado.

**Confirmado:** rechazar por box. **Pendiente:** qué devolver si coinciden los conflictos de profesional y box; no se presupone prioridad ni error múltiple.

## Flujo 4: entrada inválida y borde temporal

**Disparador:** entrada con faltantes, referencia desconocida o intervalo cuestionable. **Actor:** recepción.

1. La operación recibe los datos.
2. Valida según tipos, referencias y límites temporales acordados.
3. Si no cumple el contrato, devuelve error explícito sin modificar silenciosamente el dato.

**Ejemplos propuestos:** 09:00–09:00 y 09:30–09:00 → rechazo si se aprueba inicio anterior al fin. Para existente 09:00–09:30 y nuevo 09:30–10:00, se propone permitir adyacencia usando intervalos semiabiertos. Ninguno de estos bordes se toma como decisión aprobada por esta KB.

## Flujo 5: solicitudes simultáneas — pendiente

Dos altas pueden consultar un recurso libre antes de que cualquiera lo registre. La validación secuencial por sí sola no demuestra exclusión en ese caso.

Antes de especificar una garantía deben elegirse modelo de ejecución, almacenamiento, mecanismo de coordinación y prueba pertinente. No se promete atomicidad entre procesos, máquinas o transacciones; tampoco se elige un bloqueo concreto desde documentación de proveedores.

## Autenticación y funciones posteriores

No se define flujo de login, registro público, WhatsApp, pago ni historia clínica. El actor recepción representa el caso de uso académico; no demuestra identidad autenticada.

## Trazabilidad

US-001 → flujo 1; US-002 → flujo 2; US-003 → flujo 3; US-004 → flujo 4. Flujo 5 depende de Q03 de [preguntas abiertas](10_preguntas_abiertas.md). Los escenarios definitivos se escribirán en el futuro change mediante el CLI de OpenSpec.
