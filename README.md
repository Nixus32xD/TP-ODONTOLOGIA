# TP - Gestión de turnos odontológicos

Entrega propia de Metodología I: investigar y desarrollar una funcionalidad de agenda y turnos de pacientes para consultorios odontológicos del mercado argentino, usando Active Stack, OpenSpec y el ciclo OPSX.

Repositorio: [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).

## Estado actual

OpenSpec inicializado y Discovery documental confirmado: quince sistemas relevados, matriz ponderada y once puntos aceptados el 2026-10-15 para un consultorio pequeño. C-01 crea turnos sin solapamientos y fue archivado el 2026-10-28. C-02 agrega PostgreSQL + SQLAlchemy, migraciones Alembic e importación explícita desde SQLite; C-03 agrega autenticación JWT y permisos de personal. C-01–C-07 están implementados, validados y archivados localmente. C-07 implementa horarios, excepciones y bloqueos. La investigación documental está asistida por IA; confirmé mi revisión personal de las seis fuentes del registro el 2026-10-15. El cierre técnico no acredita por sí solo aceptación docente.

Se ejecutó `openspec init --tools codex --language es --no-animation`: configuración `spec-driven` y seis skills OPSX. Se incorporó `discovery-research` sólo en este proyecto. El estado de Active Stack conserva `version: 4` y registra `step: agents`: Discovery está registrado y la [base de conocimiento](knowledge-base/README.md) contiene diez documentos canónicos más su índice, generados desde las fuentes existentes. C-01 se implementó con FastAPI, Python 3.12+, SQLite y unittest; C-02 añadió PostgreSQL optativo y C-03 autenticación JWT. El campo step registra la última fase de fundación; el CLI de OpenSpec registra el progreso de cada change.

Para consultar el estado desde PowerShell con OpenSpec disponible en PATH:

```powershell
Set-Location -LiteralPath 'N:\Nueva carpeta\TP-ODONTOLOGIA'
openspec list --json
```

OpenSpec conserva C-01 a C-06 archivados, con cambios técnicos validados localmente. C-06 incorpora administración de catálogos; C-07 configura disponibilidad de recursos. El change [configurar-horarios-y-bloqueos](openspec/changes/configurar-horarios-y-bloqueos/) sigue activo hasta Archive. La [spec principal](openspec/specs/alta-turnos/spec.md) conserva el contrato C-01; C-07 documenta su aplicación tras migrar a SQLite v5 o PostgreSQL 0006. El [roadmap](CHANGES.md) describe el alcance completo del producto; C-08 a C-20 siguen planificados con contratos propios. La [evidencia técnica](docs/evidencia/implementacion-turnos.md), la [evidencia C-06](docs/evidencia/implementacion-catalogos.md) y la [evidencia C-07](docs/evidencia/implementacion-disponibilidad.md) distinguen pruebas, revisión humana y aceptación docente. La [selección de skills](docs/fundacion/seleccion-skills.md), el [registro](.atl/skill-registry.md) y las reglas de [AGENTS.md](AGENTS.md) y [CLAUDE.md](CLAUDE.md) conservan las decisiones del proyecto.

El proyecto comenzó desde cero con C-01 como primer cambio funcional de agenda. C-02 y C-03 amplían esa base; los changes posteriores siguen sujetos a su propio contrato, autorización y verificación. El desarrollo usa datos ficticios y no integra servicios clínicos reales.

## Stack tecnológico y estructura

Por corrección de la cátedra (2026-10-29), el sistema se trabaja con este stack:

| Parte | Tecnologías | Carpeta |
| --- | --- | --- |
| Backend | Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis, Docker / Docker Compose | [`backend/`](backend/README.md) |
| Frontend | React, TypeScript, Vite | [`frontend/`](frontend/README.md) |

```text
TP-ODONTOLOGIA/
├── backend/            # API FastAPI: agenda, PostgreSQL, catálogos y disponibilidad C-07
├── frontend/           # React + TypeScript + Vite
├── docker-compose.yml  # db (PostgreSQL), redis, backend y frontend
├── openspec/           # specs vigentes y changes archivados
├── knowledge-base/     # base de conocimiento (10 archivos)
├── docs/               # Discovery, bitácora, evidencia y consigna
├── CHANGES.md          # roadmap de 20 changes
└── AGENTS.md / CLAUDE.md
```

**Qué está implementado y qué queda planificado:** C-01 sigue disponible sobre SQLite, que conserva el valor predeterminado. C-02 agrega PostgreSQL optativo, migración Alembic e importación no destructiva; C-03 implementa autenticación JWT y permisos; C-04 agrega auditoría; C-05 administra fichas mínimas; C-06 administra catálogos ficticios; C-07 implementa disponibilidad de profesionales y boxes. C-08 a C-20 siguen planificados, con agenda de recepción, recordatorios con Redis y despliegue controlado entre sus alcances. Ver la [bitácora](docs/BITACORA.md) y las evidencias de [C-01](docs/evidencia/implementacion-turnos.md), [C-06](docs/evidencia/implementacion-catalogos.md) y [C-07](docs/evidencia/implementacion-disponibilidad.md).

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

Levanta PostgreSQL, Redis, el backend en http://127.0.0.1:8000 (Swagger en `/docs`) y el frontend en http://127.0.0.1:5173. El backend prepara una agenda ficticia de C-01 en un volumen propio si todavía no existe. La primera vez, migrar el esquema y crear el Administrador de forma interactiva:

```powershell
docker compose exec backend python -m alembic upgrade head
docker compose exec backend python -m odontologia.auth.bootstrap_admin
```

El segundo comando solicita credenciales sin mostrarlas. No se crean cuentas predeterminadas. No publicar la aplicación ni utilizar datos reales.

### Backend sin Docker

Python 3.12+ y entorno virtual local. Desde `backend/`:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt -r requirements-stack.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m odontologia.demo
```

`requirements.txt` fija las dependencias directas de C-01, `requirements-dev.txt` añade HTTPX, `requirements-lock.txt` conserva el entorno verificado de C-01 y `requirements-stack.txt` suma SQLAlchemy, psycopg, Alembic, PyJWT y redis. En el entorno actual, la suite tiene 111 pruebas SQLite; con `ODONTOLOGIA_TEST_DATABASE_URL` aislada, se ejecutan 10 pruebas adicionales de migración, concurrencia y autenticación PostgreSQL. Python 3.12.14 / SQLite 3.53.1 / PostgreSQL 18.6 temporal. Starlette emite un aviso de deprecación por HTTPX; las pruebas pasan y el aviso se conserva.

Inicializar una agenda ficticia NUEVA en disco local (no asumir N: local), y luego iniciar la API sólo en loopback, siempre desde `backend/`:

```powershell
$env:ODONTOLOGIA_DB = Join-Path $env:LOCALAPPDATA 'odontologia-c01.sqlite3'
.\.venv\Scripts\python.exe -c "import os; from odontologia import inicializar_agenda; inicializar_agenda(os.environ['ODONTOLOGIA_DB'])"
$env:JWT_SECRETO = [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
.\.venv\Scripts\python.exe -m odontologia.auth.migrar_sqlite
.\.venv\Scripts\python.exe -m odontologia.auth.bootstrap_admin
.\.venv\Scripts\python.exe -m uvicorn odontologia.api:crear_app --factory --host 127.0.0.1 --port 8000
```

### Frontend sin Docker

Node 20+. Desde `frontend/`: `npm install` y `npm run dev` (http://localhost:5173, con el backend en el puerto 8000).

Bootstrap rechaza archivos existentes sin sobrescribirlos. Para reutilizar agenda ya preparada, omitir inicialización. Detener servidor con Ctrl+C. Crear app/importar no crea DB. No ejecutar bootstrap sobre agendas ajenas ni borrar archivos para repetir.

GET http://127.0.0.1:8000/health devuelve liveness, no estado de DB. OpenAPI en /openapi.json; Swagger en /docs y ReDoc en /redoc. Las páginas interactivas usan recursos CDN de FastAPI y pueden requerir Internet para cargarlos; OpenAPI es completamente local. Iniciar sesión con POST `/sesiones` usando las credenciales locales; en Swagger, pulsar **Authorize** e ingresar `Bearer <access_token>`. Administrador y Recepción pueden crear turnos, operar fichas de pacientes y administrar datos descriptivos de profesionales, boxes y prestaciones. Sólo Administrador modifica estados activos y administra usuarios/auditoría. Profesional aún no tiene cuenta habilitada. `/sesiones/actual` muestra la identidad vigente y permite revocar la sesión propia.

POST /turnos recibe:

```json
{"paciente_id":"paciente-A","profesional_id":"profesional-A","box_id":"box-A","inicio":"2026-10-15T09:00:00-03:00","fin":"2026-10-15T09:30:00-03:00"}
```

Devuelve 201 con id y fechas UTC después del commit. Errores JSON codigo/campo/mensaje: 401 sin identidad válida, 403 sin permiso, 422 entrada inválida, 404 recurso desconocido, 409 conflicto, 503 contención y 500 almacenamiento. Campos adicionales, IDs no string, epoch numérico, fechas sin offset o precisión distinta de minutos se rechazan. El dominio valida IDs conocidos e inicio anterior a fin, sin corrección silenciosa.

Catálogos ficticios paciente-A/B, profesional-A/B y box-A/B; C-06 permite agregar otros desde `/profesionales`, `/boxes` y `/prestaciones`, con listas paginadas de hasta 100 elementos. C-07 administra horarios locales, excepciones y bloqueos; con SQLite v5/PostgreSQL 0006 cada reserva debe caber en un tramo de ambos recursos. La zona es `America/Argentina/Mendoza`; un recurso no configurado está cerrado. Cambios que afectarían turnos guardados devuelven 409. La API falla cerrada si faltan tablas de disponibilidad; el servicio standalone C-01 sin migrar conserva su contrato previo. Las prestaciones siguen independientes; C-01 no agrega `prestacion_id`. Turnos nuevos rechazan recursos inactivos y conservan su historial. No hay UI clínica, cancelación, exclusión de paciente ni idempotencia. No apto para pacientes reales ni despliegue público.

La demo conserva dos registros en su temporal y lo elimina al terminar. [Evidencia y trazabilidad](docs/evidencia/implementacion-turnos.md). Archive quedó confirmado el 2026-10-28; la revisión personal de fuentes ya estaba confirmada. Las evidencias y la aceptación de la entrega académica tienen su propio registro y no se deducen de este cierre técnico.
