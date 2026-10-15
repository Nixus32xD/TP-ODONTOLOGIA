# Denteo — evidencia pública borrador

Consulta: 2026-10-15. Investigación documental, sin cuenta, prueba funcional ni validación humana/legal. DOCUMENTADO significa descrito en documentación del proveedor; AFIRMACIÓN COMERCIAL significa anunciado; NO EVIDENCIADO no demuestra ausencia del producto.

## Identidad y oferta

DOCUMENTADO: Denteo Clínica, operado por Datasoluciones — Servicios Tecnológicos, Reconquista, Santa Fe, Argentina. Las lecturas públicas muestran datos de contacto divergentes; se conserva únicamente empresa/ciudad/país relevantes para esta comparación. [Privacidad](https://www.denteo.com.ar/privacidad.html)

AFIRMACIÓN COMERCIAL: SaaS para consultorios/clínicas, con productos relacionados de laboratorio y app Android; acceso por navegador. No se verificó disponibilidad efectiva de apps. [Producto](https://denteo.com.ar/clinica.html)

## Agenda y relación con pacientes

DOCUMENTADO: día, semana y mes; columnas por profesional o sillón; duración de 15–120 minutos; alta desde grilla o ficha; bloqueo si el paciente ya tiene otro turno a esa hora. Bloqueos propios para vacaciones/feriados. No se documentó en esta consulta bloqueo equivalente de doble reserva del profesional/sillón, sobreturnos ni lista de espera para ocupar vacantes. [Agenda](https://denteo.com.ar/docs/clinica-agenda.html)

DOCUMENTADO: confirmar es una acción de la clínica; WhatsApp no interpreta respuestas ni incluye botón de confirmación. Envíos automáticos al crear/cancelar y un recordatorio configurable; reprogramar modifica fecha/hora y rehabilita recordatorio, sin aviso inmediato del cambio. Sala de espera refleja pacientes llegados, no una lista de demanda. Reserva autónoma online, enlace público, web/redes y chatbot: NO EVIDENCIADOS. Google sincroniza desde Denteo; bloqueos de Google no vuelven automáticamente. [Agenda](https://denteo.com.ar/docs/clinica-agenda.html)

## Clínica y administración

DOCUMENTADO: odontograma FDI adulto/infantil con historial, evoluciones con autor y versiones, adjuntos e imágenes. No admite DICOM. Exporta odontograma separado y una historia PDF limitada a 100 evoluciones, sin adjuntos ni firmas. Auditoría de consultas y modificaciones; sólo el autor edita/borra su evolución. Anamnesis estructurada y periodontograma: NO EVIDENCIADOS en la guía leída. [Historia clínica](https://denteo.com.ar/docs/clinica-historia-clinica.html)

AFIRMACIÓN COMERCIAL: presupuestos con descuentos y planes de pago; facturas ARCA A/B/C; roles y permisos; reportes de cobranzas/comisiones/resultados exportables CSV/PDF desde Professional; multisede en Enterprise. Caja, señas, liquidación de obras sociales y cobros de pacientes por MercadoPago: NO EVIDENCIADOS; MercadoPago del precio corresponde a pagar la suscripción, no prueba integración de cobros clínicos. [Producto](https://denteo.com.ar/clinica.html), [Precios](https://denteo.com.ar/precios.html)

## Operación, privacidad y comercial

DOCUMENTADO como declaración del proveedor: base en Argentina; archivos/backups en Cloudflare R2 exterior; Cloudflare procesa tránsito; TLS/AES, auditoría y backups diarios; invoca Ley 25.326 y derechos de datos. Esto no acredita cumplimiento legal argentino. [Privacidad](https://www.denteo.com.ar/privacidad.html)

AFIRMACIÓN COMERCIAL: prueba 15 días sin tarjeta; Basic ARS 30.000/mes, Professional ARS 45.000/mes, Enterprise ARS 80.000/mes; límites de usuarios/pacientes/facturas/almacenamiento; soporte y migración asistida. Precio publicado observado, sin compra. Cupos y renovación difirieron entre lecturas anteriores. La revisión adicional del 2026-10-15 publica Basic 50, Professional 200 y Enterprise 1.000 mensajes WhatsApp por mes; prueba: 50 en total. Describe pago manual o débito automático por MercadoPago para la suscripción. Se conserva el antecedente de divergencias; son condiciones publicadas observadas a esta fecha, no garantía de vigencia futura ni prueba funcional. [Precios](https://denteo.com.ar/precios.html)

Fortaleza inferida: documentación explicita restricciones útiles para diseñar turnos/exportación. Diferenciador comercial: ARCA y migración Bilog. Límite: no se verificó reserva autónoma; exportación clínica parcial documentada. Adopción pública cuantificada: NO EVIDENCIADA; no se deduce de testimonios.

## Puntuación propuesta de evidencia pública

Rúbrica: 0 sin evidencia; 1 genérica; 2 comercial específica; 3 un flujo documentado; 4 varios flujos/controles documentados; 5 cobertura completa de la dimensión. No mide calidad real.

| Dimensión/peso | 0–5 | Justificación |
|---|---:|---|
| Turnos 25 | 4 | Vistas, estados, bloqueos y reprogramación documentados; concurrencia parcial. |
| Clínica 20 | 4 | Evoluciones, odontograma, versiones y exportación con límites. |
| Integraciones 15 | 3 | WhatsApp documenta envíos/restricciones; ARCA argentino anunciado sin validación funcional. |
| Administración 15 | 2 | Funciones específicas comerciales. |
| Paciente 10 | 3 | Avisos y confirmación manual detallados. |
| Seguridad/exportación 10 | 4 | Auditoría/exportación documentadas y política detallada. |
| Precio 5 | 2 | Tarifas específicas; nueva lectura fechada aclara cupos y renovación, con antecedente de divergencias. |

Puntajes: turnos=4; clinica=4; integraciones=3; administracion=2; paciente=3; seguridad=4; precio=2

Total ponderado: 67/100 (suma de puntaje × peso / 5).
