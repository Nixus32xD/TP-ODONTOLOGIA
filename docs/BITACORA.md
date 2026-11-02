# Bitácora del proceso

## 2026-10-15 - Preparación

- **Decisión del usuario:** construir una entrega propia desde cero.
- **Destino:** [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).
- **Publicación autorizada:** realizar avances con commit y push por hitos, conservando un historial del proceso.
- **Trabajo de esta etapa:** documentación inicial, checklist de la consigna e inventario del entorno. Todavía no hay código de producto ni pruebas.
- **Alcance posterior:** Discovery y fundación para seleccionar una sola funcionalidad verificable. El stack y el change aún no están decididos.
- **Revisión del usuario:** pendiente. No se registra Continuar, Ajustar ni Parar acá hasta recibir una decisión real.

Cada entrada posterior debe indicar qué cambió, evidencia disponible, resultado de la revisión y siguiente paso. Los commits y resultados de ejecución se anotan después de ocurrir.

## 2026-10-15 - Inicialización de OpenSpec

- **Primer hito publicado:** commit `fd8c209`, preparación documental, enviado mediante `git push -u origin main` al repositorio de entrega con resultado exitoso.
- **Comando ejecutado:** `openspec init --tools codex --language es --no-animation`, código de salida 0.
- **Resultado:** `openspec/config.yaml` con esquema `spec-driven` y seis skills en `.agents/skills/`: Explore, Propose, Update Change, Apply Change, Sync Specs y Archive Change.
- **Estado de Active Stack:** versión 4, `step: discovery`. Es la siguiente fase pendiente; no acredita investigación realizada ni revisión humana aprobada.
- **Validación:** `openspec list --json`, código de salida 0, devolvió `changes: []` para `N:/Nueva carpeta/TP-ODONTOLOGIA`.
- **Comprobaciones adicionales:** `openspec validate --all --json`, código de salida 0, validó 0 elementos porque todavía no hay specs ni changes. El JSON del estado se parseó correctamente. Estas comprobaciones no son tests de producto; todavía no existe implementación.
- **Pendientes:** revisión del usuario, disponibilidad de `discovery-research`, Go, evidencia del modo Full y capturas. El video y la evidencia de recuperación de memoria corresponden a etapas posteriores.
- Este hito se versiona junto a configuración, estado y skills; la publicación se comprueba contra el SHA remoto después del commit.

## 2026-10-15 - Continuar a Discovery

- **Revisión del usuario:** después de los dos avances publicados, respondió «Dale» a continuar con Discovery e incorporar `discovery-research` solamente en este proyecto.
- **Hito anterior publicado:** `00eaa9b99442598cb90c40f349501171c222080a`; SHA local/remoto comprobado y carpeta limpia antes de este avance.
- **Skill incorporada:** `Group-Active-IA/discovery-research`, commit `dd7efb7d044ea3a683b6665a3df9d949856b417f`, bajo `.agents/skills/discovery-research`, sin instalación global.
- **Ajuste:** el proveedor todavía usa `jr-orchestrator`; se sustituyó mecánicamente por `active-orchestrator` para conservar un único estado. Se conserva la licencia y se documenta la procedencia en la skill.
- **Método:** lectura pública de fuentes oficiales; no se ejecutó `web-scraper`, no se contactan proveedores ni se crean cuentas. Las fichas y el informe serán material para revisión, no pruebas de ejecución del producto.
- **Pendiente:** revisar el informe y confirmar los once puntos antes de escribir `discovery/discovery.md` y la sección `state.discovery`. La aprobación de inicio no equivale a aprobación de resultados ni a verificación personal de fuentes.

### Enfoque confirmado durante la investigación

- El usuario confirmó: «Sí, consultorio pequeño y primer change de turnos».
- Recepción gestionará turnos de varios profesionales y boxes; se propone como primer change crear un turno evitando solapamientos por profesional y por box.
- WhatsApp, pagos e historia clínica quedan para etapas posteriores. La propuesta del agente y la confirmación se registraron antes de sintetizar el MVP.
- No se decidió todavía stack, API frente a módulo, persistencia ni una garantía de concurrencia. Estos puntos deben quedar explícitos para la fundación y el diseño.

### Investigación documental y revisión cruzada

- Se redactaron quince fichas de producto en `docs/discovery/fuentes/`, más las referencias del marco argentino, con fecha 2026-10-15 y fuentes públicas oficiales.
- Se añadieron seis comprobaciones documentales del agente en `docs/discovery/verificacion-fuentes.md`; la comprobación personal del estudiante sigue pendiente.
- La revisión cruzada corrigió motivos y puntajes de integraciones: WhatsApp y oferta local no se deducen de Google Calendar, APIs genéricas ni integraciones de otros países. Los totales se calculan desde los siete puntajes registrados, no a partir de estimaciones previas.
- Se distinguieron GESDEN ONE/G5, anuncios en prelanzamiento, doble reserva advertida frente a rechazada y pagos de suscripción frente a cobros clínicos.
- Las lecturas divergentes de condiciones Denteo se conservaron como incertidumbre; no se decidió arbitrariamente qué versión era definitiva.
- **Estado:** investigación e informe para revisión. No se ha aprobado el resumen final ni se escribió la sección `state.discovery`.

### Informe preparado para revisión

- Se publicaron las fuentes como `ea2bd17f4f62cb449f16394e2f98f691c7583344` en `main`; las herramientas se habían incorporado en `14b7fff`.
- El usuario pidió continuar y retirar la mención a otros repositorios de trabajos prácticos de la documentación actual. Se aplicó la edición al README y al registro inicial.
- Se generaron `informe-discovery.md`, `informe-discovery.pdf`, `matriz-evidencia.json` y `resumen-para-revision.md`. El PDF contiene el informe principal, las quince fichas, marco argentino y once puntos: 55 páginas, identificado como borrador.
- **Verificación:** ejecución de `tools/render_discovery.py` con el Python del runtime disponible, salida 0; quince productos, 105 puntajes, pesos que suman 100 y totales exactos. Se contrastaron los hashes de las quince fichas con texto UTF-8 y finales de línea normalizados.
- **Documentación:** 68 enlaces locales válidos, sin tablas pendientes de consolidar. El PDF contiene los textos esperados, sin caracteres de sustitución ni texto fuera de los límites de página. Se renderizaron todas las páginas con `pdftoppm` y se revisaron las vistas de conjunto y tablas principales.
- **OpenSpec:** `openspec validate --all --json` finalizó con salida 0 y cero elementos; no representa tests de producto. `git diff --check` pasó. No hay implementación ni suite de comportamiento aún.
- **Pendiente:** revisión y confirmación del resumen de once puntos antes de crear el resultado canónico de Discovery y su sección de estado. La comprobación personal de al menos cinco fuentes, identificación del integrante, capturas, video y reflexión siguen pendientes.

## 2026-10-15 - Discovery confirmado y continuación a la base de conocimiento

- **Revisión real del usuario:** confirmó explícitamente los once puntos de Discovery y autorizó continuar con `discovery-research` y el siguiente paso pendiente del TP. La decisión registrada es Continuar; las preguntas abiertas conservan su estado pendiente.
- **Alcance confirmado:** entrega propia desde cero para un consultorio pequeño; recepción registra turnos de varios profesionales y boxes, evitando solapamientos de cada recurso. WhatsApp, pagos e historia clínica siguen postergados.
- **Resultado canónico:** `discovery/discovery.md`, resumen confirmado en `docs/discovery/resumen-para-revision.md` y sección `discovery` del estado. Se conservan quince fichas de competidores y las limitaciones de la investigación documental asistida por IA.
- **Siguiente fase:** `.active-orchestrator-state.json` conserva versión 4 y pasa a `step: kb`. Se generó la [base de conocimiento](../knowledge-base/README.md) desde las fuentes disponibles, con diez documentos canónicos más un índice; `state.kb` registra su procedencia y archivos. No se decide por defecto stack, API o módulo, persistencia, intervalos ni estrategia de concurrencia.
- **Edición autorizada:** revisar y ajustar la voz del informe y su PDF en primera persona cuando sea veraz, sin pedir aprobación para decisiones editoriales rutinarias. La confirmación del alcance puede expresarse como elección del estudiante; las seis comprobaciones documentales siguen atribuidas al agente.
- **Publicación vigente:** no realizar commit, push ni publicación sin nueva autorización explícita. Esta instrucción reemplaza el permiso anterior por hitos para el trabajo actual; no altera ni elimina el historial ya publicado.
- **Verificación:** los resultados de la nueva generación y revisión del PDF se registrarán al finalizar; esta entrada no acredita pruebas aún no ejecutadas ni revisión humana de la base de conocimiento.
- **Comprobación documental de la KB:** se comprobaron once archivos, los seis campos mínimos de `kb.discovery`, las once rutas del estado y la coincidencia del problema con Discovery; 83 enlaces locales de KB y metadatos existen. La revisión del agente conservó separadas las reglas confirmadas de las propuestas temporales, sin detectar contradicciones de alcance. `git diff --check` pasó para los cuatro metadatos editados. Estas comprobaciones no son tests de producto ni revisión humana.
- **Pendientes:** mi verificación personal de al menos cinco fuentes, identificación expresa del integrante, Go y evidencia Full/harnesses, capturas, video y reflexión; después de la base de conocimiento siguen roadmap y propuesta del primer change. No hay implementación ni tests de comportamiento.

### Verificación final del cierre y la KB

- Discovery canónico confirmado; `state.discovery` conserva quince competidores y verificación personal pendiente. `state.kb` registra ingestión de documentos; los diez canónicos y el índice existen. No se alteraron las secciones ajenas durante cada actualización.
- El PDF final tiene 55 páginas y declara primera persona veraz, asistencia de IA y cinco verificaciones personales pendientes. Se revisaron 55 renders, vistas de conjunto y páginas detalladas. SHA-256: `32bef0a07299913ca2e163ffd5a966827ae617989eaa47aa5ce0bd5f249fc099`.
- La comprobación final validó 146 enlaces locales, los 105 puntajes/totales y los hashes de las quince fichas, sin cambios de contenido factual respecto del hito anterior. `git diff --check` pasó; `openspec validate --all --json` pasó con cero elementos, sin representar pruebas de producto.
- HEAD permanece en `b837eabcb9a8a597989c7a83b957238ccd815fd1`; staging vacío. Todos los cambios de esta etapa quedan locales, sin commit, push ni publicación. Las modificaciones previas del parcial PHP permanecen intactas.

## 2026-10-15 - Commit autorizado y continuación al roadmap

- **Autorización actual:** el usuario pidió «haz commit y continua con lo siguiente despues de esto». Esta instrucción autoriza el commit del avance anterior; su preferencia vigente permite commits locales por petición completada, con mensajes descriptivos, validación previa y cambios no relacionados separados. Push y publicación requieren revisión y autorización explícita adicionales.
- **Hito local realizado:** `947dc63ded05bf0afbddb5ad5e77c8a04df9042c`, mensaje `docs: cerrar Discovery y crear KB con informe revisado`; 22 archivos de Discovery, base de conocimiento, PDF revisado y metadatos del mismo alcance. No se publicó este commit.
- **Validación previa al commit:** `git diff --check` finalizó con salida 0; se comprobaron 146 enlaces locales sin roturas, quince productos y 105 puntajes con totales y hashes sin cambios factuales frente al hito anterior. El PDF conserva 55 páginas y el SHA-256 registrado arriba, declara asistencia de IA y deja pendientes las cinco verificaciones personales. `openspec list --json` devolvió `changes: []`; `openspec validate --all` finalizó con salida 0 y cero elementos, sin representar tests de producto.
- **Continuación autorizada:** generar el roadmap del único change funcional candidato `C-01: crear-turno-sin-solapamientos`. No se crean todavía artefactos Propose, implementación ni pruebas de producto; stack, persistencia, contratos temporales y concurrencia siguen abiertos.
- **Adaptación de la plantilla:** la plantilla de `roadmap-generator` plantea un C-01 de fundación genérica; para respetar la consigna de una sola funcionalidad completa, esa preparación queda integrada al único change funcional de turnos. No se agrega un change de infraestructura independiente.
- **Compatibilidad de estado:** el guard de versión 2 de la skill está desactualizado frente al estado instalado de versión 4. Se conserva la versión 4 y se aplica el mismo límite de escritura: el generador sólo actualiza `state.roadmap`, y el coordinador administra `step`. No se modifican skills globales.
- **Revisiones humanas y entrega pendientes:** la autorización de continuar no acredita revisión humana del contenido de la KB ni del roadmap. Siguen pendientes verificación personal de cinco fuentes, identificación del autor, evidencia de Go/Full/harnesses, capturas, video y reflexión.
- **Resultado documental:** se generó [CHANGES.md](../CHANGES.md) con el único candidato C-01, dependencias, asignaciones con contexto, camino crítico, riesgos y lecturas de la KB. `state.roadmap` registra el resultado y `step` queda en `roadmap`; la KB conserva diez canónicos más su índice. Sigue pendiente la revisión humana del contenido. El próximo paso de fundación es seleccionar skills y generar su registro.
- **Comprobación de metadatos:** los 21 enlaces locales de README, checklist, inventario y bitácora existen; `git diff --check` de esos cuatro archivos finalizó con salida 0. Se comprobó la concordancia documental con el único candidato C-01 del roadmap; esta comprobación no es una prueba de producto ni una revisión humana. La validación independiente del roadmap y su commit corresponden al coordinador.
- **Validación independiente del coordinador:** 158 enlaces locales válidos, estado de versión 4 preservado salvo `step` y `roadmap`, y un único candidato C-01. Los hashes de contenido Git del PDF, matriz y renderer coinciden con HEAD; `git diff --check` finalizó con salida 0. No representa pruebas de producto ni revisión humana.

## 2026-10-15 - Revisión documental delegada y selección de skills

- **Autorización:** el estudiante pidió delegar la revisión de fuentes por falta de disponibilidad, corregir lo necesario explicando motivos, presentar el avance, hacer commit y push a main y continuar con la siguiente tarea. No se atribuyen lecturas personales que no realizó.
- **Publicación comprobada por el coordinador:** los commits `947dc63` y `e581b94` quedaron publicados; `git ls-remote` confirmó `e581b94e6c9605dac8f4d26afd41ccce906b1e78` en `main`. Los cambios de esta nueva etapa todavía se preparan para validación y publicación autorizada.
- **Contraste documental:** [seis fuentes oficiales revisadas de nuevo por IA](discovery/revision-documental-2026-10-15.md). Denteo: lectura actual permite fechar cupos WhatsApp y modalidades de pago de suscripción, conservando divergencias previas; Dentalink: precisar tráfico cifrado sin extender a reposo/certificación auditada; Infomed: registrar contraste del texto indexado oficial por fallos intermitentes de acceso directo. Las otras afirmaciones se confirmaron con sus límites; no se inventaron errores.
- **Integridad académica:** la asistencia está declarada. La revisión técnica delegada no acredita las cinco comprobaciones personales requeridas por la consigna; siguen pendientes junto con identificación del integrante, evidencia de entorno, video y reflexión.
- **PDF:** informe y anexo 18 actualizados, 56 páginas; SHA-256 `d9faa8743d5cffae94a82f90589fbd81563069406656defb38290ae2040c126e`. Quince productos y 105 puntajes/totales sin cambios; hash de Denteo actualizado por precisión editorial de su ficha.
- **Fundación:** [selección de skills](fundacion/seleccion-skills.md) documentada: reutilizar siete locales y herramientas globales existentes; React descartado del alcance actual y Playwright/pruebas específicas diferidos hasta el stack. No se instalaron skills ni dependencias. `step: find-skill`; generar el registro es lo siguiente. Stack y contrato de producto siguen abiertos.

## 2026-10-15 - Registro de skills del proyecto

- **Autorización actual:** el usuario pidió generar el registro y, al terminar, hacer commit y subirlo. El permiso comprende el registro y los metadatos relacionados en `main`; no acredita por sí mismo un push ejecutado ni una autorización universal futura.
- **Hito anterior publicado:** revisión documental delegada y selección de skills en `5d5a4a90895164c86e0a51aa0d1eb771421bfcb1`. Las entradas anteriores describen el estado histórico de cada etapa.
- **Resultado:** [registro de skills](../.atl/skill-registry.md) generado a partir de la selección existente y del alcance del único change de turnos. No se instalaron nuevas skills ni dependencias. El coordinador administra `step: registry` y el generador registra su sección propia del estado; la versión permanece en 4.
- **Alcance pendiente:** generar el registro no finaliza la fundación ni crea `AGENTS.md` o `CLAUDE.md`. Stack, persistencia, intervalos y concurrencia siguen abiertos. También siguen pendientes las revisiones humanas de KB/roadmap, las cinco comprobaciones personales de fuentes y los entregables de entorno, video y reflexión.
- **Siguiente paso:** revisar las reglas candidatas y generar las instrucciones específicas del proyecto. No hay implementación ni pruebas de comportamiento del producto.
- **Validación documental:** 21 bloques con 5–15 reglas cada uno, 28 rutas de archivo existentes y 181 enlaces locales válidos. Estado versión 4 preservado salvo `step` y `registry`; PDF, matriz y renderer sin cambios. `git diff --check` pasó. No representa pruebas de producto ni revisión humana de las reglas futuras.

## 2026-10-15 - Instrucciones específicas del proyecto

- **Autorización:** el usuario respondió «Dale hazlo» a generar las reglas y AGENTS.md/CLAUDE.md después del registro. Se consolidan únicamente alcance y restricciones ya autorizados; no se atribuye una revisión humana nueva de contratos, KB, roadmap ni fuentes.
- **Hito anterior publicado:** registro de skills en `197be16a2eed4b8ea0c0dbcfcfa4cd601a38d59c`. La preferencia vigente permite commit local por petición completada después de validar; esta etapa no presume autorización nueva para push o publicación.
- **Resultado:** [AGENTS.md](../AGENTS.md) y [CLAUDE.md](../CLAUDE.md) equivalentes, con contexto del consultorio, lecturas de KB y roadmap, skills disponibles y restricciones del único change. El registro añade estas convenciones sin cambiar sus 21 skills ni sus reglas compactas; no se rescaneó ni instaló nada.
- **Estado:** fase `agents`, con sección propia de la generación. La creación documental no acredita fundación completa, código de producto ni pruebas de comportamiento.
- **Pendientes:** decisiones de stack, API o módulo, persistencia, intervalos y concurrencia antes de Propose; revisiones humanas aún no acreditadas, cinco lecturas personales de fuentes, identidad académica, evidencia de Go/Full/harnesses, capturas, video y reflexión.
- **Validación de metadatos:** 53 enlaces locales existentes en los seis archivos relacionados; todos los documentos referenciados por AGENTS.md figuran en Project Conventions. Inventario de 21 skills y texto anterior a Project Conventions idénticos a HEAD. No representa pruebas de producto ni revisión humana.
- **Validación independiente:** AGENTS.md y CLAUDE.md idénticos byte a byte; tabla tecnológica igual a KB 02, ocho reglas consolidadas y 225 enlaces locales válidos. Estado v4 preservado salvo `step` y `agents`; PDF, matriz y renderer sin cambios. `git diff --check` pasó. No se ejecutaron pruebas de producto: todavía no hay implementación ni runner acordado.

## 2026-10-15 - Propuesta técnica del único change

- **Petición:** el usuario pidió continuar con la definición de stack, persistencia y reglas temporales para proponer el alta. La fase se limita a planificación; no se inicia Apply ni se atribuye revisión humana del contrato.
- **Exploración:** se contrastaron instrucciones, KB, roadmap, registro y configuración. Antes de crear el change no había specs, implementación ni tests de agenda. El runtime observado ofrece Python 3.12.14, SQLite 3.53.1 y unittest; importar esos módulos no representa ejecución de pruebas de producto. El resumen está en [exploración](exploracion/alta-turno.md).
- **Elección propuesta:** módulo Python 3.12+, SQLite local y unittest, sin framework, servidor ni dependencias externas del producto. Se documentaron alternativas y respuestas o exclusiones de Q01–Q08 en [design.md](../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md); no se promovieron a decisiones humanas aprobadas.
- **Contrato propuesto:** intervalos semiabiertos, adyacencia, offsets explícitos, precisión de minutos y persistencia UTC; prioridad de conflicto del profesional; catálogos ficticios; sin política de solapamiento del paciente, horarios, estados ni idempotencia. Competencia limitada a la operación sobre un mismo archivo en disco local, a verificar con procesos reales.
- **OpenSpec:** raíz resuelta por `openspec context --json`; change creado mediante `openspec new change crear-turno-sin-solapamientos`. Se consultaron instrucciones y dependencias antes de escribir propuesta, spec, diseño y tareas. La spec principal permanece sin crear hasta Archive.
- **Validación:** `openspec validate crear-turno-sin-solapamientos --strict --json` pasó para un change, sin incidencias. Once requisitos, 29 escenarios y 15 tareas pendientes; 246 enlaces locales válidos. Pareja AGENTS/CLAUDE idéntica, reglas compactas del registro preservadas y estado de fundación, PDF, matriz y renderer sin cambios. `git diff --check` pasó. La validación estructural no demuestra comportamiento de producto.
- **Progreso real:** los cuatro artefactos están completos; `openspec instructions apply` informa 0/15 tareas implementadas. El indicador `isComplete` de status se refiere al cierre de artefactos de planificación, no a implementación, pruebas o Archive.
- **Correcciones del agente:** se hizo observable el caso de offsets equivalentes mediante dos solicitudes reales del contrato y se separó el requisito de timeout configurable. No se presenta este ajuste documental como revisión humana con Ajustar ni se inventan errores para la defensa.
- **Git y entrega:** commit local autorizado por la preferencia vigente; sin push ni publicación nuevos. Siguen pendientes revisión humana de Propose, Apply/Verify/Archive y evidencias académicas que no puede sustituir la ejecución del agente.

## 2026-10-15 - Push autorizado y Apply verificado

- **Autorización:** el usuario pidió «hazle push y sigamos con lo siguiente» después de presentar la propuesta. Se publicaron los commits locales `60d25da` y `5093070`; `git ls-remote` confirmó `509307025550d183493b5a56fa2d16fd18d0651f` en main. Se continuó con Apply del único change; no se presenta esa autorización como lectura personal completa del spec.
- **Implementación:** módulo Python 3.12+ con SQLite local, API de alta y catálogos ficticios. Validación explícita, UTC/minuto exacto, intervalos semiabiertos, adyacencia, conflictos de profesional/box con prioridad profesional y transacción BEGIN IMMEDIATE antes de consultar. Sin servicios externos ni dependencias nuevas del producto.
- **TDD y correcciones:** se ejecutaron RED reales antes de añadir el comportamiento. Se registran baselines, GREEN, triangulación y refactors en [evidencia](evidencia/implementacion-turnos.md). Algunos tests de bordes/rollback/concurrencia/repetición ya pasaron sobre el código existente: no se fabricó un RED. Los primeros grupos usaron casos parametrizados juntos; esta diferencia de granularidad está declarada. Durante validación se detectaron y corrigieron normalización UTC que redondeaba offsets con segundos, TypeError de zona inválida y ValueError de ruta con NUL.
- **Verificación final:** `python -m unittest discover -s tests -v` pasó 43/43; `python -m odontologia.demo` produjo dos altas y dos conflictos, y eliminó su agenda temporal. `openspec validate crear-turno-sin-solapamientos --strict --json` pasó sin incidencias. Se trazaron los 29 escenarios a tests concretos; no hay health check HTTP porque no existe servidor.
- **Concurrencia real:** cada suite ejecuta siete carreras con 14 procesos Windows spawn: tres por profesional, tres por box y una con recursos distintos. Se verifican PIDs, códigos de salida, resultados y filas. Contención/timeout y rollback mediante trigger SQLite real tienen pruebas separadas. Garantía limitada al mismo archivo local vía módulo; no redes compartidas, varios equipos, SQL externo ni reconciliación de IO catastrófico.
- **Estado:** CLI Apply `all_done`, 15/15 tareas. No se archivó C-01 ni se creó la spec principal; checkbox del roadmap queda abierto hasta Archive. KB, instrucciones y metadatos reflejan lo implementado, conservando revisiones humanas y evidencias académicas como pendientes. PDF, matriz y renderer no se modificaron.
- **Git actual:** la implementación y documentación relacionada se guardan en commit local validado. El permiso de push aplicado a los commits previos no se extiende automáticamente a este avance nuevo.

## Corrección FastAPI — C-01

El usuario corrigió expresamente el stack a FastAPI y autorizó commit/push tras validar, manteniendo sólo C-01. Adaptador POST /turnos, GET /health y OpenAPI reutilizan SQLite. Dependencias fijadas, instaladas en .venv (sin cambios globales); HTTPX para TestClient. Estado previo sin HTTP conserva valor histórico, no describe el producto actual. Baseline43; suite actual53 tests. No se modifica PDF, datos reales ni proveedores externos. Archive y evidencias personales pendientes.

### Publicación verificada y preparación de demostración

Se publicó `b0abe34738d1a669c9ce60c6e52f8cbe23c4b088` en main; `git ls-remote` confirmó la misma revisión y el tracking quedó 0/0. Incluye el commit previo del dominio `a878038`. Verificación final: 53/53 tests, `pip check` sin dependencias rotas, OpenSpec strict sin incidencias y Apply 18/18. Comprobación documental: 268 enlaces locales sin roturas antes de incorporar el índice del guion; AGENTS/CLAUDE idénticos. PDF, matriz y renderer permanecieron intactos.

Se preparó el guion del video como material local de preparación, con tiempos orientativos, demostración real y límites de evidencia. Es preparación documental, no una grabación, reflexión personal ni revisión humana. No se creó C-02 ni se archivó C-01. Esta preparación posterior se guarda en commit local separado; no extiende automáticamente la publicación autorizada de la implementación.

### Ampliación del guion con vistas reales

Por pedido del usuario se amplió el guion con archivos, recorrido en pantalla, comandos, cuerpos JSON y texto orientativo para ensayar. Se capturaron ocho vistas reales de Swagger y health con datos ficticios; su procedencia y resultados están documentados en el material local de preparación. Se ejecutó desde el navegador la secuencia 201, 409 profesional, 409 box, 201 adyacencia, 422 intervalo vacío y 404 recurso desconocido. SQLite confirmó dos filas; servidor detenido y temporal propio eliminado. No se modificó código de producto, PDF, specs ni se creó otro change. La ampliación se guarda en commit local validado, sin push nuevo.


## 2026-10-15 — Confirmación personal de fuentes

La revisión personal de las seis fuentes del registro quedó confirmada por el estudiante el 2026-10-15: declaró que ya las vio y le parecen bien. Los hallazgos detallados siguen atribuidos a la investigación asistida; esta conformidad global no acredita pruebas funcionales ni una auditoría independiente.

Declaración textual del estudiante:

> la verificacion humana marcala como correcta de las fuentes ya las vi y me parecen bien

Se actualizan las seis filas del registro y el checklist de fuentes. Los registros anteriores describen el estado histórico antes de esta confirmación. No se modifican producto, C-01 ni Archive. El material local de demostración sólo ajusta sus menciones al estado de revisión de fuentes. La confirmación no equivale a aprobar otras etapas ni a entregar el TP completo. El guion permanece sin publicación por instrucción expresa.

## 2026-10-15 — Preparación de publicación del informe sin material de video

El usuario autorizó publicar el informe actualizado y pidió ignorar el material del video. Se conservó una rama de respaldo exclusivamente local de los tres commits no publicados y se reorganizó el avance sobre la revisión publicada, para que el guion y las capturas tampoco ingresen al historial de `main`. Los archivos de preparación permanecen intactos en el equipo, fuera del índice y cubiertos por reglas de `.gitignore` para el guion, las capturas y las grabaciones de video; no se ignora toda la carpeta de entrega. Se retiraron enlaces públicos a esos archivos locales.

La publicación preparada comprende el informe, PDF, registro de fuentes y documentación de estado relacionada. El PDF aprobado se conserva sin regenerar. No se modifica código de producto, specs ni estado de C-01; no se crea otro change ni se ejecuta Archive. La comprobación del push y su revisión remota se informa después de ejecutarlo.


## 2026-10-28 — Archive de C-01

Se verificó nuevamente C-01 con 53 tests satisfactorios, demo temporal y pip check; OpenSpec validó el change sin problemas. El comando nativo de Archive sincronizó alta-turnos (14 requisitos, 35 escenarios) y movió el change a [2026-10-28-crear-turno-sin-solapamientos](../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/). La [spec principal](../openspec/specs/alta-turnos/spec.md) conserva el contrato; su validación estricta fue satisfactoria y no quedan changes activos. Ver [evidencia detallada](evidencia/implementacion-turnos.md).

Se actualizan enlaces y estado técnico de C-01 en la documentación vigente; los hitos y pendientes históricos anteriores conservan su contexto. El roadmap mantiene 20 changes en seis fases: cerrar C-01 no implementa ni autoriza C-02 a C-20. No se modificó producto, tests, PDF, datos o servidor de grabación; el informe Discovery con cambios previos del autor queda fuera de esta tarea. El cierre técnico no acredita aceptación docente. Commit local y publicación se informan por separado, sin inferir autorización de push.

## 2026-10-29 — Corrección de la cátedra: stack y estructura

**Revisión del profesor:** faltaban las carpetas `backend/` y `frontend/` y había que respetar el stack tecnológico del sistema: backend con Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis (funcionalidades asincrónicas) y Docker/Docker Compose; frontend con React, TypeScript y Vite.

**Decisión (Ajustar):** el estudiante eligió crear la estructura y actualizar la documentación, sin migrar todavía la lógica. Como C-01 ya está archivado (2026-10-28), su change no se edita: el ajuste se registra en la fundación (KB 02/08 y [DD-09](../knowledge-base/09_decisiones_y_supuestos.md), AGENTS/CLAUDE con la regla R-09, roadmap y README). Cada tecnología queda asignada al change que la implementa: PostgreSQL + SQLAlchemy → C-02, JWT → C-03, React/TS/Vite → C-11, Docker Compose de despliegue → C-14, Redis con cola de recordatorios → C-17.

**Cambios realizados:**
- C-01 movido sin cambios a `backend/odontologia/` y `backend/tests/`, con sus `requirements*.txt`.
- Estructura nueva del backend: `core/config.py` (variables de entorno), `db/`, `auth/` y `workers/` como paquetes reservados con su change asignado; `requirements-stack.txt`, `Dockerfile`, `docker-entrypoint.sh` y `.env.example`.
- `frontend/` con React + TypeScript + Vite: página que consulta `GET /health` por el proxy `/api` y lista las pantallas planificadas.
- `docker-compose.yml` con PostgreSQL 16, Redis 7, backend y frontend, puertos sólo en 127.0.0.1 y secretos en `.env` (no versionado).

**Verificación en el entorno del agente:** 43 tests del dominio OK desde `backend/`; `docker compose config` válido; sintaxis de los archivos TypeScript comprobada. El entorno no tenía acceso a PyPI ni a npm, por lo que la instalación de dependencias, los 10 tests HTTP, `npm run build` y el arranque con Docker quedan para el script de comprobación en el equipo del estudiante. No se modificaron el contrato, la spec principal ni el archivo de C-01.


## 2026-11-01 — C-02: PostgreSQL y migración explícita

Se implementó C-02 dentro del change `evolucionar-esquema-y-configuracion`: persistencia PostgreSQL optativa con SQLAlchemy, versión Alembic y CLI manual para importar agendas C-01 SQLite. SQLite continúa como backend predeterminado; crear/importar la app no ejecuta DDL ni importa datos. La importación abre SQLite en sólo lectura, usa una transacción de lectura coherente, valida su esquema e integridad, rechaza solapamientos por profesional o box, exige esquema vigente y destino de agenda vacío, conserva IDs/secuencia y confirma la copia dentro de una transacción PostgreSQL. Un conflicto doble conserva prioridad profesional.

La verificación completa pasó 89 tests (incluye 8 tests de integración PostgreSQL) contra un clúster temporal PostgreSQL 18.6 aislado, `127.0.0.1:55432`, base `odontologia_test`; la instancia preexistente de 5432 no se utilizó. También se ejecutaron validaciones estrictas de OpenSpec, `pip check` y `git diff --check`. La fuente de test era ficticia y temporal; no se migraron agendas del usuario ni se conectaron servicios externos. El guard de integración requiere nombre `test` o sufijo `_test`, host loopback y puerto diferente de 5432.

La guía de operación y recuperación quedó en [backend/README.md](../backend/README.md); la [evidencia reproducible](evidencia/implementacion-turnos.md#c-02) registra comandos, resultados y límites. Cambiar de PostgreSQL a SQLite reabre la fuente pre-migración, no incorpora las altas hechas después en PostgreSQL: no existe doble escritura ni exportación inversa. Por eso la fuente se conserva y una vuelta de motor tras nuevas escrituras requiere una estrategia aparte.

C-02 está técnicamente implementado y validado, con sus tareas completas, pero sigue activo en OpenSpec y pendiente de Archive. No se hizo commit ni push. C-03 a C-20 permanecen planificados. No se modificaron `docs/discovery/informe-discovery.md` ni su PDF.

## 2026-11-02 — C-04: auditoría append-only

El usuario autorizó expresamente la política de C-04, crítica por afectar autenticación y auditoría. La solución registra sólo metadatos permitidos: turno confirmado; bootstrap, alta/cambio de cuenta; inicio/cierre de sesión; rechazo genérico de login sin actor ni identificador intentado. No persiste datos clínicos/personales, cuerpos, credenciales, hashes o tokens. La mutación y el evento comparten transacción; si falla auditoría se revierte y se responde sin éxito. Lectura paginada sólo Administrador, sin edición/borrado ordinario ni purga automática en el demo.

Se añadió migración SQLite v2 explícita (incluye actualización desde v1) y revisión Alembic PostgreSQL `20261101_0003_audit`; C-01 y RBAC C-03 permanecen vigentes. La validación completa pasó: SQLite **127 tests, OK (1 PostgreSQL skip)**, `pip check` sin dependencias rotas; PostgreSQL aislado en loopback `127.0.0.1:55432`, base `audit_test`, **12/12 tests**, incluido rollback de turnos/cuentas/sesiones cuando falla el insert de auditoría y protección append-only. Se detuvo el clúster temporal y se confirmó el puerto libre. OpenSpec strict pasó.

El change OpenSpec sigue activo, sin Archive, commit ni push: el responsable debe revisar el resultado. Discovery no se tocó. Evidencia detallada: [implementacion-turnos.md, C-04](evidencia/implementacion-turnos.md#c-04--registro-de-auditoría-de-operaciones-2026-11-02).

### Seguimiento de revisión C-04 — matriz semántica (2026-11-02)

Una revisión detectó que la base aceptaba combinaciones cruzadas aunque cada acción/recurso/resultado individual perteneciera a su catálogo. Se corrigió con una matriz exacta en el helper y un `CHECK` equivalente en SQLite y PostgreSQL. RED reprodujo combinaciones inválidas en helper y DDL; GREEN: 23 tests SQLite/schema OK y 13 tests de integración PostgreSQL OK, incluyendo todos los tipos de evento emitidos realmente. PostgreSQL temporal se detuvo y el puerto 55432 quedó libre. No hubo migración de datos, commit, push ni Archive.

## 2026-11-02 — C-05 fichas mínimas de pacientes

Se añadió `patient-management`: nombre y teléfono opcional ficticios; sin documento, fecha de nacimiento ni historia clínica. Administrador y Recepción gestionan contacto; sólo Administrador desactiva/reactiva. La baja conserva turnos y bloquea nuevas altas. Las mutaciones auditan sólo actor/acción/ID opaco en la misma transacción. PostgreSQL usa Alembic `20261102_0004_patient_management`; SQLite sube explícitamente a esquema v3; la importación C-02 convierte filas C-01 sin alterar la fuente.

TDD documentó RED para esquema, importación, catálogo de auditoría, rutas y regla de paciente inactivo; cada caso pasó tras su corrección. Validación final: SQLite **143 tests OK, 1 PG omitido**; con PostgreSQL aislado loopback **159 tests OK**; `pip check` limpio; OpenSpec strict **6/6**; `git diff --check` limpio. PostgreSQL temporal se detuvo y el puerto 55432 quedó libre. El change se archivará y comiteará localmente tras sincronizar specs; no se hará push sin autorización.

## 2026-11-02 — C-06 catálogos de recursos y prestaciones

Se implementaron catálogos paginados de profesionales, boxes y prestaciones ficticias, con API y permisos: Administrador y Recepción administran datos descriptivos; sólo Administrador cambia estados. SQLite sube a v4 y PostgreSQL usa Alembic 0005; los IDs seed e historial se conservan. La auditoría guarda metadatos permitidos dentro de la misma transacción y revierte la mutación si no puede registrar el evento. Turnos nuevos rechazan paciente, profesional o box inactivo, tras resolver primero todas las referencias.

Se mantuvo el contrato de C-01: no se añadió `prestacion_id`, cálculo de duración ni reglas de compatibilidad. La duración de prestación se valida como entero positivo en minutos. Evidencia TDD por tarea y comandos: [implementacion-catalogos.md](evidencia/implementacion-catalogos.md). Validación: SQLite **155 tests, 154 OK y 1 integración PostgreSQL omitida**; suite completa con PostgreSQL aislado **173/173 OK**; `pip check` limpio; OpenSpec strict **7/7**; `git diff --check` limpio. El clúster temporal PostgreSQL quedó detenido.

C-06 se sincronizó y archivó localmente el 2026-11-02. No se hizo push. La modificación preexistente de `docs/discovery/informe-discovery.md` quedó fuera del cambio.

## 2026-11-02 — C-07 horarios y bloqueos de agenda

Se implementaron horarios semanales, excepciones fechadas y bloqueos por profesional o box, con API para Administrador y Recepción y auditoría metadata-only atómica. Las altas nuevas requieren disponibilidad simultánea de ambos recursos. Al configurar una base migrada con turnos C-01, cada cambio valida sólo el recurso objetivo para permitir configurar profesional y box secuencialmente; un turno pasado o futuro de ese recurso que resulte incompatible conserva el rechazo 409. SQLite C-01 standalone sin `auth_schema_version` conserva su contrato; SQLite v5 activa disponibilidad cerrada por defecto y la API falla cerrada con 503 si faltan tablas declaradas. La zona IANA se fija como `America/Argentina/Mendoza`, con `tzdata` para portabilidad Windows.

Validación completa tras revisión: SQLite **200 tests OK, 1 PostgreSQL omitido**; PostgreSQL temporal aislado en `127.0.0.1:55432`, **223/223 OK**; migraciones incluidas; `pip check` limpio; prueba de carga IANA OK; OpenSpec strict **9/9**; `git diff --check` sin errores (sólo avisos normales LF/CRLF del checkout). El clúster temporal se detuvo y el puerto quedó libre. No se usó la instancia local 5432 ni servicios externos.

La [evidencia TDD y comandos](evidencia/implementacion-disponibilidad.md) registra los límites de trazabilidad por tarea: algunas rutas/servicios ya existían al retomar C-07 y no se atribuyen RED separados donde no hay evidencia; la matriz de carreras reutiliza el lock de C-01. La revisión añadió el caso límite de turno que termina exactamente a las 00:00: el turno cabe en `23:00–24:00`, pero sigue rechazándose si continúa después de medianoche. C-07 quedó sincronizado, archivado y comiteado localmente como `fd21a9a`. No se hizo push; el informe Discovery preexistente no se modificó.

## 2026-11-02 — C-09 estados y cancelaciones de turnos

Se implementó C-09 en Apply: SQLite v6 y PostgreSQL Alembic 0007 agregan estado y preservan turnos existentes; sólo `reservado` y `confirmado` ocupan recursos. Administrador y Recepción pueden confirmar, cancelar, marcar atendido o ausente. La cancelación repetida es idempotente; cada transición efectiva usa auditoría metadata-only atómica. El estado comparte el lock de altas en ambos motores y C-01 standalone conserva su contrato no migrado.

Revisión independiente corrigió dos defectos: la validación C-07 ahora ignora estados terminales al cambiar horarios, excepciones y bloqueos, y el chequeo de esquema exige `turnos.estado` antes de atender operaciones migradas. Se agregaron pruebas RED/GREEN en SQLite y PostgreSQL; los turnos ocupantes aún generan 409 y un esquema incompleto responde 503 antes de mutar.

Validación final tras sincronizar specs: SQLite **222 tests OK, 1 integración PostgreSQL omitida**; PostgreSQL temporal aislado `127.0.0.1:55432`, **251/251 OK**; `pip check` limpio; OpenSpec strict **9/9**; `git diff --check` sin errores (avisos normales LF/CRLF). El servidor temporal se detuvo y `pg_ctl status` confirmó que no corre. La [evidencia de C-09](evidencia/implementacion-estados-turnos.md) documenta comandos, resultados y límites TDD observados.

C-09 quedó sincronizado y archivado localmente; se prepara un commit separado, sin push ni publicación.

## 2026-11-02 — C-08 consultas de agenda y disponibilidad (Apply)

Se implementaron `GET /turnos` paginado por rango offset-aware, filtros y proyección de privacidad, y `GET /disponibilidad` como sugerencia local cada 15 minutos sin mutación. El Administrador puede vincular una cuenta Profesional con una ficha activa única; el JWT/identidad valida el vínculo actual y el rol Profesional sólo consulta su propia agenda. Cambio de rol/vínculo revoca sesiones. SQLite sube a v7 y PostgreSQL a Alembic 0008; C-01 standalone conserva su contrato.

Una regresión inicial de OpenAPI requería actualizar la lista de rutas. El primer run PG completo encontró dos fixtures que restablecían la revisión a 0007; tras corregir ambos para restablecer 0008, PostgreSQL pasó completo.

Validación final de Apply tras cubrir el borde a medianoche: SQLite **244 tests OK, 1 PostgreSQL omitido**; PostgreSQL aislado loopback `127.0.0.1:55432`, **275/275 OK**; `pip check` limpio; OpenSpec strict **10/10**; `git diff --check` limpio. El clúster temporal se detuvo (`pg_ctl status`: no server running; puerto 55432 libre). La [evidencia C-08](evidencia/implementacion-consultas-agenda.md) reúne TDD, contratos y límites. No se modificó Discovery.

C-08 sigue en Apply y queda pendiente revisión independiente y Archive. No hay commit ni push en este avance.

### Seguimiento C-08 — fin local exacto a medianoche

Una revisión independiente señaló el borde `23:45–00:00` con duración de 15 minutos. La prueba de regresión se añadió y ejecutó antes de cualquier cambio productivo; pasó con la lógica existente, que acepta exactamente el fin local `00:00` siguiente cuando el tramo termina en `24:00`. No se encontró defecto vigente ni se modificó código productivo. Se documenta cobertura adicional en la [evidencia C-08](evidencia/implementacion-consultas-agenda.md). Se repitieron las suites completas SQLite y PostgreSQL aislado con esta prueba nueva.

## 2026-11-02 — C-10 reprogramación atómica (Apply)

C-10 agrega `turnos.version` a SQLite v8 y PostgreSQL Alembic 0009, incrementa versión en transiciones efectivas, y permite `POST /turnos/{id}/reprogramacion` a Administrador/Recepción con control optimista. El servicio conserva paciente, duración, estado e identidad; valida agenda y ocupación bajo el lock común. Una auditoría metadata-only se confirma junto a la fila; fallos revierten todo. La consulta operativa muestra versión a Administrador/Recepción y mantiene la proyección Profesional acotada. C-01 standalone sigue sin requerir esquema/versionado.

La suite completa pasó: SQLite **271 tests OK**; PostgreSQL aislado en `127.0.0.1:55432` **312 tests OK**, 0 omitidos. Una revisión encontró que el guard de fecha rechazaba 23:30–00:00 aunque C-07 permitía el fin exacto a 24:00. Las pruebas RED reprodujeron el caso en ambos motores; el guard ahora acepta sólo fin local exacto 00:00 y sigue rechazando que el turno continúe al día siguiente. Se repitieron ambas suites completas tras el cambio. `pip check` sin dependencias rotas; OpenSpec strict válido; `git diff --check` sin errores. El clúster temporal quedó detenido y 5432 no se alteró. La [evidencia C-10](evidencia/implementacion-reprogramacion.md) registra TDD, comandos, límites y el fixture de Alembic 0008 actualizado para restaurar la revisión 0009.

La implementación queda pendiente de revisión independiente y Archive. No se hizo commit ni push. La modificación preexistente de `docs/discovery/informe-discovery.md` se preservó.

## 2026-11-02 — C-11 interfaz de operación de recepción

Se implementó la interfaz React/TypeScript para login con bearer en memoria, consulta diaria/semanal y operación de agenda, pacientes, catálogos y disponibilidad semanal, excepciones y bloqueos. Admin y Recepción operan; Professional sólo consulta su agenda. La UI conserva contratos existentes y no modifica backend ni agrega `prestacion_id` a C-01. Las respuestas del backend determinan éxito y los 409 conservan la vista sin confirmaciones optimistas.

La revisión independiente encontró tres defectos antes del cierre: faltaba explicar el 401 al volver al login, se ocultaban errores accionables de fecha local al reprogramar y podía guardarse el borrador anterior mientras cargaba otro recurso. Se añadieron pruebas de regresión RED/GREEN; los tres quedaron corregidos y la segunda revisión no encontró regresiones concretas.

Validación final: Vitest **50/50**; build Vite correcto (**35 módulos**); Playwright **3/3** con API/SQLite ficticias aisladas; `npm audit --audit-level=low` **0 vulnerabilidades**; `npm ls --depth=0` limpio; OpenSpec strict **12/12 specs** y **11/11 changes archivados**; `git diff --check` sin errores. El change quedó sincronizado y archivado como `2026-11-02-operar-agenda-desde-recepcion`. Evidencia TDD y comandos: [implementacion-recepcion.md](evidencia/implementacion-recepcion.md). No se hizo push; el informe Discovery preexistente se excluye del commit.

## 2026-11-02 — C-12 respaldo y restauración de agenda (Apply)

Se implementó backup/restauración manual y local para SQLite y PostgreSQL optativo. SQLite copia con Online Backup API y calcula los recuentos desde el snapshot; PostgreSQL obtiene los mismos 14 recuentos y ejecuta `pg_dump --snapshot` bajo la misma transacción `REPEATABLE READ`. El manifiesto incluye formato, fecha UTC, versiones, SHA-256 y `table_counts`. El hash detecta cambios accidentales del payload, pero no autentica un manifiesto que un atacante pueda reemplazar junto con el payload. Las copias son sensibles; no se incluyen secretos `.env`/JWT, envío remoto ni purga automática. La restauración exige destino nuevo y preserva todo destino activo o existente.

Validación inicial C-12: pruebas enfocadas **57 tests OK, 1 omitido por WinError 1314 al crear symlink**; suite completa backend **328 tests OK, 2 omitidos**, incluido PostgreSQL por URL no definida en esa ejecución. La suite PostgreSQL aislada corrió aparte en loopback `127.0.0.1:55432`, **41/41 OK**. `pip check` quedó limpio. `openspec validate --specs` pasó **13/13** y strict **14/14** tras sincronizar la nueva spec.

En esa verificación histórica, `docker build -f backend/Dockerfile backend` no pudo ejecutarse: `docker` no estaba reconocido y no había `docker`, `podman` ni `buildah` disponibles en Windows o WSL. No se instaló ni alteró un runtime. El clúster temporal propio se detuvo, el puerto 55432 quedó libre, su `pg_hba.conf` volvió a SCRAM y se eliminó únicamente su directorio aislado. La instancia PostgreSQL preexistente del host/5432 no se usó.

La revisión independiente encontró permisos de archivo POSIX demasiado abiertos y que faltaba un aviso tras `crear`. RED se reprodujo con `umask 022`: archivos SQLite `0644` y payload PostgreSQL ausente antes del dump; dos tests CLI también fallaron por falta del aviso. GREEN restringe staging/bundle a `0700` y payload/manifiesto a `0600` desde su creación hasta publicación en POSIX, sin cambiar ACL Windows; la CLI advierte sensibilidad y recomienda destino fuera del repo. WSL Ubuntu bajo `/tmp` pasó **2/2** tests POSIX tanto con `umask 022` como `0777`; tests CLI **8/8**; focused Windows **59 tests OK, 3 omitidos**. Suite completa final **330 tests OK, 4 omitidos**; integración PostgreSQL aislada **41/41 OK**. El cliente real PG18 escribió al payload 0600 precreado; CLI crear/verificar/restaurar pasaron contra cluster 18.6 ficticio. El cluster temporal se detuvo, puerto 55432 quedó libre y su directorio propio se eliminó.

En ese momento el change seguía activo con **19/20 tareas**; la 8.1 quedaba pendiente por el build Docker. No se había archivado ni hecho commit o push; la evidencia está en [implementacion-backup.md](evidencia/implementacion-backup.md). No se afirma recuperación humana ni en producción. La modificación preexistente de `docs/discovery/informe-discovery.md` se preservó.

### Seguimiento de revisión — publicación atómica sin reemplazo

La revisión detectó que un corte entre crear el directorio final y mover sus archivos podía dejar un bundle parcial. Se añadieron cinco pruebas RED/GREEN: excepción tras preparar staging en SQLite y PostgreSQL, colisión concurrente por un directorio vacío en ambos adapters y preservación del directorio vacío por la primitiva no-replace. La publicación ahora renombra de una vez el directorio de staging privado en el mismo volumen: `os.rename` en Windows y `renameat2(RENAME_NOREPLACE)` en Linux, sin fallback POSIX que pueda sustituir directorios vacíos. Si algo falla antes de publicar, el destino queda ausente y se limpia sólo staging propio; si hay colisión, se preserva intacta.

Validación de ese avance: publicación focalizada **5/5 OK en Windows y 5/5 OK en WSL Ubuntu**; suite C-12 focalizada Windows **64 tests OK, 3 omitidos**; suite completa Windows **335 tests OK, 4 omitidos**. El change quedó entonces en **20/21 tareas**; luego se retiró la tarea de build Docker del alcance y se archivó en 20/20, como se registra al final. El informe Discovery preexistente se preservó.

## 2026-11-02 — C-13 seguridad y observabilidad (Apply y Archive)

C-13 limita `/docs`, `/redoc` y `/openapi.json` al entorno de desarrollo explícito; conserva `/health` como liveness y agrega `/ready` con consulta de sólo lectura. Añade `X-Request-ID` validado/generado y logs estructurados con allowlist, errores públicos estables y respuestas 500 genéricas. El login aplica un límite temporal acotado por par cliente/cuenta normalizada, responde 429 con `Retry-After` y no confía en cabeceras de proxy. Uvicorn desactiva proxy headers y access log. La documentación deja clara la limitación del rate limit en proceso único.

La revisión de concurrencia corrigió reservas atómicas del límite: seis intentos simultáneos permiten como máximo cinco verificaciones; fallos de base/validación liberan su reserva y un login exitoso limpia fallos sin borrar solicitudes concurrentes. También se sanitizaron errores `ValueError` del CLI de backup para no exponer detalles del motor.

Validación reportada en ese momento: backend **360 tests OK, 4 omitidos**; frontend **50/50**; concurrencia focalizada **11/11**; OpenSpec strict **12/12** antes del archive. La revisión independiente final no encontró hallazgos. C-13 se archivó y sincronizó; entonces C-12 seguía activo con 20/21 tareas mientras se consultaba el alcance del build. La decisión posterior y el cierre de C-12 se registran abajo. No se hizo push. El informe Discovery preexistente se preserva fuera del commit.

### Aclaración posterior de alcance — 2026-11-02

El usuario definió que la entrega se arma y demuestra mostrando el proyecto y sus changes, sin requerir Docker ni Redis. El build de imagen que C-12 pedía se retira como criterio de entrega; no se afirma que haya sido ejecutado. C-14 despliegue queda opcional y fuera de la entrega. Redis puede mencionarse como antecedente de la indicación docente o alternativa futura, pero no se mantiene como dependencia; C-17 podrá proponerse con outbox PostgreSQL y canal simulado. Los registros anteriores sobre intentos Docker describen el estado de ese momento y no representan un pendiente actual de aceptación.

## 2026-11-02 — C-12 cierre tras ajustar el alcance

Se retiró la tarea de imagen Docker PG16 de C-12 porque el proyecto se presenta mediante sus changes y evidencia, sin empaquetado. Los adaptadores PostgreSQL usan clientes locales compatibles con la major del servidor; la integración aislada PG18.6 se había validado previamente. La prueba de backup que inspeccionaba un Dockerfile se quitó junto con los artefactos Docker no usados. C-12 quedó en **20/20 tareas**, pasó la suite backend con **361 tests y 4 omitidos**, `pip check` y OpenSpec strict **15/15**; se archivó con OpenSpec como `2026-11-02-respaldar-y-restaurar-agenda`. No se afirma que se haya construido una imagen ni que haya despliegue. No se hizo push.

## 2026-11-02 — C-15 historia clínica (Apply y Archive)

C-15 agrega evoluciones clínicas sintéticas en una tabla separada, consulta paginada, alta y correcciones append-only. Sólo un Profesional activo con vínculo vigente puede consultar o registrar notas para sus propias atenciones `atendido`; Administrador y Recepción no reciben contenido clínico. La auditoría registra metadatos y confirma dentro de la transacción; ante un fallo no se devuelve ni persiste la operación clínica. SQLite avanza a v9 y PostgreSQL a Alembic `20261102_0010_clinical_history`. Backup/restore incorpora la tabla y sus recuentos sin publicar texto de notas en el manifiesto.

Validación: suite backend con PostgreSQL 18.6 aislado **424 tests OK, 3 omitidos**; integración PostgreSQL existente **41/41**; pruebas C-15 de migración, restricciones, append-only y restauración real a base nueva **2/2**; OpenSpec strict **15/15**, Apply **15/15**. Se corrigieron dos pruebas que restauraban `alembic_version` a 0009 y se aisló la configuración de logging del harness Alembic para evitar contaminación de `uvicorn.error`. C-15 se archivó como `2026-11-02-registrar-historia-clinica`. No se usaron datos personales reales, no se tocó el servicio PostgreSQL del puerto 5432 y no se hizo push.
