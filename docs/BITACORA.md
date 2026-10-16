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
- **Elección propuesta:** módulo Python 3.12+, SQLite local y unittest, sin framework, servidor ni dependencias externas del producto. Se documentaron alternativas y respuestas o exclusiones de Q01–Q08 en [design.md](../openspec/changes/crear-turno-sin-solapamientos/design.md); no se promovieron a decisiones humanas aprobadas.
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
