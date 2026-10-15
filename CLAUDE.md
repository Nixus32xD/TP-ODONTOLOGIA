# TP-ODONTOLOGIA — Instrucciones para Agentes

Instrucciones específicas de esta entrega de Metodología I. Mantener este archivo y `CLAUDE.md` idénticos al actualizarlos. El proyecto parte de cero y todavía no tiene implementación de agenda ni suite de comportamiento.

## Stack Tecnológico

Tabla tomada de [la descripción general](knowledge-base/02_descripcion_general.md); los pendientes no se convierten en decisiones por generar estas instrucciones.

| Capa | Tecnología | Versión mínima / estado |
| --- | --- | --- |
| Lenguaje y runtime del producto | Pendiente de definición en fundación | Sin decisión |
| Forma de exposición | Pendiente: módulo de dominio o API | Sin contrato ni transporte definidos |
| Almacenamiento | Pendiente | No se seleccionó motor, memoria ni formato de archivo |
| Pruebas del producto | Pendiente del stack | No existe runner del producto confirmado |
| Interfaz gráfica | No obligatoria para el primer change | No seleccionada |
| Especificación y flujo | OpenSpec / Active Stack | Inventario observado, no mínimo de runtime |
| Herramienta del informe | Python, ReportLab y pypdf | Uso documental existente, no elección de stack |

## Base de Conocimiento

Leer el [índice de la KB](knowledge-base/README.md) y los documentos pertinentes antes de cambiar contratos o código.

| Documento | Qué resuelve |
| --- | --- |
| [01 — Visión y objetivos](knowledge-base/01_vision_y_objetivos.md) | Propósito y límites de la entrega |
| [02 — Descripción general](knowledge-base/02_descripcion_general.md) | Stack pendiente y estado actual |
| [03 — Actores y roles](knowledge-base/03_actores_y_roles.md) | Recepción y recursos conceptuales; sin autenticación aprobada |
| [04 — Modelo de datos](knowledge-base/04_modelo_de_datos.md) | Entidades propuestas y ejemplos ficticios |
| [05 — Reglas de negocio](knowledge-base/05_reglas_de_negocio.md) | RN-TU-01/02 confirmadas frente a propuestas pendientes |
| [06 — Funcionalidades](knowledge-base/06_funcionalidades.md) | US-001 a US-004 y aceptación candidata |
| [07 — Flujos](knowledge-base/07_flujos_principales.md) | Alta, conflictos, datos inválidos y bordes |
| [08 — Arquitectura propuesta](knowledge-base/08_arquitectura_propuesta.md) | Responsabilidades, persistencia y evidencia de concurrencia |
| [09 — Decisiones y supuestos](knowledge-base/09_decisiones_y_supuestos.md) | Procedencia y confianza de cada decisión |
| [10 — Preguntas abiertas](knowledge-base/10_preguntas_abiertas.md) | Q01–Q08 técnicas; Q09–Q10 de evidencia académica |

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

Los compact rules los resuelve el delegador desde `.atl/skill-registry.md`, generado por `skill-registry` y **versionado en este repositorio por pedido del usuario**. No duplicarlos aquí. Las rutas globales describen el equipo donde se generó el registro: comprobar disponibilidad antes de usarlas. Las skills de stack y pruebas específicas siguen pendientes; no inventar una skill ni instalarla para completar esta tabla.

## Roadmap de Changes

El plan está en [CHANGES.md](CHANGES.md): un único change funcional, **C-01 `crear-turno-sin-solapamientos`**, con Propose generado y revisión del contrato pendiente. El [diseño del change](openspec/changes/crear-turno-sin-solapamientos/design.md) propone Python, SQLite y reglas temporales; todavía no son decisiones humanas aprobadas. Bootstrap, modelos ficticios y pruebas son tareas internas del mismo change.

Camino crítico: contrato revisado → alta sin solapamientos → suite completa → Archive. WhatsApp, pagos, historia clínica, autenticación, multisede y UI completa permanecen fuera de esta porción.

Antes de Propose, leer las precondiciones y los documentos «Leer antes» del roadmap. Resolver las decisiones indispensables de Q01–Q08 para el contrato afectado antes de Apply; Q09–Q10 siguen siendo pendientes de entrega y no se dan por cumplidas al generar documentación.

## Reglas Duras (específicas del proyecto)

Estas reglas consolidan instrucciones ya confirmadas del usuario y restricciones de la consigna; no agregan reglas técnicas de un stack aún no elegido. No se encontró `~/.claude/CLAUDE.md` al generar estos archivos: no se presume herencia de reglas globales ausentes. Las instrucciones del usuario y del entorno tienen prioridad.

- **R-01 — Alcance:** implementar sólo el alta de turno acordada. Rechazar conflictos del mismo profesional o del mismo box por separado (RN-TU-01/02); no introducir sobreturnos ni otros módulos por analogía con los competidores.
- **R-02 — Datos:** nunca guardar datos reales de pacientes, información clínica real, secretos, credenciales o certificados en el repositorio, ejemplos o pruebas → usar exclusivamente datos ficticios.
- **R-03 — Integraciones:** no ejecutar integraciones externas, HTTP/SOAP, ARCA/AFIP real ni servicios de proveedores desde el ejercicio. Las consultas públicas para investigación y las herramientas del proceso no acreditan integraciones clínicas. Elegir API requiere aclarar antes el alcance permitido del transporte.
- **R-04 — Contrato:** nunca elegir silenciosamente stack, persistencia, concurrencia o políticas temporales → preparar opciones y registrar la decisión aplicable antes de implementar. `[inicio, fin)`, adyacencia y RN-TU-03 a RN-TU-07 siguen siendo propuestas. Ante un hueco, volver a Propose.
- **R-05 — Cambios y errores:** inspeccionar documentos, código y pruebas existentes; realizar cambios mínimos y reutilizar la lógica disponible. Validar entradas explícitamente y devolver errores claros; no corregir datos inválidos silenciosamente para aceptarlos.
- **R-06 — Pruebas:** cuando exista runner, seguir TDD del roadmap: baseline existente, RED ejecutado antes de producción, GREEN mínimo, triangulación y refactor con pruebas verdes. Cubrir todos los escenarios aprobados y ejecutar la suite completa; reportar fallos previos y no archivar con pruebas fallando. Una prueba secuencial no demuestra concurrencia.
- **R-07 — Evidencia:** distinguir hechos, publicidad, propuestas y «No evidenciado». Registrar comandos y resultados reales; no atribuir al estudiante verificaciones realizadas por IA ni afirmar revisión humana, tests, capturas, video o cumplimiento que no se acreditaron. Las cinco comprobaciones personales de fuentes continúan pendientes.
- **R-08 — Git:** validar antes de cada commit local autorizado por la preferencia vigente; usar mensajes descriptivos y separar cambios ajenos. Push o publicación requieren autorización explícita aplicable a ese avance. No extender el permiso concedido al registro a esta generación de instrucciones ni a publicaciones futuras.

## Flujo de Trabajo

1. Leer estas instrucciones, KB pertinente, preguntas abiertas y roadmap; contrastar el estado real del checkout.
2. Consultar `openspec list --json`. Cuando exista el change, consultar `openspec status --change "crear-turno-sin-solapamientos" --json`; el CLI posee el estado de artefactos y tareas.
3. Explorar el problema y conservar el relevamiento dentro del alcance autorizado. Proponer mediante `/opsx:propose crear-turno-sin-solapamientos`; usar instrucciones del CLI para crear artefactos y registrar las correcciones reales.
4. Revisar el contrato y resolver las decisiones indispensables. No inventar aceptación humana ni crear manualmente la estructura de OpenSpec.
5. Aplicar tareas con `/opsx:apply crear-turno-sin-solapamientos`, reglas pertinentes del registro y pruebas del contrato. Marcar tareas sólo tras ejecución comprobada.
6. Verificar la suite completa y archivar con `/opsx:archive crear-turno-sin-solapamientos` cuando corresponda. Confirmar el resultado del CLI antes de marcar C-01 terminado.
7. Actualizar la bitácora y las decisiones en Engram para este proyecto, sin exportar memoria de otros proyectos ni confundir memoria con revisión humana. Informar archivos, verificaciones y pendientes.

Generar AGENTS.md y CLAUDE.md no inicia Apply, no resuelve el stack y no completa por sí solo la entrega académica.
