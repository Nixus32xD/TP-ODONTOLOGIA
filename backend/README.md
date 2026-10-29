# Backend — TP-ODONTOLOGIA

API del sistema odontológico. Stack definido por la cátedra (corrección del 2026-10-29):
**Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis y Docker / Docker Compose.**

## Estado

| Pieza | Estado | Change |
| --- | --- | --- |
| Alta de turnos sin solapamientos (`POST /turnos`, `GET /health`) | Implementado, 53 tests, archivado | C-01 |
| Persistencia en SQLite local (`ODONTOLOGIA_DB`) | Vigente para C-01 | C-01 |
| PostgreSQL + SQLAlchemy (`odontologia/db/`) | Estructura preparada, sin implementar | C-02 |
| Autenticación JWT (`odontologia/auth/`) | Estructura preparada, sin implementar | C-03 |
| Cola de recordatorios en Redis (`odontologia/workers/`) | Estructura preparada, sin implementar | C-17 |
| Imagen Docker y servicios en Docker Compose | Preparados | C-02 / C-14 |

C-01 se conserva tal como fue archivado: sólo se movió a esta carpeta. Migrarlo a PostgreSQL exige proponer C-02 y volver a demostrar la exclusión concurrente.

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
├── tests/               # 53 tests de C-01
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
