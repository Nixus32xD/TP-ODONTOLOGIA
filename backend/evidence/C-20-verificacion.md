# Evidencia C-20 — Reportes operativos

## Alcance

C-20 agrega consultas agregadas de agenda y ledger financiero, exportación CSV y un panel para personal autorizado. Agenda acepta rangos locales semiabiertos de hasta 31 días en `America/Argentina/Mendoza`; Administrador y Recepción pueden consultarla. Finanzas sólo está disponible para Administrador y agrupa cargos, cobros y reversiones por fecha local de creación, conservando importes enteros del ledger C-19. JSON y CSV usan los mismos agregados. Las respuestas y descargas no exponen datos personales, conceptos, motivos ni contenido clínico.

La capacidad se deriva de horarios, excepciones y bloqueos; se separan estados y minutos ocupados de turnos, y se informan ocupaciones de profesional y box con capacidad real. Un recurso sin capacidad devuelve métricas de ocupación nulas. El CSV es UTF-8 con encabezados estables y neutraliza valores de texto que puedan iniciar fórmulas.

## Evidencia TDD

| Área | RED observado | GREEN y triangulación |
|---|---|---|
| Agregados de agenda | Las pruebas focales no pudieron importar `odontologia.reportes`. | Rangos vacíos/límite, varios estados, unión de disponibilidad, excepciones, bloqueos, recursos sin capacidad, ocupación y conversión horaria local cubiertos. |
| API y permisos | Las pruebas de agenda y finanzas recibieron 404 antes de implementar las rutas. | Admin/Recepción autorizados para agenda; finanzas sólo Admin; rangos inválidos, OpenAPI, privacidad y CSV/JSON coherentes verificados. |
| Finanzas | La prueba focal no pudo importar el agregador financiero. | Movimientos previos/dentro/posteriores, reversión parcial, suma exacta en centavos, día vacío y saldo de apertura/cierre cubiertos en SQLite. |
| CSV | Las pruebas no pudieron importar los serializadores previstos. | Encabezados y orden estables, UTF-8/CRLF, comillas, valores `=`, `+`, `-`, `@`, privacidad y equivalencia con JSON verificados. |
| Interfaz | Vitest no pudo resolver `./Reportes` antes de crear el panel. | Rol, filtros, agregados y descarga autenticada de CSV cubiertos; el panel no muestra finanzas a Recepción. |
| Zona horaria | La prueba de borde detectó que una conversión por offset estándar daba 13:00 UTC para 09:00 local el 18-10-1992, durante un cambio histórico de DST. | La conversión ahora usa la zona IANA para cada fecha y el caso histórico queda cubierto. |
| Snapshot del ledger | `test_movimientos_financieros_se_leen_en_un_solo_snapshot_sql` falló porque detectó 3 SELECT independientes y esperaba uno. | Cargos, cobros y reversiones se combinan en una consulta `UNION ALL`; la prueba verifica una sola sentencia. La triangulación conserva fechas locales, saldo de apertura/cierre y reversos parciales. |

## Validación ejecutada

| Área | Comando | Resultado |
|---|---|---|
| Backend completo (final después de la corrección del snapshot financiero) | `.venv/Scripts/python.exe -m unittest discover -s tests -v` desde `backend/` | **518 tests OK, 13 omitidos**, 115.405 s. |
| Backend completo (antes de esta corrección del snapshot financiero) | `.venv/Scripts/python.exe -m unittest discover -s tests -v` desde `backend/` | **517 tests OK, 13 omitidos**, 120.371 s. El snapshot OpenAPI inicial falló al no enumerar las cuatro rutas C-20; se actualizaron sus expectativas y el test focal luego pasó. |
| Reportes/API/CSV después de la corrección | `.venv/Scripts/python.exe -m unittest tests.test_reportes_operativos tests.test_api_reportes tests.test_reportes_csv -v` desde `backend/` | **14/14 OK**, 4.194 s. Incluye la regresión de consulta única y casos de apertura/cierre, reverso parcial y fecha local. |
| Prueba RED snapshot | `.venv/Scripts/python.exe -m unittest tests.test_reportes_operativos.ReportesAgendaTests.test_movimientos_financieros_se_leen_en_un_solo_snapshot_sql -v` antes del cambio | Falló como se esperaba: **3 consultas detectadas, 1 esperada**. |
| OpenAPI focal | `.venv/Scripts/python.exe -m unittest tests.test_api.ApiTests.test_openapi_y_docs -v` | **1/1 OK**. |
| PostgreSQL financiero C-20 | `.venv/Scripts/python.exe -m unittest tests.test_finanzas_postgresql_integracion -v` | **No ejecutado: 0 tests, 1 omitido** porque falta `ODONTOLOGIA_TEST_DATABASE_URL`. No se usó el puerto local disponible porque no se pudo verificar que fuera una base aislada. La integración PostgreSQL permanece pendiente. |
| Backup/restore SQLite | `.venv/Scripts/python.exe -m unittest tests.test_backup_sqlite tests.test_backup_restore_sqlite -v` | **16 tests OK, 1 omitido**; el host Windows no permite crear el symlink requerido por un caso. |
| Frontend | `npm test -- --run` desde `frontend/` | **13 archivos, 74 tests OK**. |
| Build | `npm run build` desde `frontend/` | TypeScript y Vite OK. |
| OpenSpec | `openspec validate --all --strict` | **21/21 items OK**. |
| Diff | `git diff --check` | Exit 0; sólo avisos de conversión LF→CRLF en checkout Windows. |

## Estado y limitaciones

El panel y los agregados funcionan con SQLite y las pruebas unitarias; el ledger financiero ahora se consulta con una sola sentencia para mantener el mismo snapshot de statement en PostgreSQL `READ COMMITTED`. La compilación/ejecución de integración PostgreSQL C-20 sigue pendiente porque falta `ODONTOLOGIA_TEST_DATABASE_URL`. Por ello las tareas OpenSpec 2.2 y 5.1 siguen pendientes, y C-20 no debe archivarse todavía. La tarea documental 5.2 está completa. No se hizo push ni archive. El cambio previo en `docs/discovery/informe-discovery.md` se preservó y queda fuera de este trabajo.
