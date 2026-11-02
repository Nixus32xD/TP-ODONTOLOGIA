# Tasks

## 1. Persistencia y migraciones

- [x] 1.1 Escribir primero pruebas RED para que SQLite v6 y Alembic 0007 agreguen estado restringido, amplíen auditoría e inicialicen turnos como `reservado` sin cambiar IDs ni historial; implementar las migraciones y verificar ambos motores en PostgreSQL aislado.
- [x] 1.2 Probar que el servicio standalone C-01 no exige la columna ni pierde su contrato sobre una agenda no migrada; verificar con la prueba de compatibilidad de `test_turno_lifecycle_migracion` y la suite C-01.
- [x] 1.3 Escribir pruebas RED para que la API falle con 503 antes de mutar cuando falta `turnos.estado` pese a una versión vigente; validar el cierre con SQLite y PostgreSQL.

## 2. Ocupación y dominio

- [x] 2.1 Agregar pruebas RED que demuestren que `reservado`/`confirmado` bloquean y `atendido`/`ausente`/`cancelado` liberan recursos; actualizar los predicados SQLite/PostgreSQL y verificar pruebas de alta y conflictos de ambos adaptadores.
- [x] 2.2 Escribir pruebas RED de transiciones permitidas y prohibidas, incluyendo estados terminales; implementar el servicio de ciclo de vida y verificar el módulo de pruebas del servicio sin mutar turnos ante un 409.
- [x] 2.3 Probar cancelación repetida con 200 y un solo evento, junto con atomicidad cuando auditoría falla; verificar estado e historial tras la transacción.
- [x] 2.4 Probar la carrera cancelación/alta usando los locks existentes de ambos motores; verificar que el resultado serializado no confirma altas incompatibles ni deja mutaciones parciales.
- [x] 2.5 Escribir pruebas RED para permitir cambios de horario, excepción y bloqueo sobre turnos terminales y mantener 409 para turnos ocupantes; actualizar la validación C-07 y verificar SQLite/PostgreSQL.

## 3. API y autorización

- [x] 3.1 Escribir pruebas RED para confirmación, cancelación, atención y ausencia; exponer los endpoints documentados con respuesta 200 y esquema `{id, estado}`, verificando OpenAPI y persistencia después de reabrir.
- [x] 3.2 Probar Administrador/Recepción, sesión ausente, Profesional y turno inexistente; verificar códigos 401/403/404 y que rechazos no modifiquen estado ni generen auditoría.
- [x] 3.3 Probar transiciones inválidas y llamadas repetidas; verificar 409 para transición inválida y 200 idempotente sólo para cancelación repetida.

## 4. Documentación y regresión

- [x] 4.1 Actualizar README, reglas de negocio, modelo de datos, roadmap y bitácora con estados, ocupación, migraciones y límites C-01/C-09; comprobar que ninguna sección describa todos los turnos como ocupantes tras migrar.
- [x] 4.2 Ejecutar toda la suite con SQLite y, por separado, PostgreSQL aislado en loopback y puerto distinto de 5432; comprobar `pip check`, `git diff --check` y `openspec validate --all --strict` antes del cierre y tras corregir disponibilidad y validación fail-closed.

## Workflow follow-up

- Sincronizar las deltas en las specs principales y archivar C-09 después de completar y validar Apply.
- Hacer un commit local descriptivo separado; no hacer push sin autorización explícita.
