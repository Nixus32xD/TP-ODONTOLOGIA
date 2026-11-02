# Tasks

## 1. Reporte diario de agenda

- [x] 1.1 Escribir primero pruebas RED del rango local semiabierto, límites 31 días, grupos de estado, horarios/excepciones/bloqueos y capacidad cero; verificar que fallen por funcionalidad ausente.
- [x] 1.2 Implementar cálculo de disponibilidad y ocupación por fecha/recurso sin PII; ejecutar pruebas focales y triangular recurso cerrado, excepción vacía y turnos terminales.
- [x] 1.3 Añadir prueba API para acceso Admin/Recepción y rechazo Profesional/Paciente, rangos inválidos y respuesta agregada; documentar ruta y contrato en README backend y verificar ejemplos OpenAPI.

## 2. Reporte diario financiero

- [x] 2.1 Escribir pruebas RED de cargos, cobros, reversos, apertura/saldo diario de cierre por `created_at` local, rango vacío y sumas exactas; verificar que fallen por funcionalidad ausente.
- [x] 2.2 Implementar consulta agregada reutilizando el ledger C-19 y enteros centavos; ejecutar focales SQLite y PostgreSQL y triangular movimiento antes/dentro/después del rango y reversión parcial.
- [x] 2.3 Probar Admin autorizado y Recepción/Profesional/Paciente denegados, verificar ausencia de conceptos, motivos e IDs de pacientes y documentar alcance financiero en README backend.

## 3. Exportación CSV

- [x] 3.1 Escribir pruebas RED de UTF-8, encabezados/orden estables, coherencia con JSON, fórmula, comillas, límites y permisos para ambos reportes.
- [x] 3.2 Implementar CSV a partir del mismo agregado que JSON; ejecutar focales de serialización y probar valores textuales iniciados con `=`, `+`, `-` y `@`.
- [x] 3.3 Verificar headers de descarga y especificar rutas JSON/CSV, nombres de archivos y límites en documentación API; comprobar que no se exportan datos personales ni clínicos.

## 4. Panel de reportes

- [x] 4.1 Escribir pruebas RED del filtro de fechas, tablas/agregados, acceso a CSV y visibilidad por rol; verificar fallos antes de crear el componente.
- [x] 4.2 Implementar vista local usando valores del backend, enlaces de descarga autenticados y mostrar agenda a Admin/Recepción y finanzas sólo a Admin; ejecutar Vitest y verificar cambio de rango y errores.

## 5. Cierre técnico C-20

- [x] 5.1 Ejecutar suite backend, integración PostgreSQL aislada, restore/backups SQLite pertinentes, suite frontend/build y `openspec validate consultar-reportes-operativos --strict`; registrar sólo resultados reales en evidencia C-20.
- [x] 5.2 Actualizar CHANGES.md, README/KB pertinente y BITACORA con alcance, métricas, privacidad, rutas, limitaciones y resultados; verificar enlaces, `git diff --check` y que Discovery preexistente permanezca intacto.

## Workflow follow-up

- Revisar el change y archivar después de aprobación del responsable; sincronizar sus deltas y verificar el resultado archivado.
