# Design

## Context

Ver propuesta y deltas. La reserva de SQLite ya abre la agenda existente y ejecuta `BEGIN IMMEDIATE` antes de verificar recursos, solapamientos e insertar. PostgreSQL serializa esa operación con `SELECT ... FOR UPDATE` sobre `AgendaMutex(id=1)`. Los turnos se almacenan como minutos UTC (`inicio_minuto`/`fin_minuto`); C-06 deja SQLite en versión 4 y Alembic en `20261102_0005_resource_catalogs`.

## Goals / Non-Goals

**Goals:** Administrar disponibilidad local y bloquear nuevas reservas fuera de ella; evitar carreras entre altas y cambios de configuración; rechazar modificaciones incompatibles con cualquier turno ya registrado.

**Non-Goals:** Guardar feriados por proveedor, administrar zonas por consultorio, manejar estados/cancelaciones de turnos, sumar una UI, notificar pacientes o importar calendarios.

## Decisions

- **Horario local recurrente:** fijar `America/Argentina/Mendoza` como única zona de C-07. Guardar día ISO 1–7 y horas locales como minutos desde medianoche; los tramos no cruzan el día, admiten múltiples intervalos y no se solapan. `24:00` sólo puede ser límite final. Ausencia de configuración semanal significa cerrado; la migración no inventa horarios para los recursos existentes.
- **Conversiones temporales:** mantener turnos como instantes UTC enteros por minuto, convertirlos con la zona IANA antes de calcular fecha, día y hora locales, y evaluar excepciones por fecha local. `ZoneInfo` de la biblioteca estándar maneja la conversión temporal; los datos de zona se suministran mediante el sistema y el paquete fallback. Los extremos del turno ya exigen offset explícito en C-01; los bloqueos reciben instantes con offset y se comparan en UTC. No inferir offsets desde horas de agenda.
- **Base IANA portable:** declarar `tzdata` como dependencia runtime fijada tanto en `requirements.txt` como en el lock del proyecto. `zoneinfo` recurre a este paquete cuando el sistema operativo no tiene una base IANA utilizable; comprobar en pruebas que se puede cargar `America/Argentina/Mendoza`.
- **Supuesto para excepciones (explícito para revisión):** una excepción reemplaza toda la recurrencia de un profesional o box en una fecha local; cero tramos significa cerrado. Borrar la excepción vuelve a aplicar el horario semanal. Una excepción se almacena como cabecera con ID opaco y tramos hijos para soportar cero o varias franjas.
- **Supuesto para bloqueos (explícito para revisión):** cada bloqueo aplica exactamente a un profesional o a un box, nunca a ambos ni a toda la clínica. Se almacena como intervalo UTC con ID UUID; puede atravesar fechas porque no es un tramo semanal.
- **Persistencia y referencias:** usar tablas normalizadas para configuración semanal, tramos, excepciones y bloqueos. En tablas por recurso emplear dos FKs anulables (`profesional_id` o `box_id`) y un `CHECK` que exige exactamente una; así la DB conserva integridad referencial. Excepciones tienen como máximo una por recurso y fecha local. Validar límites y solapamientos también en el dominio.
- **Serialización común:** cada alta de turno y cada mutación de horario, excepción o bloqueo SHALL adquirir el mismo lock que la reserva antes de leer disponibilidad/turnos. SQLite usa `BEGIN IMMEDIATE`; PostgreSQL bloquea `AgendaMutex(id=1)` con `FOR UPDATE`. Mantener la transacción hasta completar verificación, cambios y auditoría; una carrera queda serializada y no puede dejar un turno fuera de disponibilidad.
- **Cambios compatibles con turnos:** evaluar la configuración candidata contra todas las filas de turnos que referencian el recurso modificado, sin comparar con el reloj ni filtrar por fecha. C-01 no tiene estado ni cancelación y toda fila persistida sigue ocupando recursos; por eso incluso un turno pasado incompatibiliza el cambio de ese recurso. Al configurar un sistema migrado con turnos C-01 heredados, se puede abrir primero el profesional y luego el box: cada cambio comprueba el recurso objetivo y no trata como una invalidación nueva que el otro todavía no tenga horario. Esto permite configurar progresivamente; las altas nuevas siguen cerradas hasta que ambos recursos tengan disponibilidad vigente. El horario semanal sólo afecta fechas sin excepción; un cambio de excepción sólo afecta su fecha; un bloqueo sólo afecta turnos que se solapen con ese recurso. Si cualquier turno del recurso objetivo pierde disponibilidad, devolver 409 antes de mutar o auditar. Borrar bloqueos amplía disponibilidad; borrar excepción sí requiere comprobar la recurrencia que vuelve a aplicar.
- **API:** rutas autenticadas con `personal_operativo` para ambos roles. `GET/PUT /horarios/{tipo_recurso}/{recurso_id}` reemplaza el horario semanal completo; `GET/PUT/DELETE /horarios/{tipo_recurso}/{recurso_id}/excepciones/{fecha}` consulta, reemplaza o remueve la excepción; `GET/POST /bloqueos` lista paginado y crea; `DELETE /bloqueos/{id}` elimina. Los listados de bloqueos usan límite 50/100 y offset no negativo.
- **Auditoría:** actualizar la matriz central, checks SQLite y restricciones PostgreSQL con `horario`, `excepcion` y `bloqueo`. Acciones previstas: `horario.actualizado`, `excepcion.creada/actualizada/eliminada`, `bloqueo.creado/eliminado`. Guardar actor, acción, tipo e ID opaco; omitir fechas, tramos e intervalos. Fijar el evento en la misma transacción. Los 409 por turnos afectados no dejan evento de mutación.
- **Migraciones y compatibilidad C-01:** subir `auth_schema_version` SQLite de 4 a 5 bajo la migración explícita y en la misma transacción; añadir la revisión Alembic `20261102_0006_agenda_availability` sobre `20261102_0005_resource_catalogs`. Actualizar `REVISION_ESQUEMA_ACTUAL`, modelos, DDL de auditoría y guardas de esquema. La API valida versión y presencia de las cuatro tablas C-07 y responde 503 antes de operar si falta una. En el servicio standalone de C-01, una base sin `auth_schema_version` conserva el contrato anterior; la disponibilidad cerrada por defecto rige al migrar a SQLite v5, sin crear horarios automáticamente. No realizar downgrade destructivo.

## Risks / Trade-offs

- [La regla IANA puede cambiar por actualización de tzdata] → Usar el identificador IANA confirmado y cubrir conversión local/UTC con pruebas; no fijar un offset numérico permanente.
- [El lock global limita concurrencia de escrituras] → Mantener el mismo patrón probado que ya protege C-01 y priorizar coherencia para el tamaño del demo.
- [Los turnos pasados pueden impedir cambios de agenda] → Validar todas las filas, como exige la ausencia de estados en C-01; si una propuesta resulta incompatible, la persona operativa debe elegir una configuración que conserve disponible ese turno y el historial.
- [Las excepciones y los bloqueos pueden restringir disponibilidad] → Probar rechazo 409 y rollback de estado/evento en ambos motores.
- [Una actualización de migración puede invalidar checks existentes de auditoría] → Ampliar acción/recurso/combinación en el mismo cambio y probar lectura y escritura SQLite/PostgreSQL.

## Migration Plan

1. Aplicar SQLite v5 de forma explícita con transacción y preservar tablas/turnos/auditoría v4.
2. Aplicar Alembic 0006 tras 0005 y ampliar la revisión vigente del selector PostgreSQL.
3. Validar esquema y migración de bases nuevas y existentes; no crear horario por defecto. Tras migrar, el administrador o recepción configura horarios antes de dar nuevas altas.
4. Mantener downgrade bloqueado, como en revisiones de datos previas; para recuperación del demo usar una copia previa de la DB.
