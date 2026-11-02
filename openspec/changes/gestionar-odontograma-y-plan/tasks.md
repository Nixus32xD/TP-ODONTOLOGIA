# Tasks

## 1. Revalidación de nomenclatura y base de pruebas

- [ ] 1.1 Antes de implementar, comprobar en las fuentes oficiales el estado vigente de ISO 3950 y los códigos HL7 FDI citados; registrar edición, URL y códigos contrastados en evidencia C-16, y actualizar los artifacts si la referencia cambió antes de seguir.
- [ ] 1.2 Ejecutar y registrar baseline de backend (`python -m unittest discover -s tests -v`, desde `backend/`) y frontend (`npm test`, desde `frontend/`); confirmar que las bases de integración PostgreSQL serán de test locales y aisladas, sin Docker ni Redis.

## 2. Persistencia y migraciones aditivas

- [ ] 2.1 Escribir primero pruebas RED para tablas, claves foráneas, restricciones y conservación de versiones/etapas; implementar modelos SQLAlchemy de odontograma y planes y lograr GREEN en SQLite con `python -m unittest discover -s tests -p "test_*odontograma*" -v` y `python -m unittest discover -s tests -p "test_*planes*" -v`.
- [ ] 2.2 Escribir prueba RED de upgrade SQLite v9→v10 sobre una copia sintética C-15; agregar migración aditiva preservando filas y lograr GREEN con `python -m unittest discover -s tests -p "test_*migracion*" -v` desde `backend/`.
- [ ] 2.3 Escribir pruebas RED de upgrade PostgreSQL desde Alembic 0010 y restricciones/FK/append-only; implementar revisión 0011 y verificar en PostgreSQL aislado de test (localhost, puerto 55432, base `*_test`) con `python -m unittest discover -s tests -p "test_*odontograma*postgresql*" -v` y `alembic upgrade head`.
- [ ] 2.4 Documentar las versiones SQLite/PostgreSQL, prerequisitos y migración explícita en `backend/README.md`; verificar que los comandos documentados aplican al menos el upgrade SQLite de una base sintética y que el arranque de FastAPI no migra.

## 3. Odontograma versionado

- [ ] 3.1 Escribir pruebas RED de códigos FDI/ISO, dentición primaria/permanente, superficies individuales y compatibilidad anterior/posterior; implementar validación pura, observación opcional <=500 y errores 422, y lograr GREEN más casos límite con `python -m unittest discover -s tests -p "test_*odontograma*" -v`.
- [ ] 3.2 Escribir pruebas RED de snapshots completos, secuencia por paciente/profesional, consulta de vigente/historial y corrección append-only; implementar servicio transaccional que conserve versiones previas y lograr GREEN con el mismo patrón unittest.
- [ ] 3.3 Agregar rutas FastAPI de consulta y nueva versión, con respuestas y errores documentados en OpenAPI; cubrir escenario válido, entradas inválidas, turno no atendido y aislamiento entre profesionales con `python -m unittest discover -s tests -p "test_api_odontograma*.py" -v`.
- [ ] 3.4 Documentar el flujo API y ejemplos exclusivamente sintéticos en `backend/README.md`; verificar que OpenAPI publica los esquemas sin ejemplos de información clínica real.

## 4. Planes manuales

- [ ] 4.1 Escribir pruebas RED de alta con etapas ordenadas y prestaciones activas, rechazo de prestaciones ausentes/inactivas, inmutabilidad de etapas y conservación de referencias a prestaciones luego desactivadas; implementar servicio y lograr GREEN con `python -m unittest discover -s tests -p "test_*planes*" -v`.
- [ ] 4.2 Escribir pruebas RED de transiciones `propuesto → en_curso → completado/cancelado`, cancelación desde estados no terminales y rechazo 409 de transiciones prohibidas; implementar cambios de estado y verificar que no creen turnos ni precios con el mismo comando unittest.
- [ ] 4.3 Agregar rutas de consulta/creación/cambio de estado y pruebas de contrato `python -m unittest discover -s tests -p "test_api_planes*.py" -v`; verificar respuestas públicas y errores sin datos de turnos, precios, consentimiento ni diagnósticos.
- [ ] 4.4 Documentar rutas, etapas, estados y ejemplos sintéticos en `backend/README.md`; verificar consistencia con `resource-catalogs` y que no se amplía el contrato de `Prestacion` ni `Turno`.

## 5. Autorización y auditoría clínica

- [ ] 5.1 Escribir primero pruebas RED de rol, profesional activo/vigente, vínculo actual y turno propio atendido para cada endpoint; aplicar autorización dentro de la transacción y lograr GREEN con `python -m unittest discover -s tests -p "test_api_*clinica*.py" -v`.
- [ ] 5.2 Escribir pruebas RED de lectura/escritura metadata-only, atomicidad con auditoría, rollback ante fallo y respuestas 403 sin contenido para Admin/Recepción; extender eventos y restricciones de auditoría y verificar con `python -m unittest discover -s tests -p "test_*audit*" -v` y las pruebas clínicas.
- [ ] 5.3 Revisar cuerpos, respuestas, logs, eventos y ejemplos OpenAPI para confirmar que no contienen observaciones, nombres, etapas detalladas ni otros datos clínicos; registrar resultados en `backend/evidence/C-16-verificacion.md` mediante inspección y suite focal.

## 6. Backup y restore SQLite/PostgreSQL

- [ ] 6.1 Escribir pruebas RED de conteo/whitelist y bundle SQLite con todas las tablas nuevas; actualizar versión de esquema, manifiesto y conteo sin valores clínicos, y verificar con `python -m unittest discover -s tests -p "test_backup*" -v` desde `backend/`.
- [ ] 6.2 Escribir pruebas RED de referencias huérfanas, hash/recuentos incompatibles y restore a destino nuevo; ampliar verificación/restauración para rechazar antes de publicar, conservar fuente y validar historial completo con `python -m unittest discover -s tests -p "test_backup_restore*" -v`.
- [ ] 6.3 Verificar backup y restore PostgreSQL con evolución, odontograma versionado, plan y recuentos en un cluster local temporal y aislado (localhost:55432, base `*_test`); ejecutar `python -m unittest discover -s tests -p "test_backup*postgresql*" -v` y documentar límites si PG no está disponible.
- [ ] 6.4 Actualizar `backend/README.md` y `backend/evidence/C-16-verificacion.md` con versión soportada, comandos reales y resultados separados para SQLite y PG; comprobar que el manifiesto no filtra contenido y el restore nunca usa la base activa.

## 7. Vista clínica mínima

- [ ] 7.1 Escribir pruebas frontend RED para mostrar secciones clínicas sólo a Profesionales con una atención atendida seleccionada, cargar versiones/historial, y ocultar acciones a Administrador/Recepción; implementar componentes en React y verificar con `npm test -- --run` desde `frontend/`.
- [ ] 7.2 Cubrir formularios de códigos/superficies y creación/cambio de plan, mostrar errores de validación sin sugerir conductas clínicas, y verificar compilación con `npm run build`.
- [ ] 7.3 Documentar una verificación manual de UI con datos sintéticos en `backend/evidence/C-16-verificacion.md`; comprobar visualmente que la interfaz etiqueta el estado/versionado y no hace llamadas clínicas para Admin/Recepción.

## 8. Integración final

- [ ] 8.1 Ejecutar la suite backend completa (`python -m unittest discover -s tests -v` desde `backend/`), integración PostgreSQL aislada y suite/build frontend (`npm test -- --run` y `npm run build` desde `frontend/`); corregir regresiones sin cambiar contratos archivados.
- [ ] 8.2 Completar `backend/evidence/C-16-verificacion.md` con comandos, resultados realmente observados, estado de referencias oficiales y límites de demostración sintética; verificar `openspec validate gestionar-odontograma-y-plan --strict` antes de solicitar revisión.
