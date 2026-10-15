# Inventario del entorno

Registro de preparación del 2026-10-15. Este inventario distingue disponibilidad de herramientas de evidencia de instalación Full.

| Elemento | Resultado observado |
| --- | --- |
| Git | 2.50.1 |
| Node.js | 22.18.0 |
| OpenSpec | 1.14.2 |
| Engram CLI | 1.20.0 |
| Active Stack | Binario disponible; versión no verificada |
| MCP Context7 | Configurado en el entorno de Codex |
| MCP Engram | Configurado en el entorno de Codex |
| Go | No encontrado en PATH; esto no demuestra su ausencia en disco |
| Agente | Codex, seleccionado por el usuario |
| Skill `discovery-research` | Incorporada sólo al proyecto en `.agents/skills/discovery-research`; referencia `dd7efb7d044ea3a683b6665a3df9d949856b417f` |

## Inicialización verificada

- `openspec init --tools codex --language es --no-animation`: código de salida 0.
- `openspec/config.yaml`: esquema `spec-driven`.
- Seis skills de proyecto en `.agents/skills/`: `openspec-explore`, `openspec-propose`, `openspec-update-change`, `openspec-apply-change`, `openspec-sync-specs` y `openspec-archive-change`.
- `.active-orchestrator-state.json`: versión 4, paso siguiente `discovery`, pendiente de revisión e inicio.
- `openspec list --json`: código de salida 0, `changes: []`, raíz `N:/Nueva carpeta/TP-ODONTOLOGIA`.

Estos resultados verifican inicialización y estado del flujo. Todavía no existen pruebas de comportamiento de producto.

## Pendientes de evidencia y preparación

- Comprobar o resolver Go antes de dar por completos los requisitos de entorno.
- Acreditar la instalación de Active Stack en modo Full y registrar la lista de harnesses; la disponibilidad del binario no prueba el modo instalado.
- Obtener las capturas exigidas de instalación y harnesses. Todavía no se incorporaron capturas.
- `discovery-research` ya está disponible en el proyecto; su procedencia y adaptación de nombres se registran en `LOCAL_ADAPTATION.md`.
- Documentar el uso de Codex frente a los agentes citados por la consigna, sin atribuir una aceptación docente que todavía no se acreditó.

No se incluyen configuraciones globales, credenciales ni datos personales en este registro.

## Investigación y exportación

- Quince fichas de producto; 105 notas de matriz en rango 0 a 5 y totales ponderados recalculados. Las 92 URLs de las fichas son referencias; el conteo incluye accesos fallidos registrados y no equivale a 92 verificaciones exitosas.
- Seis comprobaciones documentales del agente; verificación personal del estudiante pendiente.
- `tools/render_discovery.py` utiliza `reportlab` y `pypdf` del runtime disponible para regenerar el informe y su matriz. No ejecuta servicios externos ni cambia el estado de Active Stack.
- La revisión de Discovery continúa pendiente; no existe aún código de producto ni suite de comportamiento.
