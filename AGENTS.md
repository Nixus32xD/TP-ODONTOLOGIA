# TP-ODONTOLOGIA — Instrucciones para Agentes

Instrucciones específicas de esta entrega de Metodología I. Mantener este archivo y `CLAUDE.md` idénticos al actualizarlos. El proyecto partió de cero y ahora tiene FastAPI, módulo de agenda, demo y 53 tests. Archive y evidencias académicas siguen pendientes.

## Stack Tecnológico

Tabla tomada de [la descripción general](knowledge-base/02_descripcion_general.md), sincronizada con el contrato implementado al autorizar continuar con Apply.

| Capa | Tecnología | Versión mínima / estado |
| --- | --- | --- |
| Lenguaje y runtime del producto | Python | 3.12+; verificado con 3.12.14 |
| Forma de exposición | FastAPI + Uvicorn | FastAPI 0.143.2; HTTP local, sin proveedores externos |
| Almacenamiento | SQLite mediante sqlite3 estándar | Archivo en disco local; verificado con SQLite 3.53.1 |
| Pruebas del producto | unittest, TestClient y multiprocessing | 53 tests; procesos spawn reales y contrato HTTP |
| Interfaz gráfica | Fuera de C-01 | Demo por consola |
| Especificación y flujo | OpenSpec / Active Stack | Change activo; Archive pendiente |
| Herramienta del informe | Python, ReportLab y pypdf | Dependencias documentales separadas del producto |

## Base de Conocimiento

Leer el [índice de la KB](knowledge-base/README.md) y los documentos pertinentes antes de cambiar contratos o código.

| Documento | Qué resuelve |
| --- | --- |
| [01 — Visión y objetivos](knowledge-base/01_vision_y_objetivos.md) | Propósito y límites de la entrega |
| [02 — Descripción general](knowledge-base/02_descripcion_general.md) | Stack del módulo y estado actual |
| [03 — Actores y roles](knowledge-base/03_actores_y_roles.md) | Recepción y recursos conceptuales; sin autenticación aprobada |
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
| Planificación de dominio | Explorar y especificar el único change | `openspec-explore`, `openspec-propose`, `openspec-update-change` |
| Implementación y cierre | Aplicar tareas revisadas, sincronizar y archivar | `openspec-apply-change`, `openspec-sync-specs`, `openspec-archive-change` |
| Revisión | Revisar un diff sin modificarlo | `review-agent` |
| Documentación de entrega | Editar y verificar los artefactos pedidos | `pdf`; `documents` o `visualize` sólo cuando corresponda al formato solicitado |

Los compact rules los resuelve el delegador desde `.atl/skill-registry.md`, generado por `skill-registry` y **versionado en este repositorio por pedido del usuario**. No duplicarlos aquí. Las rutas globales describen el equipo donde se generó el registro: comprobar disponibilidad antes de usarlas. El producto usa unittest estándar; se añadieron dependencias FastAPI/Uvicorn/Pydantic y HTTPX de pruebas sólo en .venv, sin nuevas skills.

## Roadmap de Changes

El plan está en [CHANGES.md](CHANGES.md): un único change funcional, **C-01 `crear-turno-sin-solapamientos`**, con Apply implementado y verificación técnica completa. El [diseño del change](openspec/changes/crear-turno-sin-solapamientos/design.md) define FastAPI, Python, SQLite y reglas temporales, implementadas al autorizar el usuario continuar. No se atribuye lectura personal del spec a partir de esa autorización. Bootstrap, modelos ficticios y pruebas son tareas internas del mismo change.

Camino crítico: contrato revisado → alta sin solapamientos → suite completa → Archive. WhatsApp, pagos, historia clínica, autenticación, multisede y UI completa permanecen fuera de esta porción.

Antes de Propose, leer las precondiciones y los documentos «Leer antes» del roadmap. Q01–Q08 se resolvieron para C-01; ante cambios materiales volver a Propose antes de modificar el contrato; Q09 está resuelta por confirmación personal de fuentes; Q10 sigue pendiente de entrega y no se dan por cumplidas al generar documentación.

## Reglas Duras (específicas del proyecto)

Estas reglas consolidan instrucciones ya confirmadas del usuario y restricciones de la consigna; reflejan el contrato aplicado sin agregar módulos ni reglas clínicas nuevas. No se encontró `~/.claude/CLAUDE.md` al generar estos archivos: no se presume herencia de reglas globales ausentes. Las instrucciones del usuario y del entorno tienen prioridad.

- **R-01 — Alcance:** implementar sólo el alta de turno acordada. Rechazar conflictos del mismo profesional o del mismo box por separado (RN-TU-01/02); no introducir sobreturnos ni otros módulos por analogía con los competidores.
- **R-02 — Datos:** nunca guardar datos reales de pacientes, información clínica real, secretos, credenciales o certificados en el repositorio, ejemplos o pruebas → usar exclusivamente datos ficticios.
- **R-03 — Integraciones:** no ejecutar integraciones externas, SOAP, ARCA/AFIP real ni servicios de proveedores desde el ejercicio. HTTP local de FastAPI está autorizado expresamente para C-01. Las consultas públicas para investigación y las herramientas del proceso no acreditan integraciones clínicas. La API local no tiene autenticación ni autorización de publicación pública.
- **R-04 — Contrato:** nunca elegir silenciosamente stack, persistencia, concurrencia o políticas temporales → preparar opciones y registrar la decisión aplicable antes de implementar. `[inicio, fin)`, adyacencia y RN-TU-03 a RN-TU-07 son el contrato de C-01 aplicado tras autorización de continuar. Ante un hueco, volver a Propose.
- **R-05 — Cambios y errores:** inspeccionar documentos, código y pruebas existentes; realizar cambios mínimos y reutilizar la lógica disponible. Validar entradas explícitamente y devolver errores claros; no corregir datos inválidos silenciosamente para aceptarlos.
- **R-06 — Pruebas:** cuando exista runner, seguir TDD del roadmap: baseline existente, RED ejecutado antes de producción, GREEN mínimo, triangulación y refactor con pruebas verdes. Cubrir todos los escenarios aprobados y ejecutar la suite completa; reportar fallos previos y no archivar con pruebas fallando. Una prueba secuencial no demuestra concurrencia.
- **R-07 — Evidencia:** distinguir hechos, publicidad, propuestas y «No evidenciado». Registrar comandos y resultados reales; no atribuir al estudiante verificaciones realizadas por IA ni afirmar revisión humana, tests, capturas, video o cumplimiento que no se acreditaron. La revisión personal de las seis fuentes quedó confirmada por el estudiante el 2026-10-15; no convertir esa conformidad en auditoría funcional ni atribuirle los hallazgos detallados del agente.
- **R-08 — Git:** validar antes de cada commit local autorizado por la preferencia vigente; usar mensajes descriptivos y separar cambios ajenos. Push o publicación requieren autorización explícita aplicable a ese avance. No extender permisos de push de commits ya revisados a avances nuevos o publicaciones futuras.

## Flujo de Trabajo

1. Leer estas instrucciones, KB pertinente, preguntas abiertas y roadmap; contrastar el estado real del checkout.
2. Consultar `openspec list --json`. Cuando exista el change, consultar `openspec status --change "crear-turno-sin-solapamientos" --json`; el CLI posee el estado de artefactos y tareas.
3. Explorar el problema y conservar el relevamiento dentro del alcance autorizado. Proponer mediante `/opsx:propose crear-turno-sin-solapamientos`; usar instrucciones del CLI para crear artefactos y registrar las correcciones reales.
4. Revisar el contrato y resolver las decisiones indispensables. No inventar aceptación humana ni crear manualmente la estructura de OpenSpec.
5. Aplicar tareas con `/opsx:apply crear-turno-sin-solapamientos`, reglas pertinentes del registro y pruebas del contrato. Marcar tareas sólo tras ejecución comprobada.
6. Verificar la suite completa y archivar con `/opsx:archive crear-turno-sin-solapamientos` cuando corresponda. Confirmar el resultado del CLI antes de marcar C-01 terminado.
7. Actualizar la bitácora y las decisiones en Engram para este proyecto, sin exportar memoria de otros proyectos ni confundir memoria con revisión humana. Informar archivos, verificaciones y pendientes.

Estas instrucciones no acreditan por sí solas pruebas, Archive ni entrega académica final. Verificar evidencia y estado real del CLI.
