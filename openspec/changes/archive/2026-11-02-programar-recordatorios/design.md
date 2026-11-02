# Design

## Context

Ver `proposal.md` y las capacidades delta. La ficha actual sólo guarda nombre, teléfono y estado; la confirmación y reprogramación ya se serializan con el mutex de agenda y registran auditoría en la transacción. Las migraciones son explícitas, y el manifiesto de backup exige versiones y lista de tablas exactas. La demo usa SQLite por defecto y PostgreSQL aislado en pruebas.

## Goals / Non-Goals

**Goals:**

- Conservar el consentimiento de forma explícita, denegada por defecto y revocable.
- Mantener programación e invalidación del outbox atómicas con los cambios de paciente/turno que las ocasionan.
- Hacer el procesamiento reproducible mediante reloj inyectable y un canal local sin efectos de red.
- Validar persistencia, restricciones, backup/restore e integración de SQLite y PostgreSQL.

**Non-Goals:**

- Contactar pacientes, emitir mensajes reales, usar email, WhatsApp, HTTP, servicios externos, Redis o Docker.
- Guardar una plantilla de mensaje, teléfono duplicado, información clínica, entrega externa o prueba de consentimiento más allá del booleano autorizado.
- Ejecutar procesos residentes, tareas programadas del sistema operativo o migraciones automáticas al iniciar la API.

## Decisions

1. **Una preferencia booleana en la ficha, con false por omisión.** Añadir `acepta_recordatorios` no nulo; migrar pacientes existentes a `false`. La creación puede habilitarlo sólo cuando el personal envía explícitamente `true`; PATCH permite actualizarlo sólo a Administrador o Recepción. Se incluye en la respuesta de ficha que ya consultan esos roles. Esto reutiliza el contrato de gestión de pacientes y evita almacenar un historial de consentimiento no solicitado.

2. **Outbox con clave estable y sin datos de contacto.** Añadir `recordatorios_outbox` con ID opaco, `turno_id`, `turno_version`, tipo `turno_24h`, vencimiento UTC, estado, contador de intentos y marcas de creación/actualización. Una generación positiva e índice único cubren turno+versión+tipo+generación; tras invalidar por retiro de consentimiento, el reconsentimiento crea la siguiente generación sin borrar historial; una fila sólo apunta al turno y nunca duplica teléfono, nombre ni contenido. Los estados distinguen pendiente, procesado simulado, invalidado y fallido.

3. **Plazo elegible calculado desde Mendoza y comparado con un reloj inyectable.** Interpretar el inicio del turno en `America/Argentina/Mendoza`; el vencimiento se fija a 24 horas antes. Crear la fila sólo si el turno está confirmado, tiene consentimiento y el vencimiento aún es futuro; al llegar exactamente a 24 horas o menos no se encola. En producción se usa UTC actual; pruebas entregan un reloj fijo para evitar depender de la fecha del fixture o del host.

4. **Actualizar turno, outbox y auditoría en una sola transacción serializada.** Confirmar un turno elegible crea una fila; cancelarlo invalida sus pendientes; reprogramarlo invalida la versión anterior y evalúa la nueva; retirar consentimiento invalida pendientes, y otorgarlo vuelve a evaluar turnos confirmados vigentes. Reutilizar `BEGIN IMMEDIATE` de SQLite y el mutex PostgreSQL existentes para serializar estas operaciones con el worker y evitar decisiones con estado obsoleto.

5. **Worker local de una pasada obligatoria.** Agregar un módulo CLI que exija `--once` y admita `--limit` de 1 a 100 (predeterminado 100). Una pasada selecciona como máximo esa cantidad de filas vencidas, revalida consentimiento, estado, versión y fechas bajo la transacción, y llama únicamente a un adaptador simulado local. Devuelve sólo conteos por resultado; no imprime nombres, teléfonos, IDs de pacientes ni mensajes. No habrá daemon ni reintento automático en segundo plano.

6. **Reintentos limitados a tres intentos simulados.** Un fallo creado por el adaptador de prueba incrementa el contador. Si quedan intentos, el elemento puede probarse en otra invocación explícita; al tercer fallo queda terminalmente fallido. La inyección de fallo es sólo una dependencia de pruebas, no un parámetro de operación normal. La restricción impide que una avería ficticia repita cambios de turno o produzca la apariencia de una entrega real.

7. **Migraciones y respaldo son aditivos y explícitos.** SQLite pasa de versión 10 a 11, añade la preferencia con default falso y crea la tabla; para v11 previo reconstruye el outbox y asigna generación 1 preservando filas. PostgreSQL agrega revisión Alembic `20261102_0012_appointment_reminders` sobre C-16 y crea generación/default/restricciones. El manifiesto sólo agrega el conteo del outbox y los backups compatibles se crean/restauran con el esquema vigente. Ningún arranque de API migrará automáticamente.

8. **Auditar operaciones con metadatos mínimos.** La actualización de preferencia usa acción permitida de paciente; cambios del outbox registran acciones explícitas, ID opaco de recordatorio, resultado y actor si existe. La auditoría comparte la transacción y falla cerrada. El canal simulado no registra texto ni datos de paciente.

## Risks / Trade-offs

- **Un worker pospuesto puede llegar tarde.** → Revalidar que el turno sigue en el futuro y que el recordatorio sigue vencido; invalidar si el turno ya comenzó o cambió.
- **La preferencia no prueba quién expresó consentimiento ni cuándo.** → Mantener el booleano limitado a la demostración y no describirlo como registro legal ni preparación productiva.
- **El proceso local puede detenerse antes de completar una pasada.** → Cada elemento tiene estado e intentos persistidos y clave única; otra invocación explícita reanuda lo que sigue elegible.
- **La simulación podría confundirse con entrega real.** → Usar estados y salida `simulado`, evitar credenciales y proveedores, y documentar que no se envía comunicación alguna.
- **La nueva tabla amplía el inventario del backup.** → Añadirla a whitelist/recuentos de ambos motores y verificar bundle/restauración con registros sintéticos.

## Migration Plan

1. Ejecutar baseline existente en unittest y frontend antes de cambiar código.
2. Desarrollar y probar la migración SQLite 10→11 y PostgreSQL 0011→0012 con fixtures sintéticos aislados.
3. Migrar explícitamente las bases de demostración; las filas de paciente existentes reciben consentimiento `false` y las filas del outbox empiezan vacías.
4. Actualizar comandos/documentación de migración y backup; restaurar sólo en destinos nuevos compatibles.
5. No ofrecer downgrade que borre el outbox o convierta un consentimiento cambiado en un valor implícito; cualquier reversión requiere respaldo y operación explícita fuera de este change.
