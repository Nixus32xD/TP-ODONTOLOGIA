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
- `.active-orchestrator-state.json`: versión 4, fase actual `agents`; Discovery documental y base de conocimiento registrados en sus secciones propias.
- `openspec list --json`: raíz `N:/Nueva carpeta/TP-ODONTOLOGIA`; inicialmente sin changes. Ahora existe `crear-turno-sin-solapamientos`, con planificación completa y Apply implementado; consultar progreso actual por CLI.

Estos resultados verifican inicialización y estado del flujo. El inventario inicial no era evidencia funcional; ahora la suite de producto verifica 43 tests.

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
- La [base de conocimiento](../../knowledge-base/README.md) está generada desde los documentos existentes: diez canónicos y un índice. Su contrato técnico se aplicó con la autorización de continuar; conserva pendientes de evidencia académica; no acredita revisión humana de la KB. Ahora existe módulo, demo y suite; la evidencia funcional se registra por separado.
- La edición del informe y del PDF usa primera persona sólo para elecciones veraces del estudiante y declara la investigación documental asistida por IA. No atribuye al estudiante las comprobaciones del agente.
- El PDF actualizado tiene 56 páginas y SHA-256 `d9faa8743d5cffae94a82f90589fbd81563069406656defb38290ae2040c126e`. Incluye anexo 18 con la revisión documental delegada, conserva 105 puntajes y declara pendientes las cinco lecturas personales. La QA actual está registrada en la [bitácora](../BITACORA.md).
- El registro de skills quedó publicado en `main` en `197be16a2eed4b8ea0c0dbcfcfa4cd601a38d59c`. Las instrucciones y Propose se publicaron después con autorización hasta 5093070; la implementación nueva conserva el permiso de commit local validado, sin extender el push a avances futuros. La entrega docente final sigue pendiente y no se presume permiso universal futuro.
- El [roadmap](../../CHANGES.md) está generado para un único change candidato de turnos; su revisión humana permanece pendiente. No decide stack, persistencia, contratos temporales ni concurrencia, su generación sola no acreditaba código; ahora C-01 tiene implementación y pruebas.

- La [selección de skills](../fundacion/seleccion-skills.md) reutiliza existentes y no instala herramientas nuevas. El [registro del proyecto](../../.atl/skill-registry.md) conserva las 21 skills y sus reglas compactas, y enlaza las convenciones del proyecto. [AGENTS.md](../../AGENTS.md) y [CLAUDE.md](../../CLAUDE.md) están generados con contenido idéntico, consolidando restricciones previas sin elegir stack ni crear reglas técnicas nuevas. No hubo rescaneo ni instalaciones.
- La [revisión delegada de seis fuentes](../discovery/revision-documental-2026-10-15.md) precisó Denteo, Dentalink e Infomed. La comprobación personal requerida por la consigna permanece no acreditada.


## Registro histórico de Propose preparado

- [Exploración](../exploracion/alta-turno.md) y cuatro artefactos de C-01 generados mediante el flujo del CLI; validación estricta pasó para un change, sin incidencias.
- Runtime observado: Python 3.12.14, SQLite 3.53.1 y unittest importable. Son comprobaciones del entorno, no pruebas de agenda.
- Python 3.12+, SQLite, módulo local y las reglas temporales son la propuesta del agente; aceptación de contrato pendiente. Sin instalaciones, código de producto, DB creada ni Apply.


## Apply y verificación técnica

El usuario autorizó publicar los commits pendientes y continuar; remoto main confirmado en 509307025550d183493b5a56fa2d16fd18d0651f. La implementación nueva queda en commit local para revisión, sin nuevo push automático.

Módulo Python 3.12.14/SQLite 3.53.1, sin dependencias nuevas ni servicios externos. 43 tests verdes, siete carreras por suite con 14 procesos spawn reales, rollback/contención y demo verificada. [Evidencia TDD y trazabilidad](implementacion-turnos.md). No se versionaron DB ni datos reales. Archive y revisión personal de fuentes siguen pendientes.
