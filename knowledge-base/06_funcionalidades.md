# Funcionalidades

C-01 implementa estas cuatro historias. Los checkboxes indican verificación automatizada del contrato autorizado para Apply, no revisión humana. Ver [evidencia y trazabilidad](../docs/evidencia/implementacion-turnos.md).

## Épica 1: alta de turno sin solapamientos

### US-001 — Registrar un turno válido

**Como** recepción, **quiero** registrar un turno con paciente, profesional, box e intervalo válidos **para** asignar una atención sin ocupar recursos incompatibles.

**Criterios verificados**:

- [x] CA-001-1: con profesional y box libres, el alta devuelve los datos acordados del turno.
- [x] CA-001-2: se validan los datos mínimos sin agregar datos personales reales.
- [x] CA-001-3: la operación tiene un efecto observable verificable; SQLite local y comprobación desde conexiones nuevas.

**Reglas relacionadas:** RN-TU-01/02 y RN-EX-01/03. RN-TU-06/07 aplicadas en C-01.

### US-002 — Rechazar conflicto de profesional

**Como** recepción, **quiero** conocer que el profesional ya está ocupado **para** corregir la asignación.

**Criterios verificados**:

- [x] CA-002-1: mismo profesional e intervalos superpuestos producen rechazo aunque cambie el box.
- [x] CA-002-2: se prueba superposición parcial y contención, después de acordar el intervalo.
- [x] CA-002-3: el resultado identifica el recurso en conflicto; código conflicto_profesional.
- [x] CA-002-4: no se acepta un turno adicional tras el rechazo; sin nueva fila tras rechazo.

**Reglas relacionadas:** RN-TU-01 y RN-EX-03/04; RN-TU-03/07 aplicadas en C-01.

### US-003 — Rechazar conflicto de box

**Como** recepción, **quiero** conocer que el box ya está ocupado **para** elegir otra asignación.

**Criterios verificados**:

- [x] CA-003-1: mismo box e intervalos superpuestos producen rechazo aunque cambie el profesional.
- [x] CA-003-2: se prueba superposición parcial y contención, después de acordar el intervalo.
- [x] CA-003-3: el resultado identifica el box en conflicto; prioridad de profesional ante ambos conflictos.
- [x] CA-003-4: no se acepta un turno adicional tras el rechazo; alcance conforme al diseño acordado.

**Reglas relacionadas:** RN-TU-02 y RN-EX-03/04; RN-TU-03/07 aplicadas en C-01.

### US-004 — Recibir errores claros y verificar bordes

**Como** recepción, **quiero** que los datos inválidos sean rechazados explícitamente **para** corregirlos sin cambios silenciosos.

**Criterios verificados**:

- [x] CA-004-1: faltantes, referencias desconocidas y valores temporales inválidos siguen un contrato definido; contrato de tipos y errores de C-01.
- [x] CA-004-2: intervalo vacío e invertido se rechazan según RN-TU-05.
- [x] CA-004-3: adyacencia se permite según RN-TU-03/04 aplicadas.
- [x] CA-004-4: cada caso aprobado tiene pruebas con entradas distintas y resultados observables.

**Reglas relacionadas:** RN-EX-03/04; RN-TU-03/04/05/06 aplicadas en C-01.

## Evidencia del proceso

La consigna exige escenarios dado/cuando/entonces de caso feliz, error y borde, revisión real de Propose, pruebas ejecutadas y Archive. La evidencia registra RED/GREEN ejecutados y las comprobaciones que ya pasaron al añadirse, sin fabricar RED. Runner unittest; Archive y revisiones humanas académicas siguen pendientes.

## Funcionalidades postergadas

Editar/cancelar turnos, autoservicio, notificaciones WhatsApp, pagos, facturación, historia clínica, multisede, autenticación de producción y UI completa no se convierten en historias obligatorias por aparecer en el relevamiento. Ver [01](01_vision_y_objetivos.md) y [10](10_preguntas_abiertas.md).
