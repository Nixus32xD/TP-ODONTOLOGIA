# Decisiones y supuestos

## Decisiones documentadas

### DD-01 — Entrega propia desde cero

**Estado:** confirmado por el usuario. **Decisión:** construir una entrega propia en el repositorio TP-ODONTOLOGIA. **Contexto:** la consigna pide mostrar el proceso desde un repositorio sin código. **Alternativas consideradas:** importar una implementación completa o desarrollar la entrega. **Justificación:** el usuario eligió la segunda. **Trade-off:** exige especificar e implementar; no acredita avance reutilizado.

### DD-02 — Consultorio pequeño y primer change de turnos

**Estado:** confirmado por el usuario. **Decisión:** recepción agenda varios profesionales y boxes; el primer change rechaza solapamientos por profesional y box. **Contexto:** acotar el MVP. **Alternativas consideradas:** múltiples módulos clínicos/administrativos o una operación verificable. **Justificación:** el usuario confirmó este enfoque. **Trade-off:** WhatsApp, pagos e historia clínica se postergan.

### DD-03 — Cierre del resumen Discovery

**Estado:** confirmado el 2026-10-15. **Decisión:** registrar los once puntos y continuar con `discovery-research` y la siguiente etapa pendiente. **Contexto:** había un resumen para revisión. **Alternativas consideradas:** continuar, ajustar o detener la etapa. **Justificación:** confirmación explícita actual. **Trade-off:** conserva preguntas técnicas y revisión personal pendientes; no aprueba respuestas por defecto.

### DD-04 — Investigación asistida y verificación personal separadas

**Estado:** restricción confirmada por consigna y usuario. **Decisión:** no atribuir al estudiante las seis comprobaciones documentales del agente ni afirmar que verificó cinco fuentes. **Contexto:** honestidad de la entrega. **Alternativa descartada:** presentar revisión asistida como revisión personal. **Justificación:** esa revisión sigue pendiente. **Trade-off:** Discovery documental puede alimentar fundación, pero la evidencia de entrega permanece incompleta.

### DD-05 — Datos ficticios y sin integraciones reales

**Estado:** restricción confirmada. **Decisión:** no usar pacientes reales, historia clínica, HTTP/SOAP, credenciales, certificados ni ARCA/AFIP real en el ejercicio. **Contexto:** alcance académico acotado. **Alternativa descartada:** validar contra proveedores reales. **Justificación:** instrucciones del usuario y Discovery. **Trade-off:** las pruebas no podrán acreditar integración externa ni operación clínica real.

### DD-06 — Autorización Git vigente

**Estado:** preferencia confirmada del usuario. **Decisión:** validar cada petición completada y realizar un commit local descriptivo, separando cambios no relacionados; push y publicación requieren autorización explícita aplicable. **Contexto:** esta preferencia reemplaza la prohibición anterior de commits automáticos, sin extender permisos de publicación. El registro se publicó con autorización en `197be16a2eed4b8ea0c0dbcfcfa4cd601a38d59c`; la petición actual de AGENTS.md/CLAUDE.md comprende generación y commit local, sin nuevo permiso de push. **Alternativa descartada:** heredar indefinidamente una prohibición de commit o un permiso de publicación de otra etapa. **Justificación:** instrucciones vigentes y alcance de cada autorización. **Trade-off:** el avance local queda disponible para revisión antes de una publicación futura.

## Supuestos inferidos y propuestas

### SU-01 — Escala funcional `team`

**Supuesto:** un consultorio con recepción y varios recursos se describe como `team`. **Origen:** Discovery, usuarios y alcance. **Riesgo si es falso:** confundir contexto con soporte multiusuario concurrente. **Cómo validar:** acordar modelo de ejecución antes de prometer concurrencia. No se infiere SaaS ni multitenencia.

### SU-02 — Infraestructura sin necesidad confirmada

**Supuesto:** `needs_infra:false` es una representación provisional de baja confianza de la ausencia de necesidad confirmada. **Origen:** no hay integración ni despliegue exigidos para el primer change. **Riesgo si es falso:** descartar indebidamente una base de datos u otro mecanismo necesario. **Cómo validar:** resolver persistencia y actualizar el campo si corresponde. No se elige memoria por defecto.

### SU-03 — Modelo conceptual mínimo

**Propuesta:** turno con referencias a paciente, profesional y box más inicio/fin, usando identificadores abstractos. **Origen:** datos candidatos de Discovery. **Riesgo:** asumir identidad del paciente, formato temporal o equivalencia box/sillón sin acuerdo. **Cómo validar:** revisar [04](04_modelo_de_datos.md) durante Propose.

### SU-04 — Intervalos y estructura mínima

**Propuesta:** intervalos semiabiertos, adyacencia permitida y lógica de validación/ocupación comprobable con pocos archivos. **Origen:** ejemplos candidatos del informe, no decisión del usuario. **Riesgo:** convertir una conveniencia técnica en regla de negocio aprobada. **Cómo validar:** acordar RN-TU-03/04/05 y elegir stack antes de implementar.

## Decisiones aún no adoptadas

Stack, API o módulo, persistencia, concurrencia, precisión/zona horaria, duración por prestación, horarios, estados/cancelación, simultaneidad del paciente, compatibilidad profesional-box e idempotencia. Ni Python del informe ni productos comerciales deciden esas opciones. Ver [10](10_preguntas_abiertas.md).

## Procedencia

[Discovery canónico](../discovery/discovery.md), [resumen confirmado](../docs/discovery/resumen-para-revision.md), [consigna](../docs/CONSIGNA.md), [bitácora](../docs/BITACORA.md) e instrucciones actuales del usuario. Las entradas de bitácora anteriores describen el momento en que se escribieron; no se leen como estado vigente por encima de la confirmación actual.
