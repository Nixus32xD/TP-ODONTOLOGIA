# Tasks

## 1. Vínculo de cuentas y migraciones

- [x] 1.1 Registrar baseline antes de modificar código ejecutando suite completa SQLite y PostgreSQL aislado; capturar resultados y dejar PostgreSQL detenido (SQLite 222 OK, 1 omitido; PG 251/251 OK).
- [x] 1.2 Escribir primero RED para SQLite v7 que añade vínculo profesional único y rol restringido preservando usuarios, sesiones, auditoría y claves foráneas; implementar migración y verificar desde v6.
- [x] 1.3 Escribir primero RED para Alembic 0008 y para el validador que exige la columna `usuarios.profesional_id`; migrar desde 0007, preservar datos y verificar fallo cerrado ante columna ausente.

## 2. Administración y autenticación Profesional

- [x] 2.1 Agregar pruebas RED para alta de cuenta Profesional vinculada sólo a recurso activo, rechazo de ID inexistente/inactivo, rol/vínculo incompatibles y duplicación; implementar validación de creación atómica y metadata-only.
- [x] 2.2 Agregar pruebas RED para asignar/cambiar/retirar vínculo, revocar sesiones ante rol o vínculo cambiado y preservar último Administrador; implementar actualización atómica y serializada (servicio/API; pruebas dirigidas 17/17).
- [x] 2.3 Agregar pruebas RED para login/validación de Profesional con vínculo y claim asociado, rechazo ante vínculo faltante/cambiado y bloqueo de operaciones existentes; implementar identidad fail-closed y verificar regresiones de Admin/Recepción (`test_auth_sesiones` + `test_api_auth`: 13/13; POST /turnos antes aceptaba Profesional y ahora devuelve 403 sin mutación).

## 3. Consulta paginada de turnos

- [x] 3.1 Escribir pruebas RED de servicio para offsets obligatorios, intervalo semiabierto máximo 31 días, filtros, paginación estable, estado/ID inválidos y campos completos de personal; implementar consulta SQL paginada (`test_consulta_turnos`: 3/3; proyección reducida y filtro de vínculo incluidos).
- [x] 3.2 Escribir pruebas RED API de `GET /turnos` para Admin/Recepción y Profesional, rango, filtros incompatibles con el vínculo, 401/403/404/422, proyección mínima Profesional y OpenAPI; implementar ruta de sólo lectura y verificar que ninguna petición escribe o audita (`test_api_auth` + `test_consulta_turnos`: 12/12).

## 4. Opciones de disponibilidad

- [x] 4.1 Escribir pruebas RED para inicios locales cada 15 minutos y descarte por horario/excepción, recursos inactivos, bloqueos, turnos ocupantes y duración/bordes de día; implementar servicio reutilizando las reglas de C-07/C-09 (`test_consulta_disponibilidad`: 5/5; incluye turnos reservado/confirmado, bloqueos, excepción, recurso inactivo y fin exacto 23:45–00:00; la lógica de medianoche ya existía y se añadió cobertura).
- [x] 4.2 Escribir pruebas RED API de `GET /disponibilidad` para roles, vínculo propio, entradas inválidas, no escritura/auditoría y OpenAPI; implementar consulta orientativa y verificar que `POST /turnos` sigue revalidando dentro de su transacción (`test_api_auth`: consulta Admin/Recepción/Profesional, 401/403/404/422 y sin mutaciones; suite existente `test_api_disponibilidad`: 8/8).

## 5. Documentación y regresión

- [x] 5.1 Actualizar README, KB, roadmap, bitácora y evidencia con filtros, privacidad, vínculo de cuentas, migraciones y carácter orientativo; comprobar que no se describan opciones como reservas confirmadas.
- [x] 5.2 Ejecutar suites completas SQLite y PostgreSQL aislado en loopback y puerto distinto de 5432; verificar `pip check`, `openspec validate --all --strict`, `git diff --check` y detención del servidor temporal (SQLite 244 OK + 1 omitido; PostgreSQL 275/275; `pip check` limpio; OpenSpec 10/10; `git diff --check` limpio; 55432 detenido/libre).

## Workflow follow-up

- Revisar y archivar C-08 sólo después de validación independiente.
- Realizar un commit local descriptivo separado; no hacer push/publicación sin autorización explícita.
