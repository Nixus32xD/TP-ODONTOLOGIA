# Skill Registry

Registro de disponibilidad de TP-ODONTOLOGIA, generado el 2026-10-15. Uso del delegador: seleccionar sólo las skills pertinentes e inyectar sus reglas compactas como `## Project Standards (auto-resolved)`. El inventario no obliga a usar todas las skills, instalar dependencias, adoptar un framework ni crear agentes.

Las instrucciones del usuario y el alcance confirmado prevalecen sobre las plantillas. Este registro se versiona por solicitud expresa del usuario; se omite la regla genérica de ignorar `.atl/`. No contiene credenciales, contenido de dotfiles, perfiles personales ni exportaciones de memoria. Los paths globales son ubicaciones de esta máquina, no archivos distribuidos con el repositorio: comprobarlos antes de usar y regenerar el registro en otro equipo.

## Cobertura del escaneo

- Proyecto: `.agents/skills/` presente; `.claude/skills/`, `.gemini/skills/`, `.agent/skills/` y `skills/` ausentes.
- Usuario: `.agents/skills/`, `.config/opencode/skills/` y `.codex/skills/` presentes; `.claude/skills/`, `.gemini/skills/`, `.cursor/skills/` y `.copilot/skills/` ausentes.
- Complementos habilitados pertinentes a la entrega: PDF, documentos y visualizaciones; no se recorrieron cachés históricos ni se incorporaron conectores ajenos al TP.
- Deduplicación por nombre: proyecto primero; entre globales, rutas configuradas de `.agents/skills/` primero, luego OpenCode y Codex. Las seis copias OpenCode se omiten; `active-orchestrator` allí es v2.1 y en la ruta seleccionada es v2.2. `skill-creator` de Codex también se omite por duplicado.
- Excluidos `sdd-*`, `_shared` y `skill-registry` (autorreferencia). Se leyeron SKILL.md completos hasta 200 líneas y frontmatter/secciones de reglas y patrones críticos para los más extensos.
- Resultado: **21 skills únicas**, de las cuales **7 son locales al proyecto** y **14 dependen del entorno del usuario**. Ninguna instalación nueva.

Complementos del catálogo habilitado fuera de este registro temático (disponibles en la sesión, no inexistentes):

| Skills no indexadas | Motivo |
| --- | --- |
| cloud-environment-runtime | El TP usa un checkout local Windows, sin entorno cloud administrado. |
| computer-use | No se requiere operar aplicaciones mediante UI para esta fundación. |
| google-drive, google-docs, google-drive-comments, google-sheets, google-slides | No se solicitaron archivos conectados de Drive, edición nativa ni comentarios externos. |
| plugin-management | No se necesita instalar o conectar plugins. |
| presentations | No hay presentación solicitada en esta etapa. |
| sites | No se solicitó construir ni alojar un sitio. |
| spreadsheets, excel-live-control | La evidencia actual está en Markdown/JSON/PDF, sin workbook ni sesión Excel. |
| template-creator | Se entrega un TP concreto, sin plantilla personal reutilizable solicitada. |
| create-pet, pets | No hay trabajo de mascotas animadas. |

Actualizar este alcance si una tarea posterior requiere alguno de esos entregables. No confundir este registro del TP con un inventario exhaustivo de todos los plugins de la aplicación.

## User Skills

| Trigger | Skill | Full Path |
| --- | --- | --- |
| Fundar un proyecto o continuar una fase de Active Stack | active-orchestrator | `C:/Users/Oficina/.agents/skills/active-orchestrator/SKILL.md` |
| Generar AGENTS.md o CLAUDE.md desde KB y roadmap | agents-md-generator | `C:/Users/Oficina/.agents/skills/agent-instruction/SKILL.md` |
| Elegir o aplicar perfiles de Agency Agents | agents | `C:/Users/Oficina/.agents/skills/agents/SKILL.md` |
| Buscar skills para una necesidad concreta | find-skills | `C:/Users/Oficina/.agents/skills/find-skill/SKILL.md` |
| Crear una base de conocimiento desde documentos o preguntas | kb-creator | `C:/Users/Oficina/.agents/skills/kb-creator/SKILL.md` |
| Crear o actualizar CHANGES.md y dependencias | roadmap-generator | `C:/Users/Oficina/.agents/skills/roadmap-generator/SKILL.md` |
| Crear, mejorar o evaluar una skill | skill-creator | `C:/Users/Oficina/.agents/skills/skill-creator/SKILL.md` |
| Generar o editar imágenes raster | imagegen | `C:/Users/Oficina/.codex/skills/.system/imagegen/SKILL.md` |
| Consultar documentación de productos o API de OpenAI | openai-docs | `C:/Users/Oficina/.codex/skills/.system/openai-docs/SKILL.md` |
| Revisar defectos de un diff, commit o cambio indicado | review-agent | `C:/Users/Oficina/.codex/skills/.system/review-agent/SKILL.md` |
| Listar o instalar skills de Codex a petición | skill-installer | `C:/Users/Oficina/.codex/skills/.system/skill-installer/SKILL.md` |
| Investigar competidores y confirmar los once puntos de Discovery | discovery-research | `N:/Nueva carpeta/TP-ODONTOLOGIA/.agents/skills/discovery-research/SKILL.md` |
| Implementar las tareas de un change existente | openspec-apply-change | `N:/Nueva carpeta/TP-ODONTOLOGIA/.agents/skills/openspec-apply-change/SKILL.md` |
| Archivar un change terminado | openspec-archive-change | `N:/Nueva carpeta/TP-ODONTOLOGIA/.agents/skills/openspec-archive-change/SKILL.md` |
| Explorar requisitos o diseño sin implementar | openspec-explore | `N:/Nueva carpeta/TP-ODONTOLOGIA/.agents/skills/openspec-explore/SKILL.md` |
| Proponer un change con sus artefactos de planificación | openspec-propose | `N:/Nueva carpeta/TP-ODONTOLOGIA/.agents/skills/openspec-propose/SKILL.md` |
| Sincronizar delta specs con specs principales | openspec-sync-specs | `N:/Nueva carpeta/TP-ODONTOLOGIA/.agents/skills/openspec-sync-specs/SKILL.md` |
| Revisar y mantener coherentes artefactos existentes | openspec-update-change | `N:/Nueva carpeta/TP-ODONTOLOGIA/.agents/skills/openspec-update-change/SKILL.md` |
| Leer, generar o comprobar un PDF | pdf | `C:/Users/Oficina/.codex/plugins/cache/openai-primary-runtime/pdf/26.1013.11914/skills/pdf/SKILL.md` |
| Crear o editar documentos Word y revisar su render | documents | `C:/Users/Oficina/.codex/plugins/cache/openai-primary-runtime/documents/26.1013.11914/skills/documents/SKILL.md` |
| Explicar o explorar mediante una visualización en conversación | visualize | `C:/Users/Oficina/.codex/plugins/cache/openai-bundled/visualize/1.0.49/skills/visualize/SKILL.md` |

## Compact Rules

Resúmenes operativos de 5 a 15 líneas por skill. El delegador conserva las restricciones aplicables de la skill original y resuelve conflictos con el pedido concreto; estas reglas no acreditan ejecución ni aprobación de fases.

### active-orchestrator
- Cargar el estado existente y retomar la fase acordada; no reiniciar el proyecto por defecto.
- Delegar la lógica de cada fase a su skill; no reconstruir KB, roadmap ni reglas desde el coordinador.
- Escribir únicamente version, owner y step; preservar las secciones de otras skills.
- Respetar el orden Discovery opcional, KB, roadmap, selección, registro y reglas.
- Avanzar entre fases con autorización del usuario; no instalar skills o dependencias de oficio.
- No hacer commit ni push sin autorización explícita y aplicable a la tarea.

### agents-md-generator
- Comprobar KB y leer stack, índice, roadmap, preguntas abiertas y registro existente.
- Generar AGENTS.md y CLAUDE.md en la raíz con contenido idéntico.
- Derivar reglas del stack real; no adoptar lenguajes o frameworks de los ejemplos.
- Leer reglas globales sólo para evitar duplicados; no copiar contenido personal al repositorio.
- Presentar y confirmar reglas duras nuevas; escribir únicamente las confirmadas.
- Mapear roles a skills existentes; referenciar reglas compactas sin duplicarlas y describir este registro como versionado.

### agents
- Leer guía común e índice de la biblioteca local antes de seleccionar perfiles.
- Localizar y respetar los perfiles expresamente pedidos por el usuario.
- Cargar el mínimo de perfiles complementarios y leer su cuerpo y adaptación.
- Conservar stack, contratos, alcance y herramientas comprobados del proyecto.
- No atribuir métricas o experiencia del personaje al estudiante ni copiar solicitudes de razonamiento interno.
- No interpretar selección automática de perfiles como autorización para agentes, automatizaciones o publicación.

### find-skills
- Precisar dominio y necesidad antes de buscar.
- Comprobar leaderboard y calidad de la fuente; no recomendar sólo por resultados de búsqueda.
- Contrastar reputación, adopción y repositorio del candidato con el objetivo concreto.
- Presentar opciones y utilidad; distinguir disponibilidad de necesidad de instalación.
- Aplicar el modo recomendación de este proyecto; no instalar sin una elección autorizada.

### kb-creator
- Mantener knowledge-base/ en la raíz separado de los documentos fuente en docs/.
- Generar los diez nombres canónicos y README índice; los extras no los reemplazan.
- En modo ingest leer las fuentes y Discovery, conservando su trazabilidad.
- Registrar ambigüedades en preguntas abiertas; nunca inventar stack o requisitos ausentes.
- En modo desde cero preguntar y esperar respuestas antes de generar.
- Actualizar sólo state.kb mediante lectura y escritura conservadora del estado.

### roadmap-generator
- Verificar KB y OpenSpec; leer modelo, funcionalidades, flujos, reglas y preguntas abiertas.
- Escribir CHANGES.md en la raíz con IDs C-NN y nombres kebab-case.
- Incluir estado, scope, dependencias, governance y lecturas concretas por change.
- Explicar dependencias y camino crítico sin marcar planificación como implementación.
- Respetar el único change académico: bootstrap y modelos son tareas internas, sin changes adicionales de producción.
- Escribir sólo state.roadmap, preservando schema v4 y las demás secciones.

### skill-creator
- Capturar objetivo, disparadores y formato esperado antes de redactar.
- Mantener nombre y descripción claros y recursos enlazados con lectura progresiva.
- Evitar capacidades engañosas, extracción de datos y comportamientos no autorizados.
- Preparar casos realistas y comparar ejecución con skill y baseline apropiado.
- Mostrar salidas y evaluación al usuario antes de iterar; conservar versiones y resultados separados.
- Empaquetar sólo el resultado acordado sin modificar silenciosamente la instalación original.

### imagegen
- Preferir la herramienta integrada para generación, edición y transparencias.
- Usar CLI/API únicamente cuando el usuario elija o confirme esa alternativa.
- Inspeccionar referencias y distinguir generación nueva de edición.
- Mantener las restricciones y partes que el usuario pidió conservar.
- No pedir ni imprimir claves en chat; guardar resultados con nombres descriptivos y revisar el resultado.

### openai-docs
- Consultar y abrir documentación oficial del tema exacto antes de responder consultas de OpenAI.
- Preservar modelos expresamente nombrados; no sustituirlos por uno más nuevo.
- Leer como máximo una referencia principal y ampliar sólo si el trabajo lo necesita.
- Citar la página oficial que fundamenta cada afirmación; declarar incertidumbre si falta evidencia.
- Respetar las instrucciones de mayor prioridad sobre inspección local y orden de consulta.

### review-agent
- Revisar en sólo lectura: no editar, comitear, publicar comentarios ni delegar la revisión.
- Leer instrucciones aplicables, diff completo y código/pruebas necesarios para cada hallazgo.
- Para base branch resolver upstream y merge-base antes de comparar.
- Reportar sólo defectos concretos introducidos por el cambio, con escenario demostrable.
- Ordenar hallazgos P0 a P3 y citar una ubicación del diff; si no hay, informar No findings.
- Mencionar limitaciones de prueba y riesgos residuales sin convertir hipótesis en defectos.

### skill-installer
- Listar skills o instalar únicamente las seleccionadas por el usuario.
- Usar scripts provistos, comprobando destino y origen antes de modificar el entorno.
- Abortar si el directorio destino ya existe; no sobrescribirlo silenciosamente.
- Distinguir curated, experimental y system; system ya viene preinstalado.
- Reutilizar credenciales locales sin exponerlas e informar disponibilidad en el próximo turno.

### discovery-research
- Investigar fuentes y completar los once puntos del checklist sin rellenar huecos con suposiciones.
- Usar web-scraper si está disponible; si falta, informar que el scraping automático no corrió.
- No volver a preguntar lo ya resuelto: resumirlo para confirmación.
- Separar hechos documentados, publicidad, hipótesis y preguntas abiertas.
- Confirmar el resumen antes de escribir discovery/discovery.md o state.discovery.
- Escribir sólo state.discovery y conservar las demás secciones.
- No presentar revisión documental del agente como lectura personal del estudiante.

### openspec-apply-change
- Seleccionar el change y consultar status e instructions apply por CLI antes de implementar.
- Leer todos los contextFiles y respetar los paths, schema y tareas devueltos.
- Preservar un store seleccionado en los comandos que lo aceptan.
- Detenerse si el CLI informa blocked o faltan requisitos indispensables; no inventar comportamiento.
- Mantener cambios mínimos y completar cada comportamiento antes de marcar su checkbox exacto.
- Aplicar TDD estricto y suite completa cuando exista runner, sin afirmar pruebas no ejecutadas.
- Separar contexto y consejos de operación de evidencia de cumplimiento y del estado real.

### openspec-archive-change
- Seleccionar y anunciar el change; consultar el grafo real de artefactos y tareas.
- Evaluar todas las delta specs y mostrar el resumen de sincronización antes de confirmar.
- Ejecutar sync solicitado de forma síncrona; verificar specs antes de mover changeRoot.
- No inventar requisitos principales faltantes ni archivar mientras el sync sigue en curso.
- Preservar .openspec.yaml y evitar duplicar el prefijo de fecha del archivo.
- Informar advertencias y respetar confirmaciones, paths y contratos de CLI; este proyecto exige suite verde.

### openspec-explore
- Explorar código y documentos en sólo lectura para aclarar requisitos y alternativas.
- No implementar código ni modificar configuración de workflow en modo Explore.
- Capturar artefactos sólo dentro de un alcance confirmado; una respuesta de diseño no es permiso de escritura.
- Consultar OpenSpec para conocer changes reales, sin inventar su estado.
- Señalar huecos y supuestos; derivar implementación a Propose y luego Apply.

### openspec-propose
- Resolver raíz y contexto con CLI; no inicializar OpenSpec como efecto lateral.
- Aclarar ambigüedades que cambian alcance, comportamiento o aceptación antes de crear el change.
- Crear el change mediante CLI y usar schema, paths y grafo de dependencias reales.
- Leer instructions y archivos de dependencias desde disco antes de cada artefacto.
- Crear el cierre transitivo de applyRequires, respetando artefactos skipped y delegaciones indicadas.
- Aplicar contexto y reglas como restricciones sin copiarlos textualmente en los artefactos.
- Planificar solamente; después de mostrar artefactos detenerse antes de Apply y de código de producto.

### openspec-sync-specs
- Leer delta y specs principales antes de escribir; respetar paths existentes devueltos por CLI.
- Mantener el subconjunto solicitado sin ampliar la operación a capacidades ajenas.
- Consultar instrucciones specs o reutilizar el snapshot recibido de Archive; detenerse ante error o JSON inválido.
- Fusionar inteligentemente y conservar requisitos/escenarios que el delta no modifica.
- No copiar cabeceras ADDED/MODIFIED/REMOVED/RENAMED a specs principales.
- No crear requisitos vacíos ni inventar versiones actuales faltantes; el resultado debe ser idempotente.

### openspec-update-change
- Revisar únicamente artefactos de planificación existentes; nunca código de implementación.
- Consultar status para IDs, schema y existingOutputPaths, sin asumir nombres fijos.
- Preparar propuesta coherente entre artefactos y confirmar cada revisión antes de escribir.
- No avanzar la frontera creando artefactos faltantes ready/blocked ni tocar skipped.
- Crear un archivo de glob parcialmente poblado sólo bajo alcance confirmado, instrucciones frescas y operación que falle si ya existe.
- Si cambia la intención del change, proponer uno nuevo en vez de reemplazar silenciosamente el existente.

### pdf
- Preferir dependencias del runtime y generación reproducible; conservar la fuente editable.
- Ejecutar exitosamente el marcador de operación provisto exactamente una vez antes de autoría; si falta, informar la limitación sin fingir ejecución.
- Extraer texto para contenido y renderizar páginas para verificar maquetación: una comprobación no sustituye a la otra.
- Revisar recortes, superposiciones, tablas, glifos, numeración y legibilidad tras cambios significativos.
- En formularios comprobar árbol AcroForm, valores y apariencias; no aplanar por defecto.
- Citar el resultado final verificado y no presentar un PDF sin revisión visual como terminado.

### documents
- Escribir para destinatario y propósito concretos, en voz del autor sólo con afirmaciones veraces.
- Ejecutar exitosamente el marcador de operación exactamente una vez antes de autoría DOCX; informar si falta sin simular éxito.
- Mantener título claro y estilos de Word coherentes; usar encabezados y tablas semánticos.
- Conservar el formato pedido y preferir ediciones puntuales en documentos existentes.
- No encoger texto para ocultar problemas de espacio ni usar alturas de fila que recorten contenido.
- Renderizar con render_docx.py e inspeccionar todas las páginas después de cambios significativos.
- Corregir recortes, saltos, tablas y glifos antes de entregar; no filtrar tokens internos de citas.

### visualize
- Elegir tabla Markdown o Mermaid para estructuras estáticas suficientes; HTML sólo si aporta exploración.
- Escribir un fragmento HTML literal en una ubicación durable de la tarea, sin html/head/body.
- Usar un ID raíz único, recursos permitidos y menos de 1 MB; no fetch, XHR ni WebSocket.
- Aplicar colores del tema y contraste legible; usar Lucide provisto para iconos.
- Verificar elementos consultados, identificadores JavaScript e interacción principal.
- Emitir la referencia visualize con path absoluto en la respuesta final; exportar o publicar sólo por pedido expreso.

## Project Conventions

[AGENTS.md](../AGENTS.md) y [CLAUDE.md](../CLAUDE.md) existen en la raíz y contienen instrucciones idénticas, consolidadas desde el alcance y las restricciones ya autorizados. No se importan reglas de otros proyectos ni se declara aprobación humana de contratos o reglas técnicas nuevas. El contrato de C-01 usa FastAPI, Python, SQLite, unittest y TestClient por corrección explícita del usuario; evidencias personales y Archive siguen pendientes.

Se actualiza únicamente este índice de convenciones: las 21 skills y sus reglas compactas conservan el inventario previo, sin rescaneo ni instalaciones. Las rutas globales de las otras secciones siguen requiriendo comprobación en cada equipo.

Convenciones y todos los documentos referenciados por AGENTS.md/CLAUDE.md:

| File | Path | Notes |
| --- | --- | --- |
| 02_descripcion_general.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/02_descripcion_general.md` | Documento referenciado por las instrucciones del proyecto |
| README.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/README.md` | Documento referenciado por las instrucciones del proyecto |
| 01_vision_y_objetivos.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/01_vision_y_objetivos.md` | Documento referenciado por las instrucciones del proyecto |
| 03_actores_y_roles.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/03_actores_y_roles.md` | Documento referenciado por las instrucciones del proyecto |
| 04_modelo_de_datos.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/04_modelo_de_datos.md` | Documento referenciado por las instrucciones del proyecto |
| 05_reglas_de_negocio.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/05_reglas_de_negocio.md` | Documento referenciado por las instrucciones del proyecto |
| 06_funcionalidades.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/06_funcionalidades.md` | Documento referenciado por las instrucciones del proyecto |
| 07_flujos_principales.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/07_flujos_principales.md` | Documento referenciado por las instrucciones del proyecto |
| 08_arquitectura_propuesta.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/08_arquitectura_propuesta.md` | Documento referenciado por las instrucciones del proyecto |
| 09_decisiones_y_supuestos.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/09_decisiones_y_supuestos.md` | Documento referenciado por las instrucciones del proyecto |
| 10_preguntas_abiertas.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/knowledge-base/10_preguntas_abiertas.md` | Documento referenciado por las instrucciones del proyecto |
| discovery.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/discovery/discovery.md` | Documento referenciado por las instrucciones del proyecto |
| BITACORA.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/docs/BITACORA.md` | Documento referenciado por las instrucciones del proyecto |
| skill-registry.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/.atl/skill-registry.md` | Documento referenciado por las instrucciones del proyecto |
| CHANGES.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/CHANGES.md` | Documento referenciado por las instrucciones del proyecto |
| design.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/openspec/changes/crear-turno-sin-solapamientos/design.md` | Contrato técnico aplicado por autorización de continuar; no acredita lectura personal |
| AGENTS.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/AGENTS.md` | Convenciones específicas; pareja idéntica, sin decisiones técnicas nuevas |
| CLAUDE.md | `N:/Nueva carpeta/TP-ODONTOLOGIA/CLAUDE.md` | Convenciones específicas; pareja idéntica, sin decisiones técnicas nuevas |

Revisar estas lecturas antes de resolver reglas para C-01. No afirmar implementación, pruebas de producto, revisión personal de fuentes ni instalación de harnesses a partir de este inventario.
