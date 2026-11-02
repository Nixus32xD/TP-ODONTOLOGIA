# Design

## Context

C-09 comparte un lock de agenda entre altas y transiciones, persiste estado en SQLite migrado y PostgreSQL, y confirma mutación y auditoría en una transacción. C-07 ya valida horarios, excepciones, bloqueos y ocupaciones vigentes; C-08 devuelve la proyección de agenda con campos limitados por rol. El standalone de C-01 no tiene estado ni versión y debe continuar funcionando sin migración implícita.

## Goals / Non-Goals

**Goals:**

- Añadir una operación de reprogramación que valide una precondición vigente y confirme asignación, versión y auditoría conjuntamente.
- Reutilizar las reglas de disponibilidad y exclusión ya aprobadas, serializando contra altas, transiciones y otras reprogramaciones.
- Mantener compatibilidad del contrato standalone C-01 y privacidad de auditoría/proyección.

**Non-Goals:**

- Cambiar paciente o duración, asociar prestaciones, cruzar medianoche, crear una segunda cita para el paciente, reprogramar turnos terminales o habilitar al rol Profesional.
- Añadir edición optimista a otros catálogos o modificar permisos generales.

## Decisions

1. **Versión entera positiva por turno.** La migración inicializa turnos existentes en `1`; altas migradas también comienzan en `1`. Transiciones efectivas de estado y reprogramaciones incrementan una vez dentro de la transacción. La cancelación idempotente no incrementa. Se elige versión explícita frente a `If-Match` para mantener el patrón JSON actual y permitir respuesta 409 de dominio estable; la API de turnos operativa expone la versión a Administrador/Recepción.

2. **Solicitud completa, paciente y duración inmutables.** El cuerpo requiere `version`, `inicio`, `fin`, `profesional_id` y `box_id`; campos extra se rechazan. `inicio` y `fin` conservan el contrato de offset explícito y minuto exacto, no cruzan la medianoche local y deben conservar exactamente la duración original. Se mantiene el paciente del turno. C-06 prohíbe actualmente asociar prestación; no existe referencia persistida que validar, por lo que C-10 no la agrega ni consulta ese catálogo.

3. **Validación bajo el lock común.** Antes de escribir, cargar el turno tras adquirir el lock compartido, comparar la versión, exigir estado `reservado`/`confirmado`, comprobar paciente y recursos activos, y validar disponibilidad conjunta, excepciones, bloqueos y conflictos. La consulta de ocupación excluye el ID del turno que se mueve para no colisionar consigo mismo. Se mantiene `[inicio, fin)` y se ignora la identidad del paciente al resolver exclusiones.

4. **Cambiar campos del turno existente, sin cancelar y recrear.** Actualizar intervalo y recursos en la fila original conserva su ID y referencias históricas. Si una validación o escritura falla, el rollback conserva la fila completa. Una carrera con la misma versión se serializa: una operación puede confirmar y las siguientes reciben `version_desactualizada` sin evento.

5. **Auditoría de confirmación solamente.** Añadir `turno.reprogramado` como acción permitida; almacenar sólo actor, recurso `turno`, ID opaco y resultado. Rechazos por permiso, versión, estado, recursos o disponibilidad no generan evento de mutación. El evento y la actualización se confirman en la transacción existente; un error de auditoría revierte también el cambio y el incremento de versión.

6. **Migración incremental y explícita.** SQLite migrado avanza de v7 a v8 y añade `turnos.version` con valor inicial 1; PostgreSQL añade la revisión Alembic siguiente a `20261102_0008_professional_accounts`. La migración amplía las constraints de auditoría sin reemplazar las previas. No se modifica el bootstrap ni la estructura no versionada de C-01; las operaciones del nuevo endpoint requieren el esquema migrado vigente.

## Risks / Trade-offs

- [El lock global reduce concurrencia entre agendas independientes] → Reutilizar el mutex ya aprobado y acotar la transacción a validación y escritura necesarias.
- [Una respuesta vieja de consulta puede intentar reprogramar] → Exigir versión exacta y devolver 409 sin mutación si ya cambió.
- [Agregar la nueva acción puede romper una constraint append-only existente] → Migrar el catálogo de acciones de modo aditivo en ambos motores y probar que las acciones previas sigan insertándose.
- [Un turno C-01 migrado puede tener recursos sin configuración C-07] → Aplicar la política vigente de C-07 y documentar el rechazo si el destino no cumple disponibilidad, sin alterar configuración existente.
- [La duración libre de C-01 puede no coincidir con una prestación del catálogo] → Conservar la duración guardada y no inferir una prestación.

## Migration Plan

1. Aplicar la migración SQLite v8 o la revisión Alembic correspondiente; mantener backup previo y preservar IDs, estado, intervalo y referencias existentes.
2. Desplegar el backend que valida versión de esquema antes de exponer la reprogramación; la API falla cerrada si la migración requerida está incompleta.
3. Actualizar clientes operativos para leer `version` en `GET /turnos` y reenviarla. Ante 409 por versión, recargar la fila antes de un nuevo intento.
4. Rollback: deshabilitar endpoint y volver al backend anterior. No revertir automáticamente la columna ni la constraint; mantener la migración aditiva y sus valores permite rollback de aplicación sin pérdida de turnos. Cualquier downgrade destructivo requiere procedimiento separado y copia verificada.

## Open Questions
