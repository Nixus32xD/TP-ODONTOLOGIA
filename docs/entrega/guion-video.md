# Guion para el video del TPI

Duración objetivo: **9:30** (máximo de la consigna: 10 minutos por equipo). Ajustar nombres, cantidad de integrantes y demostración a lo que realmente puedan mostrar. No afirmar validaciones humanas ni resultados que el equipo no haya revisado.

## Preparación

- Acordar quién habla en cada segmento; cada integrante debe presentarse, hablar y encender cámara al presentarse.
- Dejar backend y frontend funcionando y con datos ficticios preparados. No usar datos reales ni credenciales visibles.
- Abrir README, CHANGES, carpeta de C-20, la skill, la guía MCP, salida real de tests y aplicación.
- La búsqueda MCP demostrada en este trabajo fue de lectura sobre GitHub. No presentarla como edición remota ni como MCP propio.
- Cronometrar una pasada y recortar transiciones. Si todavía no hicieron personalmente una verificación, decirlo como pendiente.

## 0:00–0:30 | Equipo y alcance

**Mostrar:** aplicación o README; cámara encendida para presentaciones.

> «Somos [integrantes] y este es el TPI de Metodología I sobre el sistema odontológico. Vamos a mostrar el estado real del proyecto, sus changes archivados, la skill propia, una herramienta MCP y una demostración breve. Usamos datos ficticios. El roadmap completo es más amplio que lo que se puede explicar en este video.»

Cada integrante agrega: «Soy [nombre y apellido] y participé en [parte que efectivamente realizó]».

## 0:30–2:30 | Changes y trazabilidad

**Mostrar:** `CHANGES.md`; después abrir dos o tres changes completos representativos, por ejemplo C-01, C-11 y C-20. Señalar proposal/design/spec/tasks archivados y evidencia correspondiente. No leer tablas enteras.

> «El proyecto conserva el Discovery y la base de conocimiento del trabajo anterior. El roadmap organiza la evolución por dependencias. Para contar un change como terminado, comprobamos propuesta, implementación, pruebas y archivado; que aparezca en archive por sí solo no alcanza.»

> «C-01 resuelve el alta sin solapamientos de profesional y box. C-11 integra el flujo de recepción con la API. C-20 agrega reportes operativos y financieros JSON/CSV con permisos y sin exportar datos personales o clínicos. Elegimos estos ejemplos porque muestran dominio, interfaz y reportes. Los resultados concretos de sus pruebas están registrados en sus evidencias.»

**Aclaración según equipo:** la consigna pide al menos dos changes relevantes completos por integrante en total grupal, incluidos los del Parcial 2. Verifiquen antes de grabar cuántos integrantes son y cuántos changes cumplen de verdad; no contar changes incompletos.

## 2:30–5:30 | Skill propia y MCP

### Skill (2:30–4:00)

**Mostrar:** `.agents/skills/odontologia-openspec/SKILL.md`, luego `.atl/skill-registry.md`.

> «Creamos `odontologia-openspec` porque los cambios de este sistema necesitan respetar contratos, dependencias, permisos, datos ficticios y evidencia. La redactamos con ayuda de la skill `skill-creator` y la adaptamos a nuestras reglas en AGENTS, el roadmap y la Knowledge Base. La dejamos versionada dentro de `.agents/skills` y referenciada desde el registro para que el agente pueda encontrarla. La revisión que ven es de su contenido; no ejecutamos un benchmark independiente de activación.»

### MCP GitHub (4:00–5:30)

**Mostrar:** la integración GitHub conectada en Codex y la consulta/resultados reales disponibles en la sesión; luego `docs/entrega/mcp-github.md`.

> «Usamos la integración MCP de GitHub que ofrece Codex. La herramienta de búsqueda consultó `GET /reportes/agenda` en nuestro repositorio y encontró el README del backend, el roadmap y la documentación de funcionalidades. Eso permitió contrastar el alcance documentado de C-20. Fue una consulta de lectura: no modificó el repositorio. La conexión depende de autorizar GitHub en el entorno Codex y la guía reproducible no contiene credenciales.»

> «La skill y el MCP cumplen funciones distintas: la skill guía el trabajo del agente; el MCP aporta una herramienta para consultar GitHub. En esta preparación el MCP ayudó a contrastar documentación de C-20. La evidencia de tests/runtime se demuestra con nuestras verificaciones locales, no con la búsqueda remota.»

## 5:30–9:30 | Tests y sistema funcionando

**Mostrar:** salida guardada de suites recientes y luego aplicación real; Swagger si aporta al recorrido. Priorizar un flujo integrado que el backend/frontend sostengan. No ejecutar operaciones destructivas ni improvisar altas con una base desconocida.

> «Acá mostramos resultados de pruebas registrados para [change/suite, comando y resultado exactos]. La suite automatizada comprueba escenarios como [dos ejemplos reales del change]. Después recorremos [flujo disponible]: [paso breve], [respuesta observable] y [resultado en pantalla].»

> «En C-20, agenda y finanzas tienen permisos diferentes; CSV y JSON salen del mismo agregado y el CSV neutraliza fórmulas. La demostración se hace con datos ficticios. El indicador del reporte describe los registros del sistema, no demuestra por sí mismo mejoras clínicas o de productividad.»

**Cierre:**

> «El avance combina planificación, especificaciones, implementación y comprobaciones visibles. Quedan identificados por separado los elementos pendientes de revisión o entrega académica. Gracias.»

## Lista de control antes de enviar

- [ ] Duración total inferior o igual a 10 minutos.
- [ ] Todos los integrantes se presentan y explican una parte.
- [ ] El total de changes válidos satisface `2 × integrantes`; se incluyen sólo changes completos, verificados y archivados.
- [ ] Se ve la skill, su creadora, adaptación, integración y una aplicación explicada.
- [ ] Se ve el MCP conectado, una herramienta real ejecutada, su resultado y aporte.
- [ ] Se muestran pruebas reales y la aplicación corriendo.
- [ ] La pantalla no revela claves, tokens, contraseñas ni datos reales.
- [ ] Se completa aparte el TXT de entrega con enlaces accesibles, comisión, cantidad de integrantes y nombres.

## Pendientes que el guion no acredita

Este texto no prueba participación, cámara, revisión del equipo, cantidad de changes por integrante, ejecución durante la grabación, permisos de enlaces ni entrega del TXT. Verificar cada punto antes de marcarlo como cumplido.
