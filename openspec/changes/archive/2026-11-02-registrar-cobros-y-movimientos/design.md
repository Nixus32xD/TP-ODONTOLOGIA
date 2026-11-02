# Design

## Context

La API ya protege operaciones por rol y usa sesiones SQLAlchemy transaccionales, `AgendaMutex` para serializar escrituras PostgreSQL y `BEGIN IMMEDIATE` para SQLite. Auditoría se confirma en la misma sesión mediante `registrar_evento_session`. C-18 contiene un patrón de fingerprint/idempotencia, pero su tabla está acoplada a pacientes/turnos. La lista de backups y sus versiones son explícitas.

## Goals / Non-Goals

**Goals:** conservar importes exactos en ambos motores, impedir sobrepago/reversión excesiva ante concurrencia y mantener movimiento, resultado idempotente y auditoría atómicos.

**Non-Goals:** precios de prestaciones, cargos automáticos, checkout, cuentas por cobrar fiscales, facturación/ARCA, proveedores de pagos, conciliación, interés, planes de cuotas o permisos financieros para Profesional/Paciente.

## Decisions

- Guardar ARS como centavos en entero de 64 bits y exponer importes como texto decimal canónico. Validar sintaxis antes de convertir: sin signo, separadores de miles, coma, exponente, `float` o redondeo; máximo ARS 999.999.999,99 por operación. Se elige el entero frente a `float`/`Numeric` para idéntica aritmética exacta SQLite/PostgreSQL.
- Mantener un ledger de cargos, cobros y reversiones append-only con claves foráneas restrictivas. Cada cargo pertenece a una ficha; conserva concepto manual breve y monto original inmutable. Cada cobro refiere un cargo y cada reversión un cobro. Saldo = cargos − cobros + reversiones; monto cobrado no revertido nunca supera cargo y las reversiones nunca superan su cobro. No se añade precio a prestaciones ni se deduce cargo desde turnos/planes.
- Usar una tabla de idempotencia financiera distinta a C-18, limitada por actor, comando y clave, con fingerprint del JSON canónico y respuesta serializada mínima. Autenticar/autorizar primero; buscar replay antes de volver a validar saldos o topes. Fingerprint distinto da 409; el resultado original no vuelve a mutar ni auditar.
- Serializar la comprobación y escritura con el lock local ya existente, guardar movimiento, idempotencia y evento en una transacción. Si el evento no se puede escribir, rollback completo. Las carreras de sobrepago o reversión se resuelven dentro de ese lock.
- Actualizar la auditoría allowlist y sus constraints SQLite/PostgreSQL en conjunto; conservar sólo acción, tipo e ID opaco, actor y resultado. El concepto y el motivo quedan sólo en ledger y nunca en auditoría/logs.
- Añadir migración SQLite hacia schema v13 y Alembic después de `20261102_0013_patient_self_service`; incluir tablas nuevas y versión en los whitelists de backup/restore. Mantener fixtures/datos actuales.
- Mostrar movimientos en pantalla interna separada y calcular saldo en backend. La UI manda los importes como texto y conserva idempotency key al reintentar el mismo comando; no duplica cálculos monetarios en el navegador.

## Risks / Trade-offs

- Una carrera puede exceder saldo si consulta y escritura se separan → lock común y pruebas concurrentes contra SQLite/PostgreSQL.
- El concepto/motivo es texto libre → límites de tamaño, autorización de lectura financiera y exclusión de logs/auditoría.
- Cargos inmutables dificultan corregir errores → alta de reversión/movimiento compensatorio por Administrador; nunca editar o borrar la historia.
- Idempotencia mantiene respuestas/resultados → guardar sólo la referencia y respuesta necesaria, con permisos y backup explícitos; no incluir payload sensible.

## Migration Plan

Aplicar revisiones hacia delante; no alterar revisiones previas. Inicializar tablas vacías, validar constraints y después permitir lecturas/escrituras. Rollback funcional mediante deshabilitar rutas nuevas; las filas no se borran automáticamente. Los backups previos conservan sus versiones/contrato, y los nuevos bundles declaran el esquema v13/Alembic actualizado.
