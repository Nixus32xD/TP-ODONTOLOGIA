# TP - Gestión de turnos odontológicos

Entrega propia de Metodología I: investigar y desarrollar una funcionalidad de agenda y turnos de pacientes para consultorios odontológicos del mercado argentino, usando Active Stack, OpenSpec y el ciclo OPSX.

Repositorio: [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).

## Estado actual

OpenSpec inicializado y Discovery documental confirmado: quince sistemas relevados, matriz ponderada y once puntos aceptados el 2026-10-15 para un consultorio pequeño. Elegí como primer change crear turnos evitando solapamientos por profesional y box. La investigación documental está asistida por IA; confirmé mi revisión personal de las seis fuentes del registro el 2026-10-15. C-01 tiene FastAPI, módulo, demo y 53 tests automatizados; fue verificado y archivado el 2026-10-28. El cierre técnico no acredita por sí solo revisión humana ni aceptación docente.

Se ejecutó `openspec init --tools codex --language es --no-animation`: configuración `spec-driven` y seis skills OPSX. Se incorporó `discovery-research` sólo en este proyecto. El estado de Active Stack conserva `version: 4` y registra `step: agents`: Discovery está registrado y la [base de conocimiento](knowledge-base/README.md) contiene diez documentos canónicos más su índice, generados desde las fuentes existentes. El usuario autorizó continuar con Apply sobre la propuesta: FastAPI, Python 3.12+, SQLite y unittest. El campo step registra la última fase de fundación; el CLI de OpenSpec registra el progreso del change.

Para consultar el estado desde PowerShell con OpenSpec disponible en PATH:

```powershell
Set-Location -LiteralPath 'N:\Nueva carpeta\TP-ODONTOLOGIA'
openspec list --json
```

OpenSpec conserva `crear-turno-sin-solapamientos` archivado, con sus cuatro artefactos de planificación y 18 de 18 tareas completas. La [spec principal](openspec/specs/alta-turnos/spec.md) contiene el contrato vigente de alta; `openspec list --json` ya no muestra changes activos. El [diseño propuesto](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md) define FastAPI, Python 3.12+, SQLite local y unittest; propone intervalos `[inicio, fin)`, fechas con offset y exclusión concurrente limitada al mismo archivo local. La autorización de Apply no se presenta como lectura personal completa del spec; no se confunde suite verde con entrega académica final. El [roadmap](CHANGES.md) planifica 20 changes en seis fases para el producto futuro; sólo C-01 está implementado y archivado. C-02 a C-20 son propuestas, sin implementación autorizada. El change fue creado mediante el CLI, sin specs principales previas. La revisión humana del contenido de la base de conocimiento y del roadmap sigue pendiente. La [selección de skills](docs/fundacion/seleccion-skills.md) recomienda reutilizar las existentes, descarta React del alcance actual y difiere pruebas de UI hasta definir el stack. Se instalaron dependencias del producto sólo en .venv; no nuevas skills. El [registro de skills](.atl/skill-registry.md) documenta las herramientas disponibles, su alcance y las tareas a las que aplican. Las instrucciones específicas están en [AGENTS.md](AGENTS.md) y [CLAUDE.md](CLAUDE.md), con contenido idéntico y reglas consolidadas desde el alcance y las restricciones ya autorizados. Reflejan el contrato aplicado sin agregar módulos ni decisiones clínicas ajenas a C-01. El cierre de C-01 se documenta en la [evidencia](docs/evidencia/implementacion-turnos.md); los pendientes académicos se contrastan con los registros y comunicaciones actuales, sin inferir aceptación docente del Archive.

Esta entrega comienza desde cero. El alcance inicial es una funcionalidad terminada de agenda, con datos ficticios y sin integraciones clínicas reales.

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

Python 3.12+ y entorno virtual local. Desde la raíz:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m odontologia.demo
```

requirements.txt fija dependencias directas del producto, requirements-dev.txt añade HTTPX y requirements-lock.txt conserva el entorno completo verificado. Python3.12.14/SQLite3.53.1; 53 tests, incluyendo10 HTTP y procesos spawn reales. Starlette1.8.0 emite un aviso de deprecación por HTTPX0.28.1; la compatibilidad actual pasó, no se silencia el aviso.

Inicializar una agenda ficticia NUEVA en disco local (no asumir N: local), y luego iniciar la API sólo en loopback:

```powershell
$env:ODONTOLOGIA_DB = Join-Path $env:LOCALAPPDATA 'odontologia-c01.sqlite3'
.\.venv\Scripts\python.exe -c "import os; from odontologia import inicializar_agenda; inicializar_agenda(os.environ['ODONTOLOGIA_DB'])"
.\.venv\Scripts\python.exe -m uvicorn odontologia.api:crear_app --factory --host 127.0.0.1 --port 8000
```

Bootstrap rechaza archivos existentes sin sobrescribirlos. Para reutilizar agenda ya preparada, omitir inicialización. Detener servidor con Ctrl+C. Crear app/importar no crea DB. No ejecutar bootstrap sobre agendas ajenas ni borrar archivos para repetir.

GET http://127.0.0.1:8000/health devuelve liveness, no estado de DB. OpenAPI en /openapi.json; Swagger en /docs y ReDoc en /redoc. Las páginas interactivas usan recursos CDN de FastAPI y pueden requerir Internet para cargarlos; OpenAPI es completamente local.

POST /turnos recibe:

```json
{"paciente_id":"paciente-A","profesional_id":"profesional-A","box_id":"box-A","inicio":"2026-10-15T09:00:00-03:00","fin":"2026-10-15T09:30:00-03:00"}
```

Devuelve201 con id y fechas UTC después del commit. Errores JSON codigo/campo/mensaje:422 entrada inválida,404 recurso desconocido,409 conflicto,503 contención y500 almacenamiento. Campos adicionales, IDs no string, epoch numérico, fechas sin offset o precisión distinta de minutos se rechazan. El dominio valida IDs conocidos e inicio anterior a fin, sin corrección silenciosa.

Catálogos ficticios paciente-A/B, profesional-A/B y box-A/B. Intervalos [inicio,fin), adyacencia permitida; prioridad del profesional si ambos conflictos existen. Timeout5s configurable en crear_app, no expuesto en JSON. Garantía sólo mismo archivo SQLite local y escritores del módulo, sin red compartida ni SQL externo. Sin autenticación, UI clínica, cancelación, horarios, exclusión de paciente ni idempotencia; no apto para pacientes reales ni despliegue público.

La demo conserva dos registros en su temporal y lo elimina al terminar. [Evidencia y trazabilidad](docs/evidencia/implementacion-turnos.md). Archive quedó confirmado el 2026-10-28; la revisión personal de fuentes ya estaba confirmada. Las evidencias y la aceptación de la entrega académica tienen su propio registro y no se deducen de este cierre técnico.
