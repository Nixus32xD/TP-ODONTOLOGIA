# Selección de skills

Fecha: 2026-10-15. Fase `find-skill`, sólo recomendaciones. No se instalaron skills ni dependencias.

## Necesidad y criterio

La [KB](../../knowledge-base/README.md), la [arquitectura](../../knowledge-base/08_arquitectura_propuesta.md) y el [roadmap](../../CHANGES.md) definen un único change: `crear-turno-sin-solapamientos`. Stack y runner siguen pendientes; no existe frontend definido.

Consulté primero el [leaderboard skills.sh](https://skills.sh/) y luego repositorios y contenido oficial de candidatas. Los contadores son aproximaciones de las páginas consultadas en la fecha indicada; no acreditan seguridad ni calidad. La consulta web resultó suficiente: no ejecuté `npx skills` ni código remoto.

| Opción | Evidencia comprobada | Decisión y justificación |
| --- | --- | --- |
| OPSX local | Seis `SKILL.md` existentes, inventariados abajo | **Reutilizar**: cubren planificación, implementación y cierre del único change. |
| Discovery local | `SKILL.md`, licencia y adaptación existentes | **Reutilizar**: preservar trazabilidad sin instalar otra copia. |
| Active Stack global | Carpetas del proceso de fundación existentes | **Reutilizar**: completar registro e instrucciones con herramientas disponibles. |
| `vercel-react-best-practices` | Leaderboard: 805.1K instalaciones mostradas; [repo oficial Vercel](https://github.com/vercel-labs/agent-skills): 32.5K estrellas; [contenido oficial](https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/react-best-practices/SKILL.md) | **Descartar del alcance actual**: optimiza React/Next.js; no hay frontend ni stack elegido. |
| `webapp-testing` | [Repo oficial Anthropic](https://github.com/anthropics/skills): 181.3K estrellas; [contenido oficial](https://raw.githubusercontent.com/anthropics/skills/main/skills/webapp-testing/SKILL.md); instalaciones específicas no verificadas | **Diferir**: usa Playwright y servidor web; no sustituye pruebas unitarias del dominio ni existe UI definida. |
| Pruebas específicas del stack | Lenguaje y runner pendientes, Q02 | **Diferir**: seleccionar después del runtime, sin imponer Jest, PHPUnit o pytest. |

No se recomienda instalar ninguna skill nueva ahora. Ante una incorporación futura se revisarán versión, licencia, scripts, permisos y compatibilidad; la popularidad no sustituye esa revisión. No se propone ejecutar comandos de instalación en esta fase.

## Inventario comprobado

### Locales del repositorio

Ubicación `.agents/skills/`: siete carpetas con `SKILL.md` comprobadas.

- `openspec-explore`: investigación sin implementación.
- `openspec-propose`: propuesta, diseño, specs y tareas.
- `openspec-apply-change`: implementar contrato revisado.
- `openspec-update-change`: reconciliar planificación.
- `openspec-sync-specs`: sincronizar deltas.
- `openspec-archive-change`: archivar change verificado.
- `discovery-research`: relevamiento documental con licencia y adaptación conservadas.

Se verificaron presencia, nombres y descripciones locales; este inventario no acredita auditoría completa de todos sus scripts. Son herramientas de proceso, no funcionalidades clínicas ni prueba de implementación.

### Globales de proceso

Ubicación comprobada `C:/Users/Oficina/.agents/skills/`: `active-orchestrator`, `kb-creator`, `roadmap-generator`, `find-skill`, `skill-registry` y `agent-instruction`. También existe `skill-creator`, sin necesidad actual de crear otra skill. Estas carpetas pertenecen al entorno y no se copiaron al repositorio. Las herramientas editoriales de PDF no determinan el stack del producto.

## Resultado y continuidad

`state.skills.recommended` registra tres reutilizaciones. `state.skills.installed = []` significa **ninguna instalación nueva realizada por esta fase**, no ausencia de skills existentes. Sólo se actualiza la sección `skills`; se conserva esquema v4 y el paso administrado por el orquestador.

Siguiente paso: registro de skills existentes antes de generar instrucciones del proyecto. No supone empezar Apply ni resolver silenciosamente [Q01–Q08](../../knowledge-base/10_preguntas_abiertas.md). TDD y suite completa corresponden a implementación con runner disponible; esta fase recibe verificación documental.


## Actualización durante Apply

El contrato de C-01 se implementó con Python, sqlite3, unittest y multiprocessing estándar. No se instaló pytest, Playwright ni otra skill: las opciones de UI siguen fuera de alcance. Ver [evidencia](../evidencia/implementacion-turnos.md). El inventario original de selección conserva su fecha y las incertidumbres de esa etapa como historial.

## Corrección FastAPI — C-01

El usuario corrigió expresamente el stack a FastAPI y autorizó commit/push tras validar, manteniendo sólo C-01. Adaptador POST /turnos, GET /health y OpenAPI reutilizan SQLite. Dependencias fijadas, instaladas en .venv (sin cambios globales); HTTPX para TestClient. Estado previo sin HTTP conserva valor histórico, no describe el producto actual. Baseline43; suite actual53 tests. No se modifica PDF, datos reales ni proveedores externos. Archive y evidencias personales pendientes.
