# Preguntas abiertas

Estas dudas se registran para continuar sin inventar decisiones. No constituyen pedidos de confirmación editorial. Las decisiones indispensables deben resolverse antes de escribir el contrato afectado o implementar su comportamiento.

## Inconsistencias y límites detectados

### IN-01 — Estado histórico frente a confirmación actual

**Registro anterior:** consigna/bitácora/inventario describen etapas y pendientes en el momento de cada hito. **Registro actual:** el usuario confirmó los once puntos el 2026-10-15 y existe [Discovery canónico](../discovery/discovery.md). **Impacto:** leer el registro histórico como estado final podría reabrir una aprobación ya recibida. **Resolución:** mantener trazabilidad histórica y usar la confirmación actual para el cierre documental. Esto no completa verificación personal, capturas ni otras etapas.

### IN-02 — Selección de box frente a exclusión real

**Fuente A:** [Clinic Cloud](../docs/discovery/fuentes/clinic-cloud.md) documenta campos de box y duración. **Fuente B:** el objetivo confirmado exige rechazar conflictos de profesional y box. **Impacto:** confundir campos con controles dejaría sin especificar la regla central. **Resolución:** conservar RN-TU-01/02 y probarlas por separado; no atribuir la garantía al proveedor.

### IN-03 — Variantes, condiciones y jurisdicciones

[GESDEN](../docs/discovery/fuentes/gesden.md) separa ONE/G5; [Denteo](../docs/discovery/fuentes/denteo.md) conserva condiciones comerciales divergentes; [AgendaPro](../docs/discovery/fuentes/agendapro.md) registra una tensión sobre datos sensibles. Las declaraciones de normas extranjeras no acreditan cumplimiento argentino. **Resolución:** mantener límites y preguntas en las fichas, sin convertirlas en requisitos ni conclusiones legales del TP.

## Preguntas abiertas priorizadas

| ID / prioridad | Pregunta | Bloquea | Decisor / evidencia necesaria |
| --- | --- | --- | --- |
| Q01 / Alta | ¿Módulo de dominio o API, y qué significa API dentro de la restricción de no ejecutar HTTP/servicios externos? `[DISCOVERY] system_type` no puede inferirse con confianza | Contrato de exposición | Estudiante, con consigna e instrucciones vigentes |
| Q02 / Alta | ¿Qué lenguaje, dependencias mínimas y runner se usarán? `[DISCOVERY] stack` pendiente de definición en fundación | Diseño, instalación y TDD | Estudiante; comparar opciones según una porción pequeña, no el renderer del PDF |
| Q03 / Alta | ¿Qué persistencia y modelo de ejecución se necesitan, y qué concurrencia se garantiza y prueba? `[DISCOVERY] needs_infra` de baja confianza | Almacenamiento, atomicidad y evidencia | Estudiante; `false` provisional no descarta DB ni elige memoria |
| Q04 / Alta | ¿Se aprueban intervalos `[inicio, fin)`, adyacencia e inicio anterior al fin? ¿Qué precisión, zona horaria y errores por valores inválidos? | Predicado de solapamiento y bordes | Estudiante; ejemplos de RN-TU-03/04/05 |
| Q05 / Alta | ¿Duración libre, fija o por prestación? ¿Horarios, descansos, disponibilidad y cruce de día forman parte de este change? | Datos y aceptación temporal | Estudiante; no hay duración ni horario confirmados |
| Q06 / Alta | ¿Qué estados ocupan los recursos y cómo se trata la cancelación? ¿Se necesita un estado en esta porción? | Consulta de ocupación | Estudiante; evitar implementar cancelación por defecto |
| Q07 / Alta | ¿Cuál es la identidad mínima ficticia del paciente y se rechaza su doble turno? | Modelo y validación de referencias | Estudiante; simultaneidad del paciente no deducida de profesional/box |
| Q08 / Alta | ¿Box equivale a un sillón exclusivo? ¿Hay compatibilidad profesional-box, sobreturnos, idempotencia o prioridad entre errores concurrentes de recursos? | Reglas adicionales y contrato de error | Estudiante; no introducir excepciones ni deduplicación implícitas |
| Q09 / Alta para entrega | ¿Cuándo se registrará la revisión personal de al menos cinco fuentes de distintos tipos, con hallazgo y corrección? | Evidencia de verificación del TP | Estudiante; sigue pendiente, aunque el resumen fue confirmado |
| Q10 / Media para fundación, alta para entrega | ¿Quién es el integrante/autor y cómo se acreditan Full/harnesses, Go, capturas, video, reflexión y uso de Codex frente a agentes de la consigna? | Preparación/entrega completa | Estudiante y docente para la aceptación de diferencias |

## Cinco grupos de evidencia pendiente del relevamiento

`No evidenciado` no prueba inexistencia. Esta tabla mantiene trazabilidad de las dudas de mercado; resolverlas no amplía automáticamente el MVP ni autoriza contactar proveedores.

| Grupo | Qué no quedó demostrado | Fichas / fuentes documentadas |
| --- | --- | --- |
| Disponibilidad regional | Oferta contractual/soporte argentino de varias referencias internacionales | [Clinic Cloud](../docs/discovery/fuentes/clinic-cloud.md), [GESDEN](../docs/discovery/fuentes/gesden.md), [CareStack](../docs/discovery/fuentes/carestack.md) |
| Planes y condiciones | Inclusiones, extras, moneda o vigencia uniforme; condiciones Denteo divergentes | [Denteo](../docs/discovery/fuentes/denteo.md), [Dental Office](../docs/discovery/fuentes/dental-office.md), [Dentisoft](../docs/discovery/fuentes/dentisoft.md) |
| Exportación y backups | Exportación clínica integral y restauración ejecutada; reportes/declaraciones no bastan | [Dentalink](../docs/discovery/fuentes/dentalink.md), [Open Dental](../docs/discovery/fuentes/open-dental.md), [GESDEN](../docs/discovery/fuentes/gesden.md) |
| Integraciones locales | API genérica/pagos extranjeros no prueban Mercado Pago, ARCA ni obras sociales argentinas | [Dentalink](../docs/discovery/fuentes/dentalink.md), [DENTIDESK](../docs/discovery/fuentes/dentidesk.md), [CareStack](../docs/discovery/fuentes/carestack.md) |
| Adecuación argentina | Certificación/cumplimiento efectivo y controles de datos sensibles no auditados | [Marco argentino](../docs/discovery/fuentes/marco-argentino.md), [AgendaPro](../docs/discovery/fuentes/agendapro.md), [Doctoralia](../docs/discovery/fuentes/doctoralia-argentina.md) |

Las URLs y fechas originales permanecen en cada ficha y en el [informe](../docs/discovery/informe-discovery.md). Las seis comprobaciones del agente constan en [verificacion-fuentes.md](../docs/discovery/verificacion-fuentes.md); no son revisión personal del estudiante.

## Próxima decisión de implementación

El roadmap puede organizar dependencias y estas dudas sin elegir respuestas silenciosas. Antes de Apply deben quedar acordados los contratos que afecten el primer change; ante un hueco de negocio se vuelve a Propose. No se bloquea la edición documental rutinaria ni se generan código, tests o publicación desde esta KB.
