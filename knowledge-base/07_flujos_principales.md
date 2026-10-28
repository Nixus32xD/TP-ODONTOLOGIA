# Flujos principales

Flujos implementados de C-01, con datos ficticios y fechas con offset explícito. [Spec](../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/specs/alta-turnos/spec.md) y [evidencia](../docs/evidencia/implementacion-turnos.md).

## Flujo 1: alta válida

Recepción entrega IDs y datetime con offset/minuto exacto. Validar forma, fechas, intervalo y timeout antes de abrir; abrir agenda existente rw, activar FK, BEGIN IMMEDIATE, validar referencias conocidas, consultar conflictos, insertar, COMMIT y retornar Turno en UTC. FastAPI recibe JSON ISO 8601 y delega al mismo dominio; Uvicorn sirve únicamente en loopback, sin proveedores externos. Un alta confirmada se conserva al reabrir conexión.

## Flujo 2: conflicto de profesional

Profesional-A en box-A 09:00–09:30 -03:00; solicitar profesional-A en box-B 09:15–09:45 produce conflicto_profesional, sin insertar. También se prueban igualdad y ambas contenciones. Tiene prioridad ante ambos conflictos.

## Flujo 3: conflicto de box

Box-A ocupado por profesional-A 09:00–09:30 -03:00; solicitar profesional-B en box-A 09:15–09:45 produce conflicto_box, sin insertar. Se prueban ambas contenciones y datos previos intactos.

## Flujo 4: entrada inválida y bordes

Forma inválida produce entrada_invalida/campo; referencia ausente produce recurso_desconocido/campo. No se recortan IDs ni se infiere zona o redondean instantes. Intervalo vacío/invertido rechazado. Adyacencia anterior/posterior permitida; recursos independientes pueden coincidir. Duración positiva libre/cruce de día permitidos, sin disponibilidad clínica ni exclusión de paciente.

## Flujo 5: solicitudes simultáneas

Dos procesos usan el mismo archivo local y conexiones propias. BEGIN IMMEDIATE adquiere permiso antes de consultar: uno confirma, el otro observa ese turno y rechaza el recurso compartido. Si agota el timeout, agenda_ocupada sin éxito ficticio; después de liberar el lock puede volver a solicitarse explícitamente. Sin reintento automático ni idempotencia. Pruebas spawn con Event/Queue, tres repeticiones por recurso y una de recursos distintos.

## Flujo 6: fallo de almacenamiento

Fallo controlado anterior al commit produce almacenamiento_error; rollback y cierre conservan registros anteriores. Un trigger AFTER INSERT RAISE(FAIL) prueba reversión real y recuperación. No se promete reconciliación de IO extremo ni garantía sobre escritores SQL externos.

## Autenticación y funciones posteriores

Sin login, reserva pública, WhatsApp, pagos o historia clínica. Recepción es actor conceptual, no identidad autenticada de producción.
