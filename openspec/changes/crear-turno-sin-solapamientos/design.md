# Design

## Context

Ver [proposal.md](proposal.md) para el problema y [exploración](../../../docs/exploracion/alta-turno.md) para el checkout observado. La base previa tiene módulo SQLite y 43 tests. El usuario corrigió el stack a FastAPI dentro del mismo C-01. El contrato conductual propuesto está en [alta-turnos](specs/alta-turnos/spec.md); no se acredita lectura personal del spec; la implementación está autorizada por la petición actual.

## Goals / Non-Goals

**Goals:** una API HTTP local sin proveedores externos, pocos archivos, errores estables, persistencia observable y exclusión demostrable entre procesos sobre un archivo local. Mantener separados resultados del agente y revisiones humanas.

**Non-Goals:** diseñar una aplicación clínica completa, ORM, API pública, migraciones de un sistema existente, escalamiento distribuido o CRUD de catálogos. La serialización global de escrituras es suficiente para esta porción; no se promete throughput clínico.

## Decisions

### D-01 — FastAPI y dominio Python reutilizado (Q01–Q02)

Python 3.12+, FastAPI 0.143.2, Pydantic 2.14.1 y Uvicorn 0.54.0. SQLite permanece en sqlite3 estándar; unittest y multiprocessing se conservan, TestClient/HTTPX prueba el adaptador. Instalación sólo en .venv. Python 3.12.14/SQLite 3.53.1 verificados.

La estructura mínima es `odontologia/__init__.py`, `odontologia/agenda.py`, `odontologia/demo.py` y `tests/`. Se añade odontologia/api.py y tests/test_api.py al producto existente. El renderer conserva sus dependencias documentales separadas. Laravel con servidor y Node/TypeScript son alternativas viables, diferidas por preparación adicional sin UI ni red necesarias. Memoria sola se descarta para conservar evidencia de persistencia entre conexiones.

Interfaz propuesta:

```text
inicializar_agenda(ruta_db) -> None
crear_turno(ruta_db, *, paciente_id, profesional_id, box_id,
            inicio, fin, timeout_segundos=5.0) -> Turno
```

`Turno` será un valor inmutable con `id` entero positivo, tres IDs y dos `datetime` conscientes en UTC. Se devolverá después del commit. `ErrorAgenda` expondrá `codigo` estable y `campo` opcional, con mensaje comprensible, sin filtrar SQL ni paths internos. No hay compatibilidad pública previa que romper.

### D-02 — Bootstrap y esquema ficticio (Q03, Q07)

Inicialización explícita de un archivo local nuevo, sin crear directorios padres ni reemplazar archivos existentes. Reservar el archivo de forma exclusiva para evitar dos inicializaciones simultáneas; si existe, informar `agenda_existente`. La demo usa `TemporaryDirectory` del sistema; nunca el directorio temporal de otra persona ni datos reales.

Crear tablas de IDs ficticios `pacientes`, `profesionales`, `boxes` y `turnos` con ID `INTEGER PRIMARY KEY`, tres referencias y límites `inicio_minuto`/`fin_minuto` enteros UTC. Activar y comprobar `PRAGMA foreign_keys=ON` por conexión; CHECK inicio menor que fin y claves foráneas respaldan el contrato. Índices simples por profesional/inicio y box/inicio; no se pretende que un índice único impida intervalos solapados.

Bootstrap: `paciente-A/B`, `profesional-A/B`, `box-A/B`, sin nombres reales ni datos clínicos. Catálogos inmutables en este change; no hay CRUD. El alta abre sólo archivos existentes mediante conexión en modo lectura/escritura sin creación (`mode=rw`) y no inicializa el esquema silenciosamente. Los archivos de demo o pruebas son locales, temporales y no se versionan.

### D-03 — Instantes y semántica temporal (Q04–Q05)

Recibir `datetime` conscientes con offset explícito, sin segundos ni microsegundos. Rechazar `str`, fechas ingenuas y valores inválidos; no inferir zona desde Windows ni redondear. Normalizar instantes a UTC con aritmética de fecha/tiempo y convertir a minutos enteros desde epoch sin timestamps flotantes. El resultado expresa UTC; -03:00 sólo ilustra horarios argentinos, no impone un calendario histórico o una zona IANA.

Intervalos semiabiertos: `existente.inicio < solicitado.fin` y `existente.fin > solicitado.inicio`. Permite adyacencia anterior/posterior, rechaza igualdad de inicio/fin y contención. Duración positiva libre con precisión de minuto, incluso cruce de día; sin disponibilidad, horarios de atención ni duración por prestación. Es una exclusión explícita del MVP, no una afirmación de que cualquier hora sea clínicamente válida.

### D-04 — Ocupación y alcance de recursos (Q06–Q08)

Cada fila confirmada ocupa un profesional y un box exclusivo durante todo su intervalo; no se crean estados ni cancelación. No hay restricciones por paciente simultáneo o compatibilidad profesional-box. No hay excepción de sobreturnos. Si hay conflictos independientes de ambos recursos, profesional tiene prioridad; se consulta box sólo si no hay conflicto de profesional.

No se introduce idempotency key ni reintento automático. Repetir un alta confirmada es una nueva petición y produce el conflicto correspondiente; no devuelve silenciosamente el turno previo.

### D-05 — Transacción local y límite concurrente (Q03)

Una conexión por operación, sin compartir conexiones entre procesos. Python 3.12 `autocommit=True` y control SQL explícito `BEGIN IMMEDIATE`, `COMMIT`, `ROLLBACK`: no mezclar con `Connection.commit()` esperando que confirme bajo autocommit. Validar forma, fechas y timeout antes de abrir el archivo; después abrir, activar FK, iniciar transacción, validar referencias, consultar conflictos, insertar y confirmar; cerrar siempre. Ante error, revertir si `in_transaction` sigue activo, conservando la causa original si rollback o cierre también fallan.

Adquirir el permiso de escritura **antes** de consultar conflictos. SQLite admite un escritor a la vez sobre el archivo: el siguiente competidor debe consultar después del commit del anterior, sin el hueco SELECT/INSERT de transacciones separadas. El timeout de conexión por defecto es 5 segundos, configurable mediante número finito positivo; entrada inválida del timeout se rechaza antes de acceder al archivo.

No activar WAL para este MVP: se conserva el journaling normal para evitar añadir una política innecesaria. Mapear SQLITE_BUSY y SQLITE_LOCKED a `agenda_ocupada`; otros fallos de DB a `almacenamiento_error`, sin simular éxito. No garantizar recuperación de resultados inciertos ante caída de máquina/IO catastrófico; no hay protocolo de reconciliación ni idempotencia. No extrapolar a disco de red, escritores SQL que ignoren esta operación ni múltiples archivos/equipos.

### D-06 — Orden y contrato de errores

Validar forma de IDs en orden paciente/profesional/box; luego inicio, fin, relación del intervalo y timeout. Referencias conocidas se evalúan en orden paciente/profesional/box. Después: conflicto de profesional, conflicto de box, inserción y commit. Este orden hace reproducible el primer error sin publicar excepciones internas.

| Código | Campo cuando aplica | Efecto observable |
| --- | --- | --- |
| `entrada_invalida` | paciente, profesional, box, inicio, fin, intervalo o timeout | Sin alta; no corrección silenciosa |
| `recurso_desconocido` | paciente, profesional o box | Sin alta |
| `conflicto_profesional` | profesional | Sin alta; prioridad si ambos conflictos existen |
| `conflicto_box` | box | Sin alta |
| `agenda_ocupada` | ninguno | No devuelve éxito al agotar espera; rollback cuando corresponde |
| `almacenamiento_error` | ninguno | No devuelve éxito; rollback comprobable en fallos controlados anteriores al commit |
| `agenda_existente` | ninguno | Bootstrap no sobrescribe el archivo |

### D-07 — Estrategia de pruebas y demo

- Unitarias: validación, equivalencia de instantes, predicado de intervalos, contención, prioridad de error y exclusiones explícitas.
- Integración: DB temporal real, referencias, persistencia al reabrir, ningún registro ante rechazo y rollback. Para provocar el fallo anterior al commit, usar una condición de SQLite reproducible que aborte la inserción; no mockear toda la DB ni añadir hooks públicos sólo para el test.
- Multiproceso: contexto `spawn` y funciones de worker importables, agenda única inicializada antes de arrancar procesos y sincronización con Event/Barrier. Repetir por profesional y por box; comprobar resultados de ambos, códigos de salida y filas reales. No limitarse a hilos ni a dos altas secuenciales.
- Contención: una conexión mantiene `BEGIN IMMEDIATE`; el competidor usa timeout corto configurable. Verificar `agenda_ocupada`, ausencia del turno y éxito posible tras liberar el lock. Usar límites de espera amplios para evitar cuelgues, sin basar el control de competencia sólo en sleeps.
- TDD por tarea: prueba RED ejecutada antes del código mínimo, al menos dos entradas/casos por comportamiento, refactor verde y suite completa `python -m unittest discover -s tests -v`. Registrar evidencia real de cada fase; baseline previa43 tests ejecutados; ver evidencia actual.
- Demo `python -m odontologia.demo`: inicializa datos ficticios temporales, muestra alta, rechazo por cada recurso y adyacencia. No conservar datos reales ni conectar servicios.

## Risks / Trade-offs

- Serialización de todos los escritores → simple y suficiente para una demo pequeña; sin promesa de capacidad clínica.
- Escrituras directas fuera del módulo → no están cubiertas por la exclusión temporal; documentar límite y usar el módulo en demo/pruebas.
- SQLite en almacenamiento compartido de red → fuera de garantía; ejecutar competencia en archivo de disco local del sistema temporal, no asumir que la unidad N: es local.
- Errores en commit por IO extremo → informar error sin prometer exactamente una vez; escenarios controlados previos al commit sí deben verificar rollback.
- Procesos Windows `spawn` y timing → workers importables, coordinación explícita, joins acotados y limpieza final; no declarar concurrencia si esas pruebas se omiten o fallan.
- Revisión humana de Propose pendiente → registrar la propuesta y sus correcciones como trabajo del agente; no simular el momento de revisión exigido por el TP.

## Migration Plan

Se mantiene el dominio existente y su esquema; el adaptador no migra datos. El único change C-01 incorpora HTTP local por instrucción expresa. Inicializar sólo nuevas agendas ficticias y rechazar archivos existentes; sin migraciones ni borrados automáticos. Las pruebas usan temporales que les pertenecen. Revertir código por Git no autoriza eliminar agendas ajenas.

## Open Questions

No quedan decisiones técnicas omitidas para este contrato propuesto: Q01–Q08 tienen respuesta o exclusión explícita arriba. La corrección FastAPI y continuación están autorizadas expresamente; esto no acredita revisión académica personal del spec. Q09–Q10 (lecturas personales, autor y evidencia de entrega) continúan fuera del cambio funcional y no alteran su spec. Un cambio solicitado durante la revisión requiere ajustar los artefactos antes de Apply.

Fuentes técnicas y fecha de consulta: [exploración](../../../docs/exploracion/alta-turno.md). La propuesta es compatible con documentación oficial, pero la evidencia actual registra53 tests y smoke HTTP local.

### D-08 — Contrato HTTP local de C-01

crear_app(ruta_db=None, timeout_segundos=5.0) produce la aplicación sin tocar DB. Si no se pasa ruta usa ODONTOLOGIA_DB o agenda.sqlite3; inicialización explícita previa. Uvicorn se ejecuta con --factory y --host 127.0.0.1 (ver README). POST /turnos recibe objeto JSON con los cinco campos del dominio: IDs string estrictos y fechas ISO 8601 con T. Rechazar epoch numérico, campos adicionales, cuerpo inválido y fechas que incumplan offset/minuto; no recortar IDs. El endpoint síncrono permite ejecutar SQLite en el threadpool de FastAPI y usa una conexión por operación.

201 devuelve Turno persistido en UTC. Errores JSON {codigo,campo,mensaje}: entrada_invalida422, recurso_desconocido404, conflicto_profesional/box409, agenda_ocupada503, almacenamiento_error500. No filtrar input, SQL, rutas ni excepciones internas. Pydantic valida estructura antes del dominio; el orden entre múltiples errores estructurales y de dominio no promete la prioridad entre capas, aunque la prioridad de profesional sobre box permanece. Timeout sólo configuración de la fábrica, no entrada pública.

GET /health200 {status:ok} es liveness, no prueba DB. /openapi.json es local; /docs y /redoc sirven HTML con recursos CDN opcionales de FastAPI, sin llamadas de negocio a proveedores. Sin autenticación, UI clínica ni despliegue público. Los escenarios previos se conservan como contrato del dominio.
