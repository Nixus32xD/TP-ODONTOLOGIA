# Tasks

## 1. Contrato monetario y persistencia

- [x] 1.1 Agregar pruebas RED para parseo estricto a centavos, límites, overflow, aritmética del saldo y reversión acumulada; ejecutar antes de escribir el servicio monetario.
- [x] 1.2 Implementar conversión decimal-string↔centavos sin float/rounding y pruebas trianguladas de formatos, límites y valores intermedios.
- [x] 1.3 Agregar modelos/constraints/índices append-only de cargo, cobro, reversión e idempotencia; probar invariantes en SQLite y PostgreSQL concurrente.
- [x] 1.4 Crear migración SQLite v13 y Alembic posterior a 0013; probar upgrade desde v12, constraints y compatibilidad histórica.

## 2. Comandos y lectura protegida

- [x] 2.1 Probar API RED de alta cargo, cobro parcial, pago exacto, sobrepago, reversión parcial/total y roles permitidos.
- [x] 2.2 Implementar rutas/servicio transaccional con lock común, eventos metadata-only, idempotencia y rollback; triangular replay, fingerprint distinto y fallos de auditoría.
- [x] 2.3 Probar carreras de cobro y reversión en SQLite/PostgreSQL y validar que ningún saldo/crédito exceda los límites.
- [x] 2.4 Documentar OpenAPI/endpoints y verificar que ningún comando invoque proveedores, fiscalidad o transporte externo.

## 3. Backups e interfaz

- [x] 3.1 Extender manifest/whitelist, bundle y restore; probar recuentos y restauración a base nueva en SQLite/PostgreSQL sin exponer conceptos/motivos en manifest.
- [x] 3.2 Escribir pruebas frontend RED de permisos, entrada decimal, cuenta corriente y reintento idempotente; implementar UI interna con saldo proveniente de API.
- [x] 3.3 Validar backend completo, integraciones focales PostgreSQL aisladas, frontend, build y OpenSpec strict; corregir hallazgos antes de archivar.
- [x] 3.4 Actualizar CHANGES.md, README y BITACORA con reglas monetarias, evidencia, resultados y exclusiones reales.

## Workflow follow-up

- Archivar el change después de validar todas las tareas y sincronizar sus deltas en las specs principales.
