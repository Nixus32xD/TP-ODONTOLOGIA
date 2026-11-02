# TP-ODONTOLOGIA — Instrucciones para Agentes

Instrucciones específicas de esta entrega de Metodología I. Mantener este archivo y `CLAUDE.md` idénticos al actualizarlos. C-01–C-13 están implementados, validados y archivados. El cierre técnico no acredita aceptación docente ni otras evidencias académicas. El 2026-10-29 la cátedra fijó el stack del sistema y la separación en `backend/` y `frontend/` (ver Stack Tecnológico y R-09).

## Stack Tecnológico

Stack definido por la cátedra el 2026-10-29 para todo el sistema. Detalle en [la descripción general](knowledge-base/02_descripcion_general.md) y decisión en [DD-09](knowledge-base/09_decisiones_y_supuestos.md).

| Parte | Tecnología | Carpeta | Estado |
| --- | --- | --- | --- |
| Backend — lenguaje y API | Python 3.12+ y FastAPI + Uvicorn | `backend/odontologia/` | C-01 y adaptadores de C-03/C-04 implementados |
| Backend — autenticación | JWT (PyJWT) | `backend/odontologia/auth/` | Implementada en C-03; C-04 añade auditoría y está archivado |
| Backend — ORM y persistencia | SQLAlchemy + PostgreSQL | `backend/odontologia/db/` | C-02/C-03/C-04 implementados y probados en PostgreSQL temporal |
| Backend — tareas asincrónicas | Sin cola externa en el alcance actual | PostgreSQL/outbox futuro | C-17 podrá usar un worker local simulado; Redis queda como alternativa, no requisito |
| Contenedores | No requeridos para esta entrega | — | No se construyen imágenes ni se levanta Docker; C-14 queda opcional |
| Frontend | React + TypeScript + Vite | `frontend/` | Recepción implementada en C-11 |
| Persistencia | SQLite (predeterminada) y PostgreSQL optativo | `ODONTOLOGIA_DB`, `DATABASE_URL` | C-01–C-13; migraciones explícitas |
| Pruebas | unittest, TestClient y multiprocessing | `backend/tests/` | Suites SQLite y PostgreSQL aislado; evidencias exactas en CHANGES.md y docs/evidencia/ |
| Especificación y flujo | OpenSpec / Active Stack | `openspec/` | C-01–C-13 archivados |
| Herramienta del informe | Python, ReportLab y pypdf | `tools/` | Dependencias documentales separadas del producto |

## Base de Conocimiento

Leer el [índice de la KB](knowledge-base/README.md) y los documentos pertinentes antes de cambiar contratos o código.

| Documento | Qué resuelve |
| --- | --- |
| [01 — Visión y objetivos](knowledge-base/01_vision_y_objetivos.md) | Propósito y límites de la entrega |
| [02 — Descripción general](knowledge-base/02_descripcion_general.md) | Stack del módulo y estado actual |
| [03 — Actores y roles](knowledge-base/03_actores_y_roles.md) | Matriz aprobada e implementada para Administrador, Recepción y Profesional |
| [04 — Modelo de datos](knowledge-base/04_modelo_de_datos.md) | Entidades del módulo y ejemplos ficticios |
| [05 — Reglas de negocio](knowledge-base/05_reglas_de_negocio.md) | Reglas de Discovery y contrato temporal aplicado |
| [06 — Funcionalidades](knowledge-base/06_funcionalidades.md) | US-001 a US-004 y aceptación candidata |
| [07 — Flujos](knowledge-base/07_flujos_principales.md) | Alta, conflictos, datos inválidos y bordes |
| [08 — Arquitectura propuesta](knowledge-base/08_arquitectura_propuesta.md) | Responsabilidades, persistencia y evidencia de concurrencia |
| [09 — Decisiones y supuestos](knowledge-base/09_decisiones_y_supuestos.md) | Procedencia y confianza de cada decisión |
| [10 — Preguntas abiertas](knowledge-base/10_preguntas_abiertas.md) | Q01–Q08 resueltas para C-01; Q09–Q10 de evidencia académica |

El [Discovery canónico](discovery/discovery.md) registra el alcance confirmado. El estado actual y las autorizaciones aplicables se contrastan con la conversación y la [bitácora](docs/BITACORA.md); una entrada histórica no revoca instrucciones posteriores.

## Skills Disponibles

Fuente de verdad de nombres, rutas y reglas compactas: [registro de skills](.atl/skill-registry.md). Los roles siguientes organizan tareas; no crean agentes ni autorizan su ejecución por sí solos.

| Rol | Tarea | Skills pertinentes del registro |
| --- | --- | --- |
| Fundación | Mantener documentación y navegación | `active-orchestrator`, `kb-creator`, `roadmap-generator`, `find-skills`, `agents-md-generator` |
| Investigación | Contrastar evidencia pública del Discovery | `discovery-research` |
| Planificación de dominio | Explorar y especificar el change autorizado | `openspec-explore`, `openspec-propose`, `openspec-update-change` |
| Implementación y cierre | Aplicar tareas revisadas, sincronizar y archivar | `openspec-apply-change`, `openspec-sync-specs`, `openspec-archive-change` |
| Revisión | Revisar un diff sin modificarlo | `review-agent` |
| Documentación de entrega | Editar y verificar los artefactos pedidos | `pdf`; `documents` o `visualize` sólo cuando corresponda al formato solicitado |

Los compact rules los resuelve el delegador desde `.atl/skill-registry.md`, generado por `skill-registry` y **versionado en este repositorio por pedido del usuario**. No duplicarlos aquí. Las rutas globales describen el equipo donde se generó el registro: comprobar disponibilidad antes de usarlas. El producto usa unittest estándar; se añadieron dependencias FastAPI/Uvicorn/Pydantic y HTTPX de pruebas sólo en .venv, sin nuevas skills.

## Roadmap de Changes

El plan está en [CHANGES.md](CHANGES.md): 20 changes en seis fases para el producto futuro. **C-01–C-13** están implementados, verificados y archivados; **C-14** es opcional y queda fuera de esta entrega; **C-15–C-20** muestran el alcance futuro bajo la autorización global de desarrollo. Cada change requiere sus contratos y aprobaciones específicas para decisiones materiales según R-10. El [diseño de C-01](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md) documenta el contrato de alta; C-03 aplica la matriz aprobada de personal y C-04 la política aprobada de auditoría.

C-01–C-13 están archivados. El camino crítico y dependencias futuros están en CHANGES.md. El alcance de C-01 no amplía su contrato; el desarrollo global del roadmap está autorizado, sujeto a R-10 para decisiones materiales aún no aprobadas.

Antes de Propose de un change futuro, leer dependencias y documentos «Leer antes» del roadmap y resolver las decisiones materiales según governance. El desarrollo del roadmap está autorizado; no volver a pedir autorización general. Q01–Q08 se resolvieron para C-01; ante cambios materiales volver a Propose antes de modificar el contrato; Q09 está resuelta por confirmación personal de fuentes; Q10 sigue pendiente de entrega y no se dan por cumplidas al generar documentación.

## Reglas Duras (específicas del proyecto)

Estas reglas consolidan instrucciones ya confirmadas del usuario y restricciones de la consigna; reflejan el contrato aplicado sin agregar módulos ni reglas clínicas nuevas. No se encontró `~/.claude/CLAUDE.md` al generar estos archivos: no se presume herencia de reglas globales ausentes. Las instrucciones del usuario y del entorno tienen prioridad.

- **R-01 — Alcance:** conservar el contrato de alta de C-01 sin ampliarlo por analogía con los competidores; para evolución usar sólo cambios OpenSpec autorizados. C-02–C-06 están implementados dentro de cambios autorizados. El desarrollo de C-07–C-20 está autorizado por la instrucción global; resolver aprobaciones específicas exigidas por R-10 antes de políticas materiales. Rechazar conflictos del mismo profesional o box (RN-TU-01/02); no introducir sobreturnos.
- **R-02 — Datos:** nunca guardar datos reales de pacientes, información clínica real, secretos, credenciales o certificados en el repositorio, ejemplos o pruebas → usar exclusivamente datos ficticios.
- **R-03 — Integraciones y exposición:** no ejecutar integraciones externas, SOAP, ARCA/AFIP real ni servicios de proveedores desde el ejercicio. La API local de C-01/C-03 usa HTTP en loopback; C-03 exige JWT y aplica autorización en backend, pero eso no habilita publicación pública. Las consultas públicas para investigación y las herramientas del proceso no acreditan integraciones clínicas. PostgreSQL se valida aislado para pruebas; Redis y Docker no son requisitos operativos de esta entrega.
- **R-04 — Contrato:** nunca elegir silenciosamente stack, persistencia, concurrencia, permisos o políticas temporales → registrar la decisión aplicable en OpenSpec antes de implementar. `[inicio, fin)` y adyacencia son contrato de C-01; la matriz de Administrador/Recepción/Profesional está aprobada en C-03. Ante un hueco material de un change futuro, resolverlo en Propose.
- **R-05 — Cambios y errores:** inspeccionar documentos, código y pruebas existentes; realizar cambios mínimos y reutilizar la lógica disponible. Validar entradas explícitamente y devolver errores claros; no corregir datos inválidos silenciosamente para aceptarlos.
- **R-06 — Pruebas:** cuando exista runner, seguir TDD del roadmap: baseline existente, RED ejecutado antes de producción, GREEN mínimo, triangulación y refactor con pruebas verdes. Cubrir todos los escenarios aprobados y ejecutar la suite completa; reportar fallos previos y no archivar con pruebas fallando. Una prueba secuencial no demuestra concurrencia.
- **R-07 — Evidencia:** distinguir hechos, publicidad, propuestas y «No evidenciado». Registrar comandos y resultados reales; no atribuir al estudiante verificaciones realizadas por IA ni afirmar revisión humana, tests, capturas, video o cumplimiento que no se acreditaron. La revisión personal de las seis fuentes quedó confirmada por el estudiante el 2026-10-15; no convertir esa conformidad en auditoría funcional ni atribuirle los hallazgos detallados del agente.
- **R-08 — Git:** validar antes de cada commit local autorizado por la preferencia vigente; usar mensajes descriptivos y separar cambios ajenos. Push o publicación requieren autorización explícita aplicable a ese avance. No extender permisos de push de commits ya revisados a avances nuevos o publicaciones futuras.
- **R-09 — Stack indicado y alcance vigente:** la cátedra indicó el 2026-10-29 Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis, Docker/Docker Compose, React, TypeScript y Vite; se conserva como antecedente en la KB y la consigna. El usuario aclaró el 2026-11-02 que la entrega se demuestra mediante changes/pruebas y no requiere Redis ni Docker. Usar Python/FastAPI, JWT, SQLAlchemy/PostgreSQL y React/TypeScript/Vite donde ya corresponden; no agregar dependencia operativa de Redis, imágenes ni despliegue. C-17 propone outbox persistido y canal simulado; Redis es sólo alternativa futura. Código de backend sólo en `backend/` y de interfaz sólo en `frontend/`; las reglas de negocio viven en backend. Cada change requiere Propose y pruebas propias; las decisiones CRÍTICAS/ALTAS requieren aprobación específica según R-10.
- **R-10 — Governance:** el desarrollo del roadmap completo está autorizado; no volver a pedir autorización general para avanzar. Respetar el nivel de cada change en CHANGES. Para CRÍTICO o ALTO, identificar cualquier política o contrato material que aún falte acordar y pedir aprobación específica de esa decisión antes de implementarla; una vez aprobada, continuar el change sin volver a solicitar permiso por lo mismo. Para MEDIO, avanzar con checkpoints; para BAJO, implementar con pruebas. La autorización de desarrollo no incluye push ni publicación, que requieren autorización explícita aplicable.

## Flujo de Trabajo

1. Leer estas instrucciones, KB pertinente, preguntas abiertas y roadmap; contrastar el estado real del checkout.
2. Consultar `openspec list --json`; C-01–C-13 están archivados al cierre de C-12. El CLI posee el estado actual de los changes.
3. Explorar y proponer avances del roadmap global ya autorizado usando el nombre del roadmap y las instrucciones del CLI; conservar los contratos archivados y continuar el change activo antes de crear otro.
4. Revisar el contrato y resolver las decisiones indispensables. No inventar aceptación humana ni crear manualmente la estructura de OpenSpec.
5. Aplicar únicamente tareas autorizadas del change activo, con las reglas del registro y pruebas del contrato. Marcar tareas sólo tras ejecución comprobada.
6. Verificar la suite completa y archivar cada change cuando corresponda, confirmando el resultado del CLI y sincronización de specs. C-01–C-13 están archivados.
7. Actualizar la bitácora y las decisiones en Engram para este proyecto, sin exportar memoria de otros proyectos ni confundir memoria con revisión humana. Informar archivos, verificaciones y pendientes.

Estas instrucciones no acreditan por sí solas pruebas, Archive ni entrega académica final. Verificar evidencia y estado real del CLI.
