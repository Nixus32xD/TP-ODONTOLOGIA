# Discovery: once puntos confirmados

**2026-10-15 - ONCE PUNTOS CONFIRMADOS.** Confirmé explícitamente los once puntos y autoricé continuar con `discovery-research`. Esta confirmación cierra la revisión del alcance; no sustituye mi verificación personal de al menos cinco fuentes, que sigue pendiente.

Elegí una entrega propia desde cero para un **consultorio pequeño y un primer change de turnos**: recepción agenda varios profesionales y boxes, evitando solapamientos de profesional y box. Postergo WhatsApp, pagos e historia clínica. Trabajo con investigación documental asistida por IA. La confirmación abarca estos once puntos, incluidas las preguntas que permanecen abiertas; no convierte las propuestas técnicas en decisiones aprobadas.

## 1. Problema

Registrar turnos sin ocupar simultáneamente al mismo profesional ni al mismo box en un consultorio odontológico pequeño de Argentina. Confirmado el segmento y objetivo; no se realizaron entrevistas que cuantifiquen pérdidas ni demanda real.

## 2. Usuarios y roles

Recepción registra turnos. Los profesionales son recursos de agenda; paciente y box se identifican con datos ficticios. Que profesionales accedan al sistema o exista un administrador de producción es una hipótesis posterior, no un requisito del primer change. Autenticación/RBAC permanecen fuera de esta porción.

## 3. Casos de uso

- Como recepción, registrar un turno con profesional, box e intervalo válidos.
- Como recepción, recibir un rechazo claro si el profesional ya está ocupado, aunque el box sea distinto.
- Como recepción, recibir un rechazo claro si el box está ocupado, aunque el profesional sea distinto.
- Como estudiante, ejecutar pruebas que vinculen cada escenario aprobado con un resultado real.

## 4. Competidores y soluciones existentes

Quince fichas y matriz de evidencia en [informe Discovery](informe-discovery.md). Orden por relación con Argentina, no por puntuación. La investigación documental asistida por IA usa fuentes públicas y distingue DOCUMENTADO, AFIRMACIÓN COMERCIAL y No evidenciado. No se probó software. Seis comprobaciones del agente están registradas; queda pendiente mi verificación personal de al menos cinco fuentes.

## 5. Funcionalidades necesarias

Alta de un turno; datos mínimos y validación explícita; exclusión temporal de profesional y box; errores comprensibles; pruebas de feliz, conflictos y borde. Catálogos ficticios mínimos. La atomicidad concurrente será un requisito concreto sólo cuando se acuerde su modelo y cómo demostrarlo; no se declara garantizada de antemano.

## 6. Funcionalidades opcionales/postergadas

WhatsApp, reserva pública, pagos/señas, facturación, obras sociales, historia clínica/odontograma, informes extensos, IA, portal del paciente, multisede y UI completa. No son bloqueantes para completar el primer change. Diferenciadores propuestos: contrato de intervalos y errores explicables con trazabilidad spec-test.

## 7. Reglas de negocio

Confirmado: no permitir solapamientos del mismo profesional ni del mismo box. Propuestas pendientes: intervalos [inicio, fin), adyacencia permitida, inicio anterior al fin y estados que ocupan recursos. Duración por prestación, horarios, cruce de día, disponibilidad, compatibilidad profesional-box y solapamiento del paciente siguen abiertos. No se presupone una política de sobreturnos.

## 8. Integraciones

Ninguna integración real para el primer change. No HTTP, SOAP, credenciales, certificados, ARCA/AFIP real ni servicios externos en el ejercicio. Las referencias comerciales de WhatsApp/pagos se usan para Discovery; no se implementan ni se ejecutan. Engram/OpenSpec son herramientas del proceso, no integraciones clínicas.

## 9. Restricciones

Entrega propia desde cero; un change completo; cambios incrementales, evidencia real, revisión humana por etapas, datos exclusivamente ficticios y pruebas correspondientes al contrato. Stack, API o módulo, persistencia y despliegue no elegidos. Requisitos/capturas de instalación Full y Go conservan su estado pendiente en el inventario. No se presume aceptación docente de Codex frente a herramientas citadas por la consigna.

## 10. Riesgos e hipótesis

Riesgos: confundir campos visuales con controles; decidir límites temporales durante implementación; demostrar sólo secuencia y afirmar concurrencia; heredar requisitos de productos grandes; trasladar cumplimiento extranjero a Argentina; omitir revisión personal de fuentes. H1: recepción valora errores que identifiquen el recurso; H2: contrato de intervalos reduce ambigüedad; H3: una porción terminada aporta mejor evidencia académica. Son hipótesis sin validación con usuarios reales.

## 11. Preguntas abiertas

Antes de implementar deben acordarse: stack; API o módulo; persistencia; estrategia y prueba de concurrencia; identidad mínima del paciente; doble turno del paciente; duración; horarios; zona horaria; estados/cancelación; límites y adyacencia; compatibilidad profesional-box e idempotencia. También falta identificar expresamente al integrante/autor de la entrega y registrar la revisión personal de fuentes. No se eligen respuestas por defecto.

## Confirmación registrada y siguiente paso

Confirmé explícitamente los once puntos y autoricé continuar con `discovery-research` el **2026-10-15**. El resultado canónico está en [Discovery](../../discovery/discovery.md) y alimenta la base de conocimiento. La confirmación conserva las propuestas y preguntas abiertas con su estado pendiente.

La revisión personal de al menos cinco fuentes sigue pendiente y se documentará cuando se realice. El siguiente paso del flujo de fundación es la base de conocimiento, antes del roadmap y la propuesta del primer change. No se afirma que estén realizados capturas o video ni se salta directamente a implementación.
