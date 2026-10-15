# Visión y objetivos

## Propósito del sistema

Registrar turnos en un consultorio odontológico pequeño de Argentina sin ocupar simultáneamente al mismo profesional ni al mismo box; no se cuantificó demanda real mediante entrevistas.

Elegí una entrega propia desde cero y un primer change de turnos. El objetivo académico es recorrer especificación, implementación, pruebas y archivo de una funcionalidad pequeña con evidencia real. La [confirmación de Discovery](../discovery/discovery.md) permite continuar la fundación; las reglas pendientes no se consideran resueltas por esa aprobación.

## Objetivos por actor

| Actor o interesado | Objetivo principal | Objetivo secundario |
| --- | --- | --- |
| Recepción | Registrar un turno con recursos disponibles | Comprender el rechazo por profesional o box ocupado |
| Profesional, recurso de agenda | Evitar asignaciones simultáneas incompatibles | Tener una asignación identificable; acceso propio no requerido |
| Paciente ficticio, entidad | Identificar a quién corresponde el turno | Mantener datos mínimos; sin portal ni historia clínica |
| Estudiante | Completar un change verificable | Mostrar trazabilidad de decisiones, escenarios y resultados |
| Docente/revisor | Revisar proceso y evidencia | Distinguir trabajo realizado de propuestas y pendientes |

## Alcance del primer change

- Alta de un turno con paciente, profesional, box e intervalo, todos ficticios.
- Catálogos mínimos de recursos para los ejemplos, sin CRUDs completos obligatorios.
- Validación explícita según el contrato aplicado de C-01.
- Rechazo ante solapamiento del mismo profesional o del mismo box.
- Errores comprensibles y pruebas de casos válidos, conflictos y límites acordados.
- Un consultorio con varios profesionales y boxes; no es un SaaS multitenant.

El change activo es `crear-turno-sin-solapamientos`: módulo Python, SQLite local, intervalos semiabiertos y concurrencia limitada al mismo archivo mediante la operación. Ver [evidencia](../docs/evidencia/implementacion-turnos.md). Archive sigue pendiente.

## Fuera de alcance

- WhatsApp, reserva pública, portal del paciente y automatizaciones externas.
- Pagos, señas, facturación, ARCA/AFIP y obras sociales.
- Historia clínica, odontograma, diagnósticos y adjuntos de pacientes.
- Multisede, IA, reportes extensos y una interfaz gráfica completa.
- Autenticación y RBAC de producción; no se simulan como controles resueltos.
- Contactar proveedores, crear cuentas para el relevamiento o usar datos personales reales.

## Criterios de éxito propuestos

1. Un turno válido se registra una sola vez por operación exitosa conforme al contrato acordado.
2. Los conflictos de profesional y box se prueban por separado y no generan altas aceptadas.
3. Entradas inválidas y bordes acordados tienen escenarios y pruebas reales.
4. Cada afirmación de comportamiento se vincula con especificación y resultado de prueba.
5. No se declara concurrencia segura sin mecanismo y evidencia adecuados al almacenamiento elegido.

Estos criterios se verifican mediante los 43 tests del contrato implementado; no acreditan la entrega docente final. Las métricas de ausentismo, productividad o satisfacción carecen de medición en este ejercicio.

## Procedencia

[Discovery confirmado](../discovery/discovery.md), [sección D del informe](../docs/discovery/informe-discovery.md) y [consigna](../docs/CONSIGNA.md). Los sistemas relevados aportan contraste documental, no requisitos que deban copiarse.
