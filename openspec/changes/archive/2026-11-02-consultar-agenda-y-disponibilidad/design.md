# Design

## Context

La agenda ya tiene C-07 (horarios, excepciones y bloqueos) y C-09 (estados ocupantes); su alta serializada vuelve a validar disponibilidad. `usuarios` sólo admite Administrador/Recepción y no vincula cuentas a `profesionales`. SQLite autenticado está en v6 y PostgreSQL en Alembic 0007.

## Goals / Non-Goals

**Goals:** Añadir consultas de sólo lectura, limitar por rol el conjunto de turnos y campos visibles, calcular opciones reutilizando las reglas C-07/C-09 y asociar cada cuenta Profesional con un único recurso profesional.

**Non-Goals:** Crear reservas desde sugerencias, escribir o cambiar estados de turnos, permitir a Profesional consultar otros recursos, enviar datos de contacto del paciente, habilitar clínica real, reprogramar o modificar C-01 standalone.

## Decisions

- **Vínculo dentro de la cuenta.** Añadir `usuarios.profesional_id` nullable, FK restrictiva y única. Un CHECK relaciona rol Profesional con un vínculo y exige que Administrador/Recepción no tengan uno. Una tabla puente añade una segunda fuente de verdad sin ventaja para este vínculo 1:1. Los cambios de rol/asignación y revocación de sesiones se confirman juntos.
- **Migración incremental.** SQLite pasa a v7 y reconstruye `usuarios` en una transacción para reemplazar su CHECK de rol, conservando IDs, hashes, estados y sesiones. Se deshabilitan temporalmente las claves foráneas sólo durante el DDL, se copia el contenido y se ejecuta `foreign_key_check` antes del commit; se restauran después. PostgreSQL 0008 agrega columna, FK/UNIQUE y CHECK en una sola revisión transaccional. El validador de esquema requiere versión vigente y columna de vínculo en ambos motores.
- **Autorización de agenda propia.** Las cuentas Profesional autentican sólo si están activas y conservan un vínculo válido. La identidad validada incluye el `profesional_id`; el JWT de Profesional incluye ese mismo ID y la validación compara ambos para fallar cerrado ante vínculo faltante o cambiado. Reasignar/cambiar rol también revoca sesiones. Las dependencias que autorizan mutaciones siguen limitadas a Administrador/Recepción.
- **Consulta temporal en intervalos semiabiertos.** `GET /turnos` convierte `desde`/`hasta` con offset a minutos UTC, valida `[desde,hasta)` y un máximo de 31 días, y ordena por `(inicio_minuto,id)` antes de aplicar limit/offset. Filtrar con el mismo índice de turnos evita leer agenda completa para cada página. No se calcula `total` porque no forma parte del contrato.
- **Proyección de datos separada por rol.** La consulta comparte filtros SQL; la serialización de personal incluye campos operativos permitidos y excluye teléfono. La respuesta Profesional se construye por separado y sólo contiene inicio, fin y nombre del paciente. No se incluyen IDs de otros recursos ni nombres de boxes/profesionales en esa proyección.
- **Opciones como cálculo de lectura.** Un servicio de consulta selecciona una sola fecha en `America/Argentina/Mendoza`, carga una vez los tramos vigentes de profesional/box, bloqueos y turnos ocupantes, y prueba candidatos locales cada 15 minutos. Reutiliza `turno_cabe_en_tramos`, considera intervalos `[inicio,fin)`, transforma a UTC para cruzar bloqueos/turnos y descarta candidatos que terminan fuera del día. No adquiere lock de escritura ni registra auditoría. El alta conserva la transacción y sus revalidaciones como autoridad final.
- **Rangos y referencias validados antes de consultar.** Rechazar offsets ausentes, rangos invertidos o mayores a 31 días, paginación inválida y filtros desconocidos con errores claros. Para Profesional, omitir el filtro de profesional aplica el vínculo; un ID explícito distinto devuelve 403. Administración/Recepción puede combinar filtros.

## Risks / Trade-offs

- [Reconstruir `usuarios` en SQLite puede romper referencias desde sesiones/auditoría] → Migrar en transacción, conservar cada fila, comprobar `PRAGMA foreign_key_check` y probar sesiones/eventos existentes en v6→v7.
- [Un defecto de autorización podría exponer agendas de terceros] → No aceptar un ID delegado para Profesional, comparar vínculo DB/JWT, probar ataques de filtro con 403 y mantener las rutas de escritura con permisos actuales.
- [Las sugerencias pueden quedar desactualizadas inmediatamente] → Documentarlas como orientativas y probar que el alta sigue revalidando disponibilidad y conflictos dentro de su serialización existente.
- [Consultas con rangos grandes podrían escanear muchas filas] → Límite estricto de 31 días, paginación acotada, filtros indexados y orden estable.
- [Un profesional inactivo puede conservar turnos históricos] → Permitir consulta de su agenda histórica, pero no producir sugerencias con recursos inactivos; desactivar el recurso no borra asociación ni historial.

## Migration Plan

1. Escribir pruebas RED para ambas migraciones desde v6/0007, preservación de sesiones y auditoría, constraints de rol/vínculo y fail-closed de columna/versiones.
2. Aplicar SQLite v7 y PostgreSQL 0008 con asociación única; validar perfiles existentes sin reescribir roles ni sesiones.
3. Escribir pruebas RED de autenticación de Profesional, cambios de vínculo, revocación y acceso mínimo; implementar la identidad vinculada y las respuestas de cuenta.
4. Probar consultas paginadas/filtros, proyección segura por rol y opciones de disponibilidad en ambos motores; agregar rutas GET y documentación OpenAPI.
5. Ejecutar suite completa SQLite y PostgreSQL aislado, `pip check`, `openspec validate --all --strict` y `git diff --check`.

No hay downgrade seguro luego de crear vínculos Professional: restaurar backup o corregir hacia delante, sin descartar asociaciones ni sesiones en uso.
