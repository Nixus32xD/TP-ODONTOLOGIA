# MCP elegido: Context7

Fecha de verificación: 2026-11-04.

## Comparación y selección

| Candidato | Qué aporta | Conexión/permisos | Ajuste al C-21 |
| --- | --- | --- | --- |
| **Context7 MCP — elegido** | Resuelve una biblioteca y consulta documentación/código de ejemplo vigente. | Servidor remoto `https://mcp.context7.com/mcp`; plugin de Codex con inicio OAuth o configuración MCP directa. Las consultas consumen cuota; el plan gratuito publicado incluye 1.000 llamadas mensuales. Sólo consultamos documentación pública. | C-21 toca React y un flujo asíncrono; permite verificar el patrón React actual antes de cambiar la UI. No puede inspeccionar ni modificar el repo. |
| GitHub MCP Server | Busca y lee repositorios/código; también puede gestionar Issues, PR y Actions. | Servidor oficial remoto o local; OAuth/PAT según host. Sus herramientas pueden escribir; la configuración debe reducir permisos/toolsets si sólo se necesita lectura. | Puede consultar el código/issues del repositorio, pero el checkout ya contiene el componente y tests que C-21 necesita. Tiene menos valor para resolver la duda de React y mayor superficie de permisos. |

No se contrató servicio ni se configuró una API key para esta consulta. El uso de Context7 depende de disponibilidad del plugin y su cuota/autenticación de cuenta. Los planes de GitHub del usuario no se verificaron; no se presupone que el producto GitHub sea gratuito.

## Configuración reproducible en Codex

### Opción recomendada: plugin oficial

En una terminal con Codex:

```powershell
codex plugin marketplace add upstash/context7
codex plugin add context7@context7-marketplace
```

Completar el inicio de sesión del navegador y abrir una conversación nueva para que Codex cargue el plugin. La documentación vigente también permite añadir el servidor remoto `https://mcp.context7.com/mcp` directamente a la configuración MCP de Codex; no guardar una API key en el repositorio.

### Comprobar conexión y uso

1. En Codex, confirmar que están disponibles `resolve-library-id` y `query-docs` de Context7 (o consultar `codex mcp list` si se configuró desde CLI).
2. Resolver el identificador oficial con una consulta como `React` + el objetivo de búsqueda.
3. Consultar `query-docs` con el identificador devuelto; comprobar que la respuesta trae fuente y contenido de la documentación.
4. Contrastar el resultado con el contrato local y registrar límites. Para C-21 se contrastó la semántica ARIA adicionalmente con W3C.

## Límites de acceso para este TP

- Las herramientas seleccionadas son de consulta de documentación pública; no envían solicitudes al backend odontológico ni acceden a pacientes.
- No pasar información clínica, tokens, datos privados ni código confidencial a las consultas.
- El resultado de Context7 no reemplaza la documentación normativa de accesibilidad, los tests locales ni una revisión con lector de pantalla.
- El servidor y plugin son externos; si otro integrante no tiene la integración, debe conectarla antes de reproducir la llamada. La configuración local de Codex no se versiona.

## Fuentes consultadas

- GitHub, [Context7 MCP — instalación oficial](https://context7.com/docs/installation), consultada 2026-11-04.
- Context7, [guía de configuración para Codex](https://context7.com/guides/codex-mcp-setup), consultada 2026-11-04.
- GitHub, [servidor MCP oficial de GitHub](https://github.com/github/github-mcp-server), consultado 2026-11-04.
- GitHub, [instalación de GitHub MCP Server en Codex](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-codex.md), consultada 2026-11-04.
- W3C, [WAI-ARIA 1.2: role=status](https://www.w3.org/TR/wai-aria-1.2/#status), consultada 2026-11-04.
