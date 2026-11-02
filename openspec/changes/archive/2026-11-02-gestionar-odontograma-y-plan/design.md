# Design

## Context

See `proposal.md` for motivation and `specs/` for externally visible contracts. La API FastAPI usa SQLAlchemy; el dominio ya separa `EvolucionClinica` de `Paciente`, valida el turno atendido y registra auditoría en la transacción. SQLite es la persistencia predeterminada (C-15: esquema v9) y PostgreSQL usa Alembic (revisión `20261102_0010_clinical_history`). El backup mantiene listas cerradas de tablas y revisiones en su manifiesto. La UI React/Vite sólo tiene agenda, catálogos y disponibilidad; la cuenta Profesional ya ve una agenda reducida.

## Goals / Non-Goals

**Goals:**
- Introducir dos capacidades clínicas separadas del relato de evolución y de la ficha de contacto.
- Preservar versiones históricas, aplicar autorización en backend, y hacer que cada operación clínica y su auditoría sean atómicas.
- Extender migraciones y respaldo/restauración sin perder referencias; permitir una vista clínica local mínima para el Profesional.

**Non-Goals:**
- Diagnósticos, clasificación de caries/lesiones, recomendaciones, prescripciones, consentimiento, precios, pagos, turnos automáticos, archivos adjuntos o conexión con sistemas externos.
- Cambiar el contrato de `Prestacion`, asociar prestaciones a `Turno` o modificar los contratos archivados de C-01 a C-15.
- Hacer despliegue productivo o añadir Docker, Redis, nuevos servicios o dependencias de proveedores.

## Decisions

1. **Persistencia independiente y aditiva.** Agregar `OdontogramaVersion` y `HallazgoOdontograma`, más `PlanTratamiento` y `EtapaPlanTratamiento`, con tablas `versiones_odontograma`, `hallazgos_odontograma`, `planes_tratamiento` y `etapas_plan_tratamiento`. Referenciar pacientes, profesionales y prestaciones con claves foráneas restrictivas; no agregar columnas clínicas a `pacientes` ni reutilizar `EvolucionClinica` para campos estructurados. SQLite subirá de v9 a v10 y PostgreSQL tendrá una revisión Alembic nueva encadenada a `20261102_0010_clinical_history`. Se conserva el patrón de migraciones explícitas: el arranque no migra.

2. **Odontograma como snapshot completo por paciente y profesional.** Cada escritura guarda una nueva versión completa del conjunto de hallazgos, numerada en el ámbito paciente/profesional, junto con autor y fecha del servidor. Una versión previa nunca se actualiza ni elimina; el snapshot más alto es el vigente para ese ámbito. Se serializan escrituras con el bloqueo/transacción ya usado por C-15 (`BEGIN IMMEDIATE` en SQLite y el mutex de agenda en PostgreSQL) para evitar versiones duplicadas. Se rechazará el guardado si la auditoría o cualquier referencia no puede confirmarse.

3. **Nomenclatura acotada a códigos explícitos.** Aceptar piezas permanentes de cuadrantes 1–4 y posiciones 1–8, y piezas primarias de cuadrantes 5–8 y posiciones 1–5, como códigos FDI de dos dígitos. Cada superficie es individual: `M`, `D`, `O`, `I`, `B`, `V` o `L`; permitir varias superficies como lista sin duplicados. Para la compatibilidad técnica propuesta, `I` y `V` se aceptan en piezas anteriores (posiciones 1–3), y `O` y `B` en posteriores (posiciones 4–8); `M`, `D` y `L` se admiten en ambas. Validar antes de persistir con errores 422. La página oficial de [ISO 3950](https://www.iso.org/standard/68292.html) muestra ISO 3950:2016 publicada y vigente, revisada/confirmada en 2022, pero también en etapa `90.92` “to be revised” con una nueva edición en desarrollo. La página canónica [HL7 FDI surface](https://terminology.hl7.org/en/CodeSystem-FDI-surface.html) contiene los siete códigos individuales seleccionados junto con códigos compuestos, y describe su conjunto como una selección. Esta selección no es exhaustiva ni las definiciones citadas dictan reglas clínicas; al empezar Apply se debe confirmar que las fuentes siguen vigentes y revisar el contrato si cambian.

4. **Planes manuales de contenido fijo.** Crear un plan con etapas ordenadas y referencias a prestaciones activas existentes. Las etapas quedan inmutables después del alta; correcciones de contenido se expresan en un plan separado. Sólo se actualiza el estado operativo según el grafo de la spec: `propuesto → en_curso → completado` o `cancelado`, permitiendo cancelar desde `propuesto` o `en_curso`; `completado` y `cancelado` son terminales. Prestaciones desactivadas después del alta siguen referenciadas históricamente. No guardar precio, diagnóstico ni vínculo con turno. Cada transición de estado se audita.

5. **Autorización igual o más estrecha que C-15.** Revalidar cuenta Profesional activa, vínculo actual y profesional activo dentro de la transacción. Las consultas y versiones sólo exponen el stream del paciente y profesional autenticado y requieren turno `atendido` propio. Agregar `GET /profesional/atenciones-atendidas?limit&offset` como listado paginado mínimo para selección clínica: la identidad vinculada se toma de la sesión; el servidor devuelve sólo atenciones `atendido` de ese Profesional con `turno_id`, `paciente_id`, `paciente_nombre`, `inicio` y `fin`, sin teléfono ni filtro de profesional controlado por el cliente. La lectura se audita metadata-only y falla cerrada. Administrador y Recepción reciben 403 antes de consultar; sin resultados responde una página vacía.

6. **Auditoría metadata-only fail-closed.** Reusar `registrar_evento_session` y el patrón transaccional de C-15, extendiendo tipos/acciones permitidos con eventos de lectura de atenciones atendidas, lectura clínica, creación de versión, creación de plan y cambio de estado. Registrar actor, acción, tipo/referencia técnica, resultado y fecha; nunca notas, observaciones, nombres ni lista de etapas. Si falla auditoría, una escritura revierte; una lectura no devuelve contenido como éxito. No enviar datos sensibles a logs, request IDs, métricas ni OpenAPI examples.

7. **Backup completo con whitelist versionada.** Agregar las cuatro tablas al cómputo de manifiesto y validadores de SQLite y PostgreSQL, con nueva revisión de esquema. Incluir tablas/refs bajo el snapshot consistente actual, comprobar claves foráneas y recuentos antes de publicar destino, sin incluir valores clínicos en manifiesto. Mantener el procedimiento de backup local y restauración a destino nuevo; el alcance prueba bundles creados con el esquema C-16 vigente, sin añadir compatibilidad de lectura para revisiones anteriores que hoy no estén soportadas.

8. **UI clínica mínima sólo para Profesional.** Extender el área autenticada existente con una selección paginada de atenciones atendidas propias y secciones de odontograma/planes para la atención seleccionada. El listado devuelve sólo los cinco campos mínimos descritos y la API clínica vuelve a verificar autorización por solicitud. Componentes separados consumen la API ya autorizada; no cargan atenciones ni hacen llamadas clínicas desde Admin/Recepción. Mostrar datos sintéticos y los estados/versiones con etiquetas explícitas, sin sugerir decisiones médicas.

9. **Pruebas locales y PostgreSQL real aislado.** Cubrir reglas puras de códigos, API y persistencia SQLite con `unittest`; ejecutar regresión backend y frontend. La integración PostgreSQL requiere una base temporal local aislada con puerto y URL de test propios, nunca una base de desarrollo compartida; no usar Docker ni Redis. Evidencia distingue pruebas SQLite, integración PG real y la verificación manual de UI.

## Risks / Trade-offs

- **[La nomenclatura oficial puede cambiar mientras ISO 3950 está en etapa de revisión para reemplazo] →** revalidar página/edición al comenzar Apply y corregir el spec si afecta códigos antes de escribir implementación.
- **[Una interpretación de superficies podría presentarse erróneamente como criterio clínico] →** conservar la regla como validación técnica de códigos y compatibilidad básica, citar HL7, y no derivar diagnóstico, hallazgo clínico ni conducta.
- **[El snapshot completo y su historial aumentan almacenamiento] →** la demostración sólo usa datos sintéticos y no añade purga automática; el backup conserva todos los registros.
- **[Cambiar whitelist/revisión puede rechazar bundles antiguos] →** documentar la revisión soportada y probar validación previa; no mutar origen ni destino existente ante incompatibilidad.
- **[Errores de autorización o auditoría pueden exponer contenido] →** verificar autorización dentro de la operación transaccional, fallar cerrada y añadir pruebas negativas por rol, vínculo, turno y fallo de auditoría.
- **[Una restauración local puede confundirse con recuperación productiva] →** describirla como prueba técnica de datos sintéticos, sin declarar preparación productiva.

## Migration Plan

1. Antes de implementar, comprobar el estado vigente de ISO 3950 y la nomenclatura FDI de superficies; si la revisión altera los códigos, actualizar los artifacts y validar de nuevo antes de codificar.
2. Añadir migraciones aditivas de SQLite v9→v10 y Alembic desde `20261102_0010_clinical_history`; no reescribir datos clínicos existentes ni iniciar migraciones automáticamente.
3. Implementar modelos, servicios, autorización, auditoría y API en transacciones; luego ampliar backup/restore y probar en bases sintéticas nuevas y restauradas.
4. Agregar la UI para Profesional y verificar que los otros roles no ejecuten consultas clínicas.
5. Si una migración nueva falla en una base de prueba, descartar únicamente esa base de prueba y corregir la migración. No borrar ni reconstruir automáticamente una base de usuario. No se planifica downgrade destructivo: la vuelta atrás consiste en detener la versión nueva y restaurar un backup compatible a un destino nuevo, previa validación.

## Open Questions

- Ninguna decisión de contrato queda diferida. La comprobación de ISO y HL7 al inicio de Apply es una validación obligatoria de las referencias citadas, no autorización para ampliar el alcance clínico.
