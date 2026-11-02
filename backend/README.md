# Backend — TP-ODONTOLOGIA

API del sistema odontológico. Stack definido por la cátedra (corrección del 2026-10-29):
**Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis y Docker / Docker Compose.**

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
| Cola de recordatorios en Redis (`odontologia/workers/`) | Estructura preparada, sin implementar | C-17 |
| Imagen Docker y servicios en Docker Compose | Preparados | C-02 / C-14 |

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
│   └── workers/         # Redis: recordatorios en cola (C-17)
├── alembic/             # Revisiones versionadas de C-02 a C-10
├── tests/               # Regresión C-01 a C-10
├── requirements.txt         # Dependencias directas de C-01
├── requirements-dev.txt     # + HTTPX para tests
├── requirements-lock.txt    # Entorno verificado de C-01
├── requirements-stack.txt   # + SQLAlchemy, psycopg, PyJWT y redis
├── Dockerfile
├── docker-entrypoint.sh
└── .env.example
```

## Ejecutar sin Docker (Windows, desde `backend/`)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt -r requirements-stack.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m odontologia.demo
```

Para levantar la API ver el README principal. Con Docker, usar `docker compose up --build` desde la raíz.

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

Alembic aplica las revisiones consecutivas hasta C-10 (`20261102_0009_turn_rescheduling`), incluida la ficha mínima, catálogos, auditoría, disponibilidad, estados, vínculo de cuenta Profesional y versión de turnos. En Docker Compose, migrar el servicio backend con `docker compose exec backend python -m alembic upgrade head` y ejecutar el bootstrap interactivo con `docker compose exec backend python -m odontologia.auth.bootstrap_admin` después de configurar `.env`. No usar la API ni `GET /health` como comando de migración.

`POST /sesiones` recibe `identificador` y `password`; su respuesta contiene `access_token`, `token_type` y `expires_in`. En Swagger, usar **Authorize** con `Bearer <token>`. `/sesiones/actual` permite consultar y cerrar la sesión propia. El Administrador puede consultar/crear usuarios y cambiar rol/estado; Recepción puede crear turnos y operar fichas mínimas de pacientes; sólo Administrador cambia el estado activo de pacientes. Desactivar una cuenta, cambiarle el rol o cerrar sesión revoca sus tokens persistidos. Los fallos de credenciales devuelven un mensaje genérico. Las fichas contienen sólo nombre y teléfono opcional ficticios; no usar datos reales ni añadir historia clínica. Los eventos guardan sólo actor/acción/recurso/resultado/fecha; no incluyen cuerpos, nombres, teléfonos, contraseñas, hashes, JWT, datos clínicos ni el identificador de un login rechazado. `GET /auditoria?limit=50&offset=0` es sólo Administrador, admite límite 1–100 y no ofrece edición, borrado ni purga automática. Si el evento falla, la mutación se revierte y la API no informa éxito. Sin secreto o esquema migrado, las operaciones protegidas fallan cerradas con 503 mientras `/health` continúa pública.

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

Para habilitar PostgreSQL en la API después de migrar, mantener `ODONTOLOGIA_PERSISTENCIA=postgresql` y `DATABASE_URL` en el entorno del proceso y levantar Uvicorn como se indica en el README principal. En Docker, la URL debe apuntar al servicio `db` desde la red Compose; no copiar una URL local de pruebas a producción.

La suite completa incluye pruebas PostgreSQL de migración, rollback y concurrencia multiproceso. Para ejecutarlas se requiere una base de prueba dedicada cuyo nombre sea `test` o termine en `_test`, host loopback y puerto distinto de 5432:

```powershell
$env:ODONTOLOGIA_TEST_DATABASE_URL = 'postgresql+psycopg://usuario:clave@127.0.0.1:PUERTO/odontologia_test'
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Si la variable no está definida, las pruebas PostgreSQL se omiten; esa ejecución no verifica PostgreSQL.

## Copias locales de agenda (C-12)

El bundle de backup es un directorio nuevo con el payload completo (`agenda.sqlite3` o `agenda.dump`) y `manifest.json`. El manifiesto v1 incluye `created_at_utc` (ISO 8601 en UTC), `backend`, `application_version`, `schema_version`, `payload_name`, `payload_size_bytes`, `payload_sha256` (SHA-256 hexadecimal) y `table_counts` (nombre de cada tabla vigente y cantidad de filas como entero no negativo). Los conteos son agregados y no incluyen valores ni identificadores de filas. La versión del backend se define en `odontologia.version`; el esquema aceptado actualmente es SQLite `8` o PostgreSQL `20261102_0009_turn_rescheduling`. El hash detecta corrupción/cambios accidentales del payload, no autentica el manifiesto si un atacante reemplaza ambos; los conteos no prometen confidencialidad. El manifiesto no guarda URL, ruta de origen, credenciales ni datos personales.

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

Antes de copiar, la base debe declarar `auth_schema_version=8`, incluir `turnos.version`, superar `PRAGMA integrity_check` y no tener filas en `PRAGMA foreign_key_check`. No se migra ni repara el origen. El bundle se prepara en un directorio temporal exclusivo dentro del mismo padre y sólo se publica en un destino que todavía no existe; si la copia falla se elimina ese staging y se conserva intacto cualquier destino previo. La comprobación puede rechazar bases C-01 standalone sin migrar, archivos ausentes/corruptos o una revisión incompatible.

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

Para PostgreSQL, seleccionar el motor ya configurado y pasar un nombre de base nuevo (no una URL ni un path). El usuario de conexión necesita `CREATEDB` y permiso para conectarse a `postgres`. El adapter consulta primero que el destino no exista, crea una base temporal aleatoria, ejecuta `pg_restore --exit-on-error`, compara revision, constraints y los 14 recuentos contra el manifiesto, cierra sólo las conexiones que abrió y renombra el staging únicamente si el nombre final sigue libre. En cualquier error limpia sólo la base temporal propia; no termina conexiones ajenas ni borra una base existente. Los nombres se restringen a minúsculas, dígitos y guion bajo (máximo 63 caracteres).

```powershell
$env:ODONTOLOGIA_PERSISTENCIA = 'postgresql'
$env:DATABASE_URL = 'postgresql+psycopg://usuario:clave@127.0.0.1:55432/odontologia_test'
..\.venv\Scripts\python.exe -m odontologia.backup restaurar `
  'N:\copias\agenda-postgresql-2026-11-02' 'agenda_recuperada'
```

El destino pertenece al cluster configurado por `DATABASE_URL`, y debe estar ausente. La integración del adapter se validó en el cluster efímero PG18.6 local, restauró a una base nueva con revisión y conteos iguales al manifiesto, abrió otra conexión e insertó un paciente ficticio. El build PG16 sigue pendiente al no haber Docker en el host; una prueba con cliente/servidor 18.6 no demuestra el paquete de imagen PG16.

Para PostgreSQL, el adapter requiere `pg_dump` y `pg_restore` disponibles en `PATH`; ambos deben tener la misma major que el servidor (por ejemplo, clientes 16 con servidor 16). La detección consulta `--version` con argumentos fijos y sin shell; la URL y sus credenciales no se pasan en la línea de comandos ni se imprimen. La imagen backend instala únicamente `postgresql-client-16` desde el repositorio PGDG y comprueba ambas versiones durante el build; no instala un servidor. En un host local, el administrador debe instalar los clientes de la misma major que el servidor. Adapter disponible e instalación de herramientas son capas distintas: el adapter valida ejecutables presentes, pero no instala ni actualiza clientes en el host.

Al seleccionar PostgreSQL, `crear` toma el motor y la conexión ya configurados en `DATABASE_URL`, consulta la revisión Alembic y genera `agenda.dump` con `pg_dump --format=custom`. En una transacción `REPEATABLE READ` cuenta las tablas y exporta un snapshot MVCC; mantiene esa transacción abierta mientras `pg_dump --snapshot=<id>` importa el mismo snapshot. Así, las filas confirmadas mientras corre el dump no alteran ni el payload ni sus recuentos. La contraseña viaja por `PGPASSWORD` en el entorno mínimo del proceso; los argumentos son fijos y no incluyen URL ni contraseña. Antes de declarar el bundle, `pg_restore --list` debe reconocer el archivo y se vuelve a comprobar el manifiesto/hash. Este paso comprueba estructura del archivo, no efectúa una restauración de ensayo.

```powershell
$env:ODONTOLOGIA_PERSISTENCIA = 'postgresql'
$env:DATABASE_URL = 'postgresql+psycopg://usuario:clave@127.0.0.1:55432/odontologia_test'
..\.venv\Scripts\python.exe -m odontologia.backup crear 'N:\copias\agenda-postgresql-2026-11-02'
```

El proceso espera PostgreSQL en la revisión `20261102_0009_turn_rescheduling`, servidor/clientes de la misma major y un destino nuevo. La contraseña de ejemplo se reemplaza sólo en el entorno local; no guardarla en documentos ni en el manifiesto. Sin PostgreSQL local de prueba compatible, no ejecutar esta orden contra una agenda real.

La creación prepara y valida payload y manifiesto en un directorio privado del mismo volumen y publica el directorio completo con una operación atómica que no reemplaza destinos. En Windows usa `os.rename`; en Linux exige `renameat2(RENAME_NOREPLACE)` y falla cerrado si no está disponible. Una colisión que aparezca durante la publicación, incluso un directorio POSIX vacío, se conserva sin cambios; una excepción previa deja el destino final ausente y limpia sólo el staging propio. El staging, payload y manifiesto mantienen permisos POSIX `0700`/`0600`; Windows conserva ACL heredadas. La copia contiene datos sensibles y debe guardarse fuera del repositorio.

La integración de backup se ejecutó con un cluster temporal PostgreSQL 18.6 en `127.0.0.1:55432`, cliente 18.6 y la base ficticia `odontologia_test`, migrada hasta `20261102_0009_turn_rescheduling`. El comando anterior creó un dump custom de 37.173 bytes; `pg_restore --list` detectó 80 entradas y el manifiesto registró hash y 14 conteos. En una prueba, otra transacción confirmó un paciente después de exportar el snapshot y antes de invocar `pg_dump`; al restaurar el dump en una base aislada, sus 14 conteos coincidieron exactamente con `table_counts` y esa fila posterior al snapshot no estaba incluida. También se confirmó la retención de filas y auditoría ficticias. Este ensayo no usó la instancia del usuario en 5432. La prueba de build de la imagen PostgreSQL 16 queda pendiente porque Docker no está instalado en este host; esta ejecución PG18 valida el adapter con major compatible, no el cliente instalado en la imagen ni el runtime PG16.
