# Evidencia C-19 — Ledger financiero sintético

## Alcance y límites

C-19 registra cargos manuales por paciente, cobros asociados a un cargo y reversiones asociadas a un cobro. No crea cargos automáticamente desde turnos, prestaciones ni planes. Sólo se emplearon fichas, usuarios y movimientos sintéticos. No se conectaron pasarelas, bancos, ARCA ni servicios externos; no se emiten comprobantes fiscales. Esta demostración no está preparada para datos financieros reales ni para uso productivo.

## Contrato implementado

- Los importes se envían como texto decimal, se convierten a centavos enteros y no pasan por `float` ni redondeo. El límite es ARS 999.999.999,99 por movimiento. Se rechazan signo, coma, exponente, agrupadores, más de dos decimales, cero, negativos, números fuera de límite y valores JSON numéricos.
- Cargos, cobros y reversiones son append-only; las referencias se restringen para preservar historial. El saldo se deriva como cargos − cobros + reversiones. Un cobro sobre saldo pendiente y una reversión por encima del importe neto retornan 409.
- Administrador y Recepción consultan cuenta, registran cargo y cobro; sólo Administrador revierte. Profesional recibe 403. El cargo sólo se registra para ficha activa.
- Cada POST requiere `Idempotency-Key`, persistida por actor+operación+clave. Una clave y payload iguales devuelven el resultado original sin duplicar movimiento/evento; payload distinto da 409. El bloqueo serializa el chequeo de saldo y la escritura.
- Ledger, resultado idempotente y auditoría metadata-only comparten transacción. Si falla auditoría se revierten movimiento e idempotencia. Los eventos sólo guardan actor, acción, tipo/recurso opaco y resultado; no llevan paciente, importe, moneda, concepto ni motivo.
- La cuenta devuelve una lista estable de movimientos y saldo en texto decimal. Conceptos y motivos sólo se muestran a personal autorizado y no se serializan en el manifiesto de backup.

## API

| Ruta | Uso |
|---|---|
| `GET /finanzas/pacientes/{paciente_id}` | Consulta cuenta corriente, cargos, cobros, reversiones y saldo derivado. |
| `POST /finanzas/pacientes/{paciente_id}/cargos` | Cargo manual con `monto_ars` textual y `concepto`. |
| `POST /finanzas/cargos/{cargo_id}/cobros` | Cobro parcial o total con `monto_ars` textual. |
| `POST /finanzas/cobros/{cobro_id}/reversiones` | Reversión de Administrador con importe textual y `motivo` obligatorio. |

Las rutas están incluidas en OpenAPI. No hay endpoints ni dependencias de proveedor de pago o fiscalidad.

## Persistencia y backup

- SQLite migra de esquema v12 a v13 de forma aditiva y transaccional, conservando las filas existentes y ampliando las acciones auditadas permitidas.
- PostgreSQL Alembic agrega `20261102_0014_financial_ledger` después de `20261102_0013_patient_self_service`; la migración se ejecutó en schema temporal de PostgreSQL 18 aislado.
- El manifiesto y el restore incluyen `cargos_financieros`, `cobros_financieros`, `reversiones_cobros` e `idempotencia_financiera`; sólo publican conteos agregados. El bundle/restore SQLite conserva valores sintéticos de ledger y el bundle/restore PostgreSQL real conserva cargos, cobros y reversiones en base destino nueva.
- Integración PostgreSQL: localhost `127.0.0.1:55432`, base de prueba `odontologia_c16_test`, schemas temporales `c19_*`; se usó `pg_dump`/`pg_restore` de PostgreSQL 18 desde `C:\Program Files\PostgreSQL\18\bin`. No se usó 5432 ni Docker.

## Evidencia TDD

| Comportamiento | RED observado | GREEN/triangulación |
|---|---|---|
| Parser monetario | `tests.test_finanzas` falló por falta del módulo `odontologia.finanzas`. | 6 pruebas con subcasos cubren conversiones, formatos inválidos/límite, saldo/reversión, agregados grandes y rechazos no enteros. |
| Modelos y migración | `tests.test_finanzas_persistencia` falló al importar modelos inexistentes; upgrade previa no creaba ledger v13. | Constraints/índices/append-only se verificaron en SQLite y PostgreSQL; upgrade SQLite v12→v13 conserva evento previo. |
| API | `tests.test_api_finanzas` falló con 404 antes de agregar rutas. | Cargos, cobros exactos/parciales, reversión, roles, formatos, sobrepago, replay/conflicto y OpenAPI cubiertos. |
| Auditoría/transacción | La prueba de rollback mostró 500 ante excepción genérica de auditoría. | Boundary traduce el fallo a 503; movimientos e idempotencia quedan ausentes; el replay no agrega evento duplicado. |
| Concurrencia | Carreras de dos cobros/reversiones se agregaron como casos específicos. | SQLite API y PostgreSQL real permiten una operación y rechazan la otra con 409, sin exceder saldos. |
| UI | Vitest no pudo resolver el módulo `CuentaCorriente` antes de implementar la pantalla. | Frontend verifica cargo exacto, clave estable en retry ambiguo y reversión visible sólo para Administrador. |

### Revisión independiente posterior al primer cierre

La revisión detectó una carrera de selección entre cuentas, pérdida de clave al remontar la pantalla y un saldo agregado mayor a `BIGINT`. Antes de archivar, se agregaron RED/GREEN para los tres casos: los controles quedan bloqueados y se limpian IDs al cambiar de paciente, respuestas fuera de orden se descartan, la clave se conserva en `localStorage` bajo una huella SHA-256 del comando hasta confirmar el POST y refrescar la cuenta, y el formateador admite saldos agregados mayores al máximo individual. El hash evita guardar el concepto/motivo o el cuerpo del comando en almacenamiento local.

## Baseline

Antes de implementar C-19: backend relevante 76 tests OK y 1 skip; frontend 11 archivos/66 tests OK; build TypeScript/Vite OK. No se detectó fallo previo en esas pruebas focales.

## Validación final

| Área | Comando | Resultado |
|---|---|---|
| Backend completo | `ODONTOLOGIA_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/odontologia_c16_test; DATABASE_URL=$ODONTOLOGIA_TEST_DATABASE_URL; python -m unittest discover -s tests -q` desde `backend/` con Python del `.venv` y `C:\Program Files\PostgreSQL\18\bin` en `PATH` | **563 tests OK, 3 skips**, 141.865 s, después de los fixes de revisión. |
| Integración financiera PostgreSQL | `python -m unittest tests.test_finanzas_postgresql_integracion -v` | **4 tests OK**: Alembic 0013→0014, constraints y append-only, movimientos/auditoría, concurrencia de sobrepago/reversión y bundle/restore real. |
| Backup SQLite | `python -m unittest tests.test_backup_restore_sqlite tests.test_backup_manifest tests.test_backup_sqlite -q` | **25 tests OK, 1 skip**; el restore conserva cargo, cobro, reversión e idempotencia sintéticos; manifest sólo lista conteos. |
| Frontend | `npm test -- --run` | **12 archivos / 72 tests OK** después de agregar los tres casos de revisión. |
| Build | `npm run build` | TypeScript y Vite OK. |
| Cuenta Corriente y build | `npm test -- --run src/pages/CuentaCorriente.test.tsx`; `npm run build` | **6/6 tests OK**, TypeScript y Vite OK. |
| OpenSpec | `openspec validate --all --strict` | **20 specs passed, 0 failed** después de archivar C-19. |

El change se archivó localmente en `openspec/changes/archive/2026-11-02-registrar-cobros-y-movimientos/` tras completar sus 12/12 tareas y sincronizar sus deltas. No se hizo commit ni push. `docs/discovery/informe-discovery.md` se dejó fuera del alcance de C-19.
