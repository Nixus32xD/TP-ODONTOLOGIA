# CHANGES — Secuencia de Implementación

> Índice canónico de changes del proyecto **TP-ODONTOLOGIA**.
> Plan local del 2026-10-15: **un change funcional**, con Apply implementado y suite verde; verificación técnica completa, sin Archive.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificar C-01 y consultar `openspec list --json`; cuando exista, consultar `openspec status --change "crear-turno-sin-solapamientos" --json`. El CLI conserva el estado real.
2. Leer los cinco documentos de «Leer antes» y resolver las precondiciones del contrato afectado; distinguir reglas confirmadas de propuestas.
3. Tras la revisión de fundación, ejecutar `/opsx:propose crear-turno-sin-solapamientos`; revisar propuesta, diseño, escenarios y tareas antes de Apply. El nombre del CLI no lleva el ID C-01.
4. Implementar y verificar el contrato aprobado; ejecutar la suite completa y archivar con `/opsx:archive crear-turno-sin-solapamientos` sólo si las pruebas pasan.
5. Marcar `[x]` únicamente después del archivo confirmado por OpenSpec y registrar evidencia real, pendientes y revisión humana en la bitácora.

La plantilla general de `roadmap-generator` se adapta al alcance académico: bootstrap, modelos y fixtures mínimos son tareas internas de C-01. No se agregan changes de infraestructura, autenticación ni un roadmap de producción. La duración de implementación dependerá de las decisiones abiertas; no se promete una sesión de duración fija.

---

## Árbol de dependencias

```text
TP-ODONTOLOGIA
│  Precondiciones: contrato revisado y decisiones Q01–Q08 pertinentes resueltas
└── C-01 crear-turno-sin-solapamientos
       └── Verificar suite y archivar el mismo change; no es otro change
```

C-01 no depende de otros changes. Las precondiciones técnicas no son funcionalidades adicionales. OpenSpec informó `changes: []` al generar este índice; ese dato describe el origen del índice. Ahora hay tareas implementadas y verificadas; no se archivó el change.

### Paralelismo por fase

```text
GATE 0: planificación original; C-01 aún no archivado
  → C-01 crear-turno-sin-solapamientos [Agente A — contratos y dominio]
  → Apoyo sobre el mismo C-01         [Agente B — pruebas y QA]
  → Evidencia del mismo C-01          [Agente C — documentación]
```

GATE 0 representa coordinación, sin forks entre changes ni fases rígidas de OPSX. Se puede volver a Explore o Propose al detectar un hueco. La revisión y la documentación independientes pueden avanzar en paralelo; RED → GREEN → triangulación → refactor deben respetar el orden y un único responsable de escritura por archivo. No se implementa código de producción antes del test RED correspondiente.

### Camino crítico (1 change — mínimo irreducible)

```text
Contrato revisado → C-01 crear-turno-sin-solapamientos → pruebas completas → Archive
```

El objetivo es una entrega académica verificable. El camino no acredita despliegue, seguridad clínica ni preparación para producción.

### Plan óptimo con 3 agentes

Asignaciones sugeridas para el trabajo futuro; esta tabla no despacha agentes ni exige tres personas.

| Paso | Agente A (contratos y dominio) | Agente B (pruebas y QA) | Agente C (documentación) |
| --- | --- | --- | --- |
| 1 | Preparar opciones de contrato y diseño de C-01 | Revisar escenarios y estrategia de prueba | Trazar US/reglas y registrar preguntas |
| 2 | Acordar interfaz mínima del comportamiento, sin implementación anticipada | Escribir y ejecutar RED del comportamiento acordado | Documentar contrato revisado y límites |
| 3 | Escribir el mínimo código para GREEN después de RED | Ejecutar GREEN; agregar casos de triangulación en orden | Preparar instrucciones de ejecución verificables |
| 4 | Refactorizar en pasos con pruebas verdes | Ejecutar suite completa y revisar garantía concurrente acordada | Registrar comandos, resultados y evidencia de Archive |

No hay frontend definido para asignar. Las contribuciones de tres agentes son opcionales y no sustituyen revisión humana ni autoría del estudiante.

---

## FASE 1 — Alta de turno verificable

### [C-01] `crear-turno-sin-solapamientos`

- **Estado**: `[ ]` Apply implementado; suite de 53 tests y demo verdes. Ver [evidencia](docs/evidencia/implementacion-turnos.md). C-01 permanece sin marcar hasta Archive; no confundir tareas completas con entrega final.
- **Scope**: entregar una operación de alta para recepción, con recursos ficticios y rechazo de conflictos independientes de profesional y box (RN-TU-01/02).
  - Preparar dentro del mismo change el bootstrap mínimo y el runner elegidos; registrar comandos reales, sin scaffolding de módulos postergados ni instalaciones asumidas desde este roadmap.
  - Concretar representaciones mínimas de `Turno`, `Profesional`, `Box` y la identidad ficticia de `Paciente` según Q07; no añadir datos clínicos ni CRUDs completos.
  - Preparar fixtures de agenda vacía y ocupada con recursos distintos para separar conflictos. Las etiquetas y horas de la KB son ejemplos, no formatos ni duración obligatoria.
  - Definir y probar entrada, resultado y errores del alta (US-001/004), incluidos fallos de registro y ausencia de corrección silenciosa. Elegir módulo o API en Q01; no hay endpoint aprobado.
  - Implementar y probar rechazo por profesional (US-002) y box (US-003), cada uno aun cuando el otro recurso cambie. Concretar prioridad o composición del error cuando ambos entren en conflicto.
  - Implementar almacenamiento y coordinación sólo conforme a Q03. No fijar DB, archivo, memoria, migraciones, índices ni IDs UUID por completar una plantilla; usar lo necesario para el contrato revisado.
  - Especificar y probar bordes temporales acordados, validación de referencias y políticas pertinentes a esta operación; intervalos semiabiertos y adyacencia forman el contrato aplicado.
  - Vincular cada escenario aprobado con pruebas ejecutables, ejecutar la suite completa y guardar resultados antes de Archive. Actualizar especificaciones mediante el CLI, sin crear manualmente su estructura.
  - Mantener fuera del change WhatsApp, pagos, historia clínica, autenticación, multisede, interfaz gráfica completa e integraciones externas; sólo datos ficticios y HTTP local FastAPI autorizado, sin SOAP externo o ARCA/AFIP real.
- **Dependencias**: ninguna; precondiciones de contrato detalladas abajo.
- **Governance**: MEDIO — lógica de negocio de agenda; implementar con checkpoints y exponer decisiones no obvias. No modifica autenticación, pagos ni seguridad de producción.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Entidades propuestas y §Seed data inicial propuesto.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: turnos — reglas confirmadas y §Dominio: turnos — contrato aplicado.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Épica 1: alta de turno sin solapamientos; US-001 a US-004.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores y §Validación ejecutada.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Preguntas abiertas priorizadas y §Próxima decisión de implementación.

#### Precondiciones de contrato

Las respuestas aplicadas de Q01–Q08 están en [design.md](openspec/changes/crear-turno-sin-solapamientos/design.md), con alternativas y exclusiones explícitas. El usuario autorizó continuar con Apply; eso no acredita lectura personal completa de los artefactos.

| Pregunta KB | Definición necesaria para C-01 |
| --- | --- |
| Q01 | Resuelto: FastAPI HTTP local por corrección expresa del usuario; sin proveedores externos. |
| Q02 | Lenguaje, runtime, dependencias mínimas y runner; Python del informe no decide el stack del producto. |
| Q03 | Persistencia, modelo de ejecución, efecto observable y coordinación de consulta/registro; alcance de concurrencia y prueba que lo demuestra. |
| Q04 | Semántica del intervalo, adyacencia, inicio/fin inválidos, precisión y zona horaria; RN-TU-03/04/05 aplicadas en C-01. |
| Q05 | Duración, horarios, descansos, disponibilidad y cruce de día: decidir qué pertenece a esta porción y qué se posterga. |
| Q06 | Ocupaciones que cuentan y necesidad de estados; no implementar cancelación ni una máquina de estados por defecto. |
| Q07 | Identidad mínima ficticia del paciente, referencias válidas y política de doble turno del paciente. |
| Q08 | Exclusividad del box, compatibilidad profesional-box, sobreturnos, idempotencia/reintentos y prioridad ante conflictos de ambos recursos. |

Todo contrato elegido debe actualizar la propuesta y sus escenarios. Si una pregunta no aplica, registrar la exclusión y su límite; no omitirla silenciosamente. RN-TU-06/07 aplicadas en C-01.

#### Escenarios de planificación original

La tabla siguiente conserva ejemplos y pendientes del momento de planificar, no el progreso actual. El spec de C-01 y la evidencia trazan los 29 escenarios a pruebas ejecutadas. Las horas pertenecen a una misma fecha ficticia y no fijan duración de prestación.

| Tipo / historia | Dado | Cuando | Entonces / estado del contrato |
| --- | --- | --- | --- |
| Feliz / US-001 | Datos válidos y profesional/box libres | Se solicita el alta | Se obtiene el turno y un efecto observable; representación y almacenamiento pendientes. |
| Error / US-002 | Profesional-A ocupa 09:00–09:30 en box-A | Se pide profesional-A en box-B, 09:15–09:45 | Se rechaza por profesional; rechazo confirmado, error exacto y prueba de no registro pendientes. |
| Error / US-003 | Box-A está ocupado por profesional-A, 09:00–09:30 | Se pide profesional-B en box-A, 09:15–09:45 | Se rechaza por box; rechazo confirmado, forma del resultado pendiente. |
| Borde / US-004 | Existe 09:00–09:30 en los mismos recursos | Se solicita 09:30–10:00 | Se propone aceptar adyacencia; condicionado a aprobar RN-TU-03/04. |
| Inválido / US-004 | Entrada con intervalo vacío o invertido | Se solicita el alta | Se propone rechazar sin corregir; condicionado a RN-TU-05 y contrato de errores. |

Agregar a las specs escenarios de contención, recursos diferentes y fallos de registro según el contrato. Para solicitudes simultáneas, definir un escenario y prueba pertinentes al mecanismo acordado en Q03; una secuencia de altas no demuestra exclusión concurrente.

#### Validación y cierre del change

- Con runner disponible, TDD estricto: baseline de pruebas existentes (si falla, reportar como fallo previo y detener implementación); test RED ejecutado antes de código; GREEN mínimo; triangulación con al menos dos casos distintos por comportamiento; refactor con pruebas verdes en cada paso.
- Cubrir todos los escenarios aprobados con aserciones sobre resultados y efectos reales, sin tautologías. Concurrencia se prueba dentro del modelo acordado; no se extrapola a otros procesos o máquinas.
- Registrar tabla de evidencia TDD por tarea, archivo/capa de test, baseline, RED, GREEN, triangulación y refactor; comandos y resultados reales. Esta planificación documental no tiene ciclo TDD ejecutado.
- No marcar completado ni archivar si falla la suite completa. Verificar estado y artefactos con OpenSpec; no inferirlos a partir del checkbox.
- Conservar revisión humana real de Propose, correcciones y decisión, evidencia de Apply/Verify/Archive e instrucciones suficientes para repetir pruebas.

#### Pendientes de entrega que no son código de C-01

La revisión personal de las seis fuentes de seis tipos quedó confirmada por el estudiante el 2026-10-15; los hallazgos documentales previos siguen atribuidos al agente. También quedan identificación del autor, evidencias de instalación Full/harnesses y Go, capturas, video, reflexión propia, consulta Engram y revisión humana por etapa; ver [consigna](docs/CONSIGNA.md). El cierre funcional no acredita por sí solo la entrega completa.

Los commits locales requieren validación previa y separación de cambios no relacionados. **No hacer push ni publicación hasta revisión y autorización explícita del usuario.**
