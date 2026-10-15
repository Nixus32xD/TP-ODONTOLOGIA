# TP - Gestión de turnos odontológicos

Entrega propia de Metodología I: investigar y desarrollar una funcionalidad de agenda y turnos de pacientes para consultorios odontológicos del mercado argentino, usando Active Stack, OpenSpec y el ciclo OPSX.

Repositorio: [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).

## Estado actual

OpenSpec inicializado y Discovery documental confirmado: quince sistemas relevados, matriz ponderada y once puntos aceptados el 2026-10-15 para un consultorio pequeño. Elegí como primer change crear turnos evitando solapamientos por profesional y box. La investigación documental está asistida por IA; queda pendiente mi verificación personal de al menos cinco fuentes. Todavía no hay código de producto ni pruebas de comportamiento.

Se ejecutó `openspec init --tools codex --language es --no-animation`: configuración `spec-driven` y seis skills OPSX. Se incorporó `discovery-research` sólo en este proyecto. El estado de Active Stack conserva `version: 4` y registra `step: agents`: Discovery está registrado y la [base de conocimiento](knowledge-base/README.md) contiene diez documentos canónicos más su índice, generados desde las fuentes existentes. Stack, API o módulo, persistencia, límites temporales y estrategia de concurrencia permanecen abiertos; confirmar el alcance no decide esos contratos.

Para consultar el estado desde PowerShell con OpenSpec disponible en PATH:

```powershell
Set-Location -LiteralPath 'N:\Nueva carpeta\TP-ODONTOLOGIA'
openspec list --json
```

OpenSpec registra ahora el único change `crear-turno-sin-solapamientos`, con sus cuatro artefactos de planificación completos y 0 de 15 tareas implementadas. El [diseño propuesto](openspec/changes/crear-turno-sin-solapamientos/design.md) elige módulo Python 3.12+, SQLite local y unittest; propone intervalos `[inicio, fin)`, fechas con offset y exclusión concurrente limitada al mismo archivo local. La revisión del contrato antes de Apply sigue pendiente; no se confunde planificación completa con producto terminado. El [roadmap](CHANGES.md) organiza un único change candidato, `C-01: crear-turno-sin-solapamientos`, con dependencias, contexto, camino crítico y riesgos. El change fue creado mediante el CLI, sin specs principales previas. La revisión humana del contenido de la base de conocimiento y del roadmap sigue pendiente. La [selección de skills](docs/fundacion/seleccion-skills.md) recomienda reutilizar las existentes, descarta React del alcance actual y difiere pruebas de UI hasta definir el stack. No se instalaron herramientas nuevas. El [registro de skills](.atl/skill-registry.md) documenta las herramientas disponibles, su alcance y las tareas a las que aplican. Las instrucciones específicas están en [AGENTS.md](AGENTS.md) y [CLAUDE.md](CLAUDE.md), con contenido idéntico y reglas consolidadas desde el alcance y las restricciones ya autorizados. No adoptan un stack ni resuelven contratos abiertos. El siguiente trabajo es revisar el contrato propuesto antes de iniciar Apply; los pendientes del entorno y de evidencia quedan documentados para la entrega.

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

El usuario autorizó commits locales separados por petición completada, validación previa y cambios no relacionados separados. El registro de skills quedó publicado en `main` en `197be16a2eed4b8ea0c0dbcfcfa4cd601a38d59c`. Para esta petición de planificación se conserva la preferencia de commit local validado; no se presume nueva autorización de push. La entrega docente final sigue pendiente. Este permiso no constituye autorización universal para publicaciones futuras. Las revisiones humanas se documentan cuando ocurren.

## Documentación

- [Consigna y checklist de entregables](docs/CONSIGNA.md).
- [Bitácora del proceso](docs/BITACORA.md).
- [Inventario y pendientes del entorno](docs/evidencia/entorno.md).
- [Informe Discovery](docs/discovery/informe-discovery.md) y [PDF](docs/discovery/informe-discovery.pdf).
- [Discovery canónico](discovery/discovery.md) y [once puntos confirmados](docs/discovery/resumen-para-revision.md).
- [Base de conocimiento: índice y diez documentos](knowledge-base/README.md).
- [Roadmap del único change de turnos](CHANGES.md).
- [Comprobaciones documentales y revisión personal pendiente](docs/discovery/verificacion-fuentes.md).
- [Nueva revisión documental delegada: seis fuentes y motivos de ajuste](docs/discovery/revision-documental-2026-10-15.md).
- [Selección y justificación de skills](docs/fundacion/seleccion-skills.md).
- [Registro de skills del proyecto](.atl/skill-registry.md).
- [Instrucciones para agentes](AGENTS.md) y [versión equivalente para Claude](CLAUDE.md).
- [Exploración técnica](docs/exploracion/alta-turno.md), [propuesta](openspec/changes/crear-turno-sin-solapamientos/proposal.md), [spec](openspec/changes/crear-turno-sin-solapamientos/specs/alta-turnos/spec.md) y [tareas](openspec/changes/crear-turno-sin-solapamientos/tasks.md).

## Regenerar el informe PDF

Con Python 3, `reportlab`, `pypdf` y las fuentes Arial de Windows disponibles:

```powershell
python tools/render_discovery.py
```

El comando consolida tablas, calcula los totales y genera el PDF y `matriz-evidencia.json` desde las fichas. No consulta servicios externos ni modifica el estado de Active Stack. La revisión personal de al menos cinco fuentes continúa pendiente.

El README incorporará los pasos de instalación y ejecución de la suite cuando exista la implementación. Todos los ejemplos y pruebas usarán datos ficticios, sin secretos ni datos reales de pacientes.
