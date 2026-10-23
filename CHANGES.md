# CHANGES — Secuencia de Implementación

> Índice canónico de changes del proyecto **TP-ODONTOLOGIA**.
> Alcance autorizado: **un único change funcional**, C-01. Consulta de estado: 2026-10-23.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificar C-01 con `openspec list --json` y consultar `openspec status --change "crear-turno-sin-solapamientos" --json`. El CLI es la fuente de verdad del estado.
2. Leer los cinco documentos de «Leer antes» y contrastarlos con el [diseño](openspec/changes/crear-turno-sin-solapamientos/design.md), la [especificación](openspec/changes/crear-turno-sin-solapamientos/specs/alta-turnos/spec.md) y las [tareas](openspec/changes/crear-turno-sin-solapamientos/tasks.md) actuales.
3. Conservar la propuesta existente: C-01 ya está implementado. Usar `/opsx:propose` sólo ante una modificación material del contrato; no recrear el change ni repetir su implementación.
4. Revisar la evidencia y verificar lo necesario antes de `/opsx:archive crear-turno-sin-solapamientos`. El archivado es el siguiente paso técnico pendiente; esta actualización del roadmap no lo ejecuta.
5. Marcar `[x]` únicamente después de confirmar el archivado y la sincronización de las specs. Completar tareas o pasar pruebas no equivale a archivar ni acredita aceptación docente.

La plantilla de `roadmap-generator` se adapta al alcance académico acordado: bootstrap, esquema, catálogos ficticios y adaptador HTTP son tareas internas de C-01. Se conserva su ID y nombre; no se crean changes adicionales de infraestructura ni un plan de producción.

**Precedencia de contratos:** la KB conserva algunos párrafos históricos. En particular, «Estado y objetivo» y «Variables de entorno» de KB-08 todavía describen el módulo anterior sin servidor. Para el contrato actual, contrastar [design.md §D-01 y §D-08](openspec/changes/crear-turno-sin-solapamientos/design.md), el spec, las tareas 6.1–6.3 y [api.py](odontologia/api.py): FastAPI local, Uvicorn y configuración `ODONTOLOGIA_DB`. No reabrir Q01–Q08 como decisiones pendientes ni interpretar esos párrafos como una prohibición del HTTP local autorizado.

---

## Árbol de dependencias

```text
TP-ODONTOLOGIA
└── C-01 crear-turno-sin-solapamientos
    ├── Bootstrap, esquema y catálogos ficticios
    ├── Dominio de agenda, persistencia y exclusión concurrente
    └── Adaptador FastAPI, pruebas y evidencia
```

Las tres ramas son componentes del mismo change, no changes independientes. C-01 no depende de otro change. El CLI informa 18/18 tareas completas y los cuatro artefactos de planificación `done`; sigue en `openspec/changes/`, sin Archive.

### Paralelismo por fase

```text
GATE 0: C-01 implementado (18/18); revisión previa a Archive
  → Revisar o verificar C-01 [Agente A]
```

**Cero forks entre changes.** GATE 0 sólo identifica el punto actual de coordinación; no agrega una barrera rígida a OPSX. Una revisión de pruebas y otra documental pueden hacerse en paralelo sobre C-01. La consolidación y el archivado corresponden a un único responsable, después de esas revisiones.

### Camino crítico (1 change — mínimo irreducible)

```text
C-01 implementado → revisión/verificación de cierre → sincronización de specs y Archive
```

El objetivo es cerrar el change académico local. Este recorrido no acredita despliegue ni preparación para producción.

### Plan óptimo con 3 agentes

Distribución opcional del trabajo restante, sin despachar agentes ni exigir tres integrantes. No existe frontend clínico para asignar.

| Paso | Agente A (Backend Core) | Agente B (Backend Aux) | Agente C (Frontend) |
| --- | --- | --- | --- |
| 1 | Revisar dominio y consistencia del contrato | Verificar pruebas y evidencia concurrente | — |
| 2 | Consolidar resultados y archivar C-01 cuando corresponda | — | — |

Una sola persona puede realizar ambos pasos. La documentación puede revisarse durante el primero, sin modificar simultáneamente los mismos archivos.

---

## FASE 1 — Alta de turno sin solapamientos

### [C-01] `crear-turno-sin-solapamientos`

- **Estado**: `[ ]` implementación completa, **18/18 tareas** según el CLI consultado el 2026-10-23; revisión de cierre y **Archive pendientes**. La [evidencia técnica](docs/evidencia/implementacion-turnos.md) registra 53 pruebas, demo y smoke HTTP satisfactorios del 2026-10-15; no son ejecuciones nuevas de esta refactorización documental.
- **Scope**: entregables del único change, ya implementados y sujetos a revisión de cierre:
  - Inicializar explícitamente un archivo SQLite nuevo con tablas `pacientes`, `profesionales`, `boxes` y `turnos`; seis recursos ficticios y cero turnos. Preservar archivos existentes y no inicializar al importar la API.
  - Exponer `crear_turno(...) -> Turno` en [agenda.py](odontologia/agenda.py), con IDs conocidos, intervalo positivo `[inicio, fin)`, offset explícito y precisión exacta de minuto; persistir y devolver UTC sin correcciones silenciosas.
  - Rechazar solapamientos del profesional y del box por separado (US-002/003), con prioridad del profesional si ambos conflictos existen; permitir adyacencia y simultaneidad con recursos independientes (US-001/004).
  - Controlar consulta e inserción dentro de `BEGIN IMMEDIATE`, con una conexión por operación; comprobar rollback previo al commit y contención con timeout. Limitar la garantía al mismo archivo local y a escritores que usan el módulo.
  - Servir `POST /turnos` mediante FastAPI: alta `201`; errores `422/404/409/503/500` sin filtrar detalles internos. Exponer `GET /health` como liveness y documentación OpenAPI; Uvicorn en loopback, sin proveedores externos.
  - Mantener pruebas en [test_agenda.py](tests/test_agenda.py), [test_concurrencia.py](tests/test_concurrencia.py), [test_demo.py](tests/test_demo.py) y [test_api.py](tests/test_api.py): entradas válidas/inválidas, límites, persistencia, conflictos, rollback, lock real, procesos `spawn` y contrato HTTP. Conservar demo temporal reproducible y trazabilidad de escenarios a pruebas.
  - Mantener fuera WhatsApp, pagos, historia clínica, autenticación, multisede, UI clínica completa e integraciones externas. Usar sólo datos ficticios; sin publicación pública de la API.
- **Dependencias**: ninguna. Bootstrap y modelos mínimos están incluidos en C-01, sin renumerarlo a `foundation-setup`.
- **Governance**: MEDIO — reglas de negocio y transacciones de agenda, con checkpoints y decisiones explícitas conforme a las instrucciones específicas del proyecto.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Entidades propuestas y §Límites que afectan el modelo.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: turnos — contrato aplicado y §Dominio: políticas de esta porción.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Épica 1: alta de turno sin solapamientos; US-001 a US-004.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 1: alta válida y §Flujo 5: solicitudes simultáneas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores y §Validación ejecutada; aplicar la advertencia de precedencia de este índice.

#### Revisión y cierre

- Consultar `openspec instructions apply --change "crear-turno-sin-solapamientos" --json`: actualmente devuelve `all_done`, sin tareas restantes, y recomienda revisar o verificar antes de archivar.
- Contrastar el contrato con la evidencia; ejecutar `openspec validate crear-turno-sin-solapamientos --strict --json`. Antes de Archive, ejecutar la suite completa y la demo indicadas en el [README](README.md), usando sus propios temporales; no intervenir una agenda o un servidor de grabación existentes.
- Mantener evidencia real del TDD. El registro reconoce desviaciones del ciclo en algunas pruebas HTTP; una suite verde posterior no demuestra por sí sola que todos los casos tuvieron RED previo. Si se modifica comportamiento, aplicar baseline, RED, GREEN, triangulación y refactor según las reglas del proyecto.
- Archivar el mismo change y confirmar sincronización de specs y resultado del CLI antes de marcarlo cerrado. No crear C-02 para completar esta porción.
- Separar el cierre técnico de las evidencias académicas: la revisión personal de fuentes fue confirmada por el estudiante; autoría, video y estado de entrega se contrastan con sus registros y comunicaciones actuales, sin deducirlos de notas históricas de Q09/Q10 ni del estado de OpenSpec.
- Validar antes de cada commit local autorizado y separar cambios ajenos. **Push o publicación requieren revisión y autorización explícita aplicable al avance.**
