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
- `.active-orchestrator-state.json`: versión 4, fase actual `roadmap`; Discovery documental y base de conocimiento registrados en sus secciones propias.
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

- Quince fichas de producto; 105 notas de matriz en rango 0 a 5 y totales ponderados recalculados en la revisión anterior. Las URLs de las fichas son referencias; incluyen accesos fallidos registrados y su número no equivale a verificaciones exitosas.
- Seis comprobaciones documentales del agente; verificación personal del estudiante pendiente.
- `tools/render_discovery.py` utiliza `reportlab` y `pypdf` del runtime disponible para regenerar el informe y su matriz. No ejecuta servicios externos ni cambia el estado de Active Stack.
- El usuario confirmó los once puntos de Discovery y autorizó continuar el 2026-10-15. `discovery/discovery.md` y `state.discovery` registran el cierre documental, sin acreditar verificación personal de fuentes.
- La [base de conocimiento](../../knowledge-base/README.md) está generada desde los documentos existentes: diez canónicos y un índice. Conserva abiertas las decisiones de stack, persistencia, intervalos y concurrencia; no acredita revisión humana de la KB. No existe aún código de producto ni suite de comportamiento.
- La edición del informe y del PDF usa primera persona sólo para elecciones veraces del estudiante y declara la investigación documental asistida por IA. No atribuye al estudiante las comprobaciones del agente.
- El PDF revisado tiene 55 páginas y SHA-256 `32bef0a07299913ca2e163ffd5a966827ae617989eaa47aa5ce0bd5f249fc099`. La revisión final registrada en la [bitácora](../BITACORA.md) comprobó 146 enlaces locales, 105 puntajes/totales y los hashes de las quince fichas; no acredita pruebas de producto ni revisión personal de fuentes.
- El usuario autorizó commits locales separados por petición completada, con mensajes descriptivos, validación previa y cambios no relacionados separados. Su autorización explícita actual permitió el commit local `947dc63ded05bf0afbddb5ad5e77c8a04df9042c` de Discovery, KB e informe revisado. No se realiza push ni publicación hasta su revisión y autorización explícita.
- El [roadmap](../../CHANGES.md) está generado para un único change candidato de turnos; su revisión humana permanece pendiente. No decide stack, persistencia, contratos temporales ni concurrencia, y no crea artefactos Propose ni código.
