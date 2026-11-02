# Backend — TP-ODONTOLOGIA

API del sistema odontológico. Stack definido por la cátedra (corrección del 2026-10-29):
**Python, FastAPI, JWT, SQLAlchemy, SQLite y PostgreSQL optativo.**

## Estado

| Pieza | Estado | Change |
| --- | --- | --- |
| Alta de turnos sin solapamientos (`POST /turnos`, `GET /health`) | Implementado; regresión incluida en la suite; archivado | C-01 |
| Persistencia en SQLite local (`ODONTOLOGIA_DB`) | Predeterminada y compatible con C-01 | C-01 |
| PostgreSQL + SQLAlchemy, Alembic y migración explícita | Implementado, validado en PostgreSQL aislado y archivado | C-02 |
| Autenticación JWT y autorización del personal | Implementado y archivado en SQLite/PostgreSQL | C-03 |
| Auditoría append-only y `GET /auditoria` | Implementado, validado y archivado; sólo Administrador | C-04 |
| Fichas mínimas y baja lógica de pacientes | Implementado en SQLite/PostgreSQL; Administrador y Recepción gestionan datos; sólo Admin cambia estado | C-05 |
| Catálogos de profesionales, boxes y prestaciones | Implementado en SQLite/PostgreSQL; lectura paginada; baja lógica sólo Administrador | C-06 |
| Horarios semanales, excepciones y bloqueos | Implementado, validado y archivado localmente; v5 / Alembic 0006 | C-07 |
| Estados de turno y cancelación idempotente | Implementado, validado y archivado localmente; v6 / Alembic 0007 | C-09 |
| Consulta paginada, opciones orientativas y acceso Profesional vinculado | Implementado y archivado localmente; v7 / Alembic 0008 | C-08 |
| Versión de turnos para reprogramación atómica | Esquema y versionado implementados; C-10 en Apply; v8 / Alembic 0009 | C-10 |
| Recordatorios simulados | Consentimiento, programación, worker local `--once`, auditoría y backup/restore implementados en SQLite/PostgreSQL | C-17 |
| Docker / Compose y Redis | Fuera del alcance operativo acordado para esta entrega | No requeridos |

C-01 y SQLite siguen disponibles. C-02 permite PostgreSQL e importación manual desde SQLite; C-03 agrega JWT y sesiones revocables; C-04 audita metadatos; C-05 administra fichas; C-06 administra catálogos; C-07 configura horarios; C-09 añade estados y C-08 consultas. Profesional tiene una cuenta vinculada única y consulta sólo su agenda y opciones, sin escritura; Administrador/Recepción consultan agenda. La disponibilidad es orientativa y el alta vuelve a validar dentro de su transacción. C-10 agrega una versión positiva por turno para concurrencia optimista; sus operaciones están en desarrollo. El inicio de la API no ejecuta migraciones ni importa datos. La fuente SQLite C-01 no se altera; la importación rechaza fuentes con solapamientos o destinos ya poblados.

## Estructura

```text
backend/
├── odontologia/
│   ├── agenda.py        # Dominio de C-01: validación, transacción y alta
│   ├── api.py           # Adaptador FastAPI de agenda y consultas C-08
│   ├── demo.py          # Demo por consola con agenda temporal
│   ├── core/config.py   # Variables de entorno del stack
│   ├── db/              # SQLAlchemy + PostgreSQL (C-02/C-05-C-09)
│   ├── auth/            # JWT, cuentas vinculadas y sesiones (C-03/C-08)
│   ├── audit.py         # Metadatos append-only y consulta segura (C-04/C-06)
│   ├── catalogos.py     # Catálogos ficticios y auditoría atómica (C-06)
│   ├── pacientes.py     # Fichas mínimas y baja lógica (C-05)
├── alembic/             # Revisiones versionadas de C-02 a C-10
├── tests/               # Regresión C-01 a C-10
├── requirements.txt         # Dependencias directas de C-01
├── requirements-dev.txt     # + HTTPX para tests
├── requirements-lock.txt    # Entorno verificado de C-01
├── requirements-stack.txt   # + SQLAlchemy, psycopg, Alembic y PyJWT
└── .env.example
```

## Ejecutar sin Docker (Windows, desde `backend/`)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt -r requirements-stack.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m odontologia.demo
```

Para la demo opcional de API ver el README principal. Docker y Redis no forman parte de los pasos requeridos.

Swagger, ReDoc y `/openapi.json` sólo se habilitan cuando `ODONTOLOGIA_ENTORNO=desarrollo` está definido explícitamente. El `.env.example` local configura ese valor para el demo; en una instalación de producción configurar `ODONTOLOGIA_ENTORNO=produccion`. Si la variable falta o tiene otro valor, la documentación queda deshabilitada (404). Esto no reemplaza la autenticación ni la autorización de la API.

## Migrar autenticación e inicializar acceso

La migración se ejecuta explícitamente sobre una agenda ficticia existente. No crea el archivo SQLite ni se ejecuta al importar o iniciar FastAPI.

**SQLite (valor predeterminado):** desde `backend/`, con `ODONTOLOGIA_DB` apuntando a la agenda correcta:

```powershell
$env:JWT_SECRETO = [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
..\.venv\Scripts\python.exe -m odontologia.auth.migrar_sqlite
..\.venv\Scripts\python.exe -m odontologia.auth.bootstrap_admin
```

El bootstrap pide identificador y contraseña de forma interactiva y oculta; no admite credenciales por argumentos ni crea usuarios predeterminados. Guardar `JWT_SECRETO` fuera del repositorio y no reutilizar el texto ilustrativo.

**PostgreSQL:** definir `ODONTOLOGIA_PERSISTENCIA=postgresql`, `DATABASE_URL` y un secreto local; desde `backend/`:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m odontologia.auth.bootstrap_admin
```

Alembic aplica las revisiones consecutivas hasta la revisión vigente (`20261102_0014_financial_ledger`), incluida la ficha mínima, catálogos, auditoría, disponibilidad, estados, vínculos de cuenta Profesional/Paciente, versión de turnos, historia clínica sintética, odontogramas, planes manuales, outbox simulado, idempotencia del portal y ledger financiero. Aplicar migraciones y bootstrap explícitamente desde el entorno local de Python cuando se necesiten para una prueba; no usar la API ni `GET /health` como comando de migración.

`POST /sesiones` recibe `identificador` y `password`; su respuesta contiene `access_token`, `token_type` y `expires_in`. En Swagger, usar **Authorize** con `Bearer <token>`. `/sesiones/actual` permite consultar y cerrar la sesión propia. El Administrador puede consultar/crear usuarios y cambiar rol/estado; Recepción puede crear turnos y operar fichas mínimas de pacientes; sólo Administrador cambia el estado activo de pacientes. Desactivar una cuenta, cambiarle el rol o cerrar sesión revoca sus tokens persistidos. Los fallos de credenciales devuelven un mensaje genérico. Las fichas contienen sólo nombre y teléfono opcional ficticios; no usar datos reales ni añadir historia clínica. Los eventos guardan sólo actor/acción/recurso/resultado/fecha; no incluyen cuerpos, nombres, teléfonos, contraseñas, hashes, JWT, datos clínicos ni el identificador de un login rechazado. `GET /auditoria?limit=50&offset=0` es sólo Administrador, admite límite 1–100 y no ofrece edición, borrado ni purga automática. Si el evento falla, la mutación se revierte y la API no informa éxito. Sin secreto o esquema migrado, las operaciones protegidas fallan cerradas con 503 mientras `/health` continúa pública.

## C-17 — Esquema de recordatorios simulados

La migración explícita SQLite sube el esquema v10 a v11; una base v11 creada por la versión anterior de C-17 reconstruye el outbox, asigna generación 1 a las filas existentes y conserva sus datos y referencias. Alembic PostgreSQL agrega `20261102_0012_appointment_reminders` después de `20261102_0011_odontogram_treatment_plans`. Se agrega `pacientes.acepta_recordatorios`, con valor inicial `false`, y la tabla `recordatorios_outbox`, inicialmente vacía al migrar desde v10/0011, con clave de idempotencia única por turno+versión+tipo+generación, referencia restringida al turno y estados/reintentos acotados. Al retirar el consentimiento se conserva la generación invalidada; un reconsentimiento elegible crea una generación nueva sin duplicados concurrentes. El contrato de ambos motores se verifica con datos sintéticos.

`POST /pacientes` admite `acepta_recordatorios` opcional, `false` por omisión; `PATCH /pacientes/{paciente_id}` permite cambiarlo con un booleano explícito. Administrador y Recepción pueden gestionarlo desde la sección **Preferencia de recordatorios** de la agenda o al crear la ficha. La ficha muestra sólo la preferencia actual, y la interfaz refleja el cambio tras confirmación del servidor. Profesional no accede a esa sección ni carga la lista para administrarla. El evento de auditoría reutiliza `paciente.actualizado` y no guarda el valor, nombre, teléfono ni cuerpo de solicitud; si la auditoría falla, el cambio se revierte.

El arranque de FastAPI y el worker no aplican migraciones: validan el esquema existente y fallan cerrados si está desactualizado. SQLite requiere ejecutar explícitamente `python -m odontologia.auth.migrar_sqlite` sobre la agenda seleccionada; PostgreSQL requiere `python -m alembic upgrade head` con `DATABASE_URL` configurada.

Al confirmar, cambiar consentimiento o reprogramar, el servicio programa o invalida los recordatorios elegibles en la misma transacción que el cambio y su auditoría. La regla usa `America/Argentina/Mendoza`; sólo se agenda si quedan más de 24 horas. Antes de procesar, el worker vuelve a validar consentimiento, estado, versión y hora del turno.

El worker se ejecuta únicamente por invocación manual, en una pasada obligatoria (`--once`) y con límite de 1 a 100 (por omisión 100). Desde `backend/`, sobre una base de demostración ya migrada:

```powershell
$env:ODONTOLOGIA_DB = ".\agenda.sqlite3"
.\.venv\Scripts\python.exe -m odontologia.workers.recordatorios_cli --once --limit 100
```

La salida contiene sólo los conteos `procesados`, `invalidados` y `fallidos`. El canal es local y simulado: no abre conexiones de red ni contacta pacientes o proveedores; los fallos sintéticos se inyectan sólo en tests y se limitan a tres intentos.

El backup SQLite y PostgreSQL incluye `recordatorios_outbox` y su recuento. El restore compara esquema, integridad, referencias y conteos en un destino nuevo; el manifiesto no expone nombres, teléfonos ni contenido del outbox. La verificación C-17 conserva generaciones, estados pendientes, `procesado_simulado` e `invalidado` en bundles sintéticos.

## C-13 — Seguridad operativa local

`GET /health` es liveness del proceso y sigue respondiendo 200 aunque la base no esté disponible. `GET /ready` ejecuta únicamente `SELECT 1` sobre la base configurada: 200 indica conexión y 503 usa `base_no_disponible`; en SQLite abre el archivo existente en modo de sólo lectura y no crea bases ni esquemas. Cada respuesta incluye `X-Request-ID`; sólo acepta un UUID válido único, lo normaliza y reemplaza valores ausentes, repetidos, inválidos o excesivos por uno generado. Los eventos HTTP locales guardan únicamente ID, método, plantilla de ruta, estado, duración y código HTTP estable; no incluyen path crudo, query, payload, headers, dirección, token, secreto ni excepción. Uvicorn se ejecuta sin access logs ni procesamiento de `X-Forwarded-*`.

El inicio de sesión admite cinco fallos por combinación de origen de conexión y hash del identificador normalizado durante cinco minutos; el siguiente responde 429 con `Retry-After`. Para evitar que una ráfaga simultánea supere el límite antes de registrar los fallos, como máximo cinco verificaciones por combinación quedan activas a la vez; los errores de validación/base liberan su reserva, y un acceso correcto limpia los fallos confirmados sin descartar otras verificaciones activas. La ventana expira; el límite es temporal y está acotado a memoria del proceso único, por lo que no coordina múltiples workers o instancias y se reinicia al reiniciar el proceso. Los errores internos HTTP devuelven un mensaje genérico con código `error_interno`. La documentación HTTP sólo está habilitada con `ODONTOLOGIA_ENTORNO=desarrollo`; producción, variable ausente y valores no reconocidos la deshabilitan. Las operaciones de backup siguen siendo manuales y locales; un fallo usa un código/mensaje seguro y no expone el texto de `ValueError`.

`POST /pacientes` acepta `nombre` y `telefono` opcional; `GET /pacientes?limit=50&offset=0`, `GET/PATCH /pacientes/{paciente_id}` y `DELETE /pacientes/{paciente_id}` requieren sesión de Administrador o Recepción, salvo que DELETE y el cambio de `activo` en PATCH quedan sólo para Administrador. La baja es lógica; los turnos históricos permanecen y un paciente inactivo no admite nuevas altas. Los nombres repetidos se permiten; la ficha no se deduplica automáticamente.

`/profesionales`, `/boxes` y `/prestaciones` exponen `POST`, `GET` paginado, `GET/{id}` y `PATCH/{id}`. Administrador y Recepción crean, leen y editan datos descriptivos; sólo Administrador cambia `activo`. Los catálogos incluyen inactivos en la lectura; la baja conserva filas e historial. Cada nombre ocupa de 1 a 120 caracteres después de normalizar espacios. Las prestaciones exigen duración entera positiva en minutos, limitada al máximo de `INTEGER` PostgreSQL. C-01 no agrega `prestacion_id` al turno ni calcula su duración; no hay reglas de compatibilidad.

## C-07 — Disponibilidad local

La agenda usa la zona IANA `America/Argentina/Mendoza`. Python convierte los instantes UTC de los turnos y los bloqueos a fecha y día local con `zoneinfo`; se fija `tzdata==2026.6` en `requirements.txt` y `requirements-lock.txt` para que Windows tenga una base IANA portable. Se puede comprobar la instalación desde `backend/` con:

```powershell
..\.venv\Scripts\python.exe -c "from zoneinfo import ZoneInfo; print(ZoneInfo('America/Argentina/Mendoza'))"
```

SQLite sube explícitamente a esquema v5 y PostgreSQL a Alembic `20261102_0006_agenda_availability`, encadenada tras `20261102_0005_resource_catalogs`. La migración conserva los datos existentes y no inventa horarios. Todo recurso comienza sin tramos configurados; se considera cerrado hasta que Administrador o Recepción guarden su disponibilidad. Los cambios de horario, excepción o bloqueo son locales y no consultan un calendario de feriados externo.

La API requiere esa versión y las cuatro tablas de disponibilidad; si la versión figura vigente pero falta alguna tabla, responde 503 antes de aceptar operaciones protegidas. El módulo standalone de C-01 mantiene compatibilidad con una base antigua que aún no tiene `auth_schema_version`; al migrarla explícitamente a v5, una agenda sin configuración queda cerrada. Tras migrar turnos C-01, Administrador o Recepción puede configurar profesional y box de forma secuencial: cada cambio conserva los turnos del recurso que modifica; las nuevas reservas sólo se habilitan cuando ambos recursos tienen un tramo vigente.

Los contratos de gestión son `GET/PUT /horarios/{tipo_recurso}/{recurso_id}`, `GET/PUT/DELETE /horarios/{tipo_recurso}/{recurso_id}/excepciones/{fecha}` y `GET/POST /bloqueos` más `DELETE /bloqueos/{bloqueo_id}`. El tipo de recurso es `profesional` o `box`. El horario semanal reemplaza el conjunto completo de tramos por día ISO (`1` lunes a `7` domingo), cada tramo usa `inicio`/`fin` locales `HH:MM` y admite `24:00` sólo como fin. Se aceptan varios tramos adyacentes, no solapados ni nocturnos. La respuesta devuelve los siete días; un día ausente o vacío está cerrado.

## C-08 — Consulta de agenda y disponibilidad

La migración explícita añade `usuarios.profesional_id` único y una restricción que vincula el rol `profesional` a una ficha existente. SQLite sube a v7 y PostgreSQL a Alembic `20261102_0008_professional_accounts`; los turnos mantienen el estado y las restricciones de C-09. El Administrador puede asignar ese vínculo al crear o actualizar una cuenta. Cambiar rol o vínculo revoca sesiones existentes. El JWT y `/sesiones/actual` exponen el ID vinculado; la validación falla cerrada si cambia o falta.

`GET /turnos?desde=...&hasta=...&limit=50&offset=0` requiere ambos instantes ISO 8601 con offset explícito, aplica rango semiabierto de hasta 31 días y permite filtros opcionales `profesional_id`, `box_id` y `estado`. El orden es por inicio e ID; `limit` admite 1–100. Administrador y Recepción reciben campos operativos sin teléfono. Profesional sólo ve horarios y nombre de paciente de su ficha vinculada; filtrar por otro profesional devuelve 403.

`GET /disponibilidad?fecha=YYYY-MM-DD&profesional_id=...&box_id=...&duracion_minutos=...` calcula candidatos locales cada 15 minutos. Sólo devuelve intervalos que caben en los horarios o excepciones vigentes de ambos recursos, dentro del mismo día y sin bloqueos ni turnos `reservado`/`confirmado`. Los recursos inactivos no producen opciones. La respuesta es orientativa y de sólo lectura; no agrega turnos ni auditoría. `POST /turnos` vuelve a comprobar disponibilidad y solapamientos dentro de su transacción. Profesional sólo puede consultar su vínculo; no puede escribir ni administrar recursos. La implementación C-08 continúa en Apply, pendiente de regresión completa y revisión antes de Archive.

Para probar en Swagger, iniciar sesión con `POST /sesiones`, usar **Authorize** con `Bearer <access_token>` y abrir `/docs`. El contrato descargable está en `/openapi.json`. OpenAPI incluye ejemplos de los cuerpos de escritura. Por ejemplo, para reemplazar el horario del lunes y miércoles de un profesional:

```http
PUT /horarios/profesional/profesional-A
Content-Type: application/json
Authorization: Bearer <access_token>

{"dias":{"1":[{"inicio":"09:00","fin":"12:00"},{"inicio":"13:00","fin":"17:00"}],"3":[{"inicio":"09:00","fin":"12:00"}]}}
```

Para consultar esa configuración: `GET /horarios/profesional/profesional-A`. Una excepción del martes reemplaza la semana de ese día; enviar `{"tramos":[]}` lo cierra. Un bloqueo de una hora sobre un box se envía con `POST /bloqueos` y `tipo_recurso`, `recurso_id`, `inicio` y `fin`; las dos fechas deben tener offset explícito, por ejemplo `2026-11-02T12:00:00-03:00` y `2026-11-02T13:00:00-03:00`. `GET /bloqueos?limit=50&offset=0` lista y pagina; eliminar usa `DELETE /bloqueos/{bloqueo_id}`.

Las respuestas de error siguen el objeto `{codigo, campo, mensaje}`: `401` requiere una sesión válida; `403` indica rol insuficiente en rutas restringidas; `409` rechaza una reserva fuera de disponibilidad o un cambio que afectaría turnos existentes; `422` indica un cuerpo, hora o paginación inválidos. OpenAPI documenta además `404` para recursos desconocidos y `503` para fallos transaccionales.

## C-10 — Versionado para reprogramación

La migración C-10 sube SQLite a v8 y PostgreSQL a Alembic `20261102_0009_turn_rescheduling`. Agrega `turnos.version` positiva, iniciada en 1 para turnos existentes, y permite el evento de auditoría metadata-only `turno.reprogramado`. Las transiciones efectivas incrementan la versión en la misma transacción que el estado y la auditoría; repetir la cancelación no crea otro cambio ni incrementa versión.

La columna existe únicamente en el esquema migrado de la API. El contrato standalone de C-01 sigue usando sus bases sin `auth_schema_version` y no requiere `version`; no ejecutar su servicio con una base parcialmente migrada. Si una base declara v8/0009 pero carece de la columna requerida, las operaciones protegidas fallan cerradas con 503.

`GET /turnos` devuelve `version` a Administrador y Recepción; la proyección Profesional mantiene sólo `inicio`, `fin` y `paciente_nombre`. Para mover una fila existente, Administrador o Recepción envía `POST /turnos/{turno_id}/reprogramacion` con la versión que consultó:

```http
POST /turnos/42/reprogramacion
Authorization: Bearer <access_token>
Content-Type: application/json

{"version":1,"inicio":"2026-11-02T10:00:00-03:00","fin":"2026-11-02T10:30:00-03:00","profesional_id":"profesional-B","box_id":"box-B"}
```

El cuerpo no admite campos adicionales. El paciente, la duración y el estado del turno se conservan; el intervalo debe quedar en el mismo día local, dentro de los horarios y sin bloqueo ni ocupación. Una respuesta `200` devuelve la nueva versión. Ante `409 version_desactualizada`, volver a consultar `GET /turnos` y revisar la asignación antes de reintentar con la versión vigente. Los otros `409` (`turno_no_reprogramable`, `recurso_inactivo`, `fuera_de_disponibilidad`, `conflicto_profesional` o `conflicto_box`) requieren resolver la condición informada; el rechazo no altera la fila. `404` identifica un turno o destino inexistente y `422` un cuerpo inválido. Profesional no tiene permiso de escritura; ausencia de sesión responde `401`. Los ejemplos y respuestas están publicados en `/docs` y `/openapi.json`.

Una excepción identifica un recurso y fecha local `YYYY-MM-DD`; reemplaza todos sus tramos semanales de ese día. Una excepción con `tramos: []` cierra el día; eliminarla hace que vuelva a regir la semana. Como supuesto explícito del modelo, cada bloqueo pertenece exactamente a un profesional o a un box, nunca a ambos ni a toda la clínica; la solicitud usa `tipo_recurso`, `recurso_id`, `inicio` y `fin` ISO 8601 con offset. Los bloqueos se comparan como instantes UTC y el listado usa `limit` 1–100 y `offset` no negativo. Las consultas no generan eventos de auditoría.

## Preparar PostgreSQL y migrar una agenda existente

Usar únicamente una base PostgreSQL vacía que controles y una agenda SQLite ficticia. Guardar primero una copia de respaldo de la agenda, detener el proceso que la escribe y confirmar que `ODONTOLOGIA_DB` apunta a la fuente correcta. Los comandos siguientes se ejecutan desde `backend/` en PowerShell:

```powershell
$env:ODONTOLOGIA_DB = 'C:\ruta\segura\agenda-c01.sqlite3'
$env:DATABASE_URL = 'postgresql+psycopg://usuario:clave@127.0.0.1:PUERTO/odontologia'
$env:ODONTOLOGIA_PERSISTENCIA = 'postgresql'
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m odontologia.db.migrar_sqlite
```

El primer comando aplica sólo el esquema. Verificar la revisión con `..\.venv\Scripts\python.exe -m alembic current`. El segundo importa a un destino vacío y muestra conteos; no modifica ni elimina el SQLite. Si se interrumpe o el destino ya tiene datos, no repetir sobre ese destino: inspeccionar el error y preparar una base vacía controlada. No hay rollback automático ni sincronización de escrituras entre motores. Cambiar a `ODONTOLOGIA_PERSISTENCIA=sqlite` permite volver a abrir la agenda original pre-migración; cualquier alta posterior hecha sólo en PostgreSQL no aparecerá en SQLite. Antes de cambiar de motor después de usar PostgreSQL, hacer un respaldo PostgreSQL y planificar cómo conservar esas escrituras; no tratar la copia SQLite antigua como recuperación actualizada.

Para habilitar PostgreSQL en la API después de migrar, mantener `ODONTOLOGIA_PERSISTENCIA=postgresql` y `DATABASE_URL` en el entorno del proceso. Las pruebas usan un clúster aislado local; no copiar URLs o credenciales a archivos versionados.

La suite completa incluye pruebas PostgreSQL de migración, rollback y concurrencia multiproceso. Para ejecutarlas se requiere una base de prueba dedicada cuyo nombre sea `test` o termine en `_test`, host loopback y puerto distinto de 5432:

```powershell
$env:ODONTOLOGIA_TEST_DATABASE_URL = 'postgresql+psycopg://usuario:clave@127.0.0.1:PUERTO/odontologia_test'
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Si la variable no está definida, las pruebas PostgreSQL se omiten; esa ejecución no verifica PostgreSQL.

## Copias locales de agenda (C-12)

El bundle de backup es un directorio nuevo con el payload completo (`agenda.sqlite3` o `agenda.dump`) y `manifest.json`. El manifiesto v1 incluye `created_at_utc` (ISO 8601 en UTC), `backend`, `application_version`, `schema_version`, `payload_name`, `payload_size_bytes`, `payload_sha256` (SHA-256 hexadecimal) y `table_counts` (nombre de cada tabla vigente y cantidad de filas como entero no negativo). Los conteos son agregados y no incluyen valores ni identificadores de filas. La versión del backend se define en `odontologia.version`; el esquema aceptado actualmente es SQLite `13` o PostgreSQL `20261102_0014_financial_ledger`. Incluye recuentos de las tablas clínicas, `recordatorios_outbox`, `idempotencia_portal_paciente` y tablas del ledger. El hash detecta corrupción/cambios accidentales del payload, no autentica el manifiesto si un atacante reemplaza ambos; los conteos no prometen confidencialidad. El manifiesto no guarda URL, ruta de origen, credenciales ni datos personales.

Los comandos C-12 son manuales y locales; la API y el arranque no crean ni restauran copias. Los bundles contienen la base completa, incluidas fichas, cuentas/sesiones y auditoría, por lo que deben tratarse como datos sensibles. No contienen `.env` ni el secreto JWT. No se suben automáticamente, no tienen cifrado gestionado ni política de purga automática. Las pruebas usan bases temporales y datos ficticios; no demuestran recuperación humana ni preparación de producción.

Guarda cada bundle en una ruta local fuera del repositorio (por ejemplo, `N:\copias`), limita quién puede acceder y no lo compartas. La orden `crear` también muestra un aviso porque el bundle contiene datos sensibles de pacientes, cuentas y auditoría.

En POSIX, staging y bundle publicado usan modo `0700`, mientras que payload y manifiesto usan `0600` durante la preparación y después de publicar. En Windows no se cambia ni se certifica el ACL heredado del directorio/volumen; revisarlo según el equipo donde se guarde la copia.

Para SQLite, configurar la base activa y pedir un directorio de bundle nuevo desde `backend/` en PowerShell:

```powershell
$env:ODONTOLOGIA_PERSISTENCIA = 'sqlite'
$env:ODONTOLOGIA_DB = 'C:\ruta\agenda.sqlite3'
..\.venv\Scripts\python.exe -m odontologia.backup crear 'N:\copias\agenda-2026-11-02'
```

El adapter SQLite abre el origen en sólo lectura y usa la Online Backup API, que produce un snapshot coherente aunque haya conexiones concurrentes y contempla la base en modo WAL. Luego calcula `table_counts` leyendo el archivo ya copiado, no la base activa. No se usa `copy`/`Copy-Item` sobre el archivo activo. La operación no confirma transacciones ajenas ni modifica agenda, versión de esquema o auditoría.

Antes de copiar, la base debe declarar `auth_schema_version=11`, incluir `turnos.version`, `evoluciones_clinicas` y `recordatorios_outbox`, superar `PRAGMA integrity_check` y no tener filas en `PRAGMA foreign_key_check`. No se migra ni repara el origen. El bundle se prepara en un directorio temporal exclusivo dentro del mismo padre y sólo se publica en un destino que todavía no existe; si la copia falla se elimina ese staging y se conserva intacto cualquier destino previo. El payload se consolida en modo journal DELETE para que el bundle publicado contenga sólo los dos archivos esperados y no sidecars WAL. La comprobación puede rechazar bases C-01 standalone sin migrar, archivos ausentes/corruptos o una revisión incompatible.

Los rechazos usan códigos estables internos: `origen_ausente`, `origen_invalido`, `esquema_incompatible`, `integridad_invalida`, `referencias_invalidas`, `destino_existente`, `configuracion_invalida`, `bundle_invalido`, `herramienta_ausente`, `herramienta_invalida`, `version_incompatible`, `servidor_no_disponible` y `operacion_fallida`. La CLI presenta un mensaje breve; el detalle del motor no debe revelar rutas o secretos. Los estados son: bundle creado y verificado, rechazo previo sin salida, o fallo sin destino publicado. Esto no constituye evidencia de una restauración real.

La verificación es offline y de sólo lectura respecto del bundle: SQLite comprueba hash, versión de esquema, `integrity_check` y claves foráneas; PostgreSQL comprueba el manifiesto/hash y que `pg_restore --list` pueda leer el archive. No requiere conectarse al servidor ni demuestra que el destino vaya a aceptar la restauración.

```powershell
..\.venv\Scripts\python.exe -m odontologia.backup verificar 'N:\copias\agenda-2026-11-02'
```

La restauración SQLite requiere que la carpeta destino exista y que el archivo destino no exista. Se prepara en staging en el mismo volumen, se comprueban integridad, revisión y recuentos, y se publica con una operación exclusiva que rechaza carreras; nunca reemplaza la agenda activa, un archivo existente o un destino dentro del bundle. Si el filesystem no permite publicar mediante enlace duro, la operación falla cerrada y no crea un destino utilizable.

```powershell
..\.venv\Scripts\python.exe -m odontologia.backup restaurar `
  'N:\copias\agenda-2026-11-02' 'N:\pruebas\agenda-recuperada.sqlite3'
```

La suite usa fixtures ficticios: restaura a archivo nuevo, abre una conexión SQLite nueva, comprueba una fila y permite una inserción ficticia posterior. Eso acredita el flujo técnico automatizado en temporales; no acredita una recuperación de datos reales ni una revisión humana. En este host Windows no se pudo crear un symlink en la prueba (WinError 1314); el rechazo se implementa, pero esa ruta específica quedó sin prueba de ejecución.

Para PostgreSQL, seleccionar el motor ya configurado y pasar un nombre de base nuevo (no una URL ni un path). El usuario de conexión necesita `CREATEDB` y permiso para conectarse a `postgres`. El adapter consulta primero que el destino no exista, crea una base temporal aleatoria, ejecuta `pg_restore --exit-on-error`, compara revisión, constraints y los 20 recuentos contra el manifiesto, cierra sólo las conexiones que abrió y renombra el staging únicamente si el nombre final sigue libre. En cualquier error limpia sólo la base temporal propia; no termina conexiones ajenas ni borra una base existente. Los nombres se restringen a minúsculas, dígitos y guion bajo (máximo 63 caracteres).

```powershell
$env:ODONTOLOGIA_PERSISTENCIA = 'postgresql'
$env:DATABASE_URL = 'postgresql+psycopg://usuario:clave@127.0.0.1:55432/odontologia_test'
..\.venv\Scripts\python.exe -m odontologia.backup restaurar `
  'N:\copias\agenda-postgresql-2026-11-02' 'agenda_recuperada'
```

El destino pertenece al cluster configurado por `DATABASE_URL`, y debe estar ausente. La integración del adapter se validó en el cluster efímero PG18.6 local, restauró a una base nueva con revisión y conteos iguales al manifiesto, abrió otra conexión e insertó un paciente ficticio. Este resultado acredita el adapter con cliente/servidor 18.6; no acredita recuperación humana ni producción. El build de una imagen no forma parte del alcance de esta entrega.

Para PostgreSQL, el adapter requiere `pg_dump` y `pg_restore` disponibles en `PATH`; ambos deben tener la misma major que el servidor. La detección consulta `--version` con argumentos fijos y sin shell; la URL y sus credenciales no se pasan en la línea de comandos ni se imprimen. El adapter valida los ejecutables disponibles, pero no los instala ni actualiza; la integración aislada comprobada usó clientes/servidor PostgreSQL 18.6.

Al seleccionar PostgreSQL, `crear` toma el motor y la conexión ya configurados en `DATABASE_URL`, consulta la revisión Alembic y genera `agenda.dump` con `pg_dump --format=custom`. En una transacción `REPEATABLE READ` cuenta las tablas y exporta un snapshot MVCC; mantiene esa transacción abierta mientras `pg_dump --snapshot=<id>` importa el mismo snapshot. Así, las filas confirmadas mientras corre el dump no alteran ni el payload ni sus recuentos. La contraseña viaja por `PGPASSWORD` en el entorno mínimo del proceso; los argumentos son fijos y no incluyen URL ni contraseña. Antes de declarar el bundle, `pg_restore --list` debe reconocer el archivo y se vuelve a comprobar el manifiesto/hash. Este paso comprueba estructura del archivo, no efectúa una restauración de ensayo.

```powershell
$env:ODONTOLOGIA_PERSISTENCIA = 'postgresql'
$env:DATABASE_URL = 'postgresql+psycopg://usuario:clave@127.0.0.1:55432/odontologia_test'
..\.venv\Scripts\python.exe -m odontologia.backup crear 'N:\copias\agenda-postgresql-2026-11-02'
```

El proceso espera PostgreSQL en la revisión vigente `20261102_0014_financial_ledger`, servidor/clientes de la misma major y un destino nuevo. La contraseña de ejemplo se reemplaza sólo en el entorno local; no guardarla en documentos ni en el manifiesto. Sin PostgreSQL local de prueba compatible, no ejecutar esta orden contra una agenda real.

La creación prepara y valida payload y manifiesto en un directorio privado del mismo volumen y publica el directorio completo con una operación atómica que no reemplaza destinos. En Windows usa `os.rename`; en Linux exige `renameat2(RENAME_NOREPLACE)` y falla cerrado si no está disponible. Una colisión que aparezca durante la publicación, incluso un directorio POSIX vacío, se conserva sin cambios; una excepción previa deja el destino final ausente y limpia sólo el staging propio. El staging, payload y manifiesto mantienen permisos POSIX `0700`/`0600`; Windows conserva ACL heredadas. La copia contiene datos sensibles y debe guardarse fuera del repositorio.

La primera integración de backup C-12 se ejecutó antes de C-15, con un cluster temporal PostgreSQL 18.6 en `127.0.0.1:55432`, cliente 18.6 y la base ficticia `odontologia_test`, migrada entonces hasta `20261102_0009_turn_rescheduling`. El bundle registró 14 conteos; una transacción posterior al snapshot no se incluyó en el restore. C-15 amplió después el bundle con la evolución y su conteo, y verificó el restore contra `20261102_0010_clinical_history` en `backend/evidence/C-15-verificacion.md`. Estas pruebas no usaron la instancia PostgreSQL del puerto 5432. Docker/PG16 no se validaron y quedan fuera del alcance acordado.

## C-15 — Historia clínica mínima (demo ficticia)

C-15 separa las evoluciones de la ficha básica del paciente. En SQLite el esquema pasa a versión 9; en PostgreSQL la revisión Alembic es `20261102_0010_clinical_history`. La migración es aditiva y el inicio de FastAPI no la ejecuta. El backup C-12 incluye la tabla y su recuento, pero nunca el contenido de las notas en el manifiesto.

La API expone `GET /pacientes/{paciente_id}/historia`, `POST /pacientes/{paciente_id}/evoluciones` y `POST /evoluciones/{evolucion_id}/correcciones`. Sólo un Profesional activo con cuenta vigente vinculada puede consultar o agregar evoluciones de un paciente si tiene un turno propio en estado `atendido`. Recepción y Administrador no reciben contenido clínico. Las notas son texto narrativo de 1 a 5000 caracteres; no hay diagnóstico estructurado, recetas, adjuntos ni odontograma. Una corrección crea otra evolución que referencia la original; no se editan ni borran evoluciones. Las lecturas y escrituras producen auditoría de metadatos sin nombres ni contenido clínico y fallan cerradas si no se puede registrar.

Usar únicamente pacientes, cuentas y turnos ficticios de la suite o del demo local. Esta función no admite datos reales y no constituye preparación para uso clínico o productivo. No hay purga automática. El respaldo conserva la tabla y relaciones al restaurar SQLite en un archivo destino nuevo. Las pruebas PostgreSQL de C-15/C-16 verifican bundle y restore real en un cluster local de prueba, sin demostrar recuperación humana o producción.

Para ejecutar localmente en Windows, desde `backend/`, con el entorno ya instalado y `.env.example` ajustado sólo para datos de demostración:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_clinical_history*.py'
.\.venv\Scripts\python.exe -m uvicorn odontologia.api:crear_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

La suite clínica usa bases temporales y datos sintéticos. En el entorno de esta verificación no estaban disponibles `initdb`, `pg_ctl` ni `psql`: PostgreSQL se comprobó con pruebas estructurales y generación de SQL Alembic offline, no mediante migración contra un servidor. No se requieren Docker, Redis, servicios externos ni una instancia PostgreSQL para mostrar la demo SQLite.

## C-16 — Odontograma y plan manual (demo ficticia)

C-16 agrega de forma aditiva el odontograma versionado y los planes manuales. La versión vigente de SQLite pasa a `auth_schema_version=10`; PostgreSQL usa Alembic `20261102_0011_odontogram_treatment_plans`, encadenada a `20261102_0010_clinical_history`. Las migraciones son explícitas: iniciar o importar FastAPI no cambia el esquema. Ejecutar la suite de migración SQLite sobre una base sintética C-15 comprueba el upgrade v9→v10:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_odontograma_migracion.py' -v
```

Para PostgreSQL, se requiere servidor y cliente Alembic compatibles, `DATABASE_URL` configurada localmente y privilegios para aplicar las migraciones. Primero revisar que `ODONTOLOGIA_PERSISTENCIA=postgresql` y que `DATABASE_URL` apunte al entorno deseado; después ejecutar desde `backend/`:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
```

La migración añade tablas para snapshots, hallazgos, planes y etapas, con FK restrictivas, límites de códigos/estados y triggers append-only para versiones, hallazgos y etapas. No se cambia la ficha de paciente ni se enlazan automáticamente planes a turnos o precios. Una reversión automática no está disponible porque podría destruir el historial.

La prueba PostgreSQL C-16 aplicada desde Alembic 0010 hasta `head` se ejecutó en un cluster temporal local PostgreSQL 18 sobre `127.0.0.1:55432`, con base sintética `odontologia_c16_test`. El puerto `5432` no se usó. El detalle de comandos, resultados y límites está en `backend/evidence/C-16-verificacion.md`. No se requieren Docker ni Redis para iniciar o mostrar la demo SQLite.

La API clínica local permite al Profesional autenticado consultar `GET /pacientes/{paciente_id}/odontograma` y registrar una nueva versión completa con `POST /pacientes/{paciente_id}/odontograma`. El backend comprueba en cada solicitud la cuenta profesional activa y vinculada y la existencia de una atención propia `atendido`; Administrador y Recepción reciben denegación genérica. La UI no sustituye estas reglas de autorización.

Para elegir la ficha sin ampliar el contrato archivado de agenda de C-08, la UI consulta `GET /profesional/atenciones-atendidas?limit=25&offset=0`. El backend toma el Profesional de la sesión y devuelve sólo `turno_id`, `paciente_id`, `paciente_nombre`, `inicio` y `fin` para atenciones `atendido` propias; no expone teléfono ni acepta un profesional indicado por el cliente. La respuesta se pagina y se audita sin identificadores de paciente. La UI sólo realiza consultas clínicas después de seleccionar una atención; la API valida rol y atención nuevamente.

Ejemplo sintético de alta (incluye el estado completo que se desea guardar; una lista vacía registra una versión sin hallazgos):

```json
{
  "hallazgos": [
    {
      "pieza_fdi": "11",
      "superficies": ["M", "V"],
      "observacion": "Observación sintética de ejemplo."
    }
  ]
}
```

La respuesta incluye id, número de versión generado, profesional, fecha y hallazgos. La consulta devuelve `items` en orden histórico y `version_vigente`; si la versión no contiene hallazgos, se presenta literalmente como “sin registros de hallazgo”. Cada alta crea una versión append-only, incluso si reemplaza el contenido visible; no existe operación de editar o borrar versiones. Se rechazan con 422 los códigos inválidos, superficies repetidas o incompatibles, observaciones mayores a 500 caracteres y campos adicionales. Los ejemplos y pruebas usan sólo datos ficticios; no se registran diagnósticos, nombres ni recomendaciones.

Los planes manuales usan las prestaciones activas existentes; no amplían el catálogo ni agregan importes o turnos. El Profesional autorizado puede consultar `GET /pacientes/{paciente_id}/planes`, crear con `POST /pacientes/{paciente_id}/planes` y cambiar estado con `PATCH /planes/{plan_id}/estado`.

Ejemplo de creación sintético:

```json
{
  "prestaciones_ids": ["prestacion-sintetica-A", "prestacion-sintetica-B"]
}
```

El alta devuelve etapas en el orden enviado y comienza en `propuesto`. Las únicas transiciones son `propuesto → en_curso`, `propuesto → cancelado`, `en_curso → completado` y `en_curso → cancelado`; estados terminales o transiciones inválidas responden 409 y mantienen el estado previo. La respuesta contiene identificadores de prestaciones, pero no precios, diagnósticos, turnos ni datos de consentimiento. Recepción y Administrador no reciben contenido clínico.


El backup C-16 admite sólo SQLite v10 y PostgreSQL 0011. Incluye recuentos de snapshots, hallazgos, planes y etapas; el manifiesto no incluye observaciones, nombres ni valores de prestaciones. La prueba focal SQLite crea un bundle y restaura a un archivo nuevo, valida filas y recuentos y comprueba que origen/bundle no cambian. La integración PostgreSQL ejecuta pg_dump/pg_restore en la base sintética local, restaura a una base destino nueva terminada en _test y valida datos y todos los recuentos. El restore rechaza la base activa; no se hizo backup ni restore de datos reales.

## C-18 — Portal de autoservicio del paciente sintético

El esquema vigente es SQLite v12 o PostgreSQL Alembic `20261102_0013_patient_self_service`. La migración agrega `usuarios.paciente_id` único, las acciones metadata-only del portal y `idempotencia_portal_paciente`; el upgrade conserva sesiones, cuentas, turnos y eventos anteriores. La tabla de claves viaja en backup/restore y el manifiesto sólo informa conteos agregados.

El alta de la cuenta es local y exclusiva de Administrador. No existe autorregistro, invitación, activación por email/SMS, proveedor externo ni canal de comunicación. En una base de demostración, crear primero una ficha sintética mediante `POST /pacientes` y luego vincularla con `POST /usuarios`:

```json
POST /pacientes
{
  "nombre": "Paciente de demostración",
  "telefono": null,
  "acepta_recordatorios": false
}
```

Usar el `id` ficticio devuelto para `POST /usuarios`, autenticado como Administrador:

```json
{
  "identificador": "paciente.demo",
  "password": "una-frase-local-de-demostración",
  "rol": "paciente",
  "paciente_id": "<id-de-la-ficha-sintética>"
}
```

La API no devuelve el hash ni vuelve a mostrar la contraseña. El token de sesión deriva `paciente_id` del vínculo vigente; ninguna reserva acepta ese identificador en el cuerpo. Recepción y Administrador no ven el contenido del portal.

| Ruta | Uso |
|---|---|
| `GET /portal/disponibilidad?fecha=YYYY-MM-DD` | Franjas opacas de 30 minutos, sólo `inicio`/`fin`, hasta 31 días locales. |
| `GET /mis-turnos` | Turnos propios con identificador, inicio/fin, estado y versión; sin ficha, clínica o agenda identificada. |
| `POST /mis-turnos` | Reserva con `{ "inicio": "...ISO 8601 con offset..." }` y header `Idempotency-Key`. El servidor asigna recursos. |
| `POST /mis-turnos/{turno_id}/cancelacion` | Cancela un turno propio `reservado`/`confirmado` con 24 horas o más de anticipación; requiere clave. |
| `POST /mis-turnos/{turno_id}/reprogramacion` | Recibe sólo `{ "version": n, "inicio": "..." }` y clave; conserva paciente/estado/duración y revalida en transacción. |

Las claves se guardan por paciente+operación; mismo payload devuelve el resultado original y payload diferente da 409. El replay confirmado se resuelve después de verificar sesión y titularidad y antes de volver a validar vigencia/horizonte (o versión vigente sólo necesaria para una operación nueva). Ante timeout ambiguo, el cliente conserva y reusa la misma clave para la misma operación, objetivo y payload; cambia payload/objetivo/operación, cambia la clave y la descarta sólo cuando la operación y actualización de vista concluyen con éxito. El paciente puede tener como máximo tres turnos futuros activos. Los horarios se interpretan en `America/Argentina/Mendoza`; la duración de 30 minutos es una regla limitada a esta demostración, no la duración general de prestaciones. Lecturas y mutaciones registran únicamente actor/acción/recurso opaco/resultado. Si falla la auditoría se niegan lecturas o se revierte la mutación.

La UI muestra el portal sólo a `paciente`; el resto de roles conserva sus vistas. Use exclusivamente datos, identidades y credenciales ficticias. No es un sistema productivo ni está preparado para usar con pacientes reales.

Las pruebas de dominio/API se ejecutan desde `backend/` con:

```powershell
..\.venv\Scripts\python.exe -m unittest tests.test_portal_paciente tests.test_api_portal_paciente -v
```

Las integraciones PostgreSQL C-18 usan únicamente un cluster local de pruebas en `127.0.0.1:55432`, base `*_test`, schema temporal y fixtures sintéticos. Para backup/restore real se necesita `pg_dump`/`pg_restore` de la misma major que el servidor. No usar la base del puerto 5432 ni datos reales. Las evidencias separan migración, pruebas, restore y límites del host.

## C-19 — Ledger financiero sintético

La API ofrece cuenta corriente, cargos manuales, cobros y reversiones para datos de demostración. Administrador y Recepción pueden consultar cargos/movimientos, crear cargos y registrar cobros; sólo Administrador revierte un cobro. Profesional y Paciente reciben 403. El cargo requiere paciente activo, concepto de 1–200 caracteres e importe decimal en texto. Los cobros y reversiones también requieren importes positivos en texto; la reversión lleva motivo de 1–500 caracteres. Cada operación se limita a ARS 999.999.999,99; no se admiten float, coma decimal, signo, exponente, agrupadores ni más de dos decimales. El backend convierte a centavos enteros y deriva el saldo del ledger; un cobro superior al saldo o una reversión mayor al neto del cobro da 409.

| Ruta | Acción |
|---|---|
| `GET /finanzas/pacientes/{paciente_id}` | Movimientos ordenados de manera estable y saldo calculado en backend. |
| `POST /finanzas/pacientes/{paciente_id}/cargos` | Cargo manual con `{ "monto_ars": "1250.50", "concepto": "Control" }`. |
| `POST /finanzas/cargos/{cargo_id}/cobros` | Cobro parcial/total con `{ "monto_ars": "100.00" }`. |
| `POST /finanzas/cobros/{cobro_id}/reversiones` | Reversión de Administrador con `{ "monto_ars": "50.00", "motivo": "Corrección" }`. |

Los tres comandos POST requieren `Idempotency-Key` (1–128 caracteres), persistida por actor y operación. Mismo payload devuelve la respuesta original antes de revalidar el saldo; payload diferente con la misma clave da 409. El bloqueo usa `BEGIN IMMEDIATE` en SQLite y `agenda_mutex` en PostgreSQL. Movimiento, resultado idempotente y evento metadata-only se escriben en una transacción; fallo de auditoría revierte todo. Los movimientos financieros son append-only y usan referencias restrictivas. Concepto y motivo son visibles sólo en la cuenta autorizada y no se incluyen en auditoría ni manifiestos.

SQLite sube de v12 a v13 y PostgreSQL incorpora Alembic `20261102_0014_financial_ledger` después de C-18. Backup/restore incluye cargos, cobros, reversiones e idempotencia; el manifiesto sólo incluye conteos agregados. C-19 no genera cargos desde turnos/prestaciones/planes y no integra proveedor de pago, banco, ARCA ni comprobantes fiscales. Usar sólo datos sintéticos; esta demostración no está preparada para uso productivo.

Validación registrada en [evidencia C-19](evidence/C-19-verificacion.md). Suites completas: backend **562 tests OK, 3 skips del host**, frontend **69 tests OK**, build TypeScript/Vite OK. Las integraciones C-19 PostgreSQL usan schema efímero en loopback `127.0.0.1:55432`, base `*_test`, y `pg_dump`/`pg_restore` 18; no se usa el puerto 5432 ni Docker.
