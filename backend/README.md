# Backend — TP-ODONTOLOGIA

API del sistema odontológico. Stack definido por la cátedra (corrección del 2026-10-29):
**Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis y Docker / Docker Compose.**

## Estado

| Pieza | Estado | Change |
| --- | --- | --- |
| Alta de turnos sin solapamientos (`POST /turnos`, `GET /health`) | Implementado; regresión incluida en 89 tests; archivado | C-01 |
| Persistencia en SQLite local (`ODONTOLOGIA_DB`) | Predeterminada y compatible con C-01 | C-01 |
| PostgreSQL + SQLAlchemy, Alembic y migración explícita | Implementado y validado en PostgreSQL aislado; change activo pendiente de Archive | C-02 |
| Autenticación JWT (`odontologia/auth/`) | Estructura preparada, sin implementar | C-03 |
| Cola de recordatorios en Redis (`odontologia/workers/`) | Estructura preparada, sin implementar | C-17 |
| Imagen Docker y servicios en Docker Compose | Preparados | C-02 / C-14 |

C-01 y SQLite siguen disponibles. C-02 permite elegir PostgreSQL de forma explícita, versiona el esquema con Alembic y ofrece una importación manual desde SQLite. El inicio de la API no ejecuta migraciones ni importa datos. La fuente SQLite no se altera; la importación rechaza fuentes con solapamientos o destinos ya poblados.

## Estructura

```text
backend/
├── odontologia/
│   ├── agenda.py        # Dominio de C-01: validación, transacción y alta
│   ├── api.py           # Adaptador FastAPI de C-01
│   ├── demo.py          # Demo por consola con agenda temporal
│   ├── core/config.py   # Variables de entorno del stack
│   ├── db/              # SQLAlchemy + PostgreSQL (C-02)
│   ├── auth/            # JWT (C-03)
│   └── workers/         # Redis: recordatorios en cola (C-17)
├── alembic/             # Revisiones versionadas de C-02
├── tests/               # Regresión C-01 y pruebas C-02
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
