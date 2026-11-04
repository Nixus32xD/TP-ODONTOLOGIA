---
name: odontologia-openspec
description: Revisa propuestas y cambios que afecten los contratos del sistema odontológico. Usala para detectar invariantes de agenda, permisos, historia clínica, recordatorios, ledger y reportes que una revisión genérica de OpenSpec podría pasar por alto; las skills OpenSpec siguen manejando su ciclo Explore/Propose/Apply/Archive.
---

# Revisión de dominio odontológico

## Propósito

Agregar una revisión específica del negocio y la privacidad de este proyecto cuando una propuesta, delta, implementación o evidencia toque datos y operaciones odontológicas. No duplica el flujo genérico de OpenSpec.

## Uso

Lee el alcance y la especificación principal relacionada con el cambio. Selecciona sólo los invariantes correspondientes a los módulos afectados y compara los escenarios, el resultado visible y las pruebas contra ellos.

| Área afectada | Invariantes que revisar |
| --- | --- |
| Agenda y disponibilidad | Intervalos `[inicio, fin)`, zona local documentada, adyacencia válida y conflicto independiente de profesional/box; la disponibilidad orienta y el backend decide. |
| Roles, pacientes e historia clínica | Acceso mínimo por rol; el paciente sólo consulta datos propios; contenido clínico sintético y no expuesto a Recepción/Admin si el contrato lo restringe; auditoría metadata-only donde corresponda. |
| Recordatorios | Consentimiento falso por defecto; el canal simulado no llama email, WhatsApp ni proveedores. |
| Ledger y reportes | Importes exactos en centavos; saldo derivado del ledger; sin cargos automáticos; reportes agregados sin PII ni texto clínico. |
| CSV | Neutralización de fórmulas, encabezados/orden estables y ausencia de datos excluidos. |

No importes una regla de un área que el change no toca. No conviertas una práctica recomendada en política clínica nueva.

## Resultado de la revisión

Entrega una lista breve con:

- Área/invariante revisado y su fuente de verdad local.
- Escenario o borde cubierto y evidencia observable esperada.
- Omisiones o contradicciones encontradas, indicando el antes/después al corregirlas.
- Preguntas de política que el contrato no resuelve; no las completes por inferencia.

Usa datos ficticios. La skill complementa las instrucciones de `AGENTS.md`, la Knowledge Base y las skills de OpenSpec; no autoriza cambios, acceso externo ni ejecución de operaciones.
