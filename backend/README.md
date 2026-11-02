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
| Auditoría append-only y `GET /auditoria` | Implementado/validado en SQLite y PostgreSQL; sólo Administrador; Archive pendiente | C-04 |
| Cola de recordatorios en Redis (`odontologia/workers/`) | Estructura preparada, sin implementar | C-17 |
| Imagen Docker y servicios en Docker Compose | Preparados | C-02 / C-14 |

C-01 y SQLite siguen disponibles. C-02 permite elegir PostgreSQL de forma explícita, versiona el esquema con Alembic y ofrece una importación manual desde SQLite; está archivado. C-03 agrega acceso con JWT, sesiones revocables y permisos de Administrador/Recepción; está archivado. C-04 registra metadatos de turnos, cuentas y sesiones en la misma transacción; los fallos de auditoría revierten la mutación. Profesional no tiene cuenta habilitada hasta C-08. El inicio de la API no ejecuta migraciones ni importa datos. La fuente SQLite no se altera; la importación rechaza fuentes con solapamientos o destinos ya poblados.

## Estructura

```text
backend/
├── odontologia/
│   ├── agenda.py        # Dominio de C-01: validación, transacción y alta
│   ├── api.py           # Adaptador FastAPI de C-01/C-03/C-04
│   ├── demo.py          # Demo por consola con agenda temporal
│   ├── core/config.py   # Variables de entorno del stack
│   ├── db/              # SQLAlchemy + PostgreSQL (C-02/C-04)
│   ├── auth/            # JWT (C-03)
│   ├── audit.py         # Metadatos append-only y consulta segura (C-04)
│   └── workers/         # Redis: recordatorios en cola (C-17)
├── alembic/             # Revisiones versionadas de C-02, C-03 y C-04
├── tests/               # Regresión C-01 a C-04
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

Alembic aplica las revisiones consecutivas de C-01 a C-04, incluida la tabla append-only de auditoría. En Docker Compose, migrar el servicio backend con `docker compose exec backend python -m alembic upgrade head` y ejecutar el bootstrap interactivo con `docker compose exec backend python -m odontologia.auth.bootstrap_admin` después de configurar `.env`. No usar la API ni `GET /health` como comando de migración.

`POST /sesiones` recibe `identificador` y `password`; su respuesta contiene `access_token`, `token_type` y `expires_in`. En Swagger, usar **Authorize** con `Bearer <token>`. `/sesiones/actual` permite consultar y cerrar la sesión propia. El Administrador puede consultar/crear usuarios y cambiar rol/estado; Recepción sólo crea turnos. Desactivar una cuenta, cambiarle el rol o cerrar sesión revoca sus tokens persistidos. Los fallos de credenciales devuelven un mensaje genérico. Los eventos guardan sólo actor/acción/recurso/resultado/fecha; no incluyen cuerpos, contraseñas, hashes, JWT, datos clínicos ni el identificador de un login rechazado. `GET /auditoria?limit=50&offset=0` es sólo Administrador, admite límite 1–100 y no ofrece edición, borrado ni purga automática. Si el evento falla, la mutación se revierte y la API no informa éxito. Sin secreto o esquema migrado, las operaciones protegidas fallan cerradas con 503 mientras `/health` continúa pública.

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
