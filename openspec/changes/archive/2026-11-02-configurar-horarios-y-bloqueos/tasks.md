# Tasks

## 1. Persistencia y migraciones

- [x] 1.1 Escribir pruebas RED de esquema SQLite v5 y PostgreSQL 0006 para recursos, FKs y restricciones de tramos; confirmar fallo antes de producción.
- [x] 1.2 Implementar migraciones v5/0006 después de v4/0005, ampliar matriz y DDL de auditoría y conservar datos; pasar pruebas de migración nueva y upgrade desde versiones previas.
- [x] 1.3 Declarar y fijar `tzdata` para disponibilidad IANA portable; probar que carga `America/Argentina/Mendoza` y documentar zona local, versionado y condición inicial de agenda cerrada en backend README.

## 2. Contratos y servicios de disponibilidad

- [x] 2.1 Agregar pruebas RED de validación para días ISO, tramos locales, adyacencia, cruces de día, solapamientos, excepciones y bloques; confirmar rechazo sin escritura.
- [x] 2.2 Implementar modelos y servicios transaccionales para horarios semanales completos, excepciones por fecha y bloqueos con ID opaco; verificar CRUD y paginación por servicio en SQLite.
- [x] 2.3 Documentar los contratos y supuestos de excepción/recurso del bloqueo en backend README; comprobar que coincidan con los modelos y salidas del servicio.

## 3. API y auditoría

- [x] 3.1 Escribir primero pruebas RED de endpoints, validación de cuerpos, autenticación, permisos, respuestas y paginación; implementar `GET/PUT /horarios`, gestión de excepciones y `GET/POST/DELETE /bloqueos` hasta pasar los casos.
- [x] 3.2 Cubrir con pruebas de regresión la matriz de auditoría para horarios/excepciones/bloqueos, metadatos omitidos, atomicidad y rollback al fallar la auditoría en SQLite/PostgreSQL.
- [x] 3.3 Actualizar OpenAPI y README con ejemplos de consultas y mutaciones; verificar `/openapi.json`, `/docs` y errores 401/403/409/422.

## 4. Aplicar disponibilidad a nuevas reservas

- [x] 4.1 Escribir pruebas RED para conversión UTC a `America/Argentina/Mendoza`, ambos recursos, excepción que reemplaza semanal, día cerrado en esquema migrado, compatibilidad standalone C-01, bloqueos y turno que cruza medianoche; implementar la validación hasta pasar triangulación de bordes.
- [x] 4.2 Escribir primero una prueba RED donde una modificación afecte un turno pasado ya registrado; validar todos los turnos del recurso modificado y que tanto ese turno como futuros bloquean cambios incompatibles con HTTP 409, sin evento ni modificación de configuración. Permitir la configuración secuencial del profesional y box tras migrar turnos C-01.
- [x] 4.3 Añadir pruebas de carrera entre reserva y cambio de disponibilidad usando lock común (`BEGIN IMMEDIATE`/`AgendaMutex FOR UPDATE`); verificar que ningún estado confirmado deje una reserva fuera de disponibilidad.

## 5. Validación integrada

- [x] 5.1 Ejecutar suite completa en SQLite y PostgreSQL aislado, migraciones, `pip check`, `openspec validate --all --strict` y `git diff --check`; corregir sólo fallos introducidos por C-07. Resultado: SQLite 199 tests OK (1 integración PostgreSQL omitida), PostgreSQL aislado 222/222 OK, `pip check` limpio, zona IANA cargada, OpenSpec strict 8/8 y diff-check limpio. Ver `docs/evidencia/implementacion-disponibilidad.md`.

## Workflow follow-up

- Archivar C-07 después de completar Apply y la validación integrada, sincronizando las specs y registrando evidencia.
