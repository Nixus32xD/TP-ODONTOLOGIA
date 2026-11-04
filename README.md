# TP - Gestión de turnos odontológicos

Entrega propia de Metodología I: investigar y desarrollar una funcionalidad de agenda y turnos de pacientes para consultorios odontológicos del mercado argentino, usando Active Stack, OpenSpec y el ciclo OPSX.

Repositorio: [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).

## Estado actual

OpenSpec inicializado y Discovery documental confirmado: quince sistemas relevados, matriz ponderada y once puntos aceptados el 2026-10-15 para un consultorio pequeño. C-01 crea turnos sin solapamientos y fue archivado el 2026-10-28. C-02 agrega PostgreSQL + SQLAlchemy, migraciones Alembic e importación explícita desde SQLite; C-03 agrega autenticación JWT y permisos de personal. C-01–C-13 y C-15–C-20 están implementados, validados y archivados localmente. C-20 agrega reportes JSON/CSV y un panel local, respaldados por integración PostgreSQL temporal. C-14 despliegue sigue opcional y fuera de esta entrega. La investigación documental está asistida por IA; confirmé mi revisión personal de las seis fuentes del registro el 2026-10-15. El cierre técnico no acredita por sí solo aceptación docente.

Se ejecutó `openspec init --tools codex --language es --no-animation`: configuración `spec-driven` y seis skills OPSX. Se incorporó `discovery-research` sólo en este proyecto. El estado de Active Stack conserva `version: 4` y registra `step: agents`: Discovery está registrado y la [base de conocimiento](knowledge-base/README.md) contiene diez documentos canónicos más su índice, generados desde las fuentes existentes. C-01 se implementó con FastAPI, Python 3.12+, SQLite y unittest; C-02 añadió PostgreSQL optativo y C-03 autenticación JWT. El campo step registra la última fase de fundación; el CLI de OpenSpec registra el progreso de cada change.

Para consultar el estado desde PowerShell con OpenSpec disponible en PATH:

```powershell
Set-Location -LiteralPath 'N:\Nueva carpeta\TP-ODONTOLOGIA'
openspec list --json
```

OpenSpec conserva C-01 a C-13 y C-15 a C-20 archivados y validados localmente. C-09 gestiona estados de turno; C-10 reprograma de forma atómica; C-11 opera la agenda desde recepción; C-12 respalda/restaura la agenda; C-13 endurece seguridad y observabilidad; C-15–C-18 agregan historia clínica sintética, odontograma y planes, recordatorios simulados y autoservicio de pacientes; C-19 agrega un ledger financiero de cargos/cobros/reversiones; C-20 agrega reportes operativos JSON/CSV y panel. El [roadmap](CHANGES.md) describe el alcance completo; C-14 despliegue es opcional y queda fuera de esta entrega. Las evidencias distinguen pruebas, revisión humana y aceptación docente. La [selección de skills](docs/fundacion/seleccion-skills.md), el [registro](.atl/skill-registry.md) y las reglas de [AGENTS.md](AGENTS.md) y [CLAUDE.md](CLAUDE.md) conservan las decisiones del proyecto.

El proyecto comenzó desde cero con C-01 como primer cambio funcional de agenda. C-02 y C-03 amplían esa base; los changes posteriores siguen sujetos a su propio contrato, autorización y verificación. El desarrollo usa datos ficticios y no integra servicios clínicos reales.

## Stack tecnológico y estructura

Por corrección de la cátedra (2026-10-29), el sistema se trabaja con este stack:

| Parte | Tecnologías | Carpeta |
| --- | --- | --- |
| Backend | Python, FastAPI, JWT, SQLAlchemy, SQLite y PostgreSQL optativo | [`backend/`](backend/README.md) |
| Frontend | React, TypeScript, Vite | [`frontend/`](frontend/README.md) |

```text
TP-ODONTOLOGIA/
├── backend/            # API FastAPI: agenda, PostgreSQL, catálogos, C-07 y consultas C-08
├── frontend/           # React + TypeScript + Vite
├── openspec/           # specs vigentes y changes archivados
├── knowledge-base/     # base de conocimiento (10 archivos)
├── docs/               # Discovery, bitácora, evidencia y consigna
├── CHANGES.md          # roadmap de 20 changes
└── AGENTS.md / CLAUDE.md
```

**Qué está implementado y qué queda planificado:** C-01 sigue disponible sobre SQLite, que conserva el valor predeterminado. C-02 agrega PostgreSQL optativo y migración Alembic; C-03 implementa JWT y permisos; C-04 agrega auditoría; C-05 administra fichas mínimas; C-06 administra catálogos; C-07 disponibilidad; C-08 consultas; C-09 estados; C-10 reprogramación; C-11 interfaz de recepción; C-12 backup/restauración; C-13 seguridad y observabilidad. C-15–C-19 agregan historia clínica sintética, odontograma y planes, recordatorios simulados, portal paciente y ledger financiero manual; C-20 agrega reportes operativos. C-14 despliegue queda opcional. Ver la [bitácora](docs/BITACORA.md) y las evidencias por change.

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
- [Skill propia del TPI y evidencia de uso](docs/entrega/evidencia-skill-mcp.md).
- [Guía de conexión y uso del MCP GitHub](docs/entrega/mcp-github.md).
- [Guion de video TPI (máximo 10 minutos)](docs/entrega/guion-video.md).
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

### Demostración del trabajo

La entrega se presenta mostrando el repositorio, el roadmap y los changes OpenSpec, junto con la evidencia de pruebas. No es necesario construir imágenes, usar Docker/Compose, levantar servicios ni publicar el proyecto.

Para revisar el estado de OpenSpec:

```powershell
openspec list --json
openspec status --change respaldar-y-restaurar-agenda --json
openspec validate --all --strict
```

Para una inspección interactiva opcional, el backend puede iniciarse localmente con el flujo sin Docker descrito abajo; esto no es requisito de presentación ni una declaración de despliegue.

### Backend sin Docker

Python 3.12+ y entorno virtual local. Desde `backend/`:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt -r requirements-stack.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m odontologia.demo
```

`requirements.txt` fija las dependencias directas de C-01, `requirements-dev.txt` añade HTTPX, `requirements-lock.txt` conserva el entorno verificado de C-01 y `requirements-stack.txt` suma SQLAlchemy, psycopg, Alembic y PyJWT. En el entorno actual, la suite tiene 111 pruebas SQLite; con `ODONTOLOGIA_TEST_DATABASE_URL` aislada, se ejecutan 10 pruebas adicionales de migración, concurrencia y autenticación PostgreSQL. Python 3.12.14 / SQLite 3.53.1 / PostgreSQL 18.6 temporal. Starlette emite un aviso de deprecación por HTTPX; las pruebas pasan y el aviso se conserva.

Inicializar una agenda ficticia NUEVA en disco local (no asumir N: local), y luego iniciar la API sólo en loopback, siempre desde `backend/`:

```powershell
$env:ODONTOLOGIA_DB = Join-Path $env:LOCALAPPDATA 'odontologia-c01.sqlite3'
.\.venv\Scripts\python.exe -c "import os; from odontologia import inicializar_agenda; inicializar_agenda(os.environ['ODONTOLOGIA_DB'])"
$env:JWT_SECRETO = [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
$env:ODONTOLOGIA_ENTORNO = 'desarrollo'
.\.venv\Scripts\python.exe -m odontologia.auth.migrar_sqlite
.\.venv\Scripts\python.exe -m odontologia.auth.bootstrap_admin
.\.venv\Scripts\python.exe -m uvicorn odontologia.api:crear_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

### Frontend sin Docker

Node 20+. Desde `frontend/`: `npm install` y `npm run dev` (http://localhost:5173, con el backend en el puerto 8000).

Bootstrap rechaza archivos existentes sin sobrescribirlos. Para reutilizar agenda ya preparada, omitir inicialización. Detener servidor con Ctrl+C. Crear app/importar no crea DB. No ejecutar bootstrap sobre agendas ajenas ni borrar archivos para repetir.

GET `http://127.0.0.1:8000/health` devuelve liveness, sin comprobar la base; `GET /ready` prueba conectividad con `SELECT 1` y responde 503 si no está disponible. OpenAPI (`/openapi.json`), Swagger (`/docs`) y ReDoc (`/redoc`) se habilitan sólo con `ODONTOLOGIA_ENTORNO=desarrollo`; producción, valor ausente o desconocido los deshabilita. Las páginas interactivas usan recursos CDN de FastAPI y pueden requerir Internet para cargarlos; OpenAPI es completamente local. Iniciar sesión con POST `/sesiones` usando las credenciales locales; en Swagger, pulsar **Authorize** e ingresar `Bearer <access_token>`. Administrador y Recepción pueden crear turnos, consultar la agenda, operar fichas y administrar datos descriptivos de profesionales, boxes y prestaciones. Sólo Administrador modifica estados activos y administra usuarios/auditoría. En C-08, Administrador vincula cuentas Profesionales a una ficha única; Profesional sólo consulta turnos y disponibilidad de su vínculo, sin teléfono ni escritura. `/sesiones/actual` muestra la identidad vigente y permite revocar la sesión propia.

POST /turnos recibe:

```json
{"paciente_id":"paciente-A","profesional_id":"profesional-A","box_id":"box-A","inicio":"2026-10-15T09:00:00-03:00","fin":"2026-10-15T09:30:00-03:00"}
```

Devuelve 201 con id y fechas UTC después del commit. Errores JSON codigo/campo/mensaje: 401 sin identidad válida, 403 sin permiso, 422 entrada inválida, 404 recurso desconocido, 409 conflicto, 503 contención y 500 almacenamiento. Campos adicionales, IDs no string, epoch numérico, fechas sin offset o precisión distinta de minutos se rechazan. El dominio valida IDs conocidos e inicio anterior a fin, sin corrección silenciosa.

Catálogos ficticios paciente-A/B, profesional-A/B y box-A/B; C-06 permite agregar otros desde `/profesionales`, `/boxes` y `/prestaciones`, con listas paginadas de hasta 100 elementos. C-07 administra horarios locales, excepciones y bloqueos; una reserva debe caber en un tramo de ambos recursos. C-09 añade estados y sólo `reservado`/`confirmado` ocupan recursos. C-08 agrega `GET /turnos` con `desde`/`hasta` con offset y rango máximo de 31 días, filtros por profesional/box/estado y paginación hasta 100. La respuesta Profesional sólo muestra horarios y nombre del paciente de su ficha. `GET /disponibilidad` requiere fecha Mendoza, profesional, box y duración positiva; devuelve opciones cada 15 minutos que caben en horarios/excepciones y no pisan bloques ni turnos ocupantes. Las opciones no reservan: `POST /turnos` revalida dentro de la operación. SQLite v7/PostgreSQL 0008 requieren una migración explícita para vínculos de cuenta Profesional; el servicio standalone C-01 conserva su contrato previo. Cambios que afectarían turnos ocupantes devuelven 409; los terminales se conservan. No hay UI clínica, exclusión del paciente ni operación con datos reales. No apto para pacientes reales ni despliegue público.

La demo conserva dos registros en su temporal y lo elimina al terminar. [Evidencia y trazabilidad](docs/evidencia/implementacion-turnos.md). Archive quedó confirmado el 2026-10-28; la revisión personal de fuentes ya estaba confirmada. Las evidencias y la aceptación de la entrega académica tienen su propio registro y no se deducen de este cierre técnico.
