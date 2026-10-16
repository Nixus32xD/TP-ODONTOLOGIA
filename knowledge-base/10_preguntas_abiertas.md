# Preguntas abiertas

Estas dudas se registran para continuar sin inventar decisiones. No constituyen pedidos de confirmación editorial. Las decisiones indispensables deben resolverse antes de escribir el contrato afectado o implementar su comportamiento.

## Inconsistencias y límites detectados

### IN-01 — Estado histórico frente a confirmación actual

**Registro anterior:** consigna/bitácora/inventario describen etapas y pendientes en el momento de cada hito. **Registro actual:** el usuario confirmó los once puntos el 2026-10-15 y existe [Discovery canónico](../discovery/discovery.md). **Impacto:** leer el registro histórico como estado final podría reabrir una aprobación ya recibida. **Resolución:** mantener trazabilidad histórica y usar la confirmación actual para el cierre documental. La revisión personal fue confirmada posteriormente por el estudiante; capturas y otras etapas mantienen su estado propio.

### IN-02 — Selección de box frente a exclusión real

**Fuente A:** [Clinic Cloud](../docs/discovery/fuentes/clinic-cloud.md) documenta campos de box y duración. **Fuente B:** el objetivo confirmado exige rechazar conflictos de profesional y box. **Impacto:** confundir campos con controles dejaría sin especificar la regla central. **Resolución:** conservar RN-TU-01/02 y probarlas por separado; no atribuir la garantía al proveedor.

### IN-03 — Variantes, condiciones y jurisdicciones

[GESDEN](../docs/discovery/fuentes/gesden.md) separa ONE/G5; [Denteo](../docs/discovery/fuentes/denteo.md) conserva condiciones comerciales divergentes; [AgendaPro](../docs/discovery/fuentes/agendapro.md) registra una tensión sobre datos sensibles. Las declaraciones de normas extranjeras no acreditan cumplimiento argentino. **Resolución:** mantener límites y preguntas en las fichas, sin convertirlas en requisitos ni conclusiones legales del TP.

## Preguntas abiertas priorizadas

| ID / prioridad | Pregunta | Bloquea | Decisor / evidencia necesaria |
| --- | --- | --- | --- |
| Q01 / Resuelto para C-01 | FastAPI local con POST /turnos, GET /health y documentación OpenAPI; dominio SQLite reutilizado. | No bloquea Apply | Contrato publicado y continuación autorizada; no acredita revisión personal |
| Q02 / Resuelto para C-01 | Python 3.12+, FastAPI, Pydantic, Uvicorn; unittest y HTTPX/TestClient para pruebas. Dependencias locales fijadas. | No bloquea Apply | Contrato publicado y continuación autorizada; no acredita revisión personal |
| Q03 / Resuelto para C-01 | SQLite local, BEGIN IMMEDIATE y pruebas spawn sobre mismo archivo; sin infraestructura externa. | No bloquea Apply | Contrato publicado y continuación autorizada; no acredita revisión personal |
| Q04 / Resuelto para C-01 | [inicio, fin), adyacencia, inicio anterior a fin, offset explícito, UTC/minuto exacto. | No bloquea Apply | Contrato publicado y continuación autorizada; no acredita revisión personal |
| Q05 / Resuelto para C-01 | Duración positiva libre y cruce de día; horarios/descansos/disponibilidad excluidos. | No bloquea Apply | Contrato publicado y continuación autorizada; no acredita revisión personal |
| Q06 / Resuelto para C-01 | Sin estados/cancelación; todas las filas confirmadas ocupan recursos. | No bloquea Apply | Contrato publicado y continuación autorizada; no acredita revisión personal |
| Q07 / Resuelto para C-01 | IDs ficticios paciente-A/B y referencias conocidas; paciente simultáneo permitido con recursos diferentes. | No bloquea Apply | Contrato publicado y continuación autorizada; no acredita revisión personal |
| Q08 / Resuelto para C-01 | Box exclusivo; sin compatibilidad adicional, sobreturnos o idempotencia; prioridad de profesional. | No bloquea Apply | Contrato publicado y continuación autorizada; no acredita revisión personal |
| Q09 / Resuelta por confirmación personal | El estudiante confirmó el 2026-10-15 que vio y considera correctas las seis fuentes de seis tipos del registro. Hallazgos y correcciones previos atribuidos a IA. | Evidencia de fuentes registrada; no acredita auditoría funcional | Confirmación expresa del estudiante, conservada en verificacion-fuentes.md |
| Q10 / Media para fundación, alta para entrega | ¿Quién es el integrante/autor y cómo se acreditan Full/harnesses, Go, capturas, video, reflexión y uso de Codex frente a agentes de la consigna? | Preparación/entrega completa | Estudiante y docente para la aceptación de diferencias |

## Cinco grupos de evidencia pendiente del relevamiento

**Respuestas aplicadas disponibles:** [diseño de C-01](../openspec/changes/crear-turno-sin-solapamientos/design.md) responde Q01–Q08 con decisiones o exclusiones explícitas. El usuario autorizó continuar con Apply después de presentar la propuesta; no se atribuye por ello lectura personal completa del spec. Q09 está resuelta por confirmación personal; Q10 continúa pendiente.

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

Q01–Q08 están implementadas conforme al contrato de C-01. Ante un cambio de comportamiento se actualiza Propose antes de modificar código. Q09 quedó resuelta por confirmación personal; Q10 y otras evidencias humanas siguen pendientes; generación de documentación, memoria o tests no las reemplazan.
