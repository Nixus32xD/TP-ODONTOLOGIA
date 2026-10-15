# Informe Discovery: gestión de turnos odontológicos

**Metodología I - TP-ODONTOLOGIA**

**Fecha de consulta y edición:** 15 de octubre de 2026.

**Estado:** BORRADOR PARA REVISIÓN. No acredita aprobación del Discovery ni revisión personal del estudiante.

**Responsable de revisión:** estudiante. **Integrante/autor de la entrega:** pendiente de identificación expresa.

## Resumen ejecutivo

El proyecto se orienta a un consultorio odontológico pequeño de Argentina, con recepción, varios profesionales y boxes. El usuario confirmó ese segmento y eligió como primer change el alta de turnos que evite solapamientos de profesional y box. Se propone una entrega propia desde cero, con datos ficticios y una única funcionalidad verificable; WhatsApp, pagos e historia clínica quedan para etapas posteriores.

Se relevaron quince sistemas mediante páginas comerciales, ayudas, manuales y condiciones oficiales. La comparación distingue funciones documentadas de afirmaciones del proveedor y de características no evidenciadas. La matriz mide cobertura documental pública, no calidad real, seguridad efectiva, aceptación clínica ni relación precio/calidad. Su orden prioriza la relación con Argentina y el problema del TP; no es un ranking comercial.

La agenda por profesional, los recordatorios, la ficha clínica y la administración aparecen en varias ofertas, con alcances y planes diferentes. Las fuentes más útiles para este primer change describen duración, recursos, bloqueos y excepciones: una advertencia de doble reserva, una sala de espera o una escala visual de calendario no equivalen a impedir un solapamiento. Tampoco la existencia de una API genérica prueba integración argentina.

La oportunidad propuesta es académica y debe validarse: demostrar con un contrato pequeño y pruebas que un intervalo no ocupa simultáneamente al mismo profesional o box. No se afirma que exista un vacío de mercado. Se mantienen abiertas la duración, los horarios, el tratamiento de estados, el solapamiento del paciente, la persistencia, la concurrencia y la forma de exposición del módulo. El stack se elegirá durante la fundación, después de revisar esas decisiones.

Este material incluye fichas, puntuación reproducible, recomendaciones, seis comprobaciones documentales del agente y referencias. La revisión personal de al menos cinco fuentes por el estudiante continúa pendiente. No se contactaron proveedores, se crearon cuentas ni se usaron datos reales. Discovery no se cierra con este borrador.

# A. Comparación de sistemas

## Método, alcance y etiquetas

Fecha común de consulta: **2026-10-15**. Se consultaron fuentes públicas y se registraron los accesos fallidos; no se probó ningún sistema. Las fichas conservan las limitaciones de plan, variante, región, antigüedad y accesibilidad. El PDF incorpora su contenido como anexo; en Markdown cada nombre enlaza la ficha detallada.

- **DOCUMENTADO (D):** manual, ayuda, contrato o política oficial describe un flujo, control o condición. Una declaración en política documenta lo que dice el proveedor; no certifica su ejecución.
- **AFIRMACIÓN COMERCIAL (C):** landing, ficha de venta, comparación de planes o cifra promocional del proveedor. No equivale a verificación funcional independiente.
- **No evidenciado (NE):** no se encontró respaldo suficiente en el material consultado. No demuestra inexistencia, indisponibilidad ni incumplimiento.

Las cifras de adopción se registran únicamente cuando las publica el proveedor; conservan su unidad, variante y región. No se transforman profesionales, usuarios o descargas en número de clínicas. Los importes corresponden a la fecha y condiciones de la página; no constituyen cotización ni se convierten monedas ambiguas.

## A.1 Identidad y relevancia para Argentina

Orden analítico por presencia/oferta local evidenciada, pertinencia dental y utilidad como referencia. Los productos internacionales sirven para contrastar flujos; su inclusión no acredita oferta argentina.

<!-- identity:start -->
| Producto / ficha | Empresa y país | Segmento | Modalidad | URL y consulta |
| --- | --- | --- | --- | --- |
| [Denteo](fuentes/denteo.md) | Datasoluciones / Argentina | Consultorio y clínica dental | SaaS/navegador | [Oficial](https://denteo.com.ar/clinica.html); 2026-10-15 |
| [Dentalink](fuentes/dentalink.md) | Healthatom / Chile; oferta Argentina | Individual, clínica y sucursales | Nube/navegador | [Oficial](https://web-ar.softwaredentalink.com/); 2026-10-15 |
| [DENTIDESK](fuentes/dentidesk.md) | DENTIDESK CHILE SpA / Chile | Clínica dental; académico separado | SaaS | [Oficial](https://www.dentidesk.com/); 2026-10-15 |
| [OdontoSoft Millennium](fuentes/odontosoft.md) | GB Systems / Argentina y USA | Consultorio y clínica dental | Windows; web opcional | [Oficial](https://gbsystems.com/os/); 2026-10-15 |
| [Doctoralia Argentina](fuentes/doctoralia-argentina.md) | Doctoralia / origen y entidad AR NE; oferta Argentina | Especialista y centro de salud | Agenda online | [Oficial](https://pro.doctoralia.com/ar/agenda-doctoralia-para-especialistas); 2026-10-15 |
| [AgendaPro](fuentes/agendapro.md) | AgendaPro Inc. / país de origen NE; oferta Argentina | Citas multirrubro; oferta dental | Nube | [Oficial](https://agendapro.com/ar/dental/software-odontologico); 2026-10-15 |
| [Odontosys](fuentes/odontosys.md) | Razón social NE / Uruguay | Consultorio dental | Windows, web y móvil | [Oficial](https://odontosys.com/); 2026-10-15 |
| [Simples Dental](fuentes/simples-dental.md) | Entidad jurídica NE / Brasil | Consultorio, clínica y redes | Web y móvil | [Oficial](https://www.simplesdental.com/); 2026-10-15 |
| [Dental Office](fuentes/dental-office.md) | Entidad jurídica NE / Brasil | Consultorio y clínica dental | Online/app según plan | [Oficial](https://www.dentaloffice.com.br/); 2026-10-15 |
| [Clinic Cloud](fuentes/clinic-cloud.md) | Doctoralia España/Internet SL / España | Clínica multiespecialidad/dental | Navegador | [Oficial](https://clinic-cloud.com/tarifas); 2026-10-15 |
| [GESDEN ONE/G5](fuentes/gesden.md) | INFOMED SOFTWARE SL / España | Clínica dental | ONE servicio; G5 licencia | [Oficial](https://www.infomedsoftware.com/software/gesden/gesden-one/); 2026-10-15 |
| [Open Dental](fuentes/open-dental.md) | Open Dental Software / USA | Consultorio y clínica dental | Autohospedado; cloud US | [Oficial](https://www.opendental.com/); 2026-10-15 |
| [Dentrix Ascend](fuentes/dentrix-ascend.md) | Henry Schein One / USA | Consultorio, grupo y DSO | Cloud | [Oficial](https://www.dentrixascend.com/); 2026-10-15 |
| [CareStack](fuentes/carestack.md) | Good Methods Global Inc. / USA | Consultorio, grupo y DSO | Cloud | [Oficial](https://carestack.com/company); 2026-10-15 |
| [Dentisoft](fuentes/dentisoft.md) | Dentisoft Technologies / USA | Consultorio dental | Cloud; Desktop distinto | [Oficial](https://dentisoft.com/corporate.html); 2026-10-15 |
<!-- identity:end -->

## A.2 Cobertura resumida

Cada celda conserva la clasificación de evidencia y refiere a la ficha correspondiente. La tabla resume agenda, clínica, integraciones argentinas/WhatsApp y oferta; los campos completos de reserva, automatización, administración, operación, seguridad, comercial y adopción están en las fichas anexas.

<!-- coverage:start -->
| Producto | Agenda | Clínica | Argentina / WhatsApp | Oferta |
| --- | --- | --- | --- | --- |
| [Denteo](fuentes/denteo.md) | D: vistas, recursos y bloqueos | D: odontograma/evoluciones | D: WhatsApp manual; C: ARCA | C: ARS/mes; divergencias pendientes |
| [Dentalink](fuentes/dentalink.md) | D: agenda y reserva con recursos | C: módulos dentales | C: WhatsApp/obras sociales AR | C: cotización; importe NE |
| [DENTIDESK](fuentes/dentidesk.md) | C: intervalos y reserva web | C: anamnesis y especialidades | D: WhatsApp manual; AR NE | D: prueba 15 días; tarifa NE |
| [OdontoSoft Millennium](fuentes/odontosoft.md) | D histórico: asignación/concurrencia | D histórico: odontograma/pagos | WhatsApp y ARCA NE | C: USD compra; vigencia pendiente |
| [Doctoralia Argentina](fuentes/doctoralia-argentina.md) | D: duración, consulta y servicios | C: registro; dental específico NE | C: WhatsApp; pagos AR NE | C: ARS/mes facturado anual |
| [AgendaPro](fuentes/agendapro.md) | D: vistas, recursos y bloqueos | C: ficha, imágenes y evolución | C: WhatsApp; fiscal próximo | C: ARS/mes; WhatsApp extra |
| [Odontosys](fuentes/odontosys.md) | D: crear, editar y duración | C: ficha/odontograma/perio | D: confirmar/cancelar WhatsApp | C: cotización; importe NE |
| [Simples Dental](fuentes/simples-dental.md) | C: sillones, bloqueos y enlace | C: odontograma y tratamiento | C: WhatsApp; pagos brasileños | C: BRL/mes con cobro anual |
| [Dental Office](fuentes/dental-office.md) | C: dentista, enlace y espera | C: odontograma; perio opcional | C: WhatsApp; Pix/NF Brasil | C: BRL mensual/anual; extras |
| [Clinic Cloud](fuentes/clinic-cloud.md) | D: cita, box opcional y duración | C: odontograma/perio por módulo | D: WhatsApp asistido; AR NE | C: EUR/mes + IVA; extras |
| [GESDEN ONE/G5](fuentes/gesden.md) | D: reserva G5; límites de variante | C: módulos ONE | D: WhatsApp G5; fiscal AR NE | D: propuesta; importe NE |
| [Open Dental](fuentes/open-dental.md) | D: recursos, bloques y reglas | D: chart, perio e imágenes | WhatsApp/local AR NE | D: USD/sede/mes; servicios extra |
| [Dentrix Ascend](fuentes/dentrix-ascend.md) | D: alta, duración y aviso conflicto | D: informe clínico | WhatsApp/local AR NE | C: cotización; importe NE |
| [CareStack](fuentes/carestack.md) | D: bloques y double booking | D: notas, perio e historia | WhatsApp/local AR NE | C: monto mensual; moneda NE |
| [Dentisoft](fuentes/dentisoft.md) | C: agenda; controles NE | C: registros/charting Pro | WhatsApp/local AR NE | C: Starter gratis; moneda NE |
<!-- coverage:end -->

# B. Matriz ponderada de evidencia

## Escala y cálculo

Los siete criterios suman 100 %. Cada nota se toma de la línea `Puntajes:` de la ficha, conservando su justificación. **Total = suma de (peso × nota / 5)**. La matriz y los totales se generan con `tools/render_discovery.py`; `matriz-evidencia.json` conserva notas, pesos, ruta y SHA-256 de cada ficha para detectar cambios de fuente.

| Nota | Significado |
|---|---|
| 0 | Sin evidencia suficiente de la dimensión consultada. |
| 1 | Afirmación comercial genérica o cobertura muy limitada. |
| 2 | Afirmación comercial específica. |
| 3 | Documentación detallada de un flujo o condición. |
| 4 | Documentación de varios flujos y controles, con faltantes explícitos. |
| 5 | Documentación completa de todos los criterios de la dimensión. |

Una nota cero no significa ausencia de función. No se pondera mejor un producto por ser barato, popular o tener más certificaciones anunciadas. El criterio de integraciones se refiere a **integraciones locales argentinas y WhatsApp**: APIs, pagos brasileños o seguros estadounidenses no obtienen por sí solos esa cobertura. Precios publicados pueden obtener 2 aunque estén completos comercialmente; no se premia el importe más bajo. Los scores de variantes distintas deben leerse con sus límites y no como una única edición con todas las funciones.

**Columnas:** T = gestión de turnos y automatización (25 %); C = funcionalidad odontológica clínica (20 %); I = integraciones locales y WhatsApp (15 %); A = administración, cobros y facturación (15 %); P = experiencia del paciente (10 %); S = seguridad, exportación y trazabilidad (10 %); Pr = precio y facilidad de adopción (5 %).

<!-- matrix:start -->
| Producto | T 25 | C 20 | I 15 | A 15 | P 10 | S 10 | Pr 5 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Denteo | 4 | 4 | 3 | 2 | 3 | 4 | 2 | 67/100 |
| Dentalink | 4 | 2 | 2 | 3 | 3 | 3 | 1 | 56/100 |
| DENTIDESK | 2 | 2 | 2 | 2 | 2 | 3 | 1 | 41/100 |
| OdontoSoft Millennium | 3 | 3 | 0 | 3 | 2 | 2 | 2 | 46/100 |
| Doctoralia Argentina | 4 | 2 | 2 | 1 | 2 | 2 | 2 | 47/100 |
| AgendaPro | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 45/100 |
| Odontosys | 4 | 2 | 3 | 2 | 3 | 3 | 1 | 56/100 |
| Simples Dental | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 40/100 |
| Dental Office | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 40/100 |
| Clinic Cloud | 4 | 2 | 3 | 3 | 3 | 2 | 2 | 58/100 |
| GESDEN ONE/G5 | 3 | 2 | 4 | 2 | 4 | 3 | 1 | 56/100 |
| Open Dental | 4 | 4 | 0 | 3 | 3 | 4 | 3 | 62/100 |
| Dentrix Ascend | 4 | 3 | 0 | 2 | 3 | 2 | 1 | 49/100 |
| CareStack | 4 | 4 | 0 | 4 | 3 | 3 | 2 | 62/100 |
| Dentisoft | 1 | 2 | 0 | 2 | 2 | 2 | 1 | 28/100 |
<!-- matrix:end -->

La matriz no reemplaza demos, pruebas de concurrencia, auditorías ni análisis de contratación. La documentación antigua o la falta de fuentes públicas limita la confianza; la ficha explica esos casos. Las notas son una herramienta de trazabilidad del relevamiento, no una recomendación automática de compra.

# C. Hallazgos e hipótesis

## C.1 Estándares observados en las ofertas

Agenda por profesional, estados, recordatorios y ficha del paciente aparecen en varias fuentes, por ejemplo [AgendaPro](fuentes/agendapro.md), [Doctoralia](fuentes/doctoralia-argentina.md), [Dental Office](fuentes/dental-office.md) y [Open Dental](fuentes/open-dental.md). Esto permite describir capacidades recurrentes en la muestra, no requisitos universales del mercado.

El dato crítico del turno incluye profesional, recurso físico e intervalo. [Clinic Cloud](fuentes/clinic-cloud.md) documenta box opcional y duración puntual; [Open Dental](fuentes/open-dental.md) distingue tiempo con y sin profesional. [Dentrix Ascend](fuentes/dentrix-ascend.md) documenta una advertencia de doble reserva que puede ignorarse. Por eso el TP debe expresar si una regla avisa o rechaza, y probar cada recurso por separado.

La automatización varía: enviar una plantilla desde WhatsApp Web, interpretar una respuesta, publicar un enlace y reservar conversacionalmente son flujos distintos. Las condiciones, versiones y extras de [GESDEN](fuentes/gesden.md), [Odontosys](fuentes/odontosys.md) y [Simples Dental](fuentes/simples-dental.md) impiden agruparlos como una misma capacidad sin matices.

## C.2 Diferenciadores respaldados y declarados

Se consideran diferenciadores documentales cuando una fuente explica un comportamiento concreto: restricciones de exportación y confirmación manual en [Denteo](fuentes/denteo.md); reglas y excepciones de agenda en [Open Dental](fuentes/open-dental.md); widget/flujo de cita y WhatsApp asistido en [Clinic Cloud](fuentes/clinic-cloud.md). Se proponen como referencias de diseño, sin afirmar superioridad.

Los diferenciales comerciales incluyen captación mediante directorio/reseñas en [Doctoralia Argentina](fuentes/doctoralia-argentina.md), API y automatización en planes de [AgendaPro](fuentes/agendapro.md), especialidades y licencia de escritorio en [OdontoSoft](fuentes/odontosoft.md), y ecosistemas de pagos/seguros en productos internacionales. La publicidad de una función, integración o estándar no equivale a prueba de ejecución, certificación examinada ni adecuación argentina.

## C.3 Lagunas documentales relevantes para Argentina

Las fuentes no permiten comparar uniformemente exclusión atómica bajo solicitudes simultáneas, restauración de backups ejecutada, exportación clínica íntegra, retención y adecuación local. Son lagunas del relevamiento, **no vacíos demostrados del mercado**. Tampoco la ausencia de ARCA, Mercado Pago u obras sociales en una página demuestra que el proveedor no ofrezca alguna integración mediante contrato.

Las jurisdicciones se mantienen separadas. RGPD, HIPAA, LGPD y normas españolas no acreditan cumplimiento argentino. Las [leyes argentinas consultadas](fuentes/marco-argentino.md) justifican minimizar datos y postergar historia clínica; no autorizan a presentar este ejercicio como sistema sanitario certificado.

Hay incertidumbres explícitas: condiciones de WhatsApp/renovación divergentes entre lecturas de Denteo; tensión entre secciones sobre datos sensibles en AgendaPro; manual histórico de OdontoSoft; variantes ONE/G5 de GESDEN; tablas de precios que pierden iconos y disponibilidad regional de servicios. Deben revisarse antes de contratar o convertir anuncios en requisitos.

## C.4 Oportunidades como hipótesis verificables

- **Hipótesis H1:** recepción necesita saber por qué un turno fue rechazado y qué recurso está ocupado. Validación propuesta: revisar con el estudiante casos de profesional y box independientes; no se entrevistó recepción real.
- **Hipótesis H2:** un contrato pequeño de intervalos explícitos reduce ambigüedades. Validación propuesta: ejemplos de solapamiento parcial, contención y borde, antes de elegir algoritmo o base de datos.
- **Hipótesis H3:** demostrar una operación de alta de punta a punta ofrece más evidencia académica que anunciar múltiples módulos incompletos. Validación: escenarios acordados, tests reales y registro de Verify/Archive.
- **Hipótesis H4:** separación de datos ficticios y funciones posteriores facilita una revisión honesta. Validación: inspección de fixtures y contrato; sin HTTP/SOAP, credenciales, ARCA real ni pacientes reales.

# D. Referencias para demos, UX y alcance

## D.1 Cinco productos prioritarios para una eventual demo

Son prioridades de revisión futura, no demos realizadas. No se crean cuentas ni se contacta a proveedores en esta entrega.

| Producto | Motivo y foco de revisión |
|---|---|
| [Denteo](fuentes/denteo.md) | Contexto argentino y guías explícitas. Contrastar profesional/box/paciente, confirmación manual y límites de exportación; resolver divergencias comerciales. |
| [Dentalink](fuentes/dentalink.md) | Relevancia regional y oferta dental. Revisar recursos, duración, exclusión efectiva y qué funciones/integraciones corresponden al mercado argentino. |
| [Dentidesk](fuentes/dentidesk.md) | Referencia dental latinoamericana. Revisar agenda, disponibilidad y distinción entre reserva, aviso y confirmación, según lo documentado. |
| [OdontoSoft](fuentes/odontosoft.md) | Contexto argentino y escritorio/multiusuario. Contrastar manual histórico con versión actual, concurrencia y reglas por doctor. |
| [Doctoralia Argentina](fuentes/doctoralia-argentina.md) | Oferta localizada y guía de configuración. Revisar duración, consultas/profesionales, reserva y comunicaciones con sus límites de plan. |

## D.2 Tres referencias de UX

**Clinic Cloud:** flujo de alta que reúne paciente, profesional, duración y box; útil para revisar orden y claridad de campos. El manual no demuestra exclusividad del box. [Ficha y ayuda](fuentes/clinic-cloud.md).

**Doctoralia Argentina:** configuración progresiva de consulta, horario, servicio y disponibilidad, más reserva multicanal. Útil para distinguir configuración interna de autoservicio del paciente. No se verificó la experiencia visual mediante uso real. [Ficha y guía](fuentes/doctoralia-argentina.md).

**Open Dental:** vistas por recursos, listas y reglas con excepciones explícitas. Útil para estudiar estados y explicar conflictos. Es referencia documental; no se propone copiar pantallas, complejidad ni condiciones estadounidenses. [Ficha y manuales](fuentes/open-dental.md).

## D.3 MVP y primera porción verificable

**Imprescindibles del primer change:** crear un turno con identificadores ficticios de paciente, profesional y box; inicio y fin válidos; rechazar ocupación temporal del mismo profesional o del mismo box; devolver errores comprensibles; cubrir casos válidos, conflictos y bordes con tests. Los catálogos mínimos pueden ser fixtures; no se requiere desarrollar CRUDs completos.

**Diferenciadores propuestos para la entrega:** contrato visible de intervalos, error que identifica el recurso en conflicto y trazabilidad entre spec, test y resultado. Son objetivos del TP, no ventajas comerciales probadas. La atomicidad frente a solicitudes concurrentes sólo podrá declararse si el mecanismo elegido y su prueba lo demuestran.

**Postergados:** WhatsApp, reservas públicas, pagos/señas, facturación/ARCA, obras sociales, historia clínica/odontograma, reportes amplios, IA, portal del paciente, multisede y una interfaz completa. Autenticación y permisos de producción no se simulan como resueltos por el módulo académico.

## D.4 Un único change candidato

**Nombre propuesto:** `crear-turno-sin-solapamientos`.

Recepción necesita registrar un turno sin asignar simultáneamente al mismo profesional ni al mismo box. Esta porción permite acordar reglas, implementarlas y verificar errores de negocio y bordes con datos ficticios. El usuario confirmó el objetivo; el contrato detallado se discutirá durante fundación/Propose. No se creó todavía un change de OpenSpec.

| Ejemplo candidato | Resultado a especificar |
|---|---|
| Turno válido, profesional y box libres | Alta exitosa con los datos acordados. |
| Mismo profesional, intervalo superpuesto, otro box | Rechazo por conflicto de profesional. |
| Mismo box, intervalo superpuesto, otro profesional | Rechazo por conflicto de box. |
| Intervalo vacío o fin anterior al inicio | Error explícito de datos inválidos. |
| Un turno empieza exactamente al finalizar otro | Propuesta: permitir adyacencia con intervalo [inicio, fin); decisión todavía pendiente. |
| Dos altas simultáneas por el mismo recurso | Mecanismo y evidencia de atomicidad pendientes de elegir persistencia. |

**Decisiones abiertas:** stack; API o módulo; persistencia; concurrencia; zona horaria/representación temporal; duración fija o por prestación; horarios habilitados y cruces de día; estados que ocupan recurso; cancelación; doble turno del paciente; disponibilidad/compatibilidad profesional-box y política de idempotencia. No se eligen silenciosamente en este informe.

# Verificación de fuentes

**Comprobación documental del agente; revisión personal del estudiante PENDIENTE.** Se contrastaron páginas públicas, no el software. La consigna exige revisión personal del estudiante y esa evidencia no se sustituye con este registro. Fecha: 2026-10-15.

| Fuente y tipo | Afirmación examinada | Hallazgo, clasificación y corrección |
|---|---|---|
| [Clinic Cloud: crear cita](https://clinic-cloud.com/faq/agenda-y-comunicaciones/como-dar-una-cita-en-mi-agenda). Ayuda oficial. | Selección de box y duración implica evitar solapamientos. | D: explica box opcional y duración puntual. NE: exclusión de box. Corrección: separar campos disponibles de regla de rechazo. Revisión personal pendiente. |
| [AgendaPro: uso de agenda](https://ayuda.agendapro.com/es/articles/6486845-como-usar-la-seccion-agenda). Tutorial de ayuda. | Minutos de los bloques indican duración clínica configurable. | D: escala visual del calendario. No prueba duración de una prestación. Corrección: no usar ese ajuste como evidencia clínica. Revisión personal pendiente. |
| [INFOMED: condiciones](https://www.infomedsoftware.com/condiciones_generales_venta/). Contrato del proveedor. | Backups/exportación acreditan disponibilidad y cumplimiento argentino. | D: obligaciones condicionadas a alojamiento/propuesta y disponibilidad de contenido tras baja; formato no explicitado allí. NE: Argentina. Corrección: conservar variante y condición contractual. Revisión personal pendiente. |
| [Dentalink: inicio](https://www.softwaredentalink.com/). Landing comercial. | ISO/HIPAA/GDPR anuncian certificación y cumplimiento comprobados. | C: referencias de seguridad del proveedor. No se examinó certificado ni auditoría. Corrección: clasificar comercial; no acreditar cumplimiento argentino. Revisión personal pendiente. |
| [Denteo: precios](https://denteo.com.ar/precios.html). Oferta comercial. | Cupos WhatsApp y modalidad Mercado Pago/renovación son condiciones uniformes. | Lecturas públicas divergentes; no se fija condición definitiva. Corrección: registrar incertidumbre, no confundir pago de suscripción con cobro clínico y requerir confirmación vigente. Revisión personal pendiente. |
| [AgendaPro: privacidad](https://agendapro.com/ar/politica-de-privacidad). Política del proveedor. | La oferta clínica basta para demostrar admisión de datos sensibles. | Las secciones 6 y 8 requieren aclaración conjunta sobre datos sensibles remitidos por comercios. Se registra una pregunta contractual, sin concluir ilegalidad ni aptitud clínica. Revisión personal pendiente. |

Las seis comprobaciones cubren ayuda, condiciones contractuales, página comercial, precios y política de privacidad. Las interpretaciones examinadas son riesgos de lectura, no errores atribuidos al estudiante. El registro ampliado está en [verificación de fuentes](verificacion-fuentes.md). Se recomienda abrir estos enlaces, contrastar personalmente cada afirmación, anotar fecha, hallazgo y corrección propia, y revisar las dos leyes del marco argentino. No se fabrican capturas ni verificaciones personales.

# Referencias y trazabilidad

Las referencias de cada producto están en su ficha, con fecha, clasificación y límites. El PDF añade todas las fichas como anexos. Las URLs siguientes se extraen de esas notas; la fecha de consulta común es 2026-10-15, salvo fecha editorial indicada por cada fuente. Que una URL figure aquí no significa que sea accesible permanentemente ni que se haya operado una cuenta.

<!-- references:start -->
## Denteo

- Privacidad: [https://www.denteo.com.ar/privacidad.html](https://www.denteo.com.ar/privacidad.html). Consulta: 2026-10-15.
- Producto: [https://denteo.com.ar/clinica.html](https://denteo.com.ar/clinica.html). Consulta: 2026-10-15.
- Agenda: [https://denteo.com.ar/docs/clinica-agenda.html](https://denteo.com.ar/docs/clinica-agenda.html). Consulta: 2026-10-15.
- Historia clínica: [https://denteo.com.ar/docs/clinica-historia-clinica.html](https://denteo.com.ar/docs/clinica-historia-clinica.html). Consulta: 2026-10-15.
- Precios: [https://denteo.com.ar/precios.html](https://denteo.com.ar/precios.html). Consulta: 2026-10-15.

## Dentalink

- Sitio general: [https://www.softwaredentalink.com/](https://www.softwaredentalink.com/). Consulta: 2026-10-15.
- Argentina: [https://web-ar.softwaredentalink.com/](https://web-ar.softwaredentalink.com/). Consulta: 2026-10-15.
- Primera cita: [https://ayuda.softwaredentalink.com/es/articles/9488188-agenda-la-primera-cita](https://ayuda.softwaredentalink.com/es/articles/9488188-agenda-la-primera-cita). Consulta: 2026-10-15.
- Agenda online: [https://ayuda.softwaredentalink.com/es/articles/9493139-configura-tu-agenda-online](https://ayuda.softwaredentalink.com/es/articles/9493139-configura-tu-agenda-online). Consulta: 2026-10-15.
- Gerty: [https://ayuda.softwaredentalink.com/es/articles/17061686-gerty](https://ayuda.softwaredentalink.com/es/articles/17061686-gerty). Consulta: 2026-10-15.
- Índice clínico: [https://ayuda.softwaredentalink.com/es/collections/13749514-potencia-tu-gestion-clinica](https://ayuda.softwaredentalink.com/es/collections/13749514-potencia-tu-gestion-clinica). Consulta: 2026-10-15.
- Reportes Excel: [https://ayuda.softwaredentalink.com/es/articles/9493465-reportes-excel](https://ayuda.softwaredentalink.com/es/articles/9493465-reportes-excel). Consulta: 2026-10-15.
- Perfil: [https://ayuda.softwaredentalink.com/es/articles/9493109-nueva-seccion-mi-perfil](https://ayuda.softwaredentalink.com/es/articles/9493109-nueva-seccion-mi-perfil). Consulta: 2026-10-15.
- Soporte: [https://www.softwaredentalink.com/soporte](https://www.softwaredentalink.com/soporte). Consulta: 2026-10-15.
- Contratación: [https://softwaredentalink.com/comenzar](https://softwaredentalink.com/comenzar). Consulta: 2026-10-15.

## DENTIDESK

- Términos: [https://app.dentidesk.com/terminos.php](https://app.dentidesk.com/terminos.php). Consulta: 2026-10-15.
- Sitio: [https://www.dentidesk.com/](https://www.dentidesk.com/). Consulta: 2026-10-15.
- Características: [https://www.dentidesk.cl/dentidesk/feature](https://www.dentidesk.cl/dentidesk/feature). Consulta: 2026-10-15.
- Noticias: [https://www.dentidesk.com/?from=MEDICALDESK](https://www.dentidesk.com/?from=MEDICALDESK). Consulta: 2026-10-15.
- Ayuda enlazada: [https://dentidesk.freshdesk.com/support/solutions](https://dentidesk.freshdesk.com/support/solutions). Consulta: 2026-10-15.

## OdontoSoft Millennium

- Sitio español: [https://gbsystems.com/os/](https://gbsystems.com/os/). Consulta: 2026-10-15.
- Prestaciones: [https://gbsystems.com/os/producto.htm](https://gbsystems.com/os/producto.htm). Consulta: 2026-10-15.
- Manual, pp. 24–27: [https://gbsystems.com/os/manual/manual_odontosoft_demo.pdf](https://gbsystems.com/os/manual/manual_odontosoft_demo.pdf). Consulta: 2026-10-15.
- Seguridad: [https://odontosoft.com/security.htm](https://odontosoft.com/security.htm). Consulta: 2026-10-15.
- Precios publicados: [https://odontosoft.com/prices.htm](https://odontosoft.com/prices.htm). Consulta: 2026-10-15.

## Doctoralia Argentina

- Producto Argentina: [https://pro.doctoralia.com/ar/agenda-doctoralia-para-especialistas](https://pro.doctoralia.com/ar/agenda-doctoralia-para-especialistas). Consulta: 2026-10-15.
- Guía de configuración de reserva: [https://pro.doctoralia.com/ar/guias/configuracion-de-la-reserva-de-cita](https://pro.doctoralia.com/ar/guias/configuracion-de-la-reserva-de-cita). Consulta: 2026-10-15.
- Precios Argentina: [https://pro.doctoralia.com/ar/precio](https://pro.doctoralia.com/ar/precio). Consulta: 2026-10-15.

## AgendaPro

- Oferta dental argentina: [https://agendapro.com/ar/dental/software-odontologico](https://agendapro.com/ar/dental/software-odontologico). Consulta: 2026-10-15.
- Ayuda: uso de la agenda: [https://ayuda.agendapro.com/es/articles/6486845-como-usar-la-seccion-agenda](https://ayuda.agendapro.com/es/articles/6486845-como-usar-la-seccion-agenda). Consulta: 2026-10-15.
- Planes Argentina: [https://agendapro.com/ar/planes](https://agendapro.com/ar/planes). Consulta: 2026-10-15.
- Política de privacidad: [https://agendapro.com/ar/politica-de-privacidad](https://agendapro.com/ar/politica-de-privacidad). Consulta: 2026-10-15.

## Odontosys

- Sitio: [https://odontosys.com/](https://odontosys.com/). Consulta: 2026-10-15.
- Privacidad: [https://odontosys.com/privacidad.html](https://odontosys.com/privacidad.html). Consulta: 2026-10-15.
- Instalación: [https://help.odontosys.com/knowledge-base/como-instalar-odontosys/](https://help.odontosys.com/knowledge-base/como-instalar-odontosys/). Consulta: 2026-10-15.
- Crear cita: [https://help.odontosys.com/knowledge-base/como-crear-una-cita/](https://help.odontosys.com/knowledge-base/como-crear-una-cita/). Consulta: 2026-10-15.
- Duraciones: [https://help.odontosys.com/knowledge-base/para-que-sirve-la-configuracion-minima-y-predeterminada-de-la-agenda/](https://help.odontosys.com/knowledge-base/para-que-sirve-la-configuracion-minima-y-predeterminada-de-la-agenda/). Consulta: 2026-10-15.
- Índice agenda: [https://help.odontosys.com/article-categories/agenda/](https://help.odontosys.com/article-categories/agenda/). Consulta: 2026-10-15.
- Confirmación: [https://help.odontosys.com/knowledge-base/confirmacion-de-asistencia/](https://help.odontosys.com/knowledge-base/confirmacion-de-asistencia/). Consulta: 2026-10-15.
- Ayuda: [https://help.odontosys.com/](https://help.odontosys.com/). Consulta: 2026-10-15.

## Simples Dental

- Inicio oficial: [https://www.simplesdental.com/](https://www.simplesdental.com/). Consulta: 2026-10-15.
- Agenda: [https://www.simplesdental.com/agenda-online](https://www.simplesdental.com/agenda-online). Consulta: 2026-10-15.
- Prontuario: [https://www.simplesdental.com/prontuario-digital](https://www.simplesdental.com/prontuario-digital). Consulta: 2026-10-15.
- Planes y precios: [https://www.simplesdental.com/planos-e-precos](https://www.simplesdental.com/planos-e-precos). Consulta: 2026-10-15.

## Dental Office

- Inicio: [https://www.dentaloffice.com.br/](https://www.dentaloffice.com.br/). Consulta: 2026-10-15.
- Planes: [https://www.dentaloffice.com.br/planos/](https://www.dentaloffice.com.br/planos/). Consulta: 2026-10-15.
- Agenda Digital: [https://www.dentaloffice.com.br/agenda-para-dentistas/](https://www.dentaloffice.com.br/agenda-para-dentistas/). Consulta: 2026-10-15.
- Prontuario electrónico: [https://www.dentaloffice.com.br/prontuario/](https://www.dentaloffice.com.br/prontuario/). Consulta: 2026-10-15.

## Clinic Cloud

- Tarifas e identificación: [https://clinic-cloud.com/tarifas](https://clinic-cloud.com/tarifas). Consulta: 2026-10-15.
- Descripción odontológica: [https://clinic-cloud.com/blog/clinic-cloud-software-para-consultorio-odontologico](https://clinic-cloud.com/blog/clinic-cloud-software-para-consultorio-odontologico). Consulta: 2026-10-15.
- Configurar agenda: [https://clinic-cloud.com/faq/agenda-y-comunicaciones/configuracion-de-agendas](https://clinic-cloud.com/faq/agenda-y-comunicaciones/configuracion-de-agendas). Consulta: 2026-10-15.
- Crear citas: [https://clinic-cloud.com/faq/agenda-y-comunicaciones/como-dar-una-cita-en-mi-agenda](https://clinic-cloud.com/faq/agenda-y-comunicaciones/como-dar-una-cita-en-mi-agenda). Consulta: 2026-10-15.
- Widget: [https://clinic-cloud.com/faq/agenda-y-comunicaciones/calendario-online-en-p%C3%A1gina-web-de-cl%C3%ADnica](https://clinic-cloud.com/faq/agenda-y-comunicaciones/calendario-online-en-p%C3%A1gina-web-de-cl%C3%ADnica). Consulta: 2026-10-15.
- WhatsApp: [https://clinic-cloud.com/faq/configuracion-centro/recodatorio-de-citas-via-whatsapp](https://clinic-cloud.com/faq/configuracion-centro/recodatorio-de-citas-via-whatsapp). Consulta: 2026-10-15.
- Ayuda comunicaciones: [https://clinic-cloud.com/faq/agenda-y-comunicaciones](https://clinic-cloud.com/faq/agenda-y-comunicaciones). Consulta: 2026-10-15.
- Exportación contable: [https://clinic-cloud.com/blog/el-sistema-de-gestion-de-clinicas-clinic-cloud-ii](https://clinic-cloud.com/blog/el-sistema-de-gestion-de-clinicas-clinic-cloud-ii). Consulta: 2026-10-15.

## GESDEN ONE/G5

- Condiciones, cláusulas 1 y 3: [https://www.infomedsoftware.com/condiciones_generales_venta/](https://www.infomedsoftware.com/condiciones_generales_venta/). Consulta: 2026-10-15.
- ONE: [https://www.infomedsoftware.com/software/gesden/gesden-one/](https://www.infomedsoftware.com/software/gesden/gesden-one/). Consulta: 2026-10-15.
- Cita online, pp. 3-17 impresas: [https://www.infomedsoftware.com/wp-content/themes/softwareinfomed/_pdfs/multi_manuales/infomed_manual_gesden-g5-cita-online.pdf](https://www.infomedsoftware.com/wp-content/themes/softwareinfomed/_pdfs/multi_manuales/infomed_manual_gesden-g5-cita-online.pdf). Consulta: 2026-10-15.
- Automation, pp. 3-13: [https://www.infomedsoftware.com/wp-content/themes/softwareinfomed/_pdfs/multi_manuales/infomed_manual_gesden-g5-automation.pdf](https://www.infomedsoftware.com/wp-content/themes/softwareinfomed/_pdfs/multi_manuales/infomed_manual_gesden-g5-automation.pdf). Consulta: 2026-10-15.
- Manuales: [https://www.infomedsoftware.com/soporte/manuales/](https://www.infomedsoftware.com/soporte/manuales/). Consulta: 2026-10-15.
- Blog del proveedor: [https://www.infomedsoftware.com/migracion-datos-seguridad-software-gesden-infomed-digitalizacion-garantizar-ciberseguridad-proteccion-escalabilidad-optimizacion-actualizaciones-rendimiento/](https://www.infomedsoftware.com/migracion-datos-seguridad-software-gesden-infomed-digitalizacion-garantizar-ciberseguridad-proteccion-escalabilidad-optimizacion-actualizaciones-rendimiento/). Consulta: 2026-10-15.

## Open Dental

- Contacto: [https://www.opendental.com/site/contact.html](https://www.opendental.com/site/contact.html). Consulta: 2026-10-15.
- Tarifas: [https://www.opendental.com/site/fees.html](https://www.opendental.com/site/fees.html). Consulta: 2026-10-15.
- Appointments Module: [https://www.opendental.com/manual/appointments.html](https://www.opendental.com/manual/appointments.html). Consulta: 2026-10-15.
- Appointment Rules: [https://www.opendental.com/manual/appointmentrules.html](https://www.opendental.com/manual/appointmentrules.html). Consulta: 2026-10-15.
- Web Sched New Patient: [https://www.opendental.com/manual/webschednewpatsetup.html](https://www.opendental.com/manual/webschednewpatsetup.html). Consulta: 2026-10-15.
- Chart Module: [https://www.opendental.com/manual/chart.html](https://www.opendental.com/manual/chart.html). Consulta: 2026-10-15.
- Módulos: [https://www.opendental.com/manual/modules.html](https://www.opendental.com/manual/modules.html). Consulta: 2026-10-15.
- Account Module: [https://www.opendental.com/manual/account.html](https://www.opendental.com/manual/account.html). Consulta: 2026-10-15.
- API: [https://www.opendental.com/site/apiappointments.html](https://www.opendental.com/site/apiappointments.html). Consulta: 2026-10-15.
- Permissions: [https://www.opendental.com/manual/permissions.html](https://www.opendental.com/manual/permissions.html). Consulta: 2026-10-15.
- Backups: [https://www.opendental.com/manual/backups.html](https://www.opendental.com/manual/backups.html). Consulta: 2026-10-15.

## Dentrix Ascend

- Sitio oficial: [https://www.dentrixascend.com/](https://www.dentrixascend.com/). Consulta: 2026-10-15.
- Descripción del proveedor: [https://www.dentrixascend.com/about-us/why-dentrix-ascend/](https://www.dentrixascend.com/about-us/why-dentrix-ascend/). Consulta: 2026-10-15.
- Crear cita: [https://hsps.pro/DentrixAscend/Help/Scheduling_appointments_for_existing_patients.htm](https://hsps.pro/DentrixAscend/Help/Scheduling_appointments_for_existing_patients.htm). Consulta: 2026-10-15.
- Índice de agenda: [https://hsps.pro/DentrixAscend/Help/Scheduling.htm](https://hsps.pro/DentrixAscend/Help/Scheduling.htm). Consulta: 2026-10-15.
- Double booking: [https://hsps.pro/DentrixAscend/Help/Handling_the_double-booking_of_providers.htm](https://hsps.pro/DentrixAscend/Help/Handling_the_double-booking_of_providers.htm). Consulta: 2026-10-15.
- Release: [https://learn.dentrixascend.com/new-online-booking-service/](https://learn.dentrixascend.com/new-online-booking-service/). Consulta: 2026-10-15.
- Paquetes: [https://www.dentrixascend.com/dental-solutions/dentrix-ascend-packages-and-suites/](https://www.dentrixascend.com/dental-solutions/dentrix-ascend-packages-and-suites/). Consulta: 2026-10-15.
- Llenar huecos: [https://hsps.pro/DentrixAscend/Help/Filling_openings.htm](https://hsps.pro/DentrixAscend/Help/Filling_openings.htm). Consulta: 2026-10-15.
- Patient Clinical Report: [https://hsps.pro/DentrixAscend/Help/Patient_Clinical_Report.htm](https://hsps.pro/DentrixAscend/Help/Patient_Clinical_Report.htm). Consulta: 2026-10-15.

## CareStack

- Compañía: [https://carestack.com/company](https://carestack.com/company). Consulta: 2026-10-15.
- Developer: [https://developer.carestack.com/](https://developer.carestack.com/). Consulta: 2026-10-15.
- Planes: [https://carestack.com/pricing](https://carestack.com/pricing). Consulta: 2026-10-15.
- Release 5.39: [https://carestack.zendesk.com/hc/en-us/articles/35330253336340-5-39-Release-Features](https://carestack.zendesk.com/hc/en-us/articles/35330253336340-5-39-Release-Features). Consulta: 2026-10-15.
- FAQ comercial: [https://carestack.com/dental-software/faq](https://carestack.com/dental-software/faq). Consulta: 2026-10-15.
- Release 5.30: [https://carestack.zendesk.com/hc/en-us/articles/13007543408404-5-30-Release-Features](https://carestack.zendesk.com/hc/en-us/articles/13007543408404-5-30-Release-Features). Consulta: 2026-10-15.

## Dentisoft

- Proveedor: [https://dentisoft.com/corporate.html](https://dentisoft.com/corporate.html). Consulta: 2026-10-15.
- Comparación Cloud Starter/Cloud Pro: [https://www.dentisoft.com/compare.html](https://www.dentisoft.com/compare.html). Consulta: 2026-10-15.
- Precios: [https://www.dentisoft.com/index.php/pricing.html](https://www.dentisoft.com/index.php/pricing.html). Consulta: 2026-10-15.
- Declaración HIPAA y seguridad: [https://www.dentisoft.com/index.php/hipaa.html](https://www.dentisoft.com/index.php/hipaa.html). Consulta: 2026-10-15.

## Marco argentino

- Texto actualizado oficial: [https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion](https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion). Consulta: 2026-10-15.
- Texto actualizado oficial: [https://www.argentina.gob.ar/normativa/nacional/ley-26529-160432/actualizacion](https://www.argentina.gob.ar/normativa/nacional/ley-26529-160432/actualizacion). Consulta: 2026-10-15.

<!-- references:end -->

## Limitaciones y próxima revisión

No hubo entrevistas, demos ejecutadas, compra, contacto comercial, auditoría técnica/legal ni datos reales. Las páginas son susceptibles de cambio, algunas tablas pierden indicadores visuales y ciertos manuales son históricos. Se registran en cada ficha los accesos fallidos o insuficientes; no se atribuyen capacidades a una fuente inaccesible.

El siguiente paso es revisar este informe y el [resumen de once puntos](resumen-para-revision.md), corregir supuestos y decidir Continuar, Ajustar o Parar acá. Sólo después de la confirmación explícita corresponde escribir el resultado canónico `discovery/discovery.md` y actualizar `state.discovery`. La base de conocimiento, el roadmap y Propose siguen pendientes.
