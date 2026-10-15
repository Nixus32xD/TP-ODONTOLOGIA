# Open Dental — ficha de evidencia pública

Consulta: **2026-10-15**. Borrador para revisión. Sólo investigación pública; sin cuenta, ejecución, contacto ni datos reales. `DOCUMENTADO`: manual/ayuda oficial; `AFIRMACIÓN COMERCIAL`: declaración del proveedor; `NO EVIDENCIADO`: sin respaldo revisado.

## Identidad y alcance

**AFIRMACIÓN COMERCIAL:** Open Dental Software, Salem, Oregon, Estados Unidos; gestión dental. [Contacto](https://www.opendental.com/site/contact.html). **DOCUMENTADO:** software autohospedado local/remoto con licencia/soporte; Cloud figura para Estados Unidos como cargo adicional. No se asume Cloud disponible en Argentina. [Tarifas](https://www.opendental.com/site/fees.html).

## Funciones relevadas

| Dimensión | Evidencia y límites |
|---|---|
| Agenda | **DOCUMENTADO:** vistas por operatories/profesionales y clínica, barras de duración/tiempo del profesional, bloques, búsqueda de huecos, pinboard y listas. [Appointments Module](https://www.opendental.com/manual/appointments.html). |
| Sobreturnos/solapamientos | **DOCUMENTADO:** reglas pueden impedir doble reserva por procedimiento/tiempo de profesional; tiempo sin profesional puede superponerse. Web Sched permite desactivar prevención global, conservando reglas específicas. No prueba concurrencia atómica de solicitudes simultáneas. [Appointment Rules](https://www.opendental.com/manual/appointmentrules.html). |
| Reserva | **DOCUMENTADO:** Web Sched New Patient define tipos, duración, operatories, profesionales, bloqueos permitidos y prevención de double booking; genera URL. 24/7, widget/redes concretas, WhatsApp/chatbot que reserve y cancelación/reprogramación autónoma: **NO EVIDENCIADOS** en fuentes abiertas aquí. [Web Sched New Patient](https://www.opendental.com/manual/webschednewpatsetup.html). |
| Confirmación/cambios/espera | **DOCUMENTADO:** acciones break, unscheduled, completar/eliminar, estados de confirmación y ASAP. [Agenda](https://www.opendental.com/manual/appointments.html). Recordatorios/confirmaciones y Web Sched Recall/ASAP aparecen como eServices tarifados. Flujo interactivo completo de confirmación del paciente: **NO EVIDENCIADO** aquí. [Tarifas](https://www.opendental.com/site/fees.html). |
| Clínica | **DOCUMENTADO:** chart gráfico con evolución, perio, información médica, notas, imágenes, consentimientos y tratamientos planeados; notas libres bajo odontograma no guardan historial. Anamnesis estructurada completa: **NO EVIDENCIADA**. [Chart Module](https://www.opendental.com/manual/chart.html). Planes/presupuestos: módulo propio evidenciado en documentación; no se revisó detalle de fases. [Módulos](https://www.opendental.com/manual/modules.html). |
| Administración | **DOCUMENTADO:** pagos, ingreso no devengado/anticipos, cuotas, estados de cuenta, recibos/invoice y seguros/claims. Cierre/arqueo de caja local, señas ligadas a reserva, Mercado Pago, ARCA y liquidación de obras sociales argentinas: **NO EVIDENCIADOS**. [Account Module](https://www.opendental.com/manual/account.html). |
| Integraciones | **DOCUMENTADO:** API Appointments incluye crear/actualizar/confirmar, slots y Web Sched. Chart tiene bridges y DoseSpot/Ensora eRx. WhatsApp e integraciones locales argentinas: **NO EVIDENCIADOS**. Ninguna API fue ejecutada. [API](https://www.opendental.com/site/apiappointments.html), [Chart](https://www.opendental.com/manual/chart.html). |
| Operación | **DOCUMENTADO:** clínicas y vistas; permisos granulares para pagos/imagen/CSV/backups, acciones registradas en audit trail. [Agenda](https://www.opendental.com/manual/appointments.html), [Permissions](https://www.opendental.com/manual/permissions.html). Soporte internacional email/teléfono, capacitación/webinars con tarifas. [Tarifas](https://www.opendental.com/site/fees.html), [Contacto](https://www.opendental.com/site/contact.html). |
| Seguridad/salida | **DOCUMENTADO:** backups al menos diarios, cifrado recomendado y comprobación restaurando fuera de producción para autohospedado; responsabilidad operativa del cliente. Exportación CSV de estados e imágenes con permisos. No demuestra exportación integral interoperable ni restauración ejecutada. Cumplimiento argentino: **NO EVIDENCIADO**. [Backups](https://www.opendental.com/manual/backups.html), [Permissions](https://www.opendental.com/manual/permissions.html). |

## Modelo comercial y adopción

**DOCUMENTADO:** tarifa US inicial **199 USD/mes/sede**, contrato de 12 meses, hasta 3 profesionales; tarifa reducida publicada **149 USD/mes/sede** tras 12 meses, sujeta a la vigente al alcanzarlos. Otros países **89 USD/mes/sede**, 12 meses, hasta 3 profesionales; Argentina no se individualiza. **20 USD/mes** por profesional adicional salvo exclusiones. Web Sched New+Existing **75 USD/mes/sede**, Recall **75 USD/mes/sede**, ASAP **20 USD/mes/sede** (gratis con Recall). SMS tiene cargos por mensaje; conversión y capacitación aparte. Elegibilidad regional de eServices debe confirmarse. [Tarifas](https://www.opendental.com/site/fees.html).

Prueba: enlace a Trial visible; alcance/caducidad **NO EVIDENCIADOS**. Gratuidad está documentada para escuelas dentales y algunos países en desarrollo; no se asume que Argentina encuadre. [Tarifas](https://www.opendental.com/site/fees.html), [Contacto](https://www.opendental.com/site/contact.html). Adopción cuantitativa pública específica en fuentes revisadas: **NO EVIDENCIADA**.

Fortaleza documental: agenda/configuración con excepciones explícitas y permisos. Diferencial: autohospedaje y API documentada. Límite: mantenimiento/backups locales y eServices separados; no se valida calidad real, seguridad efectiva ni adaptación fiscal/legal argentina.

## Puntuación documental

0 sin evidencia; 1 comercial genérica; 2 comercial específica; 3 documentación de un flujo; 4 varios flujos/controles; 5 todos los criterios documentados. Integraciones puntúa locales argentinas/WhatsApp, no API general. Total = suma(peso × nota / 5); no mide calidad real.

| Dimensión | Peso | Nota / 5 | Razón |
|---|---:|---:|---|
| Turnos | 25 | 4 | Vistas/reglas/bloqueos detallados, concurrencia no demostrada. |
| Clínica | 20 | 4 | Varios flujos clínicos documentados. |
| Integraciones | 15 | 0 | Sin evidencia de WhatsApp/locales argentinas. |
| Administración | 15 | 3 | Flujo financiero detallado, cobertura local pendiente. |
| Paciente | 10 | 3 | Web Sched detallado, autogestión incompleta. |
| Seguridad/exportación | 10 | 4 | Permisos/backups/salida parcial con controles. |
| Precio | 5 | 3 | Tarifas, condiciones y extras detallados. |
| **Total ponderado** | **100** | **62/100** | Cobertura documental. |

Puntajes: turnos=4; clinica=4; integraciones=0; administracion=3; paciente=3; seguridad=4; precio=3
