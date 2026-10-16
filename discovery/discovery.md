# Discovery — TP-ODONTOLOGIA

**Fecha:** 2026-10-15. **Estado:** once puntos confirmados por el usuario; cierre documental de Discovery autorizado.

Elegí una entrega propia desde cero para un consultorio odontológico pequeño de Argentina. Trabajo con investigación documental asistida por IA. La confirmación de este alcance no acredita entrevistas, pruebas de productos ni revisión personal de fuentes: mi revisión personal de las seis fuentes fue confirmada el 2026-10-15. El [informe](../docs/discovery/informe-discovery.md), sus [fichas](../docs/discovery/fuentes/) y el [registro de comprobaciones](../docs/discovery/verificacion-fuentes.md) conservan la evidencia y sus límites.

## 1. Problema que resuelve

Quiero registrar turnos sin ocupar simultáneamente al mismo profesional ni al mismo box en un consultorio odontológico pequeño. El segmento y el objetivo están confirmados. No se realizaron entrevistas que permitan cuantificar pérdidas ni demanda real.

## 2. Usuarios y roles

Recepción registra los turnos de varios profesionales y boxes. El profesional es un recurso de agenda; paciente y box se identifican con datos ficticios. El acceso de profesionales y un administrador de producción son hipótesis posteriores. Autenticación y permisos por rol quedan fuera del primer change.

## 3. Casos de uso

- Como recepción, registrar un turno con profesional, box e intervalo válidos.
- Como recepción, recibir un rechazo claro si el profesional ya está ocupado, aunque el box sea distinto.
- Como recepción, recibir un rechazo claro si el box ya está ocupado, aunque el profesional sea distinto.
- Como estudiante, ejecutar pruebas que vinculen cada escenario aprobado con un resultado real.

## 4. Competidores y soluciones existentes

El relevamiento asistido por IA reúne quince sistemas: Denteo, Dentalink, DENTIDESK, OdontoSoft Millennium, Doctoralia Argentina, AgendaPro, Odontosys, Simples Dental, Dental Office, Clinic Cloud, GESDEN ONE/G5, Open Dental, Dentrix Ascend, CareStack y Dentisoft. La matriz del [informe](../docs/discovery/informe-discovery.md) compara evidencia documental pública, con notas y precios condicionados a variante, región, plan y fecha. Su orden prioriza la relación con Argentina y no constituye un ranking comercial.

Distingo DOCUMENTADO, AFIRMACIÓN COMERCIAL y No evidenciado. No se probó software. Las seis comprobaciones documentales del agente se distinguen de mi revisión personal posterior de esas fuentes, confirmada el 2026-10-15. No afirmo que exista un vacío de mercado.

## 5. Funcionalidades necesarias

El primer change incluye alta de un turno, datos mínimos con validación explícita, exclusión temporal del profesional y del box, errores comprensibles, catálogos ficticios mínimos y pruebas de casos válidos, conflictos y bordes. La atomicidad concurrente será un requisito concreto cuando se acuerden su modelo y la forma de demostrarlo; todavía no se declara garantizada.

## 6. Funcionalidades opcionales y postergadas

Postergo WhatsApp, reserva pública, pagos y señas, facturación, obras sociales, historia clínica y odontograma, informes extensos, IA, portal del paciente, multisede y UI completa. No bloquean el primer change. Propongo como diferenciadores académicos un contrato explícito de intervalos, errores explicables y trazabilidad entre especificaciones y pruebas; aún deben concretarse y validarse.

## 7. Reglas de negocio

Está confirmado que no se permiten solapamientos del mismo profesional ni del mismo box. Mantengo como propuestas pendientes los intervalos [inicio, fin), la adyacencia permitida, el inicio anterior al fin y los estados que ocupan recursos. También quedan abiertos duración por prestación, horarios, cruce de día, disponibilidad, compatibilidad profesional-box y solapamiento del paciente. No presupongo una política de sobreturnos.

## 8. Integraciones

No incluyo integraciones reales en el primer change. El ejercicio no usa HTTP, SOAP, credenciales, certificados, ARCA/AFIP real ni servicios externos. Las capacidades comerciales de WhatsApp y pagos forman parte del relevamiento documental, sin implementación ni ejecución. Engram y OpenSpec son herramientas del proceso, no integraciones clínicas.

## 9. Restricciones

La entrega será propia y desde cero, con un change completo, cambios incrementales, evidencia real, revisión humana por etapas, datos exclusivamente ficticios y pruebas del contrato acordado. Stack, API o módulo, persistencia y despliegue siguen sin elegir. La confirmación del resumen no resuelve esas decisiones técnicas. El inventario conserva pendientes los requisitos y capturas de instalación Full y Go; tampoco se presume aceptación docente de Codex frente a las herramientas citadas por la consigna. No afirmo que estén realizados capturas o video.

## 10. Riesgos e hipótesis

Los riesgos principales son confundir campos visuales con controles, decidir límites temporales durante la implementación, demostrar sólo secuencia y afirmar concurrencia, heredar requisitos de productos grandes, trasladar cumplimiento extranjero a Argentina y omitir la revisión personal de fuentes.

Mantengo tres hipótesis sin validar con usuarios reales: recepción valora errores que identifiquen el recurso ocupado (H1); un contrato de intervalos reduce ambigüedad (H2); una porción terminada aporta mejor evidencia académica (H3).

## 11. Preguntas abiertas

Antes de implementar deben acordarse stack, API o módulo, persistencia, estrategia y prueba de concurrencia, identidad mínima del paciente, doble turno del paciente, duración, horarios, zona horaria, estados y cancelación, límites y adyacencia, compatibilidad profesional-box e idempotencia. También falta identificar expresamente al integrante/autor. Mi revisión personal de fuentes ya quedó registrada. No elijo respuestas por defecto.

## Confirmación y continuación

El usuario confirmó explícitamente los once puntos el 2026-10-15 y autorizó continuar con `discovery-research`. Esta confirmación permite registrar el resultado canónico y alimentar la base de conocimiento. Las preguntas abiertas conservan su carácter pendiente y la revisión personal de fuentes quedó confirmada posteriormente el 2026-10-15. El siguiente paso es la base de conocimiento; después corresponden roadmap y propuesta del primer change, sin saltar directamente a implementación.
