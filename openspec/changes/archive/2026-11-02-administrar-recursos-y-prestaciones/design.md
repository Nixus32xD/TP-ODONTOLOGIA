# Design

## Context

La persistencia tiene adaptadores SQLite y PostgreSQL, migraciones versionadas, RBAC y auditoría con una matriz cerrada de acciones. Los turnos de C-01 no guardan prestación y los catálogos profesional/box sólo contienen IDs ficticios. C-05 aporta el patrón de catálogos autenticados, estado activo, paginación, baja lógica y auditoría atómica.

## Goals / Non-Goals

**Goals:** Mantener catálogos ficticios administrables y detectar recursos inactivos en nuevas altas; conservar referencias existentes.

**Non-Goals:** Asociar prestaciones a turnos, calcular intervalos, validar compatibilidades o agendas horarias, agregar cuentas para profesionales o integrar servicios externos.

## Decisions

- Extender Profesional y Box con nombre y activo; crear Prestacion con nombre, duración positiva en minutos y activo. Mantener los IDs seed `profesional-A/B` y `box-A/B`; asignarles nombres ficticios estables durante la migración.
- Generar IDs opacos para nuevas altas. Usar rutas separadas por recurso y una estructura de servicio común sólo si los patrones actuales lo permiten; las reglas de validación y autorización permanecerán explícitas.
- Aplicar límites de lista existentes (50 por defecto, 100 máximo). Administrador y Recepción podrán crear, leer y actualizar datos descriptivos; sólo Administrador podrá cambiar estado activo.
- Bloquear nuevas altas de turnos con profesional o box inactivo dentro de la misma transacción que verifica referencias y conflictos. Mantener el orden de C-01: primero referencias desconocidas, luego estados, luego conflictos.
- Subir esquema SQLite de v3 a v4 y Alembic de 0004 a 0005; incorporar restricciones/acciones de auditoría en servicio, esquema y modelo PostgreSQL. Registrar cada mutación y su evento antes de confirmar, con rollback conjunto.
- No agregar `prestacion_id` a Turno. El catálogo no modifica contratos ni filas históricas de C-01.

## Risks / Trade-offs

- [Los IDs seed antiguos carecen de nombre] → La migración agrega nombres demostrativos estables sin cambiar IDs ni turnos.
- [La lista de acciones de auditoría existe en más de una capa] → Actualizar y probar servicio, DDL SQLite y modelo/revisión PostgreSQL como una sola unidad.
- [Un recurso se desactiva concurrentemente con una reserva] → Leer el estado dentro de la transacción de alta serializada ya usada por agenda en cada adaptador.
- [La prestación no modifica turnos] → La duración queda informativa en C-06; cualquier aplicación futura requiere change separado y revisión explícita del contrato.

## Migration Plan

Aplicar migraciones aditivas preservando los IDs y turnos actuales. Para rollback, conservar esquema aplicado y restaurar copia de la base demo; no eliminar campos ni tablas en downgrade destructivo. Validar en SQLite y PostgreSQL aislado antes de archivar.
