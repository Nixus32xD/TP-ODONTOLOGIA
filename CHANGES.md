# CHANGES — Secuencia de Implementación

> Índice canónico del proyecto **TP-ODONTOLOGIA**, actualizado el 2026-10-28.
> **Plan del producto completo; implementación actual limitada a C-01.** C-02 a C-20 son changes futuros propuestos, no funcionalidades entregadas ni autorizaciones para ejecutarlas.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Elegir el change por objetivo y dependencias. Consultar `openspec list --json` y, si ya existe, `openspec status --change "<nombre>" --json`; el CLI determina su estado real.
2. Leer los documentos de «Leer antes». Para cada change futuro, ampliar la KB y acordar los contratos aún no definidos antes de implementar; una referencia a una exclusión de C-01 identifica una decisión a revisar, no un requisito ya aprobado.
3. Cuando se autorice ese avance, ejecutar `/opsx:propose <nombre-kebab-case>` y revisar propuesta, diseño, escenarios y tareas. Los IDs C-NN son índices del roadmap, no prefijos obligatorios del nombre CLI. C-01 ya existe: conservarlo.
4. Implementar únicamente el alcance autorizado, verificar con evidencia real y usar `/opsx:archive <nombre>` al cerrar. Diseñar y probar cada ampliación sin cambiar silenciosamente el comportamiento anterior.
5. Marcar `[x]` sólo después del archivado confirmado y la sincronización de specs. Un roadmap, un test verde o una propuesta no acreditan revisión humana, implementación futura ni aceptación docente.

### Alcance del producto y de esta entrega

La aclaración del usuario del 2026-10-28 corrige el índice anterior: **hacer sólo C-01 ahora no significa planificar sólo C-01**. El producto futuro es un sistema para un consultorio odontológico pequeño, con recepción, profesionales y boxes: agenda operativa, catálogos, acceso seguro, interfaz de recepción, recuperación de datos y, después, módulos clínicos, comunicación con pacientes y administración.

- **Entrega actual:** C-01 `crear-turno-sin-solapamientos`, con 18/18 tareas completas y Archive confirmado el 2026-10-28; la spec principal es [alta-turnos](openspec/specs/alta-turnos/spec.md). No se cambia su nombre, su spec, su código ni su contrato.
- **MVP operativo futuro:** C-02 a C-14 completan una agenda de recepción administrable y un despliegue controlado. La seguridad, la auditoría y la restauración deben verificarse antes de habilitar datos reales.
- **Evolución del producto:** C-15 a C-20 agregan clínica, odontograma/plan de tratamiento, recordatorios, reserva del paciente, cobros y reportes. Se proponen para mostrar el alcance completo; su implementación requiere priorización y contratos propios.
- **Opciones no comprometidas:** multisede/SaaS multitenant, IA, obras sociales y facturación electrónica ARCA no se vuelven obligatorias por aparecer en productos comparados. Si se eligen, se agregarán changes posteriores con investigación y aprobación específicas. C-19 no incluye emisión fiscal ni conexión con pagos reales.

La KB y las instrucciones existentes documentan principalmente la porción académica C-01. Sus exclusiones siguen vigentes para esa implementación; las capacidades futuras de este roadmap son propuestas nuevas de planificación, no ampliaciones retroactivas de las US-001 a US-004. Para C-02+ faltan criterios específicos que se deben desarrollar en la KB y Propose del change correspondiente. Hasta una autorización posterior se mantienen datos ficticios y ninguna integración externa real.

**Base técnica preservada:** Python/FastAPI y SQLite local. Bootstrap y modelos mínimos ya pertenecen a C-01; no se renumera como `foundation-setup`. C-02 prepara la evolución del esquema. Una migración a otro motor, la tecnología de frontend, el hosting y los proveedores quedan como decisiones futuras justificadas. El contrato actual se consulta en [design.md](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md), [spec.md](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/specs/alta-turnos/spec.md) y [api.py](odontologia/api.py); los párrafos históricos «sin servidor» y «sin variables» de KB-08 no sustituyen FastAPI, Uvicorn y `ODONTOLOGIA_DB` ya implementados.

### Decisiones que habilita la planificación

| Decisión pendiente | Change que debe resolverla | Condición previa a su implementación |
| --- | --- | --- |
| Versionado de esquema y necesidad de otro motor | C-02 | Compatibilidad con agendas existentes, migración reversible y prueba con copia ficticia; no cambiar SQLite por plantilla |
| Identidades, permisos, sesiones y auditoría | C-03/C-04 | Matriz de acceso y eventos revisados; aprobación humana antes de código de seguridad |
| Datos mínimos, prestaciones y disponibilidad | C-05/C-06/C-07 | Campos, bajas y excepciones definidos sin perder referencias históricas |
| Estados, cancelación y reprogramación | C-09/C-10 | Transiciones y concurrencia especificadas; exclusión del paciente explícitamente decidida |
| UI y operación desplegada | C-11/C-12/C-13/C-14 | Elegir frontend, probar recuperación y seguridad; no extrapolar SQLite a una red compartida |
| Datos clínicos, comunicaciones y dinero | C-15 a C-20 | Revisión de permisos, privacidad, reglas clínicas/monetarias y proveedor cuando corresponda; sólo simulación en este ejercicio |

---

## Árbol de dependencias

```text
C-01 crear-turno-sin-solapamientos (implementado y archivado)
└── C-02 evolucionar-esquema-y-configuracion
    └── C-03 autenticar-y-autorizar-personal
        └── C-04 registrar-auditoria-de-operaciones
            ├── C-05 administrar-pacientes
            ├── C-06 administrar-recursos-y-prestaciones
            │   └── C-07 configurar-horarios-y-bloqueos
            ├── C-09 gestionar-estados-y-cancelaciones (también C-05, C-06)
            └── C-12 respaldar-y-restaurar-agenda

C-05 + C-07 + C-09
└── C-08 consultar-agenda-y-disponibilidad
    └── C-10 reprogramar-turnos-atomicamente (también C-09)
        └── C-11 operar-agenda-desde-recepcion (también C-08)

C-11 + C-12
└── C-13 endurecer-seguridad-y-observabilidad
    ├── C-14 desplegar-mvp-en-entorno-controlado
    ├── C-15 registrar-historia-clinica (también C-05, C-06)
    │   └── C-16 gestionar-odontograma-y-plan
    ├── C-17 programar-recordatorios (también C-08, C-09, C-10)
    ├── C-18 habilitar-reserva-del-paciente (también C-08, C-10)
    └── C-19 registrar-cobros-y-movimientos (también C-05, C-06, C-09)
        └── C-20 consultar-reportes-operativos (también C-08, C-09)
```

Los números son identificadores estables agrupados por capacidad, no un orden de ejecución por sí solos: C-09 precede a C-08 porque una consulta operativa debe conocer qué estados ocupan recursos. Las dependencias declaradas en cada ficha son el contrato del grafo. C-01 ya fue verificado y archivado el 2026-10-28. C-02 es el siguiente change planificado; su Propose y su implementación requieren autorización posterior.

### Paralelismo por fase

Los GATES expresan dependencias del plan futuro; sólo C-01 está actualmente completado y archivado. El símbolo `✓` significa «una vez verificado y cerrado». No imponen fases rígidas a OPSX.

```text
GATE 0: C-01 ✓
  → C-02 → C-03 → C-04               [Agente A — secuencia de fundamento]

GATE 1: C-04 ✓                       ← FORK
  → C-05 pacientes                   [Agente A]
  → C-06 recursos/prestaciones       [Agente B]
  → C-12 backup/restauración         [Agente C — apoyo operativo]

GATE 2: C-05 y C-06 ✓
  → C-09 estados/cancelación         [Agente A]
  → C-07 horarios/bloqueos           [Agente B]

GATE 3: C-07 y C-09 ✓
  → C-08 → C-10                     [Agente A]
  → C-11 tras C-10 ✓                [Agente C]
  → C-13 tras C-11 y C-12 ✓         [Agente A]

GATE 4: C-13 ✓                       ← FORK
  → C-14 despliegue                  [Agente A]
  → C-17 recordatorios               [Agente B]
  → C-18 reserva del paciente        [Agente C]
  → C-15 clínica                     [Agente A — después de C-14 en el plan]
  → C-19 cobros                      [Agente B — después de C-17 en el plan]

GATE 5: C-15 y C-19 ✓
  → C-16 odontograma/plan            [Agente A — requiere C-15]
  → C-20 reportes                    [Agente B — requiere C-19]
```

En GATE 5 cada rama puede empezar cuando se complete su propio prerrequisito; no debe esperar a la otra. En GATE 4 las cinco ramas son independientes entre sí, pero sólo se asignan tres a la vez. Las demás dependencias ya quedan satisfechas por los ancestros de C-13. Acordar interfaces y propiedad de archivos antes de ejecutar en paralelo; rutas, esquema y contratos compartidos se consolidan por un responsable, no mediante escrituras simultáneas.

### Camino crítico (11 changes — mínimo irreducible)

Para el **MVP operativo hasta C-14**, una ruta de mayor longitud por dependencias es:

```text
C-01 → C-02 → C-03 → C-04 → C-05 → C-09 → C-08 → C-10 → C-11 → C-13 → C-14
```

La rama `C-04 → C-06 → C-07 → C-08` tiene la misma longitud que `C-04 → C-05 → C-09 → C-08`; C-09 también requiere C-06. **La cadena dibujada no basta sola:** C-06/C-07 y C-12 son prerrequisitos paralelos obligatorios; el conjunto mínimo del MVP contiene C-01 a C-14. Se cuenta longitud en changes para mostrar precedencias, no un plazo calculado: las duraciones no están estimadas.

Si se prioriza todo el producto C-01 a C-20, las rutas más largas llegan a C-16 o C-20 y tienen **12 changes**: reemplazan el final `C-13 → C-14` por `C-13 → C-15 → C-16` o `C-13 → C-19 → C-20`. Clínica y cobros no bloquean el primer despliegue de la agenda; cada extensión requiere su propia verificación y actualización del paquete de despliegue antes de habilitarla.

### Plan óptimo con 3 agentes

Secuencia compatible con dependencias, sin prometer una optimización temporal no medida. Es una distribución técnica opcional; no significa tres integrantes de la entrega ni despacha agentes. Cada paso empieza cuando termina el anterior; `—` indica disponibilidad sin otro change asignado.

| Paso | Agente A (Backend Core) | Agente B (Backend Aux) | Agente C (Frontend) |
| --- | --- | --- | --- |
| 0 | C-01 cerrado el 2026-10-28 | — | — |
| 1 | C-02 | — | — |
| 2 | C-03 | — | — |
| 3 | C-04 | — | — |
| 4 | C-05 | C-06 | C-12 (apoyo operativo) |
| 5 | C-09 | C-07 | — |
| 6 | C-08 | — | — |
| 7 | C-10 | — | — |
| 8 | — | — | C-11 |
| 9 | C-13 | — | — |
| 10 | C-14 | C-17 | C-18 |
| 11 | C-15 | C-19 | — |
| 12 | C-16 | C-20 | — |

---

## FASE 1 — Porción entregada y cierre académico

### [C-01] `crear-turno-sin-solapamientos`

- **Estado**: `[x]` implementado y archivado el 2026-10-28: 18/18 tareas completas. Ver [archivo del change](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/), [spec principal](openspec/specs/alta-turnos/spec.md) y [evidencia de cierre](docs/evidencia/implementacion-turnos.md). Se ejecutaron nuevamente 53 pruebas y la demo antes del Archive.
- **Scope**:
  - Conservar bootstrap explícito de SQLite con `Paciente`, `Profesional`, `Box`, `Turno` ficticios; alta validada con `[inicio, fin)`, minuto exacto y UTC; conflictos independientes y `BEGIN IMMEDIATE` sobre un archivo local.
  - Conservar `POST /turnos` con `201`, errores `422/404/409/503/500`, `GET /health` de liveness y documentación OpenAPI; sin crear DB al importar.
  - Conservar trazabilidad de US-001 a US-004, tests de entradas/bordes/rollback/concurrencia y demo temporal. El mismo change quedó archivado con su contrato preservado; este cierre no implementa capacidades futuras.
- **Dependencias**: ninguna; infraestructura y modelos mínimos ya incluidos.
- **Governance**: MEDIO.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Entidades propuestas.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: turnos — contrato aplicado.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Épica 1: alta de turno sin solapamientos.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 5: solicitudes simultáneas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores.

## FASE 2 — Fundamento evolutivo, acceso y trazabilidad

> Todas las fichas C-02 a C-20 están pendientes de Propose y de autorización de implementación. Endpoints, entidades y pruebas enumerados son objetivos propuestos, no contratos HTTP vigentes. Los niveles ALTO/CRITICO exigen revisión humana antes de escribir código del dominio afectado.

### [C-02] `evolucionar-esquema-y-configuracion`

- **Estado**: `[ ]` planificado; sin change creado en OpenSpec.
- **Scope**:
  - Añadir registro de versión de esquema y migraciones incrementales sobre copia ficticia; conservar IDs y turnos de C-01, sin bootstrap destructivo ni inicialización automática al importar.
  - Separar configuración de entorno de datos y documentar restauración/reversión de una migración fallida. Evaluar si SQLite local sigue alcanzando; cualquier cambio de motor debe justificarse y probar la misma exclusión concurrente antes de adoptarlo.
  - Tests: agenda existente preservada, aplicación de migración una sola vez, fallo intermedio sin pérdida y rechazo de versión incompatible; mantener suite de regresión de C-01.
- **Dependencias**: C-01.
- **Governance**: ALTO — configuración y evolución de datos existentes.
- **Leer antes**:
  - [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) §Stack tecnológico.
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Alcance del modelo.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Preguntas abiertas priorizadas.

### [C-03] `autenticar-y-autorizar-personal`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Definir `Usuario`, rol y sesión para administración, recepción y profesional; aprobar matriz de permisos antes de elegir mecanismo de autenticación y gestionar contraseñas/sesiones con controles apropiados.
  - Proponer `POST /sesiones`, `DELETE /sesiones/actual`, `GET /sesiones/actual` y administración restringida de usuarios; proteger `POST /turnos` sin alterar su regla de solapamientos ni la semántica de errores de dominio.
  - Tests: acceso válido, credenciales inválidas, sesión expirada/revocada y acceso de un rol a recursos prohibidos (`401/403`); no confiar sólo en ocultar botones.
- **Dependencias**: C-02.
- **Governance**: CRITICO — autenticación y autorización.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §RBAC — matriz de permisos conceptual.
  - [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) §API (si aplica).
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.

### [C-04] `registrar-auditoria-de-operaciones`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Modelar `EventoAuditoria` con actor, acción, recurso, resultado e instante; definir qué operaciones deben quedar registradas y su relación transaccional con el cambio de negocio.
  - Proponer `GET /auditoria` restringido y paginado; registrar altas, cambios de acceso y posteriores mutaciones sin incluir contraseñas, tokens, cuerpos clínicos o datos sensibles en logs generales.
  - Tests: atribución correcta, registro de operaciones relevantes, acceso denegado a lectura no autorizada y política explícita ante fallo del almacenamiento de auditoría; sin borrado/edición ordinaria de eventos.
- **Dependencias**: C-02, C-03.
- **Governance**: CRITICO — audit trail.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Datos y responsabilidad.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.
  - [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) §Decisiones documentadas.

## FASE 3 — Catálogos y agenda operativa

### [C-05] `administrar-pacientes`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Evolucionar `Paciente` desde el identificador ficticio a una ficha de identificación/contacto mínimo, con campos y reglas de duplicados acordados; conservar las referencias de turnos anteriores.
  - Proponer `POST/GET /pacientes`, `GET/PATCH /pacientes/{id}` y baja lógica restringida; acceso por rol y auditoría. No incluir historia clínica en esta ficha.
  - Tests: alta/consulta/edición, dato inválido, duplicado definido por contrato, permisos y baja sin borrar turnos; pruebas exclusivamente ficticias.
- **Dependencias**: C-02, C-03, C-04.
- **Governance**: MEDIO — identidad y referencias de negocio; política de datos revisada antes de habilitar uso real.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Datos y responsabilidad.
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Entidades propuestas.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Excepciones globales y restricciones confirmadas.

### [C-06] `administrar-recursos-y-prestaciones`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Añadir administración de `Profesional`, `Box` y `Prestacion` con estado activo, duración propuesta y compatibilidades expresamente acordadas; no borrar referencias históricas ni imponer esas políticas a C-01 retroactivamente.
  - Proponer `POST/GET/PATCH /profesionales`, `/boxes` y `/prestaciones` con rutas por ID para edición; impedir nuevas asignaciones a recursos inactivos mediante reglas explícitas del nuevo contrato.
  - Tests: CRUD mínimo, duración inválida, referencia desconocida, baja con turnos existentes y control de permisos/auditoría; sin exigir un rol de usuario por cada profesional.
- **Dependencias**: C-02, C-03, C-04.
- **Governance**: MEDIO.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Actores del sistema.
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Límites que afectan el modelo.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: políticas de esta porción.

### [C-07] `configurar-horarios-y-bloqueos`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Añadir `HorarioAtencion`, `ExcepcionHorario` y `BloqueoAgenda` por profesional/box; acordar zona horaria del consultorio, descansos, cruce de día y qué ocurre si un bloqueo afecta turnos existentes.
  - Proponer `GET/PUT /horarios`, `POST /bloqueos` y `DELETE /bloqueos/{id}`; validar nuevas altas dentro de disponibilidad sin aceptar excepciones silenciosas ni cancelar turnos por crear un bloqueo.
  - Tests: franja disponible, fuera de horario, feriado/bloqueo, límites adyacentes y conflicto concurrente entre bloqueo y alta; preservar reglas de profesional/box de C-01.
- **Dependencias**: C-06.
- **Governance**: MEDIO.
- **Leer antes**:
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: políticas de esta porción.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 4: entrada inválida y bordes.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Preguntas abiertas priorizadas.

### [C-08] `consultar-agenda-y-disponibilidad`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Proponer `GET /turnos` por rango, profesional, box y estado, con límites de rango/paginación; `GET /disponibilidad` devuelve opciones compatibles con horarios, bloqueos y estados que ocupan recursos.
  - Reutilizar semántica temporal y reglas de exclusión en las consultas; filtrar por permisos de recepción/profesional y exponer sólo los datos necesarios. Una opción libre es orientativa: el alta debe revalidarla dentro de su transacción.
  - Tests: agenda vacía, límites de rango, filtros combinados, recurso desconocido, cancelado que libera recursos y dos solicitantes que ven la misma opción libre antes de reservar.
- **Dependencias**: C-05, C-07, C-09.
- **Governance**: MEDIO — consulta con reglas de disponibilidad y acceso.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Entidades propuestas.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: turnos — contrato aplicado.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 1: alta válida.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 5: solicitudes simultáneas.

### [C-09] `gestionar-estados-y-cancelaciones`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Añadir estados de turno y transiciones revisadas: reservado, confirmado, atendido, ausente y cancelado como propuesta inicial; definir cuáles ocupan recursos y cómo se conserva el historial.
  - Proponer `POST /turnos/{id}/confirmacion` y `POST /turnos/{id}/cancelacion`; modificar consultas de exclusión para liberar sólo ocupaciones canceladas. Migrar filas existentes a un estado ocupante, sin alterar su horario o identidad.
  - Tests: transición válida/inválida, cancelación repetida con resultado explícito, permisos, liberación de recursos y competencia cancelación/alta; sin borrado físico de evidencia.
- **Dependencias**: C-04, C-05, C-06.
- **Governance**: MEDIO — máquina de estados y ocupación.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Límites que afectan el modelo.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: políticas de esta porción.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.

### [C-10] `reprogramar-turnos-atomicamente`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Proponer `POST /turnos/{id}/reprogramacion` para cambiar intervalo y recursos con control de versión/competencia acordado; revalidar referencias, estado, disponibilidad y exclusión dentro de la misma operación.
  - Conservar el turno original si falla la nueva asignación y auditar el cambio confirmado. Decidir expresamente exclusión simultánea del paciente: C-01 la permite con recursos distintos; cualquier nueva restricción necesita escenarios y migración de contrato propios.
  - Tests: nueva franja válida, conflicto de cada recurso, falla previa al commit sin pérdida del original y dos reprogramaciones competidoras; no implementar como cancelar y luego crear en transacciones separadas.
- **Dependencias**: C-08, C-09.
- **Governance**: MEDIO.
- **Leer antes**:
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: turnos — contrato aplicado.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 5: solicitudes simultáneas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores.

## FASE 4 — Interfaz de recepción y operación recuperable

### [C-11] `operar-agenda-desde-recepcion`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Elegir tecnología de frontend compatible con la API y construir login, vista diaria/semanal de agenda y selección de paciente/profesional/box/prestación; integrar formularios mínimos de catálogos y horarios ya expuestos, sin duplicar reglas en la UI.
  - Consumir alta, consulta, confirmación, cancelación y reprogramación; mostrar estado pendiente hasta respuesta, conflictos por recurso, validaciones y actualización de disponibilidad. Incluir navegación por teclado y estados de carga/vacío/error.
  - Tests E2E con backend y datos ficticios: alta válida, conflicto que llega desde API, cancelación y reprogramación; probar permisos de servidor incluso manipulando la vista y evitar afirmar éxito por actualización optimista.
- **Dependencias**: C-08, C-10.
- **Governance**: MEDIO — flujo operativo; autenticación reutilizada, no rediseñada.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §RBAC — matriz de permisos conceptual.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 1: alta válida.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Responsabilidades y directorios.

### [C-12] `respaldar-y-restaurar-agenda`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Preparar comandos restringidos de backup coherente del almacenamiento y restauración sobre un destino nuevo, con manifiesto de versión/integridad; definir retención, protección y recuperación sin sobrescribir la agenda activa.
  - Documentar recuperación de una copia, validación de esquema y prueba de alta tras restaurar; adaptar el mecanismo al motor realmente elegido en C-02, incluyendo adjuntos si se incorporan después.
  - Tests: backup durante actividad controlada, archivo corrupto/incompatible, destino existente preservado y restauración ejecutada con comprobación de filas; conservar copia no equivale a demostrar recuperación.
- **Dependencias**: C-02, C-03, C-04.
- **Governance**: ALTO — backup y restauración.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Seed data inicial propuesto.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Cinco grupos de evidencia pendiente del relevamiento.

### [C-13] `endurecer-seguridad-y-observabilidad`

- **Estado**: `[ ]` planificado.
- **Scope**:
  - Revisar la superficie API/UI: autorización por recurso, sesiones, secretos, límites de solicitudes y rangos, protección de la interfaz según el mecanismo de sesión y exposición de documentación por entorno; cerrar fallos con contratos y pruebas revisados.
  - Añadir logs operativos sin información sensible, identificador de correlación, errores públicos estables y readiness separada de `GET /health`; definir alertas mínimas por fallo de DB/backup sin afirmar cumplimiento normativo.
  - Tests: accesos indebidos, abuso de límites, errores sin secretos/rutas, readiness ante DB caída y regresión del flujo de recepción. Revisar permisos, recuperación y política de datos antes de autorizar información real.
- **Dependencias**: C-11, C-12.
- **Governance**: CRITICO — seguridad y acceso a datos.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Rutas públicas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Cinco grupos de evidencia pendiente del relevamiento.

### [C-14] `desplegar-mvp-en-entorno-controlado`

- **Estado**: `[ ]` planificado; cierre del MVP operativo futuro.
- **Scope**:
  - Elegir y documentar un entorno de despliegue de una sola clínica; preparar paquete reproducible, configuración por entorno y pasos de migración con respaldo, rollback y control de acceso/red. No habilitar despliegue público por generar este roadmap.
  - Agregar verificación automatizada de instalación y smoke del recorrido de recepción en entorno de prueba con datos ficticios; incluir guía de arranque/parada y recuperación referenciada a C-12.
  - Criterios de salida: suite/E2E completos, readiness real, concurrencia validada en el almacenamiento y modo de ejecución elegidos, restauración comprobada y revisión humana de habilitación. Si se cambia el modelo de ejecución, volver a probar sus garantías.
- **Dependencias**: C-13.
- **Governance**: ALTO — configuración operativa y despliegue.
- **Leer antes**:
  - [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) §Criterios de éxito propuestos.
  - [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) §Infraestructura y confianza.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Validación ejecutada.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Próxima decisión de implementación.

## FASE 5 — Evolución clínica del producto

> Extensión posterior a la agenda, con datos ficticios durante desarrollo. Antes de admitir información clínica real se necesita revisar los contratos de acceso, confidencialidad, trazabilidad, conservación y recuperación; el TP no acredita esa habilitación.

### [C-15] `registrar-historia-clinica`

- **Estado**: `[ ]` planificado; extensión a priorizar.
- **Scope**:
  - Proponer `HistoriaClinica` y `EvolucionClinica` vinculadas al paciente, profesional y atención; acordar campos mínimos y permisos profesionales antes de escribir código o incorporar información real.
  - Proponer `GET /pacientes/{id}/historia` y `POST /pacientes/{id}/evoluciones`, con correcciones trazables en lugar de sobrescribir silenciosamente una evolución; acceso clínico separado de recepción y auditoría de consultas/cambios.
  - Tests ficticios: acceso autorizado/denegado, referencia inexistente, corrección que conserva el original y ausencia de contenido clínico en logs generales; extender prueba de backup/restauración al nuevo esquema.
- **Dependencias**: C-05, C-06, C-13.
- **Governance**: CRITICO — datos clínicos y trazabilidad.
- **Leer antes**:
  - [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) §Fuera de alcance.
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Datos y responsabilidad.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.

### [C-16] `gestionar-odontograma-y-plan`

- **Estado**: `[ ]` planificado; extensión clínica.
- **Scope**:
  - Definir `HallazgoOdontograma`, `PlanTratamiento` y sus prestaciones/etapas, con nomenclatura y transiciones revisadas por quien define el dominio; no inferir diagnósticos ni automatizar decisiones clínicas.
  - Proponer consulta/registro versionado de odontograma y plan por paciente, con detalle de estado, profesional y fecha; una nueva versión no elimina observaciones previas. Presentar vista clínica mínima sobre la base UI existente.
  - Tests ficticios: pieza/superficie inválida, cambio permitido/prohibido, historial preservado, acceso restringido y restauración de la versión vigente y su historial.
- **Dependencias**: C-15.
- **Governance**: CRITICO — datos y reglas clínicas.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Límites que afectan el modelo.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.

## FASE 6 — Comunicación, autoservicio y administración

> Ramas independientes de la extensión clínica; no bloquean C-14. Se ejecutan con dobles/simuladores hasta elegir y autorizar cualquier proveedor externo. Cada change incluye una actualización controlada del despliegue cuando se habilite, sin considerar desplegadas sus funciones por cerrar C-14.

### [C-17] `programar-recordatorios`

- **Estado**: `[ ]` planificado; canal real pendiente de decisión.
- **Scope**:
  - Modelar preferencia de contacto y `Recordatorio`/outbox ligada al turno; definir anticipación, zona horaria, consentimiento y contenido mínimo sin datos clínicos. Preparar adaptador simulado antes de evaluar email o WhatsApp.
  - Programar sólo turnos elegibles; invalidar recordatorios anteriores al cancelar/reprogramar. Persistir estado/intentos y clave de deduplicación para evitar envíos repetidos; fallar el aviso no debe duplicar ni borrar el turno.
  - Tests: envío simulado, rechazo/fallo de canal, reintento acotado, petición repetida, cancelación y cambio horario; no afirmar entrega por aceptar un trabajo en cola.
- **Dependencias**: C-08, C-09, C-10, C-13.
- **Governance**: ALTO — notificaciones y datos de contacto.
- **Leer antes**:
  - [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) §Integraciones externas.
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Datos y responsabilidad.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Cinco grupos de evidencia pendiente del relevamiento.

### [C-18] `habilitar-reserva-del-paciente`

- **Estado**: `[ ]` planificado; autoservicio posterior al flujo interno.
- **Scope**:
  - Definir identidad/vinculación del paciente y permisos propios, evitando publicar el catálogo o la agenda identificada del consultorio; ofrecer sólo opciones de disponibilidad y datos mínimos.
  - Proponer rutas y vista de autoservicio para reservar y consultar/cancelar/reprogramar únicamente turnos propios, con política de anticipación acordada, límites de solicitudes y deduplicación explícita; reutilizar exclusión transaccional del backend.
  - Tests E2E ficticios: reserva válida, dos pacientes compitiendo por el mismo horario, intento de acceder a turno ajeno, cancelación fuera de política y repetición tras respuesta interrumpida; no confiar en IDs difíciles de adivinar como autorización.
- **Dependencias**: C-08, C-10, C-13.
- **Governance**: CRITICO — identidad y autorización del paciente.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §RBAC — matriz de permisos conceptual.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 5: solicitudes simultáneas.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.

### [C-19] `registrar-cobros-y-movimientos`

- **Estado**: `[ ]` planificado; administración no fiscal, sin proveedor de pagos real.
- **Scope**:
  - Proponer `Cargo`, `Cobro` y `Reversion` vinculados al paciente/prestación, con moneda y precisión acordadas; representar importes exactamente y rechazar valores incorrectos sin redondear o compensar silenciosamente.
  - Proponer `POST /cobros`, consulta de saldo/movimientos y reversión autorizada con motivo; conservar historial y probar idempotencia de comandos monetarios. Sin facturas fiscales, ARCA, conciliación bancaria ni pasarela real en este change.
  - Tests ficticios: cobro válido, monto inválido/excesivo, repetición, reversión parcial/total según contrato, permisos y auditoría; un fallo intermedio no debe alterar el saldo ni registrar éxito ficticio.
- **Dependencias**: C-05, C-06, C-09, C-13.
- **Governance**: CRITICO — dinero y audit trail.
- **Leer antes**:
  - [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) §Fuera de alcance.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) §Decisiones documentadas.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Cinco grupos de evidencia pendiente del relevamiento.

### [C-20] `consultar-reportes-operativos`

- **Estado**: `[ ]` planificado; cierre de la primera evolución administrativa.
- **Scope**:
  - Proponer `GET /reportes/agenda` y `GET /reportes/cobros` con rangos acotados, permisos y exportación restringida; mostrar ocupación, cancelaciones/ausencias y movimientos monetarios según definiciones acordadas, sin confundir turnos reservados con atenciones realizadas.
  - Añadir panel mínimo y exportación reproducible sobre consultas del backend, sin incluir historia clínica por defecto ni formular recomendaciones automáticas; evitar duplicar fórmulas en UI y API.
  - Tests: rango vacío, límites horarios/zona, estado cancelado, reversos y totales exactos, permisos de exportación y consistencia entre panel/descarga; los indicadores son datos del sistema, no mejoras de productividad demostradas.
- **Dependencias**: C-08, C-09, C-19.
- **Governance**: MEDIO — consultas derivadas con permisos; cálculo monetario reutiliza el contrato crítico de C-19.
- **Leer antes**:
  - [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) §Criterios de éxito propuestos.
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Datos y responsabilidad.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.
