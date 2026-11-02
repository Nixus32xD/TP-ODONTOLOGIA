# Evidencia de implementación del alta de turnos

Fecha de inicio: 2026-10-15. El usuario autorizó continuar con Apply sobre la propuesta publicada en `5093070`; esto no se presenta como evidencia de que haya leído personalmente todo el spec. Sólo datos ficticios y archivos temporales propios.

Runtime observado: Windows, Python 3.12.14, SQLite 3.53.1. Las ejecuciones usan el Python del runtime disponible; comando reproducible con Python 3.12+: `python -m unittest discover -s tests -v`.

## TDD Cycle Evidence

No había tests ni código de producto antes del primer RED; no se presenta una suite vacía como baseline funcional. Los conteos incluyen métodos unittest; los subcasos se indican aparte. Una comprobación de comportamiento existente puede quedar verde al añadirse: se documentará como triangulación/verificación, sin fabricar un RED.

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1 | tests/test_agenda.py (BootstrapTests) | integración | Sin implementación previa | ModuleNotFoundError: odontologia | 3/3 | Catálogos y agenda vacía; turno preservado al repetir; archivo ajeno intacto | No necesario; suite verde |
| 1.2 | tests/test_agenda.py (AperturaTests) | integración | 3/3 | 2 ImportError: crear_turno ausente | 5/5 | Agenda ausente y padre inexistente; no creación implícita | No necesario; suite verde |
| 2.1 | tests/test_agenda.py (AltaValidaTests) | integración | 5/5 | 2 AttributeError: retorno None | 7/7 | Dos turnos distintos, UTC y datos persistidos al reabrir conexión | No necesario; suite verde |
| 2.2 | tests/test_agenda.py (IdentificadoresTests) | integración | 7/7 | 28 subcasos fallidos: código de error incorrecto | 10/10 | Tres campos, tipos, espacios, 64/65, referencias y prioridad | No necesario; suite verde |
| 2.3 | tests/test_agenda.py (FechasTests) | integración | 10/10 | Fecha sin offset aceptada; después offset de segundos redondeado | 18/18 | Tipos, precisión, UTC, límites, intervalo y minutos anteriores a epoch | No necesario; suite verde |
| 2.4 | tests/test_agenda.py (TimeoutTests) | integración | 18/18 | Timeout cero producía almacenamiento_error | 21/21 | Positivos 0.1/5/1 y ocho inválidos, antes de abrir archivo | No necesario; suite verde |
| 3.1 | tests/test_agenda.py (ProfesionalTests) | integración | 21/21 | Se aceptaba superposición parcial | 24/24 | Igualdad, ambas contenciones y offsets equivalentes; BEGIN IMMEDIATE antes de consulta | No necesario; suite verde |
| 3.2 | tests/test_agenda.py (BoxTests) | integración | 24/24 | Se aceptaba conflicto de box | 27/27 | Igualdad/contenciones y prioridad con dos conflictos; refactor de consultas duplicadas conservó 27/27 | Consultas unificadas; 27/27 |
| 3.3 | tests/test_agenda.py (BordesTests) | integración | 27/27 | No hubo RED: comportamiento ya correcto | 30/30 | Adyacencia anterior/posterior, recursos distintos, paciente simultáneo y cruce de día; verificación sin código adicional | No necesario; suite verde |
| 4.1 | tests/test_agenda.py (RollbackTests) | integración | 30/30 | No hubo RED: cierre SQLite ya revertía | 32/32 | Trigger AFTER INSERT RAISE(FAIL), FK real, reapertura y recuperación; refactor a ROLLBACK explícito conservó 32/32 | ROLLBACK explícito; 32/32 |
| 4.2 | tests/test_agenda.py (ContencionTests) | integración | 32/32 | SQLITE_BUSY se devolvía como almacenamiento_error | 34/34 | Dos timeouts, datos previos preservados y recuperación tras liberar lock | No necesario; suite verde |
| 4.3 | tests/test_concurrencia.py (test_concurrencia.py) | multiproceso | 34/34 | No hubo RED: serialización ya implementada en 3.1 | 37/37 | 3 carreras por profesional, 3 por box y 1 de recursos distintos; 14 procesos spawn con PID diferente; sin sleeps de coordinación | No necesario; suite verde |
| 4.4 | tests/test_agenda.py (ReintentosYErroresTests) | integración | 37/37 | No hubo RED: contrato ya cubierto por conflictos/apertura | 39/39 | Repetición con offsets equivalentes, archivo ausente/no SQLite conservado; mensajes públicos claros sin rutas internas | Mensajes públicos; 39/39 |
| 5.1 | tests/test_demo.py (test_demo.py) | proceso CLI | 39/39 | Módulo odontologia.demo inexistente | 41/41 | Demo repetible, dos altas/dos conflictos, temporales eliminados y rutas con espacios | JSON ASCII; 41/41 |
| 5.2 | tests/ + trazabilidad (Suite completa + trazabilidad) | integración | 41/41 | Refuerzos reales de fecha/ruta inválida registrados abajo; sin RED artificial de documentación | 43/43 | 29 escenarios trazados, demo, código/KB/instrucciones coherentes; límites declarados | No necesario; suite verde |

Interfaz de alta: `crear_turno(ruta_db, *, paciente_id, profesional_id, box_id, inicio, fin, timeout_segundos=5.0) -> Turno`. El resultado inmutable incluye ID entero positivo, referencias e instantes UTC; no expone una API de red.

## Preparación de agenda

`inicializar_agenda(ruta_db)` reserva exclusivamente un archivo nuevo; no crea directorios ni reemplaza agendas existentes. Los catálogos contienen paciente-A/B, profesional-A/B y box-A/B. No representan pacientes reales. Las pruebas usan TemporaryDirectory del sistema; los archivos DB no se versionan.

## Límites de esta evidencia

Este registro crecerá con ejecuciones reales. No acredita despliegue clínico, integración externa, revisión personal de fuentes ni Archive. Hasta completar el resto de tareas no se declara terminado el comportamiento.


## Trazabilidad de escenarios

Cada escenario del spec se vincula a un test ejecutable; los subcasos cubren variantes de entrada.

| Escenario | Test |
| --- | --- |
| Agenda nueva | `test_agenda.BootstrapTests.test_agenda_nueva_tiene_seis_recursos_sin_turnos` |
| Preparación repetida | `test_agenda.BootstrapTests.test_preparacion_repetida_conserva_turno` |
| Alta sin agenda | `test_agenda.AperturaTests.test_alta_sin_agenda_no_crea_archivo` |
| Identificadores conocidos | `test_agenda.AltaValidaTests.test_alta_retorna_datos_y_persiste_al_reabrir` |
| Referencia desconocida | `test_agenda.IdentificadoresTests.test_referencias_desconocidas_y_longitud_limite` |
| Entrada de identificador inválida | `test_agenda.IdentificadoresTests.test_forma_invalida_en_cada_campo` |
| Offsets equivalentes | `test_agenda.ProfesionalTests.test_offset_equivalente_conflicta` |
| Intervalo vacío o invertido | `test_agenda.FechasTests.test_intervalo_vacio_e_invertido` |
| Fecha sin offset o precisión inválida | `test_agenda.FechasTests.test_tipos_y_precision_rechazados_en_ambos_limites` |
| Alta en agenda vacía | `test_agenda.AltaValidaTests.test_alta_retorna_datos_y_persiste_al_reabrir` |
| Persistencia después de cerrar conexión | `test_agenda.AltaValidaTests.test_dos_altas_distintas_se_conservan` |
| Superposición parcial por profesional | `test_agenda.ProfesionalTests.test_solapamiento_parcial_profesional_otro_box` |
| Contención por profesional | `test_agenda.ProfesionalTests.test_igualdad_y_contencion_profesional` |
| Superposición por box con profesional distinto | `test_agenda.BoxTests.test_solapamiento_box_otro_profesional` |
| Contención por box | `test_agenda.BoxTests.test_igualdad_y_contenciones_box` |
| Ambos recursos en conflicto | `test_agenda.BoxTests.test_prioridad_profesional_con_conflictos_independientes` |
| Adyacencia posterior | `test_agenda.BordesTests.test_adyacencia_anterior_y_posterior` |
| Adyacencia anterior | `test_agenda.BordesTests.test_adyacencia_anterior_y_posterior` |
| Superposición de recursos diferentes | `test_agenda.BordesTests.test_recursos_distintos_y_paciente_simultaneo_permitido` |
| Cruce de medianoche | `test_agenda.BordesTests.test_cruce_de_dia_y_duracion_libre` |
| Paciente simultáneo con recursos distintos | `test_agenda.BordesTests.test_recursos_distintos_y_paciente_simultaneo_permitido` |
| Dos procesos compiten por profesional | `test_concurrencia.ConcurrenciaTests.test_dos_procesos_profesional` |
| Dos procesos compiten por box | `test_concurrencia.ConcurrenciaTests.test_dos_procesos_box` |
| Contención que agota la espera | `test_agenda.ContencionTests.test_timeout_de_escritor_y_recuperacion` |
| Fallo controlado antes de confirmar | `test_agenda.RollbackTests.test_fallo_despues_de_insertar_revierte_y_libera_agenda` |
| Archivo no accesible | `test_agenda.ReintentosYErroresTests.test_archivo_inaccesible_y_no_sqlite_no_se_reemplazan` |
| Repetición después de éxito | `test_agenda.ReintentosYErroresTests.test_repeticion_no_es_idempotente` |
| Timeout positivo | `test_agenda.TimeoutTests.test_timeout_positivo` |
| Timeout inválido | `test_agenda.TimeoutTests.test_timeout_invalido_no_accede_a_agenda` |


## Observaciones TDD y límites

Los RED registrados son fallos reales de nuevas pruebas antes de implementar su comportamiento. En 3.3, 4.1, 4.3 y 4.4 las nuevas pruebas pasaron sobre lógica ya implementada; se registran como triangulación/verificación. No se degradó el código para producir fallos artificiales. Los primeros grupos de bootstrap/IDs se escribieron con casos parametrizados juntos antes de GREEN, no con un ciclo separado por cada subcaso; queda explícita esa diferencia respecto de TDD estrictamente granular.

Refuerzo posterior de 2.3: con 41 tests verdes se añadió una zona horaria inválida que provocó dos TypeError internos (inicio/fin). Se corrigió su traducción a entrada_invalida y la suite quedó 42/42. También se comprobó que la normalización UTC no redondee offsets con segundos y que rechace valores fuera del rango representable.

Concurrencia: siete carreras por ejecución de suite, con 14 procesos hijos, coordinación por Event/Queue, tres repeticiones por recurso compartido y una con recursos independientes. Sólo mismo archivo local mediante el módulo. Contención y rollback tienen pruebas separadas. No hay promesa de reconciliación tras caída de máquina/IO extremo ni idempotencia.

43 tests incluyen demo ejecutada como proceso independiente, limpieza de TEMP propio y repetición. No hubo datos reales, mocks de DB completa, servicios externos ni instalación de dependencias del producto. La demo produce JSON ASCII escapado para funcionar también al redirigir stdout en Windows.

Refuerzo posterior de 4.4: una ruta con NUL producía ValueError interno. Tras RED real con 42 tests previos verdes, se tradujo a almacenamiento_error tanto al abrir como al inicializar; suite 43/43. No se cambió el contrato de rutas inválidas.


## Verificación final

43/43 tests verdes y demo con dos altas/dos conflictos y agenda temporal eliminada. OpenSpec validate --strict válido, sin incidencias. Comprobación documental: 264 enlaces, pareja AGENTS/CLAUDE idéntica, stack igual a KB, 21 reglas compactas preservadas y PDF/matriz/renderer intactos. Sin DB ni secretos versionados. No hay servidor, por lo que no corresponde health check HTTP. Las pruebas se ejecutaron en Windows/Python 3.12.14/SQLite 3.53.1; no se extrapola a versiones, discos de red o equipos no comprobados.

## Corrección FastAPI dentro del mismo C-01

El usuario corrigió expresamente el stack a FastAPI y autorizó commit/push tras validar. El módulo SQLite conserva sus reglas y transacciones; se añade sólo un adaptador HTTP, sin otro change ni módulos clínicos. PDF y fuentes personales no se modifican.

### TDD Cycle Evidence — ampliación HTTP

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.1 | tests/test_api.py | HTTP+SQLite real | 43/43 previos | Ejecutado: ModuleNotFoundError odontologia.api | Alta201 persistida pasó | Adyacencia, recursos distintos y entradas inválidas | Descripciones de modelos, suite53/53 |
| 6.2 | tests/test_api.py | HTTP+SQLite real | AltaHTTP verde | No RED separado: pruebas añadidas ya verdes | Conflictos409,404,422,500,503 pasaron | Ambos recursos, lock real y recuperación, agenda ausente/corrupta | Sin refactor funcional |
| 6.3 | tests/test_api.py | ASGI+smoke servidor | 53/53 | No RED separado: health/OpenAPI ya implementados al añadir tests | Health/docs/OpenAPI y smoke pasaron | Health sinDB; rutas/esquemas; JSON inválido | Documentación sincronizada |

No se afirma cumplimiento100% del ciclo estricto: los manejadores y health se implementaron con el adaptador tras el primer RED, antes de añadir sus tests específicos. Se conserva la evidencia real sin introducir fallos artificiales. El test de persistencia detectó además una conexión SQLite de verificación abierta: se corrigió el test usando contextlib.closing, sin modificar el dominio.

### Trazabilidad de los seis escenarios HTTP añadidos

| Scenario | Test method (ApiTests) |
| --- | --- |
| Alta HTTP persistida | test_alta_201_y_persistencia; test_adyacencia_y_recursos_independientes |
| JSON inválido o coerción no permitida | test_entrada_invalida_sin_coercion; test_cuerpo_faltante_malformado_y_no_objeto |
| Conflictos HTTP independientes | test_conflictos_independientes_y_prioridad |
| Fallo o contención HTTP | test_agenda_ausente_y_no_sqlite_500_sin_fuga; test_lock_real_503_y_recuperacion |
| Health sin DB | test_health_no_crea_agenda_ni_afirma_readiness |
| Documentación del único caso de uso | test_openapi_y_docs |

Son seis escenarios HTTP nuevos; los29 escenarios del dominio conservan su trazabilidad previa. test_recurso_desconocido_404 completa el mapeo por cada catálogo.

### Verificación actual ejecutada

- Python3.12.14, SQLite3.53.1, FastAPI0.143.2, Pydantic2.14.1, Uvicorn0.54.0, Starlette1.8.0, HTTPX0.28.1, Windows. Dependencias únicamente en .venv; requirements-lock.txt fija todas las versiones observadas. DNS falló temporalmente durante pip; reintento con PyPI oficial completó instalación.
- .venv/Scripts/python.exe -m unittest discover -s tests -v: 53 tests, OK (43 anteriores +10 HTTP). Incluye los14 procesos spawn de las siete carreras originales.
- .venv/Scripts/python.exe -m odontologia.demo: dos altas, conflictos por ambos recursos y temporal eliminado.
- openspec validate crear-turno-sin-solapamientos --strict --json: un change válido, cero issues.
- Smoke Uvicorn real: subproceso propio --factory, bind127.0.0.1 puerto efímero, DB temporal propia; GET /health200, POST /turnos201 con ID1 y OpenAPI con dos rutas. Arranque y esperas acotados, terminación en finally, temporal eliminado. No tráfico a proveedores.
- git diff --check: sin errores; sólo aviso de conversiónLF/CRLF en archivos Windows.
- Advertencia upstream: Starlette1.8.0 depreca uso de HTTPX en TestClient; no se silencia ni se presenta como fallo. Pruebas actuales pasan.

Health es liveness, no readiness; no crea agenda. API síncrona usa threadpool y una conexión por operación; protección concurrente sigue en el dominio BEGIN IMMEDIATE, no en memoria del servidor. Swagger/ReDoc pueden usar recursosCDN; /openapi.json es completamente local. No se afirma producción, autenticación ni cumplimiento académico final.


## Cierre técnico de C-01 — 2026-10-28

Antes de archivar se ejecutó `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`: **53 tests, 3.608 s, OK**. La suite incluye contratos HTTP, rollback, contención y procesos reales `spawn`, con archivos temporales propios; no se usó ni modificó la agenda de grabación. La demo `python -m odontologia.demo` confirmó alta, conflicto de profesional, conflicto de box y adyacencia; dos turnos en su temporal y limpieza confirmada. `python -m pip check`: sin dependencias incompatibles. El aviso de deprecación Starlette/HTTPX ya documentado no se silenció.

`openspec validate crear-turno-sin-solapamientos --strict --json`: 1 change válido y cero problemas. Con 18/18 tareas y los cuatro artefactos completos, `openspec archive crear-turno-sin-solapamientos --yes --json` confirmó el archivo [2026-10-28-crear-turno-sin-solapamientos](../../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/) y `specsUpdated: true`: 14 requisitos añadidos, sin modificaciones, bajas ni renombres.

La [spec principal de alta-turnos](../../openspec/specs/alta-turnos/spec.md) conserva el texto de Purpose y todos los requisitos/35 escenarios de la delta, incluidos los escenarios HTTP incorporados después del registro original de 29 escenarios del dominio. Sólo se normalizó el espacio en blanco junto a las cabeceras de la spec principal; no se alteró el contrato. `openspec validate --specs --strict --json`: 1 spec válida y cero problemas. `openspec list --json`: ningún change activo; `openspec list --specs --json`: alta-turnos, 14 requisitos.

Este cierre no crea ni implementa C-02 a C-20, no cambia código o tests y no acredita revisión humana, entrega final ni aceptación docente. La evidencia TDD anterior conserva sus límites y no se inventa un ciclo RED/GREEN nuevo para el archivado. Publicación pendiente de autorización explícita aplicable.

## 2026-10-29 — Reubicación en backend/ por la estructura de la cátedra

El código y las pruebas de C-01 se movieron sin modificaciones a `backend/odontologia/` y `backend/tests/` (con `git mv`), junto con los archivos `requirements*.txt`. Los comandos de esta evidencia se ejecutan ahora desde `backend/`. Comprobación tras el movimiento, en Linux con Python 3.12: `python -m unittest tests.test_agenda tests.test_concurrencia tests.test_demo` → **43 tests OK** (incluye los 14 procesos spawn). Los 10 tests HTTP requieren FastAPI instalado y se verifican en el equipo Windows con el script de comprobación; el resultado se registra en la bitácora.


## C-02

### PostgreSQL optativo y migración de agenda

### Alcance verificado

- SQLite conserva el default y el contrato C-01. PostgreSQL sólo se selecciona con `ODONTOLOGIA_PERSISTENCIA=postgresql` y `DATABASE_URL`; crear la app no abre conexión ni aplica cambios de esquema.
- Alembic versiona el esquema PostgreSQL. `python -m alembic upgrade head` es explícito y repetible.
- `python -m odontologia.db.migrar_sqlite` lee la agenda indicada por `ODONTOLOGIA_DB` y requiere una revisión Alembic vigente y tablas de negocio vacías en destino. La fuente se abre de sólo lectura y se conserva.
- El lector inicia una transacción de lectura antes de las consultas, valida integridad, claves foráneas, estructura y referencias; rechaza solapamientos previos por profesional o box y permite adyacencia `[inicio, fin)`. Si coinciden ambos conflictos, prioriza profesional.
- La importación conserva catálogos, turnos, IDs y secuencia dentro de una única transacción PostgreSQL. Los errores intermedios revierten todos los datos insertados.
- PostgreSQL valida referencias y serializa altas mediante una fila mutex transaccional; errores de timeout se mapean al contrato público de C-01.

### Verificación realizada

Comandos ejecutados desde `backend/` con el entorno `.venv` del repositorio:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
..\.venv\Scripts\python.exe -m pip check
openspec validate --all --strict
git diff --check
```

La suite completa pasó **89 tests**, incluidos **8 tests de integración PostgreSQL**, sobre una instancia temporal PostgreSQL **18.6**, bind `127.0.0.1`, puerto `55432`, base `odontologia_test`. Se verificaron upgrade inicial/repetido, preservación de IDs y secuencia, API, concurrencia multiproceso por profesional y box, timeout, rollback y rechazo de revisión desconocida. La validación OpenSpec estricta, `pip check` y `git diff --check` también pasaron. Starlette/HTTPX todavía emite un aviso de deprecación; no afecta el resultado.

Los casos de seguridad del test runner aceptan solamente DB llamada `test` o con sufijo `_test`, host loopback y puerto distinto de 5432; se rechazaron nombres parecidos (`contest`, `odontologia_test_backup`), host externo, puerto 5432 y puerto implícito. No se conectó a la instancia preexistente de 5432. El clúster temporal se detuvo por su PGDATA exacto; `pg_ctl status` confirmó `no server running` y el puerto 55432 quedó sin listener. La herramienta rechazó la eliminación recursiva del directorio temporal, por lo que el PGDATA detenido queda pendiente de limpieza; no se intentó otro método.

### Límites y recuperación

La verificación usó exclusivamente filas ficticias temporales; no se migró la base del usuario ni se conectaron servicios externos. El cluster de prueba fue PostgreSQL 18.6 local; no es validación del servicio PostgreSQL 16 de Docker Compose ni de un entorno productivo.

La migración es una copia unidireccional: la agenda SQLite original queda preservada y puede seleccionarse de nuevo antes de que PostgreSQL reciba nuevas escrituras. Si ya se confirmaron altas sólo en PostgreSQL, volver a la SQLite original deja esas altas fuera; el proyecto no implementa doble escritura, exportación inversa ni reconciliación. Hacer respaldo del destino y acordar una migración de retorno antes de cambiar el backend después de operar. No se modificó el default SQLite.

C-02 está implementado y sus tareas técnicas están completas; el change sigue activo en OpenSpec, pendiente de Archive. No se hizo commit ni push y no se editó Discovery.

## Implementación y evidencia C-03 — 2026-11-01

Se incorporó autenticación JWT HS256 con sesiones persistidas y revocables, contraseñas derivadas con scrypt, migración SQLite explícita, revisión Alembic encadenada sobre C-02 y bootstrap interactivo del primer Administrador. La autorización aplica la matriz aprobada: Administrador gestiona cuentas y usa las operaciones disponibles; Recepción crea turnos; Profesional queda sin acceso hasta C-08. `POST /turnos` conserva el contrato de dominio C-01 y exige sesión vigente. `/health` se mantiene público y no accede a la DB.

El control del último Administrador activo surgió de la revisión final de seguridad: la primera prueba falló porque podía desactivarse o degradarse esa cuenta; se agregó una restricción transaccional y ambas variantes ahora devuelven 409. El OpenAPI documenta 401, 403 y 503 para los recursos protegidos. No hay usuarios, contraseñas ni JWT por defecto. El testimonio de la documentación no habilita pacientes reales ni despliegue público.

### Verificación ejecutada

Comandos y evidencia:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -q
..\.venv\Scripts\python.exe -m pip check
openspec validate --all --strict
git diff --check
```

La suite SQLite final pasó **111 tests**; el test de PostgreSQL se omite si no se define la URL aislada. Con `ODONTOLOGIA_TEST_DATABASE_URL` apuntando a `odontologia_test` sobre loopback `127.0.0.1:55432`, la suite completa pasó **121 tests**, incluyendo upgrade Alembic C-01→C-03, bootstrap contra PostgreSQL, login API, revocación al cambiar rol y cierre seguro con revisión desactualizada. El clúster PostgreSQL 18 temporal `C:\Users\Oficina\AppData\Local\Temp\tp-odontologia-c03-pg-dafa8ca7ea694e288b7b78bb2b6f9833` se detuvo por su PGDATA exacto; el puerto 55432 quedó sin listener. No se usó la instancia preexistente 5432 ni servicios externos. `pip check` informó `No broken requirements found`; OpenSpec strict validó cuatro artefactos/especificaciones sin problemas; `git diff --check` no informó errores (Git sí advierte normalización LF/CRLF en archivos del checkout Windows).

TDD documentado: suite base 81/1 skip; pruebas de esquema 2/2, SQLite migration 3/3, scrypt 3/3, almacenamiento 2/2, usuarios 3/3 (más el guard del último administrador), configuración 7/7, bootstrap 2/2, servicio de sesiones 3/3, migración CLI SQLite 2/2 y API HTTP 5/5 pasaron tras cada GREEN. Los nuevos tests API inicialmente fallaron porque las rutas todavía no existían. No se creó commit ni se hizo push. La revisión del diff y Archive de C-03 quedan pendientes.

La base de cambios previa a esta implementación era `3c34879510594348034bfaa5472456078335cc28`; los cambios C-03 siguen locales y sin commit. El archivo `docs/discovery/informe-discovery.md` contiene un cambio preexistente del usuario y se preservó sin incluirlo en el alcance C-03.
