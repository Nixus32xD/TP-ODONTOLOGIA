# Funcionalidades

Un único change candidato reúne estas historias. No son changes creados ni funcionalidades terminadas. Los criterios que dependen de reglas temporales o persistencia conservan la marca **pendiente** hasta Propose.

## Épica 1: alta de turno sin solapamientos

### US-001 — Registrar un turno válido

**Como** recepción, **quiero** registrar un turno con paciente, profesional, box e intervalo válidos **para** asignar una atención sin ocupar recursos incompatibles.

**Criterios de aceptación candidatos**:

- [ ] CA-001-1: con profesional y box libres, el alta devuelve los datos acordados del turno.
- [ ] CA-001-2: se validan los datos mínimos sin agregar datos personales reales.
- [ ] CA-001-3: la operación tiene un efecto observable verificable; almacenamiento y forma de comprobarlo pendientes.

**Reglas relacionadas:** RN-TU-01/02 y RN-EX-01/03. RN-TU-06/07 son propuestas.

### US-002 — Rechazar conflicto de profesional

**Como** recepción, **quiero** conocer que el profesional ya está ocupado **para** corregir la asignación.

**Criterios de aceptación candidatos**:

- [ ] CA-002-1: mismo profesional e intervalos superpuestos producen rechazo aunque cambie el box.
- [ ] CA-002-2: se prueba superposición parcial y contención, después de acordar el intervalo.
- [ ] CA-002-3: el resultado identifica el recurso en conflicto; forma exacta del error pendiente.
- [ ] CA-002-4: no se acepta un turno adicional tras el rechazo; garantía de registro pendiente del diseño.

**Reglas relacionadas:** RN-TU-01 y RN-EX-03/04; RN-TU-03/07 propuestas.

### US-003 — Rechazar conflicto de box

**Como** recepción, **quiero** conocer que el box ya está ocupado **para** elegir otra asignación.

**Criterios de aceptación candidatos**:

- [ ] CA-003-1: mismo box e intervalos superpuestos producen rechazo aunque cambie el profesional.
- [ ] CA-003-2: se prueba superposición parcial y contención, después de acordar el intervalo.
- [ ] CA-003-3: el resultado identifica el box en conflicto; prioridad ante ambos conflictos pendiente.
- [ ] CA-003-4: no se acepta un turno adicional tras el rechazo; alcance conforme al diseño acordado.

**Reglas relacionadas:** RN-TU-02 y RN-EX-03/04; RN-TU-03/07 propuestas.

### US-004 — Recibir errores claros y verificar bordes

**Como** recepción, **quiero** que los datos inválidos sean rechazados explícitamente **para** corregirlos sin cambios silenciosos.

**Criterios de aceptación candidatos**:

- [ ] CA-004-1: faltantes, referencias desconocidas y valores temporales inválidos siguen un contrato definido; formato y tipos pendientes.
- [ ] CA-004-2: intervalo vacío e invertido se rechazan si se aprueba RN-TU-05.
- [ ] CA-004-3: adyacencia se permite si se aprueban RN-TU-03/04; no se marca aprobada de antemano.
- [ ] CA-004-4: cada caso aprobado tiene pruebas con entradas distintas y resultados observables.

**Reglas relacionadas:** RN-EX-03/04; RN-TU-03/04/05/06 propuestas.

## Evidencia del proceso

La consigna exige escenarios dado/cuando/entonces de caso feliz, error y borde, revisión real de Propose, pruebas ejecutadas y Archive. TDD se aplicará durante implementación cuando se seleccione un runner; esta generación documental no produce una fase RED/GREEN ficticia.

## Funcionalidades postergadas

Editar/cancelar turnos, autoservicio, notificaciones WhatsApp, pagos, facturación, historia clínica, multisede, autenticación de producción y UI completa no se convierten en historias obligatorias por aparecer en el relevamiento. Ver [01](01_vision_y_objetivos.md) y [10](10_preguntas_abiertas.md).
