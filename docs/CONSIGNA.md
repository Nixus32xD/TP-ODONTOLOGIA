# Consigna y checklist de entrega

Fuente: [consigna original de Metodología I](consigna/desarrollo-active-stack.pdf), copia del archivo proporcionado `F:\Oficina\Documents\desarrollo-active-stack.pdf`.

Este checklist resume requisitos de la consigna; no acredita su cumplimiento. La bitácora debe registrar la revisión humana de cada etapa y su decisión: Continuar, Ajustar o Parar acá.

## Etapa 0 - Preparación

- [ ] Go, Git y Node instalados; agente de código funcionando. La consigna menciona OpenCode o Claude Code; el trabajo solicitado utilizará Codex y debe dejar explícita esa diferencia.
- [ ] Active Stack en modo Full, con evidencia de instalación y lista de harnesses instalados.
- [x] Repositorio nuevo con Git y sin código previo.
- [ ] Capturas del instalador finalizado y de los harnesses.

## Etapa 1 - Inicio de la fundación

- [x] Inicializar OpenSpec: `openspec init --tools codex --language es --no-animation`, finalizado con código 0. El flujo completo de Active Stack continúa pendiente.
- [x] Elegir Discovery en la bifurcación; el usuario confirmó continuar el 2026-10-15.
- [x] Incluir `.active-orchestrator-state.json` con el estado real: versión 4, fase `roadmap`; Discovery documental y base de conocimiento registrados.
- [x] Registrar inspección y decisión de continuar desde la inicialización; confirmación explícita de los once puntos de Discovery el 2026-10-15.

## Etapa 2 - Discovery

- [x] Ejecutar `discovery-research` y guardar sus once puntos en [Discovery canónico](../discovery/discovery.md) y `.active-orchestrator-state.json`: problema, usuarios, casos de uso, competidores, funcionalidades necesarias, opcionales, reglas de negocio, integraciones, restricciones, riesgos y preguntas abiertas.
- [x] Registrar la confirmación del alcance por el usuario: consultorio pequeño, primer change de turnos sin solapamientos de profesional y box; propuestas técnicas y preguntas abiertas conservadas como pendientes.
- [x] Investigar Argentina, Latinoamérica y referencias internacionales con fuentes públicas, URL y fecha; accesos fallidos registrados.
- [x] Relevar los campos por producto en quince fichas, conservando límites y datos **No evidenciados**.
- [x] A: comparar 15 sistemas, ordenados por relevancia para Argentina. Once puntos documentales confirmados; comprobación personal de fuentes pendiente.
- [x] B: matriz de 0 a 5, total ponderado, escala y tratamiento de datos no evidenciados.
- [x] C: estándares, diferenciadores, lagunas documentales y oportunidades como hipótesis; no se afirma un vacío de mercado por ausencia de fuentes.
- [x] D: cinco prioridades para demo futura, tres referencias de UX y un MVP acotado. Las demos no se realizaron.
- [x] Distinguir documentación de funciones, afirmaciones comerciales y falta de evidencia; sin pruebas funcionales de los proveedores.
- [ ] Verificación humana: comprobar personalmente al menos cinco fuentes de distintos tipos; registrar afirmación, hallazgo y corrección. La revisión del agente no sustituye esta comprobación.
- [x] Preparar localmente `docs/discovery/informe-discovery.md`, su PDF y los once puntos en `docs/discovery/resumen-para-revision.md`; resultado canónico adicional en `discovery/discovery.md`.
- [ ] Publicar o entregar la versión actualizada del PDF y documentos; requiere nueva autorización explícita. La preparación local no acredita entrega final.

Pesos de la matriz:

| Criterio | Peso |
| --- | ---: |
| Turnos y automatización | 25 % |
| Funcionalidad odontológica clínica | 20 % |
| Integraciones locales y WhatsApp | 15 % |
| Administración, cobros y facturación | 15 % |
| Experiencia del paciente | 10 % |
| Seguridad, exportación y trazabilidad | 10 % |
| Precio y facilidad de adopción | 5 % |

## Etapas 3 a 5 - Fundación

- [x] [`knowledge-base/`](../knowledge-base/README.md): diez archivos canónicos de visión, descripción, actores, modelos de datos, reglas de negocio, features, flujos, arquitectura, decisiones y preguntas abiertas, más un índice; generados desde los documentos existentes.
- [ ] Revisar coherencia con el Discovery, incluyendo duración de prestaciones, sillones/boxes, solapamientos y preguntas sin evidencia.
- [x] [`CHANGES.md`](../CHANGES.md): dependencias, asignaciones con contexto, camino crítico y riesgos del único change candidato `C-01: crear-turno-sin-solapamientos`, alineado con el MVP.
- [ ] Revisar humanamente el roadmap y registrar la decisión; generarlo no acredita su aprobación.
- [ ] `find-skill`: decidir qué recomendaciones instalar o descartar, con justificación de una línea por recomendación.
- [ ] Generar `.atl/skill-registry.md`.
- [ ] Revisar y confirmar las reglas candidatas; generar `AGENTS.md` y `CLAUDE.md` en raíz. Agregar reglas del dominio cuando corresponda.
- [ ] Registrar inspección y decisión humana de cada etapa.

La generación local de la base de conocimiento no acredita su revisión humana ni resuelve por defecto stack, persistencia, intervalos o concurrencia.

## Etapa 6 - Un change completo

- [ ] Elegir una sola funcionalidad pequeña del MVP y justificarla en dos o tres líneas en `proposal.md`.
- [ ] Explore: relevar problema y código actual; conservar resumen del relevamiento.
- [ ] Propose: generar `proposal.md`, `design.md`, `specs/` y `tasks.md`; revisar el spec completo y registrar correcciones reales con Ajustar cuando correspondan.
- [ ] Especificar al menos tres escenarios dado/cuando/entonces: feliz, error de negocio y borde.
- [ ] Apply: implementar el contrato aprobado. Si falta una decisión, volver a Propose.
- [ ] Verify: ejecutar tests por cada escenario y health checks aplicables; documentar comandos y resultados. No archivar con pruebas fallando.
- [ ] Archive: archivar el change y actualizar las especificaciones y el estado.

La implementación puede ser API o módulo de dominio; la interfaz gráfica no es obligatoria. La elección del stack deriva de la base de conocimiento.

## Etapa 7 - Memoria

- [ ] Mostrar decisiones, hallazgos y convenciones guardados en Engram para este proyecto.
- [ ] Realizar una consulta que recupere contexto de una sesión anterior y explicar su utilidad en el video.

## Entrega final

- [ ] Repositorio con fundación, Discovery, specs vigentes, change archivado, implementación y tests.
- [ ] README suficiente para clonar, instalar y ejecutar las pruebas.
- [ ] Historial de commits que muestre el proceso, no un único commit final; participación individual demostrable si es grupal.
- [ ] PDF profesional: portada, resumen ejecutivo de hasta una página, A, B, C, D, verificación de fuentes y referencias completas.
- [ ] Video de 8 a 12 minutos, con pantalla trabajando realmente, revisión de Propose y Ajustar, tests, Archive y consulta Engram. Cada integrante participa y enciende cámara al presentarse.
- [ ] Reflexión de 1 a 2 páginas escrita por los estudiantes: errores del Discovery, uso de Ajustar, valor de la especificación, utilidad de la fundación, participación y declaración de uso de IA.
- [ ] Sin secretos ni datos reales de pacientes; sin contactar proveedores ni crear cuentas con datos personales para investigarlos.

## Evaluación

| Criterio | Puntos |
| --- | ---: |
| Discovery | 25 |
| Verificación de fuentes | 10 |
| Fundación | 20 |
| Change OPSX | 25 |
| Video | 10 |
| Reflexión | 5 |
| Trazabilidad y participación | 5 |
| **Total** | **100** |
