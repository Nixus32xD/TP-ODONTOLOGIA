# Aplicación: Skill + MCP sobre C-21

**TP de Metodología I — 4 de noviembre de 2026**

## Cambio

Se creó C-21 `mejorar-estados-vacios-reportes`, vinculado al panel de C-20. Cuatro escenarios cubren agenda vacía, finanzas vacías con agenda disponible, resultados con datos y error de consulta. El alcance se limita a la presentación React.

**Cierre:** la ficha Skills/MCP adjunta originalmente pedía dejar el change pendiente. La instrucción posterior del usuario pidió archivarlo, y la consigna general del TPI cuenta changes archivados; se siguió esa instrucción y se archivó localmente el 2026-11-04. No se hizo push.

## Uso y hallazgos

La guía `skill-creator` (de la fuente Anthropic, cargada desde la copia de Codex ya disponible) orientó propósito, alcance de activación, salida y revisión de la skill del proyecto. Se revisó críticamente su primer borrador y se acotó al dominio. No se corrió su harness de evaluación automatizada porque requiere `claude`/harness separado; no se afirma ese resultado.

Se usó Context7 MCP: `resolve-library-id` para React devolvió `/reactjs/react.dev`; `query-docs` consultó el renderizado de estados asíncronos JSX. Después, la skill `odontologia-openspec` guio la revisión del contrato y del diff. El informe público de W3C se usó para confirmar `role="status"`, ya que la respuesta de Context7 no definía ese aspecto normativo.

La skill detectó que el caso de éxito vacío no tenía mensaje y que una tabla financiera vacía podía sugerir datos omitidos. Se implementaron mensajes de estado independientes para cada dataset vacío; los resultados con datos conservan tablas y los errores mantienen `role="alert"`.

## Evidencia técnica

- RED: se añadieron casos; 2 fallaron porque faltaba `role="status"` y 3 pasaron.
- GREEN: tests focales `Reportes.test.tsx`: 5/5.
- Validación global: 77 tests frontend aprobados en 13 archivos; `npm run build` pasó.
- OpenSpec: cuatro escenarios en `specs/operational-reporting/spec.md`; se validó en modo estricto y luego se archivó la delta.
- Revisión crítica: el primer texto de la skill duplicaba procedimientos OPSX y era genérico; se acotó a invariantes odontológicos. Context7 confirmó el patrón de UI, pero no ARIA; W3C completó la fuente normativa.

## Alcance y límites de la evidencia

La búsqueda GitHub MCP realizada anteriormente correspondió al change archivado C-20; no se cuenta como aplicación del MCP al C-21. No se ejecutó una prueba con lector de pantalla ni se afirma revisión humana de terceros. La skill y Context7 apoyaron el análisis, pero los tests locales verifican el comportamiento implementado. Los guiones para los videos quedan sólo en el checkout y excluidos de Git.

Archivos principales: `openspec/changes/archive/2026-11-04-mejorar-estados-vacios-reportes/`, `frontend/src/pages/Reportes.tsx`, `frontend/src/pages/Reportes.test.tsx`, `.agents/skills/odontologia-openspec/SKILL.md` y `docs/skills-mcp/mcp-context7.md`.
