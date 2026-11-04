# MCP utilizado: GitHub

## Propósito y capacidad

Se utilizó la integración MCP de GitHub disponible en Codex para buscar contenido del repositorio remoto y contrastarlo con el checkout local. La herramienta `github_search` permite localizar archivos y fragmentos del repositorio; otras herramientas disponibles permiten consultar archivos y metadatos. Para este TP se limita a lectura; no se publicaron cambios mediante el MCP.

## Configuración reproducible

1. En Codex, conectar/autorizar la aplicación GitHub desde Plugins o Apps.
2. Dar acceso al repositorio `Nixus32xD/TP-ODONTOLOGIA` con permisos de lectura suficientes para buscar archivos.
3. En una conversación con Codex, invocar la herramienta GitHub `search` indicando una frase del endpoint y el repositorio. No copiar tokens al repositorio ni a la conversación.
4. Comparar los resultados con los archivos locales. Registrar consulta, resultado y conclusión en la evidencia del change donde se use.

La conexión es provista por el entorno Codex: no hay un proceso MCP propio, manifiesto de servidor local ni credenciales versionadas. La disponibilidad en otra cuenta depende de que conecte la app GitHub.

## Ejecución observada en esta preparación

- Herramienta: MCP GitHub `github_search`.
- Repositorio: `Nixus32xD/TP-ODONTOLOGIA`.
- Consulta: `GET /reportes/agenda`.
- Resultado: encontró `knowledge-base/06_funcionalidades.md`, `CHANGES.md` y `backend/README.md` en el commit remoto `0571390536d50cd68e3b0886fa5988aca6a07eeb`.
- Aporte: permitió contrastar que C-20 reportes está implementado y archivado, y corroborar endpoints JSON/CSV y permisos descritos en la documentación local.
- Límite: esta llamada demuestra búsqueda remota y lectura; no demuestra una modificación remota ni verifica por sí sola el comportamiento de la aplicación.
