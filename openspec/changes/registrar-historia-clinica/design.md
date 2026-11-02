# Design

## Context

El backend persiste `Paciente`, `Turno`, `Usuario` y `EventoAuditoria` en SQLAlchemy. SQLite versiona su esquema de autenticación con una migración transaccional explícita; PostgreSQL usa Alembic. El catálogo de auditoría tiene restricciones de acciones y recursos y es append-only. El backup local valida una lista cerrada de tablas y versiones. La ficha de paciente no contiene clínica; la agenda limita a Profesional a sus propios turnos y los estados `atendido`, `ausente` y `cancelado` son terminales. Ver [proposal.md](proposal.md) y las deltas de `clinical-history`, `personal-auth`, `audit-trail` y `agenda-backup-restore`.

## Goals / Non-Goals

**Goals:**

- Aislar las notas clínicas y autorizar el acceso con la identidad Profesional vigente y su vínculo actual.
- Vincular cada nota a paciente, profesional y turno atendido coincidentes; preservar originales y correcciones.
- Hacer verificables las lecturas y escrituras mediante auditoría metadata-only con política fail-closed.
- Extender migraciones SQLite/Alembic y el backup/restore local manteniendo las filas existentes.

**Non-Goals:**

- No crear historia clínica longitudinal compartida entre profesionales ni acceso clínico de Administración o Recepción.
- No incorporar diagnóstico codificado, recetas, odontograma, plan de tratamiento, adjuntos, imágenes, exportación ni borrado de contenido.
- No conectar servicios externos ni habilitar uso productivo, datos reales, Docker o Redis.

## Decisions

1. **Persistencia clínica separada.** Agregar una tabla `evoluciones_clinicas` con ID opaco, `paciente_id`, `profesional_id`, `turno_id`, nota narrativa, fecha de creación UTC y una referencia opcional `corrige_a_id` a la evolución corregida. Las claves foráneas usarán `RESTRICT`; la tabla de pacientes y sus respuestas no cambian. La capa de dominio verificará que la combinación de paciente/profesional coincida con el turno y que su estado sea `atendido`. Se descarta agregar columnas clínicas a `pacientes` porque mezclaría contactos con información clínica y expondría la nota por endpoints existentes.

2. **Acceso por autor-profesional y atención finalizada.** Los endpoints protegidos serán `GET /pacientes/{paciente_id}/historia`, `POST /pacientes/{paciente_id}/evoluciones` y `POST /evoluciones/{evolucion_id}/correcciones`. Cada solicitud derivará `profesional_id` exclusivamente de la sesión vigente. Las consultas devolverán sólo evoluciones de turnos atendidos por ese profesional para el paciente; no se aceptará un profesional enviado por el cliente. Corrección requerirá que el registro pertenezca al mismo profesional y a una atención que siga siendo la referencia. Administración y Recepción no accederán a estos endpoints. Se descarta compartir por paciente todo el historial porque excede el acceso necesario para la atención propia.

3. **Nota libre acotada e inmutable.** La nota será texto UTF-8 no vacío, recortado en extremos y limitado a 5000 caracteres. La corrección será una nueva fila referida a la evolución que corrige; la original no se actualiza ni elimina. La aplicación no ofrecerá update/delete y la persistencia impedirá cambios o borrado ordinarios mediante las protecciones append-only correspondientes. Se descartan campos estructurados, archivos y notas sin límite para reducir superficie y mantener C-16 separado.

4. **Auditoría en el mismo almacenamiento y fail-closed.** Se ampliará el catálogo existente para acciones de consulta concedida/denegada, alta y corrección, usando tipos de recurso breves compatibles con sus longitudes. El evento contendrá actor, acción, resultado e ID opaco interno cuando sea conocido; nunca nota, nombre, teléfono, credenciales, cuerpo ni texto enviado por el cliente. Una lectura añadirá y confirmará su evento antes de devolver la nota; si falla, devolverá error de disponibilidad sin contenido. Una escritura y su evento se confirmarán en una sola transacción. Las denegaciones autenticadas también serán auditadas; un identificador de recurso desconocido o no validado se registrará como nulo.

5. **Vínculos referenciales y correcciones.** Se mantendrán claves foráneas a paciente, profesional, turno y evolución origen con borrado restringido. El servicio validará el estado `atendido` y coincidencia de los tres IDs dentro de la misma transacción que guarda la evolución. Cada corrección referenciará la evolución que corrige, pertenecerá al mismo paciente, profesional y turno, y conservará el registro referenciado. Se descarta cascada de borrado para no destruir trazabilidad.

6. **Migración y recuperación hacia delante.** SQLite avanzará de la versión de esquema 8 a 9 en una transacción: añadirá la tabla clínica y actualizará las restricciones del catálogo de auditoría preservando todas las filas y triggers append-only. PostgreSQL añadirá una revisión Alembic posterior a `20261102_0009_turn_rescheduling`, con cambios equivalentes y downgrade destructivo bloqueado. El camino de migración C-01 SQLite a PostgreSQL no importará clínica desde una fuente que no la contiene. Se actualizarán versiones, tabla permitida y recuentos del backup/restore para ambos motores. No se reescribirán migraciones archivadas ni se sobrescribirá una base al restaurar.

7. **Datos de demostración únicamente.** Fixtures, ejemplos, escenarios y demostración usarán nombres y notas sintéticas. La documentación indicará que el almacenamiento local y sus copias contienen información sensible y que no está validado para uso clínico real. Se descarta inferir que la prueba técnica o el cifrado del backup autorizan datos productivos.

## Risks / Trade-offs

- **[El rol profesional puede cambiar entre solicitudes]** → Resolver profesional desde la identidad vigente en cada acceso y validar cuenta activa/vínculo actual antes de consultar o escribir.
- **[El turno puede no corresponder a los IDs suministrados]** → Validar turno atendido, paciente y profesional dentro de la transacción; usar claves foráneas restrictivas y devolver errores genéricos.
- **[La auditoría de lectura agrega escritura y puede reducir disponibilidad]** → Confirmar el evento antes de responder y fallar cerrado sin revelar notas si el almacenamiento no está disponible.
- **[Ampliar restricciones de auditoría puede bloquear migración por catálogo divergente]** → Verificar revisión/esquema conocido, migrar en transacción, copiar eventos previos y abortar sin mutaciones ante incompatibilidad.
- **[Una copia incluye notas sensibles aunque el manifiesto no las exponga]** → Mantener el flujo de backup local existente, indicar sensibilidad, preservar permisos actuales y no transmitir ni purgar copias automáticamente.
- **[Texto narrativo puede contener identificadores que el sistema no detecte]** → No alegar anonimización automática; usar sólo registros sintéticos de demostración y no solicitar ni importar datos reales.

## Migration Plan

1. Incorporar las nuevas tablas y restricciones en modelos y revisiones de esquema sin alterar las filas, rutas ni contratos anteriores.
2. Avanzar el esquema SQLite versionado y Alembic de forma explícita y transaccional, verificando preservación de auditoría y claves foráneas.
3. Actualizar la lista de tablas/recuentos/versiones del backup y comprobar creación y restauración en destino nuevo.
4. Activar la API después de validar esquema soportado; si una versión falta o no es reconocida, rechazar las operaciones clínicas y requerir migración explícita.
5. No ofrecer downgrade que elimine evoluciones. Corregir defectos mediante una migración hacia delante; conservar antes el backup local existente según C-12.
