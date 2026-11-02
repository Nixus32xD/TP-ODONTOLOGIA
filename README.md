# TP - Gestión de turnos odontológicos

Entrega propia de Metodología I: investigar y desarrollar una funcionalidad de agenda y turnos de pacientes para consultorios odontológicos del mercado argentino, usando Active Stack, OpenSpec y el ciclo OPSX.

Repositorio: [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).

## Estado actual

OpenSpec inicializado y Discovery documental confirmado: quince sistemas relevados, matriz ponderada y once puntos aceptados el 2026-10-15 para un consultorio pequeño. C-01 crea turnos sin solapamientos y fue archivado el 2026-10-28. C-02 agrega PostgreSQL + SQLAlchemy, migraciones Alembic y una importación explícita desde SQLite; su implementación se validó en una instancia de prueba local aislada y permanece activa en OpenSpec, pendiente de Archive. La investigación documental está asistida por IA; confirmé mi revisión personal de las seis fuentes del registro el 2026-10-15. El cierre técnico no acredita por sí solo aceptación docente.

Se ejecutó `openspec init --tools codex --language es --no-animation`: configuración `spec-driven` y seis skills OPSX. Se incorporó `discovery-research` sólo en este proyecto. El estado de Active Stack conserva `version: 4` y registra `step: agents`: Discovery está registrado y la [base de conocimiento](knowledge-base/README.md) contiene diez documentos canónicos más su índice, generados desde las fuentes existentes. El usuario autorizó continuar con Apply sobre la propuesta: FastAPI, Python 3.12+, SQLite y unittest. El campo step registra la última fase de fundación; el CLI de OpenSpec registra el progreso del change.

Para consultar el estado desde PowerShell con OpenSpec disponible en PATH:

```powershell
Set-Location -LiteralPath 'N:\Nueva carpeta\TP-ODONTOLOGIA'
openspec list --json
```

OpenSpec conserva `crear-turno-sin-solapamientos` archivado, con 18/18 tareas completas. C-02 está activo y sus diez tareas de implementación se completaron; sus artefactos de planificación aún no se archivaron. La [spec principal](openspec/specs/alta-turnos/spec.md) contiene el contrato C-01. El [roadmap](CHANGES.md) planifica 20 changes en seis fases para el producto futuro; C-01 está archivado y C-02 está implementado y validado localmente. C-03 a C-20 siguen planificados. El [cierre técnico C-01](docs/evidencia/implementacion-turnos.md) y la [evidencia C-02](docs/evidencia/implementacion-turnos.md#c-02) distinguen pruebas, revisión humana y aceptación docente. La revisión humana de la base de conocimiento y del roadmap sigue pendiente. La [selección de skills](docs/fundacion/seleccion-skills.md), el [registro](.atl/skill-registry.md) y las reglas de [AGENTS.md](AGENTS.md) y [CLAUDE.md](CLAUDE.md) conservan las decisiones del proyecto.

Esta entrega comienza desde cero. El alcance inicial es una funcionalidad terminada de agenda, con datos ficticios y sin integraciones clínicas reales.

## Stack tecnológico y estructura

Por corrección de la cátedra (2026-10-29), el sistema se trabaja con este stack:

| Parte | Tecnologías | Carpeta |
| --- | --- | --- |
| Backend | Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis, Docker / Docker Compose | [`backend/`](backend/README.md) |
| Frontend | React, TypeScript, Vite | [`frontend/`](frontend/README.md) |

```text
TP-ODONTOLOGIA/
├── backend/            # API FastAPI: C-01 (alta de turnos) + estructura de db/, auth/ y workers/
├── frontend/           # React + TypeScript + Vite
├── docker-compose.yml  # db (PostgreSQL), redis, backend y frontend
├── openspec/           # specs vigentes y changes archivados
├── knowledge-base/     # base de conocimiento (10 archivos)
├── docs/               # Discovery, bitácora, evidencia y consigna
├── CHANGES.md          # roadmap de 20 changes
└── AGENTS.md / CLAUDE.md
```

**Qué está implementado y qué es estructura:** C-01 sigue disponible sobre SQLite, que conserva el valor predeterminado. C-02 agrega un backend PostgreSQL optativo, migración Alembic y CLI de importación no destructiva; se probó contra una instancia local temporal en el puerto 55432, sin tocar la base preexistente de 5432. JWT (C-03), la interfaz de recepción en React (C-11), la cola de recordatorios en Redis (C-17) y el despliegue con Docker (C-14) siguen planificados. Ver la [bitácora C-02](docs/BITACORA.md#2026-11-01--c-02-postgresql-y-migración-explícita) y su [evidencia](docs/evidencia/implementacion-turnos.md#c-02).

## Recorrido de la entrega

0. Preparar el entorno y registrar evidencia real.
1. Iniciar la fundación con Active Stack y OpenSpec.
2. Investigar el mercado y verificar fuentes del Discovery.
3. Generar y revisar la base de conocimiento.
4. Generar y revisar el roadmap.
5. Elegir skills y revisar las reglas del agente.
6. Completar un change: Explore, Propose, Apply, Verify y Archive.
7. Demostrar memoria y recuperación de contexto con Engram.

El usuario autorizó commits locales separados por petición completada, validación previa y cambios no relacionados separados. El registro de skills quedó publicado en `main` en `197be16a2eed4b8ea0c0dbcfcfa4cd601a38d59c`. El usuario autorizó el push de los commits pendientes: AGENTS/CLAUDE y Propose se publicaron hasta 509307025550d183493b5a56fa2d16fd18d0651f. El usuario autorizó commit y push del avance actual tras corregir el stack a FastAPI, siempre limitado a C-01. La entrega docente final sigue pendiente. Este permiso no constituye autorización universal para publicaciones futuras. Las revisiones humanas se documentan cuando ocurren.

## Documentación

- [Consigna y checklist de entregables](docs/CONSIGNA.md).
- [Bitácora del proceso](docs/BITACORA.md).
- [Inventario y pendientes del entorno](docs/evidencia/entorno.md).
- [Informe Discovery](docs/discovery/informe-discovery.md) y [PDF](docs/discovery/informe-discovery.pdf).
- [Discovery canónico](discovery/discovery.md) y [once puntos confirmados](docs/discovery/resumen-para-revision.md).
- [Base de conocimiento: índice y diez documentos](knowledge-base/README.md).
- [Roadmap completo del producto](CHANGES.md).
- [Comprobaciones documentales y revisión personal confirmada](docs/discovery/verificacion-fuentes.md).
- [Nueva revisión documental delegada: seis fuentes y motivos de ajuste](docs/discovery/revision-documental-2026-10-15.md).
- [Selección y justificación de skills](docs/fundacion/seleccion-skills.md).
- [Registro de skills del proyecto](.atl/skill-registry.md).
- [Instrucciones para agentes](AGENTS.md) y [versión equivalente para Claude](CLAUDE.md).
- [Exploración técnica](docs/exploracion/alta-turno.md), [propuesta](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/proposal.md), [spec](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/specs/alta-turnos/spec.md) y [tareas](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/tasks.md).

## Regenerar el informe PDF

Con Python 3, `reportlab`, `pypdf` y las fuentes Arial de Windows disponibles:

```powershell
python tools/render_discovery.py
```

El comando consolida tablas, calcula los totales y genera el PDF y `matriz-evidencia.json` desde las fichas. No consulta servicios externos ni modifica el estado de Active Stack. La revisión personal de las seis fuentes fue confirmada por el estudiante el 2026-10-15; se conserva la atribución de los hallazgos a IA.

Todos los ejemplos y pruebas usan datos ficticios, sin secretos ni pacientes reales.


## Ejecutar producto y pruebas

### Con Docker Compose (stack completo)

Requiere Docker Desktop. Desde la raíz:

```powershell
Copy-Item .env.example .env   # completar POSTGRES_PASSWORD y JWT_SECRETO con valores locales
docker compose up --build
```

Levanta PostgreSQL, Redis, el backend en http://127.0.0.1:8000 (Swagger en `/docs`) y el frontend en http://127.0.0.1:5173. El backend prepara una agenda ficticia de C-01 en un volumen propio si todavía no existe.

### Backend sin Docker

Python 3.12+ y entorno virtual local. Desde `backend/`:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt -r requirements-stack.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m odontologia.demo
```

`requirements.txt` fija las dependencias directas de C-01, `requirements-dev.txt` añade HTTPX, `requirements-lock.txt` conserva el entorno verificado de C-01 y `requirements-stack.txt` suma SQLAlchemy, psycopg, Alembic, PyJWT y redis. Python 3.12.14 / SQLite 3.53.1; 89 tests en la suite completa. Con `ODONTOLOGIA_TEST_DATABASE_URL` aislada, 8 pruebas adicionales verifican PostgreSQL. Starlette 1.8.0 emite un aviso de deprecación por HTTPX 0.28.1; las pruebas pasan y el aviso se conserva.

Inicializar una agenda ficticia NUEVA en disco local (no asumir N: local), y luego iniciar la API sólo en loopback, siempre desde `backend/`:

```powershell
$env:ODONTOLOGIA_DB = Join-Path $env:LOCALAPPDATA 'odontologia-c01.sqlite3'
.\.venv\Scripts\python.exe -c "import os; from odontologia import inicializar_agenda; inicializar_agenda(os.environ['ODONTOLOGIA_DB'])"
.\.venv\Scripts\python.exe -m uvicorn odontologia.api:crear_app --factory --host 127.0.0.1 --port 8000
```

### Frontend sin Docker

Node 20+. Desde `frontend/`: `npm install` y `npm run dev` (http://localhost:5173, con el backend en el puerto 8000).

Bootstrap rechaza archivos existentes sin sobrescribirlos. Para reutilizar agenda ya preparada, omitir inicialización. Detener servidor con Ctrl+C. Crear app/importar no crea DB. No ejecutar bootstrap sobre agendas ajenas ni borrar archivos para repetir.

GET http://127.0.0.1:8000/health devuelve liveness, no estado de DB. OpenAPI en /openapi.json; Swagger en /docs y ReDoc en /redoc. Las páginas interactivas usan recursos CDN de FastAPI y pueden requerir Internet para cargarlos; OpenAPI es completamente local.

POST /turnos recibe:

```json
{"paciente_id":"paciente-A","profesional_id":"profesional-A","box_id":"box-A","inicio":"2026-10-15T09:00:00-03:00","fin":"2026-10-15T09:30:00-03:00"}
```

Devuelve201 con id y fechas UTC después del commit. Errores JSON codigo/campo/mensaje:422 entrada inválida,404 recurso desconocido,409 conflicto,503 contención y500 almacenamiento. Campos adicionales, IDs no string, epoch numérico, fechas sin offset o precisión distinta de minutos se rechazan. El dominio valida IDs conocidos e inicio anterior a fin, sin corrección silenciosa.

Catálogos ficticios paciente-A/B, profesional-A/B y box-A/B. Intervalos [inicio,fin), adyacencia permitida; prioridad del profesional si ambos conflictos existen. Timeout5s configurable en crear_app, no expuesto en JSON. Garantía sólo mismo archivo SQLite local y escritores del módulo, sin red compartida ni SQL externo. Sin autenticación, UI clínica, cancelación, horarios, exclusión de paciente ni idempotencia; no apto para pacientes reales ni despliegue público.

La demo conserva dos registros en su temporal y lo elimina al terminar. [Evidencia y trazabilidad](docs/evidencia/implementacion-turnos.md). Archive quedó confirmado el 2026-10-28; la revisión personal de fuentes ya estaba confirmada. Las evidencias y la aceptación de la entrega académica tienen su propio registro y no se deducen de este cierre técnico.
