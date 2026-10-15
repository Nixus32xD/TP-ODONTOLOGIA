# Consigna y checklist de entrega

Fuente: [consigna original de Metodología I](consigna/desarrollo-active-stack.pdf), copia del archivo proporcionado `F:\Oficina\Documents\desarrollo-active-stack.pdf`.

Este checklist resume requisitos de la consigna; no acredita su cumplimiento. La bitácora debe registrar la revisión humana de cada etapa y su decisión: Continuar, Ajustar o Parar acá.

## Etapa 0 - Preparación

- [ ] Go, Git y Node instalados; agente de código funcionando. La consigna menciona OpenCode o Claude Code; el trabajo solicitado utilizará Codex y debe dejar explícita esa diferencia.
- [ ] Active Stack en modo Full, con evidencia de instalación y lista de harnesses instalados.
- [ ] Repositorio nuevo con Git y sin código previo.
- [ ] Capturas del instalador finalizado y de los harnesses.

## Etapa 1 - Inicio de la fundación

- [ ] Ejecutar Active Stack dentro del repositorio y comenzar con `openspec init`.
- [ ] Elegir Discovery en la bifurcación; es obligatorio en este TP.
- [ ] Incluir `.active-orchestrator-state.json` con el estado real.
- [ ] Registrar inspección y decisión humana antes de avanzar de etapa.

## Etapa 2 - Discovery

- [ ] Ejecutar `discovery-research` y guardar su checklist de once puntos: problema, usuarios, casos de uso, competidores, funcionalidades necesarias, opcionales, reglas de negocio, integraciones, restricciones, riesgos y preguntas abiertas.
- [ ] Investigar Argentina, Latinoamérica y soluciones internacionales relevantes con fuentes verificables, URL y fecha de consulta.
- [ ] Relevar por producto: identidad/proveedor/país, segmento, modalidad, agenda, turnos digitales, automatización, gestión clínica, administración, integraciones, operación, seguridad/cumplimiento, modelo comercial, fortalezas/limitaciones y adopción evidenciada.
- [ ] A: comparar al menos 15 sistemas, ordenados por relevancia para Argentina. Toda característica sin respaldo público dice **No evidenciado**.
- [ ] B: puntuar de 0 a 5, incluir total ponderado y explicar la escala y el tratamiento de datos no evidenciados.
- [ ] C: analizar estándares, diferenciadores reales, vacíos argentinos y oportunidades.
- [ ] D: recomendar cinco competidores para demo, tres referencias de UX y un MVP con imprescindibles, diferenciadores y etapas posteriores.
- [ ] Distinguir funcionalidades comprobadas de afirmaciones comerciales.
- [ ] Verificación humana: comprobar personalmente al menos cinco fuentes de distintos tipos; registrar afirmación, hallazgo y corrección. La revisión del agente no sustituye esta comprobación.
- [ ] Entregar `docs/discovery/informe-discovery.md`, su PDF y el resultado estructurado de los once puntos en la misma carpeta.

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

- [ ] `knowledge-base/`: diez archivos canónicos de visión, descripción, actores, modelos de datos, reglas de negocio, features, flujos, arquitectura, decisiones y preguntas abiertas.
- [ ] Revisar coherencia con el Discovery, incluyendo duración de prestaciones, sillones/boxes, solapamientos y preguntas sin evidencia.
- [ ] `CHANGES.md`: dependencias, asignaciones con contexto, camino crítico y riesgos, alineados con el MVP.
- [ ] `find-skill`: decidir qué recomendaciones instalar o descartar, con justificación de una línea por recomendación.
- [ ] Generar `.atl/skill-registry.md`.
- [ ] Revisar y confirmar las reglas candidatas; generar `AGENTS.md` y `CLAUDE.md` en raíz. Agregar reglas del dominio cuando corresponda.
- [ ] Registrar inspección y decisión humana de cada etapa.

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
