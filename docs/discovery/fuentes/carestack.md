# CareStack — ficha de evidencia pública

Consulta: **2026-10-15**. Borrador para revisión. Sin cuenta, ejecución, contacto ni datos reales. `DOCUMENTADO`: ayuda/release/manual oficial; `AFIRMACIÓN COMERCIAL`: landing/FAQ comercial; `NO EVIDENCIADO`: sin respaldo observado.

## Identidad y alcance

**AFIRMACIÓN COMERCIAL:** CareStack, compañía multinacional con sede estadounidense en Celebration, Florida y presencia en India. Su portal developer identifica Good Methods Global Inc. Ofrece gestión dental cloud para consultorios, grupos/DSOs y especialidades. [Compañía](https://carestack.com/company), [Developer](https://developer.carestack.com/), [Planes](https://carestack.com/pricing).

## Funciones relevadas

| Dimensión | Evidencia y límites |
|---|---|
| Agenda | **DOCUMENTADO:** producción mensual/profesional, operatory/ubicación y duración; marcar profesional no disponible afecta box y avisa sobre citas; bloques y double booking configurable. La release describe conflictos de bloques y ajustes de duración de clipboard. Vistas diarias/semanales completas y exclusión transaccional simultánea: **NO EVIDENCIADAS**. [Release 5.39](https://carestack.zendesk.com/hc/en-us/articles/35330253336340-5-39-Release-Features). |
| Reserva | **AFIRMACIÓN COMERCIAL:** agenda online con opción reserva o solicitud; portal vinculado al sitio, elección de profesional/ubicación. Horario 24/7, redes sociales, WhatsApp y bot que reserve: **NO EVIDENCIADOS** en fuentes revisadas. [FAQ comercial](https://carestack.com/dental-software/faq). |
| Confirmar/cancelar/reprogramar/espera | **AFIRMACIÓN COMERCIAL:** SMS de confirmación actualiza agenda y existen waitlists. **DOCUMENTADO:** cancelar/no-show con motivo/cargo y reprogramar desde citas; cola de reprogramación. Autogestión de cancelación/reprogramación por paciente: **NO EVIDENCIADA**. [FAQ](https://carestack.com/dental-software/faq), [Release 5.30](https://carestack.zendesk.com/hc/en-us/articles/13007543408404-5-30-Release-Features), [5.39](https://carestack.zendesk.com/hc/en-us/articles/35330253336340-5-39-Release-Features). |
| Automatización | **AFIRMACIÓN COMERCIAL:** SMS programados/recurrentes y recordatorios. **DOCUMENTADO:** campañas email de formularios de historia médica pendientes. [FAQ](https://carestack.com/dental-software/faq), [5.39](https://carestack.zendesk.com/hc/en-us/articles/35330253336340-5-39-Release-Features). |
| Clínica | **AFIRMACIÓN COMERCIAL:** odontograma, planes/fases, perio e imágenes integradas. **DOCUMENTADO:** notas/plantillas, preferencias de chart 2D/3D, perio y formulario medical history/medicaciones; tratamientos vinculables a citas. [FAQ](https://carestack.com/dental-software/faq), [5.39](https://carestack.zendesk.com/hc/en-us/articles/35330253336340-5-39-Release-Features). |
| Administración | **AFIRMACIÓN COMERCIAL:** CS Pay, pagos online/planes, seguro y reportes. **DOCUMENTADO:** recibos email, gateways, reembolsos con errores, pagos de seguros y reconciliación multicentro. Cierre/arqueo de caja argentino, señas de reserva, Mercado Pago, ARCA y obras sociales locales: **NO EVIDENCIADOS**. [FAQ](https://carestack.com/dental-software/faq), [5.39](https://carestack.zendesk.com/hc/en-us/articles/35330253336340-5-39-Release-Features). |
| Integraciones | **AFIRMACIÓN COMERCIAL:** portal REST API, webhooks/extractos; comunicaciones/documentos/condiciones médicas y terceros como Ring Central/Pearl; eRx DoseSpot separado. No se ejecutaron API ni integraciones; no equivalen a soporte argentino. [Developer](https://developer.carestack.com/), [FAQ](https://carestack.com/dental-software/faq). |
| Operación | **DOCUMENTADO:** permisos por perfil y restricciones de ubicación. **AFIRMACIÓN COMERCIAL:** soporte/capacitación, auditoría y descargas de reportes. [5.39](https://carestack.zendesk.com/hc/en-us/articles/35330253336340-5-39-Release-Features), [Planes](https://carestack.com/pricing). |
| Seguridad/salida | **AFIRMACIÓN COMERCIAL:** backups automáticos, restricciones IP/horario, 2FA del portal, CSV de listas y pagos cifrados. HIPAA se menciona; no certificado examinado. Exportación clínica integral, restauración comprobada y cumplimiento argentino: **NO EVIDENCIADOS**. [FAQ](https://carestack.com/dental-software/faq). |

## Modelo comercial y adopción

**AFIRMACIÓN COMERCIAL:** página US publica Essentials desde **$829/mes** e Intelligence desde **$1299/mes**; **código monetario no explicitado en el texto revisado**, por lo que no se asume USD/ARS ni se convierte. Cotización según sedes/sillones/profesionales; posibles cargos de implementación/migración/capacitación. Add-ons VoiceStack/CareRevenue/Ace DSN; terceros pueden trasladar tarifa API. Demo gratis; prueba de uso y plan gratis **NO EVIDENCIADOS**. La tabla extraída omite indicadores de inclusión: confirmar alcance. [Pricing](https://carestack.com/pricing).

**AFIRMACIÓN COMERCIAL:** compañía declara más de 3.000 consultorios; no comprobado independientemente. [Compañía](https://carestack.com/company). Argentina: disponibilidad, soporte e implementaciones **NO EVIDENCIADOS**, sin asumir indisponibilidad.

Fortaleza: releases detallan contingencias de agenda/permisos. Diferencial anunciado: clínica, pagos, comunicación y RCM en nube. Límites: variantes/regiones y extras; no se valida calidad ni adecuación clínica/legal.

## Puntuación documental

0 sin evidencia; 1 comercial genérica; 2 comercial específica; 3 documentación de un flujo; 4 varios flujos/controles; 5 todos los criterios documentados. Total = suma(peso × nota / 5); no mide calidad real.

| Dimensión | Peso | Nota / 5 | Razón |
|---|---:|---:|---|
| Turnos | 25 | 4 | Varios controles en releases; concurrencia no cubierta. |
| Clínica | 20 | 4 | Varios flujos y notas documentados. |
| Integraciones | 15 | 0 | WhatsApp/locales argentinas no evidenciadas. |
| Administración | 15 | 4 | Pagos/reembolsos/reportes documentados. |
| Paciente | 10 | 3 | Portal documentado en releases, autogestión incompleta. |
| Seguridad/exportación | 10 | 3 | Permisos documentados, salida integral sin respaldo. |
| Precio | 5 | 2 | Importes/mes visibles, código monetario pendiente. |
| **Total ponderado** | **100** | **62/100** | Cobertura documental. |

Puntajes: turnos=4; clinica=4; integraciones=0; administracion=4; paciente=3; seguridad=3; precio=2
