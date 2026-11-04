# Evidencia de Skill propia y MCP

## Skill propia

- Nombre: `odontologia-openspec`.
- Necesidad: orientar cambios OpenSpec del sistema odontológico con sus límites de arquitectura, governance, datos ficticios, tests y evidencia.
- Creadora usada: skill global `skill-creator` de Codex. La adaptación toma reglas ya confirmadas en `AGENTS.md`, `CHANGES.md` y la Knowledge Base.
- Integración: `.agents/skills/odontologia-openspec/SKILL.md`, incluida en el repositorio. `AGENTS.md` y `CLAUDE.md` referencian el registro de skills del proyecto; `.atl/skill-registry.md` contiene las reglas compactas.
- Aplicación: durante esta revisión se usaron esas instrucciones para evaluar C-20 como change reciente donde demostrar el flujo, sin modificar ni reabrir su contrato archivado.
- Límite de validación: no se ejecutó benchmark automático de activación ni evaluación ciega; la revisión de contenido es manual y debe ser comprendida por el equipo.

## MCP GitHub

La guía reproducible está en [mcp-github.md](mcp-github.md). En esta preparación se ejecutó una búsqueda real del endpoint `GET /reportes/agenda` en `Nixus32xD/TP-ODONTOLOGIA`; los resultados coincidieron con documentación remota de C-20. La búsqueda fue de lectura y no cambió archivos del repositorio remoto.

## Evidencia para mostrar en el video

1. Abrir el `SKILL.md`, explicar necesidad, adaptación y cómo la descubre el registro.
2. Abrir la guía MCP y mostrar la consulta GitHub ejecutada y sus resultados del repositorio.
3. Mostrar la evidencia C-20 local y explicar que la búsqueda corroboró la documentación; la verificación de tests y runtime proviene de los registros locales, no de GitHub.
4. El equipo debe leer/revisar el contenido y explicar con sus palabras la skill y el MCP antes de presentar la entrega.
