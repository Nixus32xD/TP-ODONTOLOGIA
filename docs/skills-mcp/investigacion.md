# Investigación: Skill propia y MCP

**TP de Metodología I — 4 de noviembre de 2026**

## Necesidad y change seleccionado

Se revisó el roadmap OpenSpec completo: C-01–C-13 y C-15–C-20 ya estaban archivados; C-14 despliegue estaba excluido. La opción más acotada para demostrar una skill y un MCP sin tocar contratos sensibles era extender C-20 con una mejora de interfaz. Se propuso C-21 `mejorar-estados-vacios-reportes`: comunicar accesiblemente que un reporte consultado con éxito no contiene datos.

## Skill

La guía creadora fue `skill-creator`, disponible en Codex en `C:/Users/Oficina/.agents/skills/skill-creator/SKILL.md`; su fuente es [Anthropic Skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator). Es compatible como guía de escritura de `SKILL.md`, aunque su harness de pruebas apunta a Claude. Codex también documenta su creador integrado `$skill-creator` [en su guía oficial](https://developers.openai.com/plugins/build/skills); no es una función de OpenSpec. Para reproducir en Codex, invocar `$skill-creator`; alternativamente instalar la carpeta del repositorio autor en `.agents/skills/`, comprobarla en la lista de skills y leer su `SKILL.md`. En este entorno ya estaba disponible la copia global; se usó esa guía, no el comando integrado.

La skill del proyecto `odontologia-openspec` ayuda a revisar cambios del dominio mediante invariantes concretos: agenda semiabierta, separación de permisos, auditoría sin datos clínicos, consentimiento en recordatorios, ledger monetario y privacidad de reportes. Para C-21 su aporte fue comprobar que la solución permaneciera en presentación, preservara el acceso de cada dataset y no alterara API ni cálculo. Los procedimientos generales de OpenSpec permanecen en sus skills propias.

El primer borrador era demasiado amplio y repetía OPSX; una revisión crítica lo redujo a reglas de dominio y criterios de revisión. Se registra como skill local versionada del proyecto, no como una funcionalidad provista por OpenSpec. OpenSpec administra cambios y contratos; la skill orienta al agente. No se ejecutó la evaluación automatizada de la creadora, pues su harness está orientado a Claude; se documenta como límite, no como benchmark aprobado.

## MCP

Se compararon Context7 MCP y GitHub MCP Server. GitHub sirve para buscar/leer repositorios y realizar operaciones de Issues, PR o Actions con permisos configurados. El checkout ya ofrecía el código de C-20; consultar GitHub no resolvía el patrón de React que motivaba este change. Context7 permite resolver la biblioteca React y consultar documentación oficial pertinente, con herramientas de lectura. Se eligió Context7 por relevancia y menor alcance de acceso en esta tarea.

La consulta real resolvió React como `/reactjs/react.dev` y pidió orientación sobre renderizado de estados asíncronos en JSX. La respuesta llevó a revisar el estado de datos en la interfaz. Context7 no estableció la semántica normativa de ARIA; se contrastó por separado con W3C: `role="status"` implica anuncio cortés y atómico. Sin datos de pacientes, credenciales ni llamadas a servicios del consultorio.

## Configuración y fuentes

La guía oficial de Context7 para Codex documenta plugin y endpoint remoto `https://mcp.context7.com/mcp`; puede requerir inicio de sesión y las cuotas dependen del plan. No se usó servicio pago ni se guardaron tokens. GitHub MCP también depende de credenciales/permisos de cuenta; el plan y límites particulares de GitHub no se verificaron, así que no se atribuye un costo específico.

La integración de fundación incluye skill, registro `.atl/skill-registry.md`, instrucciones `AGENTS.md`/`CLAUDE.md`, referencias MCP desde `README.md` y documentos de configuración, selección y evidencia. El roadmap enlaza el C-21 preparado.

Fuentes oficiales consultadas el 2026-11-04:

- [Context7: instalación](https://context7.com/docs/installation) y [configuración en Codex](https://context7.com/guides/codex-mcp-setup).
- [Servidor MCP de GitHub](https://github.com/github/github-mcp-server) y [guía de Codex](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-codex.md).
- [React: gestión de estado](https://github.com/reactjs/react.dev/blob/main/src/content/learn/managing-state.md).
- [W3C WAI-ARIA 1.2: status](https://www.w3.org/TR/wai-aria-1.2/#status).
- [OpenSpec](https://github.com/Fission-AI/OpenSpec): CLI de especificación y ciclo de cambios.
- [Anthropic Skills: skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator), consultada 2026-11-04.
- [OpenAI: crear skills en Codex](https://developers.openai.com/plugins/build/skills), consultada 2026-11-04.
