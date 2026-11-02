# Design

## Context

La agenda ya ofrece persistencia SQLite y PostgreSQL con migraciones explícitas. Autenticación y administración de cuentas tienen su propio esquema y transacciones; C-04 debe insertar auditoría dentro de esas mismas transacciones, sin abrir conexiones paralelas. Ver `proposal.md` y los contratos de `audit-trail` y `alta-turnos`.

## Goals / Non-Goals

**Goals:**
- Conservar la atomicidad en ambos backends y no confirmar mutaciones sin su evento.
- Consultar eventos con un DTO allowlist y paginación acotada.
- Mantener migraciones explícitas y compatibilidad con instalaciones C-01–C-03.

**Non-Goals:**
- No guardar snapshots, cuerpos, valores anteriores/nuevos ni datos identificatorios clínicos.
- No crear retención configurable, purga, exportación ni edición de eventos.
- No auditar lecturas comunes ni rechazos de autorización fuera de login.

## Decisions

1. **Una tabla `eventos_auditoria` en cada backend preparado.** Campos: ID entero ascendente, instante UTC, actor opcional, acción de catálogo, tipo de recurso de catálogo, ID de recurso opcional y resultado (`confirmado` o `rechazado`). Los identificadores de sesión no se guardan. Las FK hacia cuentas usarán `ON DELETE RESTRICT`; la app no ofrece borrado de cuentas ni eventos. Índice compuesto por instante e ID para lectura estable. Se elige esquema común en SQLite/PostgreSQL para que la API conserve el mismo contrato.
2. **Inserción mediante la transacción existente.** Los servicios recibirán la conexión SQLite o sesión SQLAlchemy ya abierta y agregarán el evento antes del commit actual. Bootstrap, login válido, logout y operaciones de cuentas se ajustan para que mutación/evento compartan commit. El rechazo de login usa una transacción independiente de sólo auditoría y recién devuelve 401 después del commit; falla de audit se traduce a 503 genérico. No se incluyen errores de credenciales ni identificador intentado.
3. **Un módulo de auditoría con operaciones de escritura acotadas y lectura.** Los escritores llaman a un helper que sólo acepta acciones, recursos y resultados predefinidos, y no recibe diccionarios arbitrarios ni payload. La lectura mapea explícitamente a un modelo de salida seguro. No se agrega `UPDATE`/`DELETE` de eventos en la capa de aplicación.
4. **Migración explícita y additive.** SQLite agrega la tabla e índice mediante migración versionada idempotente; PostgreSQL incorpora DDL a la preparación explícita vigente y verifica que no exista deriva. Ni importar módulos ni crear la app crea tablas. Las cuentas ya existentes se preservan y el historial empieza con eventos posteriores a la migración.
5. **Paginación por `limit` y `offset`.** Default 50, máximo 100, offset desde cero. Se rechazan límites fuera de rango en validación API y se ordena por `created_at DESC, id DESC` para evitar inestabilidad entre eventos con misma fecha.

## Risks / Trade-offs

- [El registro append-only en SQLite no evita que un operador con acceso directo al archivo lo altere] → La garantía es de la API de demo; limitar permisos del archivo y no ofrecer endpoints de mutación.
- [Una falla del almacenamiento de auditoría bloquea la operación relacionada] → Comportamiento fail-closed aprobado; respuesta genérica y rollback de la unidad completa.
- [Historial sin purga puede crecer] → Demo local con volumen bajo; no borrar automáticamente. Definir retención requerirá un cambio futuro explícito.
- [Cambiar firmas de servicios puede afectar llamadas existentes] → Mantener wrappers compatibles donde sea posible y ejecutar la suite completa SQLite y PostgreSQL.

## Migration Plan

1. Aplicar migración SQLite y DDL explícito PostgreSQL sin alterar datos existentes.
2. Desplegar código que escriba los eventos junto con las mutaciones.
3. Validar API, permisos, orden/paginación y rollback en los dos backends.
4. Si la migración falla, detener la puesta en marcha y conservar el esquema anterior; no borrar ni reconstruir la base. No existe rollback destructivo automático.

## Open Questions
