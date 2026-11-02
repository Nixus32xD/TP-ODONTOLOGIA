# Flujos principales

Flujos implementados de C-01 y C-07, con datos ficticios y fechas con offset explícito. [Spec de C-01](../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/specs/alta-turnos/spec.md), [change C-07](../openspec/changes/configurar-horarios-y-bloqueos/) y [evidencia](../docs/evidencia/implementacion-turnos.md).

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

## Flujo 8: consultar agenda y opciones orientativas — C-08 (Apply)

Administrador o Recepción consulta `GET /turnos` con `desde` y `hasta` offset-aware, rango semiabierto de hasta 31 días, filtros opcionales y paginación limitada. Profesional necesita una cuenta vinculada de forma única a una ficha; el JWT y la sesión validada fijan ese ID. Si filtra otro profesional, recibe 403. Su proyección sólo contiene inicio, fin y nombre del paciente; la consulta operativa omite teléfonos.

`GET /disponibilidad` toma una fecha `America/Argentina/Mendoza`, profesional, box y duración positiva. Propone inicios cada 15 minutos que caben en los tramos vigentes de ambos recursos, sin bloquear por estados terminales y excluyendo recursos inactivos, bloqueos y turnos `reservado`/`confirmado`. La consulta no escribe ni audita. El `POST /turnos` posterior vuelve a validar recursos, horarios y conflictos dentro de su transacción; una sugerencia no es una reserva.

## Autenticación y funciones posteriores

C-08 mantiene la consulta autenticada; no habilita reserva pública, WhatsApp, pagos o historia clínica. No se conecta a proveedores externos ni se usan datos reales.

## Flujo 7: reserva con disponibilidad C-07

La API valida SQLite v5 o PostgreSQL Alembic 0006 y falla con 503 si la versión o alguna tabla C-07 falta. Bajo el mismo lock de escritura que protege la reserva, convierte inicio/fin UTC a `America/Argentina/Mendoza`; rechaza el cruce de fecha local, busca la excepción del día y, si no existe, usa la semana. El intervalo completo debe caber en un solo tramo del profesional y del box y no solaparse con bloqueos. Un horario ausente o un día vacío quedan cerrados. Las validaciones de recursos y solapamientos C-01 siguen vigentes.

Administrador o Recepción puede reemplazar el horario semanal completo, guardar o borrar una excepción y crear/listar/borrar bloqueos. Cada mutación y su evento metadata-only comparten transacción; si auditoría falla, ambas se revierten. Antes de confirmar un cambio se revisan sin filtrar por pasado/futuro los turnos del recurso modificado; una incompatibilidad retorna 409 `turnos_afectados` y no registra evento. Esta validación por recurso permite configurar primero profesional y luego box después de migrar turnos C-01; nuevas reservas siguen exigiendo ambos. El servicio standalone de C-01 sobre una base sin migración conserva su comportamiento original hasta que se migre a v5.
