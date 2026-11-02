# Design

## Context

El esquema SQLite autenticado está en versión 5 y PostgreSQL en Alembic `20261102_0006_agenda_availability`; `turnos` aún no tiene estado. Las altas se serializan con `BEGIN IMMEDIATE` en SQLite y con la fila compartida `AgendaMutex` en PostgreSQL. C-01 standalone no versionado permanece separado de la API migrada.

## Goals / Non-Goals

**Goals:** Persistir el estado, controlar transiciones mediante operaciones protegidas, dejar que sólo estados activos ocupen profesional/box y preservar auditoría e historial.

**Non-Goals:** Reprogramar (C-10), habilitar cuentas Profesional, consultar/listar agenda (C-08), borrar turnos o añadir automatización por hora.

## Decisions

- **Un estado en la fila del turno.** Agregar una columna restringida a cinco valores, inicializada como `reservado`. Evita una entidad secundaria que requeriría sincronizar estado actual y eventos; los cambios históricos confirmados ya quedan en auditoría. Las filas previas reciben `reservado` sin tocar sus demás campos.
- **Migraciones aditivas por motor.** SQLite avanzará de versión 5 a 6; Alembic agregará revisión `20261102_0007_turn_status` después de C-07. La misma migración amplía las constraints de auditoría para `turno.estado_actualizado`; SQLite reconstruye la tabla append-only dentro de la transacción y copia todas las filas históricas antes de recrear índice y triggers. Las altas de estado se activan sólo con el esquema migrado. Un downgrade que descartara estados no es seguro, así que la migración debe rechazarlo y requerir una corrección hacia delante.
- **Transiciones y rutas explícitas.** Implementar confirmación, cancelación, atención y ausencia por operación dedicada. La capa de dominio valida el estado actual tras adquirir el lock; estados terminales no se reabren. Evita un endpoint genérico capaz de saltar transiciones.
- **Una ocupación calculada por estado.** Los predicados de conflicto de profesional y box, y las validaciones de C-07 al modificar horarios, excepciones y bloqueos, filtrarán `reservado`/`confirmado` después de migrar. Los estados terminales permanecen como historial y no bloquean la configuración posterior; los turnos ocupantes siguen causando 409. C-01 standalone sin la columna conserva consultas y semántica originales; no se agrega acceso a cuentas Profesional.
- **Validación fail-closed del esquema migrado.** La API comprobará también la presencia de `turnos.estado`, además de la versión y las tablas de C-07. Una versión vigente con esa columna ausente responderá 503 antes de consultar o mutar la agenda; SQLite usa `PRAGMA table_info` y PostgreSQL `information_schema.columns`.
- **La transición comparte el lock de alta.** SQLite toma `BEGIN IMMEDIATE`; PostgreSQL bloquea `AgendaMutex` y actualiza el turno dentro de la misma transacción. Así una alta concurrente no puede comprobar el estado anterior a una cancelación y confirmar una ocupación duplicada.
- **Idempotencia sólo para cancelar.** Si ya está cancelado, responder el estado existente sin escribir transición/auditoría. Las demás transiciones no repetibles responden conflicto. Cada mutación efectiva registra `turno.estado_actualizado` con resultado `confirmado` y metadatos mínimos; mutación y evento comparten transacción, reutilizando la política de auditoría existente.

## Risks / Trade-offs

- [Las filas previas pasan a ser cancelables por primera vez] → La migración las marca `reservado`, ocupante y no destructivo, para no liberar agenda accidentalmente.
- [Dos motores pueden divergir en constraints o transacciones] → Mantener contratos comunes y probar migración, rollback, auditoría y competencia en SQLite y PostgreSQL aislado.
- [Marcar atendido/ausente una cita futura liberaría recursos] → Las operaciones sólo las ejecuta Administrador/Recepción y los estados son explícitos; no hay automatización de fecha y cada cambio queda auditado.
- [El downgrade perdería estados] → No implementar una reversión destructiva; conservar backup y recuperar mediante una migración hacia delante.

## Migration Plan

1. Añadir columna y constraint de estado en los dos motores; rellenar todas las filas existentes como `reservado` en la misma migración.
2. Validar presencia de versión, columna y constraints en las operaciones migradas; conservar la ruta standalone de C-01 sin migrar.
3. Añadir los servicios de transición, ajustar los predicados de exclusión y exponer operaciones protegidas con auditoría atómica.
4. Probar casos de transición, repetición, fallo de auditoría y carreras; ejecutar suite SQLite y PostgreSQL aislado.
5. Si una migración falla, revertir su transacción. Tras usar estados no reservados, no downgrade; restaurar backup o crear una migración correctiva hacia delante.

## Open Questions

Ninguna para esta porción: transiciones, estados ocupantes, permisos e idempotencia quedan definidos por la propuesta aprobada.
