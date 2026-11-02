# CHANGES — Secuencia de Implementación

> Índice canónico del proyecto **TP-ODONTOLOGIA**, actualizado el 2026-11-02.
> **Plan del producto completo; C-01-C-13 y C-15 están implementados, validados y archivados localmente. C-14 es opcional y queda fuera de la entrega; C-16-C-20 siguen planificados, con decisiones materiales según R-10.**
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Elegir el change por objetivo y dependencias. Consultar `openspec list --json` y, si ya existe, `openspec status --change "<nombre>" --json`; el CLI determina su estado real.
2. Leer los documentos de «Leer antes». Para cada change futuro, ampliar la KB y resolver en OpenSpec los contratos aún no definidos antes de implementar; las decisiones materiales de governance se aprueban según R-10. Una exclusión de C-01 identifica una decisión a revisar, no un requisito ya aprobado.
3. Para cada avance del roadmap global autorizado, ejecutar `/opsx:propose <nombre-kebab-case>` y revisar propuesta, diseño, escenarios y tareas. Los IDs C-NN son índices del roadmap, no prefijos obligatorios del nombre CLI. C-01 ya existe: conservarlo.
4. Implementar únicamente el alcance autorizado, verificar con evidencia real y usar `/opsx:archive <nombre>` al cerrar. Diseñar y probar cada ampliación sin cambiar silenciosamente el comportamiento anterior.
5. Marcar `[x]` sólo después del archivado confirmado y la sincronización de specs. Un roadmap, un test verde o una propuesta no acreditan revisión humana, implementación futura ni aceptación docente.

### Alcance del producto y de esta entrega

La aclaración del usuario del 2026-10-28 corrige el índice anterior: **hacer sólo C-01 ahora no significa planificar sólo C-01**. El producto futuro es un sistema para un consultorio odontológico pequeño, con recepción, profesionales y boxes: agenda operativa, catálogos, acceso seguro, interfaz de recepción, recuperación de datos y, después, módulos clínicos, comunicación con pacientes y administración.

- **Entrega académica archivada:** C-01 `crear-turno-sin-solapamientos`, con 18/18 tareas completas y Archive confirmado el 2026-10-28; la spec principal es [alta-turnos](openspec/specs/alta-turnos/spec.md). No se cambia su nombre, su spec, su código ni su contrato. C-02, C-03 y C-04 también están implementados, validados y archivados localmente.
- **MVP académico demostrable:** C-03 a C-13 completan una agenda de recepción administrable, con cambios revisables, pruebas y demostración local. C-02 ya aporta el backend PostgreSQL optativo y está archivado; la seguridad, auditoría y recuperación usan datos ficticios. No se requiere desplegar el sistema ni levantar contenedores.
- **Evolución del producto:** C-15 a C-20 agregan clínica, odontograma/plan de tratamiento, recordatorios, reserva del paciente, cobros y reportes. C-15 quedó implementado y archivado; las capacidades C-16 a C-20 siguen propuestas, con contratos propios.
- **Opciones no comprometidas:** multisede/SaaS multitenant, IA, obras sociales y facturación electrónica ARCA no se vuelven obligatorias por aparecer en productos comparados. Si se eligen, se agregarán changes posteriores con investigación y aprobación específicas. C-19 no incluye emisión fiscal ni conexión con pagos reales.

La KB y las instrucciones existentes documentan principalmente la porción académica C-01. Sus exclusiones siguen vigentes para esa implementación; las capacidades futuras del roadmap no amplían retroactivamente las US-001 a US-004. C-02 concreta la migración a PostgreSQL conservando la fuente SQLite; C-03/C-04 autenticación, permisos y auditoría; C-05 la ficha mínima; C-06 catálogos; C-07 disponibilidad; C-08 consultas de agenda; C-09 estados; y C-10 reprogramación atómica. C-01 standalone conserva compatibilidad. Se mantienen datos ficticios y ninguna integración externa real.

**Antecedente de stack de la cátedra (2026-10-29):** el profesor indicó Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis, Docker/Docker Compose, React, TypeScript y Vite ([DD-09](knowledge-base/09_decisiones_y_supuestos.md)). El alcance de esta entrega, aclarado por el usuario el 2026-11-02, no requiere Docker ni Redis: se construye y presenta mediante los changes, pruebas y demo local. Redis puede mencionarse como alternativa futura, sin dependencia operativa; el despliegue queda fuera de la entrega. La historia de la consigna se conserva como antecedente, no como trabajo completado.

**Base técnica de C-01:** Python/FastAPI y SQLite local, movidos sin cambios a `backend/`. Bootstrap y modelos mínimos ya pertenecen a C-01; no se renumera como `foundation-setup`. Hosting y proveedores siguen siendo decisiones futuras justificadas. El contrato actual se consulta en [design.md](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md), [spec.md](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/specs/alta-turnos/spec.md) y [api.py](backend/odontologia/api.py).

### Decisiones que habilita la planificación

| Decisión / capacidad | Change que la resuelve | Estado o condición |
| --- | --- | --- |
| Versionado de esquema y migración a PostgreSQL con SQLAlchemy (stack de la cátedra) | C-02 | Implementado, validado con PostgreSQL aislado y archivado; copia unidireccional, fuente SQLite preservada. |
| Identidades, permisos, sesiones y auditoría | C-03/C-04 | C-03 y C-04 implementados, validados y archivados. |
| Datos mínimos, prestaciones y disponibilidad | C-05/C-06/C-07 | C-05–C-07 implementados y archivados localmente; C-09 extiende el esquema a SQLite v6/Alembic 0007 |
| Estados, cancelación y reprogramación | C-09/C-10 | C-09 y C-10 implementados, validados y archivados; versión optimista, operación atómica y sin exclusión por paciente adicional |
| UI, recuperación y seguridad demostrables | C-11/C-12/C-13 | Interfaz en React + TypeScript + Vite, pruebas locales, changes y evidencia; sin despliegue requerido |
| Datos clínicos, comunicaciones y dinero | C-15 a C-20 | Revisión de permisos, privacidad, reglas clínicas/monetarias y proveedor cuando corresponda; sólo simulación en este ejercicio |

---

## Árbol de dependencias

```text
C-01 crear-turno-sin-solapamientos (implementado y archivado)
└── C-02 evolucionar-esquema-y-configuracion (implementado y archivado)
    └── C-03 autenticar-y-autorizar-personal (implementado y archivado)
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
    ├── C-15 registrar-historia-clinica (también C-05, C-06)
    │   └── C-16 gestionar-odontograma-y-plan
    ├── C-17 programar-recordatorios (también C-08, C-09, C-10)
    ├── C-18 habilitar-reserva-del-paciente (también C-08, C-10)
    └── C-19 registrar-cobros-y-movimientos (también C-05, C-06, C-09)
        └── C-20 consultar-reportes-operativos (también C-08, C-09)
```

Los números son identificadores estables agrupados por capacidad, no un orden de ejecución por sí solos: C-09 precede a C-08 porque una consulta operativa debe conocer qué estados ocupan recursos. C-01 está archivado desde el 2026-10-28; C-02 a C-10 también están archivados.

### Paralelismo por fase

Los GATES expresan dependencias del plan futuro. C-01–C-07 están archivados localmente. El símbolo `✓` significa «una vez verificado y cerrado». No imponen fases rígidas a OPSX.

```text
GATE 0: C-01 ✓ → C-02 ✓ → C-03 ✓ → C-04 ✓

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
  → C-15 clínica                     [Agente A]
  → C-17 recordatorios               [Agente B]
  → C-18 reserva del paciente        [Agente C]
  → C-19 cobros                      [Agente B]

GATE 5: C-15 y C-19 ✓
  → C-16 odontograma/plan            [Agente A — requiere C-15]
  → C-20 reportes                    [Agente B — requiere C-19]
```

En GATE 5 cada rama puede empezar cuando se complete su propio prerrequisito; no debe esperar a la otra. En GATE 4 las cinco ramas son independientes entre sí, pero sólo se asignan tres a la vez. Las demás dependencias ya quedan satisfechas por los ancestros de C-13. Acordar interfaces y propiedad de archivos antes de ejecutar en paralelo; rutas, esquema y contratos compartidos se consolidan por un responsable, no mediante escrituras simultáneas.

### Camino crítico (10 changes — mínimo irreducible)

Para el **MVP académico demostrable hasta C-13**, una ruta de mayor longitud por dependencias es:

```text
C-01 → C-02 → C-03 → C-04 → C-05 → C-09 → C-08 → C-10 → C-11 → C-13
```

La rama `C-04 → C-06 → C-07 → C-08` tiene la misma longitud que `C-04 → C-05 → C-09 → C-08`; C-09 también requiere C-06. **La cadena dibujada no basta sola:** C-06/C-07 y C-12 son prerrequisitos paralelos obligatorios; el conjunto mínimo del MVP contiene C-01 a C-13. C-14 es opcional y queda fuera de esta entrega. Se cuenta longitud en changes para mostrar precedencias, no un plazo calculado: las duraciones no están estimadas.

Si se prioriza todo el producto C-01 a C-20, las rutas más largas llegan a C-16 o C-20 y tienen **12 changes**: `C-01 → … → C-13 → C-15 → C-16` o `C-01 → … → C-13 → C-19 → C-20`. Clínica y cobros siguen siendo extensiones independientes del MVP académico; no requieren un paquete de despliegue.

### Plan óptimo con 3 agentes

Secuencia compatible con dependencias, sin prometer una optimización temporal no medida. Es una distribución técnica opcional; no significa tres integrantes de la entrega ni despacha agentes. Cada paso empieza cuando termina el anterior; `—` indica disponibilidad sin otro change asignado.

| Paso | Agente A (Backend Core) | Agente B (Backend Aux) | Agente C (Frontend) |
| --- | --- | --- | --- |
| 0 | C-01 cerrado el 2026-10-28 | — | — |
| 1 | C-02 archivado; C-03 archivado | — | — |
| 2 | C-04 archivado | — | — |
| 3 | C-05 archivado | C-06 | C-12 (apoyo operativo) |
| 4 | C-09 | C-07 | — |
| 5 | C-08 | — | — |
| 6 | C-10 | — | — |
| 7 | — | — | C-11 |
| 8 | C-13 | — | — |
| 9 | C-15 | C-17 | C-18 |
| 10 | C-16 | C-19 | C-20 |

---

## FASE 1 — Porción entregada y cierre académico

### [C-01] `crear-turno-sin-solapamientos`

- **Estado**: `[x]` implementado y archivado el 2026-10-28: 18/18 tareas completas. Ver [archivo del change](openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/), [spec principal](openspec/specs/alta-turnos/spec.md) y [evidencia de cierre](docs/evidencia/implementacion-turnos.md). Se ejecutaron nuevamente 53 pruebas y la demo antes del Archive. Desde el 2026-10-29 su código vive en `backend/` (movido sin cambios por la estructura pedida por la cátedra).
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

> C-01–C-10 están archivados localmente y validados. C-11 a C-20 siguen planificados con desarrollo global autorizado. Las decisiones materiales de governance CRÍTICO/ALTO requieren aprobación específica antes del código.

### [C-02] `evolucionar-esquema-y-configuracion`

- **Estado**: implementado, validado localmente y archivado. La evidencia de C-02 está en [implementacion-turnos.md#c-02](docs/evidencia/implementacion-turnos.md#c-02).
- **Scope**:
  - Añadir registro de versión de esquema y migraciones incrementales sobre copia ficticia; conservar IDs y turnos de C-01, sin bootstrap destructivo ni inicialización automática al importar.
  - Separar configuración de entorno de datos y documentar recuperación ante una migración fallida. Importar a PostgreSQL con SQLAlchemy en un entorno local aislado, sin borrar la fuente; la copia es unidireccional y no sincroniza escrituras posteriores de PostgreSQL hacia SQLite.
  - Tests: agenda existente preservada, aplicación de migración una sola vez, fallo intermedio sin pérdida y rechazo de versión incompatible; mantener suite de regresión de C-01.
- **Dependencias**: C-01 (archivado).
- **Governance**: ALTO — configuración y evolución de datos existentes.
- **Leer antes**:
  - [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) §Stack tecnológico.
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Alcance del modelo.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Preguntas abiertas priorizadas.

### [C-03] `autenticar-y-autorizar-personal`

- **Estado**: implementación verificada y change archivado.
- **Scope entregado**: JWT HS256 respaldado por sesiones revocables; derivación scrypt; migraciones explícitas SQLite y Alembic PostgreSQL; bootstrap interactivo sin credenciales por defecto; Administrador gestiona cuentas y operaciones disponibles, Recepción crea turnos, Profesional no accede hasta C-08. `POST /turnos` está protegido sin cambios en reglas ni errores del dominio C-01.
- **Evidencia**: suites SQLite (111) y PostgreSQL temporal aislada (121) completas; `pip check`, `openspec validate --all --strict` y `git diff --check` ejecutados. Ver [registro C-03](docs/evidencia/implementacion-turnos.md#implementación-y-evidencia-c-03--2026-11-01); C-03 está archivado.
- **Dependencias**: C-02.
- **Governance**: CRITICO — autenticación y autorización.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §RBAC — matriz de permisos conceptual.
  - [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) §API (si aplica).
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.

### [C-04] `registrar-auditoria-de-operaciones`

- **Estado**: implementado, validado localmente y archivado el 2026-11-02. Ver [change archivado](openspec/changes/archive/2026-11-02-registrar-auditoria-de-operaciones/) y [evidencia C-04](docs/evidencia/implementacion-turnos.md#c-04--registro-de-auditoría-de-operaciones-2026-11-02).
- **Scope**:
  - Añadir `eventos_auditoria` append-only en SQLite y PostgreSQL, con actor, acción, recurso, resultado e instante UTC y sin datos personales, clínicos, secretos ni payloads.
  - `GET /auditoria` queda restringido a Administrador, con paginación estable y acotada. Registrar turnos confirmados, bootstrap/alta/cambio de cuentas, login/logout y rechazo genérico de login.
  - Mutación y evento comparten transacción; si falla el evento se revierte el cambio. No hay edición, borrado ordinario ni purga automática. Pruebas locales cubren SQLite y PostgreSQL aislado.
- **Dependencias**: C-02, C-03.
- **Governance**: CRITICO — audit trail.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Datos y responsabilidad.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.
  - [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) §Decisiones documentadas.

## FASE 3 — Catálogos y agenda operativa

### [C-05] `administrar-pacientes`

- **Estado**: implementado, validado localmente y archivado el 2026-11-02. Ver [change archivado](openspec/changes/archive/2026-11-02-administrar-pacientes/) y [evidencia C-05](docs/evidencia/implementacion-turnos.md#c-05--fichas-mínimas-de-pacientes-2026-11-02).
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

- **Estado**: implementado, validado localmente y archivado el 2026-11-02. Ver [change archivado](openspec/changes/archive/2026-11-02-administrar-recursos-y-prestaciones/) y [evidencia C-06](docs/evidencia/implementacion-catalogos.md).
- **Scope**:
  - Administrar catálogos ficticios de `Profesional`, `Box` y `Prestacion`: Administrador y Recepción crean, consultan y editan datos descriptivos; sólo Administrador cambia el estado activo. No se borran referencias históricas.
  - Exponer listado paginado, consulta por ID, alta y edición. La duración de prestación es un entero positivo en minutos. No se agregan relaciones de compatibilidad ni `prestacion_id` al contrato C-01; C-01 tampoco calcula el turno desde la duración.
  - Bloquear nuevas altas de turnos para paciente, profesional o box inactivo, preservando turnos existentes. Registrar metadatos de auditoría permitidos en la misma transacción; si falla el evento, revertir la mutación.
  - Persistencia: SQLite v4 y Alembic 0005, conservando IDs seed, turnos e importación previa.
- **Dependencias**: C-02, C-03, C-04.
- **Governance**: MEDIO.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Actores del sistema.
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Límites que afectan el modelo.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: políticas de esta porción.

### [C-07] `configurar-horarios-y-bloqueos`

- **Estado**: Implementado, validado y archivado localmente; commit `fd21a9a` (sin push).
- **Scope**:
  - SQLite v5 y Alembic `20261102_0006_agenda_availability`; `America/Argentina/Mendoza`, con `tzdata` fijado para Windows.
  - `GET/PUT /horarios`, gestión de excepciones fechadas y `GET/POST/DELETE /bloqueos`, para Administrador y Recepción. Excepción reemplaza la semana del recurso/día; lista vacía cierra; bloqueo pertenece a exactamente un profesional o box.
  - Nuevas reservas deben caber en un tramo del profesional y del box, sin cruce de medianoche ni solapamiento con bloqueos. Cambios incompatibles con turnos ocupantes (`reservado`/`confirmado`), incluso pasados, devuelven 409; los terminales se conservan pero no bloquean la reconfiguración.
  - La API valida versión, tablas C-07 y la columna `turnos.estado`, y falla cerrada; el servicio standalone C-01 en SQLite no migrado preserva su contrato. Auditoría metadata-only y atómica.
  - Evidencia: [implementacion-disponibilidad.md](docs/evidencia/implementacion-disponibilidad.md).
- **Dependencias**: C-05, C-06.
- **Governance**: MEDIO.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §límites que afectan el modelo.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: horarios y disponibilidad — C-07.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 7: reserva con disponibilidad C-07.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Preguntas abiertas priorizadas.

### [C-08] `consultar-agenda-y-disponibilidad`

- **Estado**: implementado, validado y archivado localmente el 2026-11-02. Ver [change archivado](openspec/changes/archive/2026-11-02-consultar-agenda-y-disponibilidad/) y [evidencia](docs/evidencia/implementacion-consultas-agenda.md). Sin push.
- **Scope**:
  - `GET /turnos`: rangos offset-aware semiabiertos de hasta 31 días, filtros por profesional/box/estado, paginación estable; Admin/Recepción ven datos operativos sin teléfono y Profesional sólo su propio horario y nombre de paciente.
  - `GET /disponibilidad`: candidatos cada 15 minutos en `America/Argentina/Mendoza`; intersecta horario/excepción de ambos recursos, filtra inactivos, bloqueos y estados ocupantes C-09. Las opciones no reservan y `POST /turnos` revalida en su transacción.
  - Cuenta Profesional con FK única al recurso, asignable sólo por Administrador; vínculo incorporado a JWT e identidad validada; cambio de rol/vínculo revoca sesiones. C-01 standalone conserva su compatibilidad.
  - Migraciones: SQLite v7 y PostgreSQL Alembic 0008, preservando filas existentes. Suites completas: SQLite 244 OK y PostgreSQL aislado 275/275; `pip check`, OpenSpec strict y `git diff --check` limpios. Ver [evidencia C-08](docs/evidencia/implementacion-consultas-agenda.md).
- **Dependencias**: C-05, C-07, C-09.
- **Governance**: MEDIO — consulta con reglas de disponibilidad y acceso.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Entidades propuestas.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: turnos — contrato aplicado.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 1: alta válida.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 5: solicitudes simultáneas.

### [C-09] `gestionar-estados-y-cancelaciones`

- **Estado**: Implementado, validado y archivado localmente; commit local separado de C-07.
- **Scope aplicado**:
  - Estado restringido: `reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`; transiciones `reservado`→`confirmado`/`cancelado` y `confirmado`→`atendido`/`ausente`/`cancelado`; los estados terminales permanecen en historial.
  - Sólo estados `reservado` y `confirmado` ocupan profesional/box. Alta nueva responde `reservado`; migración conserva ID, referencias e intervalo de turnos existentes.
  - Endpoints protegidos `POST /turnos/{id}/confirmacion`, `/cancelacion`, `/atencion`, `/ausencia` para Administrador y Recepción; respuesta de transición `{id, estado}`. Cancelación repetida responde igual sin otra mutación auditada.
  - Acción de auditoría `turno.estado_actualizado`, metadata-only y atómica; SQLite v6 reconstruye tabla append-only preservando eventos, PostgreSQL usa Alembic `20261102_0007_turn_status`. Transiciones comparten lock de altas en ambos motores.
  - Compatibilidad del servicio C-01 standalone no migrado; Profesional continúa sin acceso a la API; no hay reprogramación ni borrado físico.
- **Dependencias**: C-04, C-05, C-06.
- **Governance**: MEDIO — máquina de estados y ocupación.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Límites que afectan el modelo.
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: políticas de esta porción.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.

### [C-10] `reprogramar-turnos-atomicamente`

- **Estado**: implementado, validado y archivado localmente el 2026-11-02. Ver [change archivado](openspec/changes/archive/2026-11-02-reprogramar-turnos-atomicamente/) y [evidencia](docs/evidencia/implementacion-reprogramacion.md). Sin push.
- **Scope**:
  - `POST /turnos/{id}/reprogramacion` para Administrador/Recepción; versión esperada obligatoria, intervalos offset-aware de precisión al minuto, conserva paciente/duración/estado y cambia intervalo/profesional/box.
  - Sólo turnos `reservado` o `confirmado`; revalida recursos, horarios/excepciones, bloqueos y ocupación en una operación serializada. Versión obsoleta, conflicto, terminal o fallo de auditoría conservan fila y versión sin evento de mutación. Incluye el fin exacto a medianoche cuando el tramo termina a `24:00`; rechaza continuar después.
  - Reprogramación y auditoría `turno.reprogramado` se confirman en la misma transacción; solicitudes concurrentes con versión igual producen una confirmación y un 409. C-01 standalone conserva su contrato histórico.
  - C-01 permite turnos simultáneos del paciente cuando profesional y box son distintos; C-10 preserva esa regla. La prestación no se guarda ni se asocia durante la reprogramación.
  - Suites completas tras el ajuste de medianoche: SQLite 271/271 y PostgreSQL aislado 312/312; `pip check`, OpenSpec strict y `git diff --check` limpios. La evidencia registra una desviación TDD para pruebas de éxito/concurrencia por implementación adelantada durante 2.1.
- **Dependencias**: C-08, C-09.
- **Governance**: MEDIO.
- **Leer antes**:
  - [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) §Dominio: turnos — contrato aplicado.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 5: solicitudes simultáneas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores.

## FASE 4 — Interfaz de recepción y operación recuperable

### [C-11] `operar-agenda-desde-recepcion`

- **Estado**: implementado, validado y archivado localmente el 2026-11-02. Ver [change archivado](openspec/changes/archive/2026-11-02-operar-agenda-desde-recepcion/) y [evidencia C-11](docs/evidencia/implementacion-recepcion.md). Sin push.
- **Scope**:
  - Interfaz React + TypeScript + Vite con inicio/cierre de sesión en memoria; Admin y Recepción gestionan agenda, turnos, fichas de pacientes, catálogos y disponibilidad; Profesional sólo consulta su propia agenda.
  - Alta, consulta diaria/semanal, confirmación, cancelación, atención, ausencia y reprogramación usan contratos existentes y sólo informan éxito tras respuesta del backend. Los errores de validación/409 se muestran sin ocultar la configuración vigente.
  - No modifica el backend ni añade `prestacion_id` al turno C-01. Vitest, Playwright con SQLite y datos ficticios aislados, accesibilidad de teclado y errores de sesión; evidencia y comandos en `docs/evidencia/implementacion-recepcion.md` y `frontend/README.md`.
- **Dependencias**: C-08, C-10.
- **Governance**: MEDIO — flujo operativo; autenticación reutilizada, no rediseñada.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §RBAC — matriz de permisos conceptual.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) §Flujo 1: alta válida.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Responsabilidades y directorios.

### [C-12] `respaldar-y-restaurar-agenda`

- **Estado**: Implementado, validado y archivado localmente el 2026-11-02; 20/20 tareas completadas. Ver `openspec/changes/archive/2026-11-02-respaldar-y-restaurar-agenda/`.
- **Scope**:
  - Implementar respaldos completos, manuales y locales para SQLite y PostgreSQL optativo, con manifiesto UTC, versiones, `table_counts` del mismo snapshot y SHA-256; el hash detecta alteración accidental, pero no autentica el manifiesto.
  - Restaurar únicamente en un destino explícito nuevo, validando esquema, integridad, claves foráneas y recuentos; no sobrescribir destinos, purgar copias ni incluir secretos `.env`/JWT o enviar datos a servicios externos.
  - Verificar actividad concurrente, copia corrupta/incompatible, destino existente preservado, recuperación con datos ficticios y una escritura posterior; distinguir evidencia técnica de prueba humana o de producción.
  - La suite backend final pasa (361 tests, 4 omitidos); `pip check` está limpio; la integración PostgreSQL aislada pasó (41/41); OpenSpec strict pasó (15/15). Los adapters usan herramientas cliente locales de la misma major que el servidor. No se construyen imágenes ni se requiere Docker en esta entrega.
- **Dependencias**: C-02, C-03, C-04.
- **Governance**: ALTO — backup y restauración.
- **Leer antes**:
  - [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) §Seed data inicial propuesto.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Persistencia, concurrencia y errores.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Cinco grupos de evidencia pendiente del relevamiento.

### [C-13] `endurecer-seguridad-y-observabilidad`

- **Estado**: Implementado, validado y archivado el 2026-11-02; ver `openspec/changes/archive/2026-11-02-endurecer-seguridad-y-observabilidad/`.
- **Scope**:
  - Revisar la superficie API/UI: autorización por recurso, sesiones, secretos, límites de solicitudes y rangos, protección de la interfaz según el mecanismo de sesión y exposición de documentación por entorno; cerrar fallos con contratos y pruebas revisados.
  - Añadir logs operativos sin información sensible, identificador de correlación, errores públicos estables y readiness separada de `GET /health`; definir alertas mínimas por fallo de DB/backup sin afirmar cumplimiento normativo.
  - Tests: accesos indebidos, abuso de límites, errores sin secretos/rutas, readiness ante DB caída y regresión del flujo de recepción. Revisar permisos, recuperación y política de datos antes de autorizar información real.
  - Apply 12/12; backend 360 tests OK y 4 omitidos; frontend 50 tests OK; prueba focalizada de concurrencia 11/11; OpenSpec strict 12/12 antes de Archive. Revisión independiente final: sin hallazgos. Sin push.
- **Dependencias**: C-11, C-12.
- **Governance**: CRITICO — seguridad y acceso a datos.
- **Leer antes**:
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Rutas públicas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.
  - [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) §Cinco grupos de evidencia pendiente del relevamiento.

### [C-14] `desplegar-mvp-en-entorno-controlado`

- **Estado**: Opcional y diferido fuera de la entrega académica; no es requisito del MVP demostrable.
- **Scope**:
  - Conservar el antecedente de la propuesta de despliegue; no construir imágenes, iniciar servicios ni publicar el sistema como parte de la entrega.
  - Si más adelante se requiere despliegue, abrir un change nuevo con alcance, tecnología y validación aprobados por la cátedra. Redis puede evaluarse como alternativa, sin compromiso de uso.
- **Dependencias**: ninguna mientras permanezca diferido.
- **Governance**: ALTO si se reactiva configuración o despliegue.
- **Leer antes**: [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Alcance vigente.

## FASE 5 — Evolución clínica del producto

> Extensión posterior a la agenda, con datos ficticios durante desarrollo. Antes de admitir información clínica real se necesita revisar los contratos de acceso, confidencialidad, trazabilidad, conservación y recuperación; el TP no acredita esa habilitación.

### [C-15] `registrar-historia-clinica`

- **Estado**: `[x]` implementado, validado y archivado el 2026-11-02; ver `openspec/changes/archive/2026-11-02-registrar-historia-clinica/` y `backend/evidence/C-15-verificacion.md`.
- **Scope**:
  - Evoluciones clínicas narrativas sintéticas y paginadas; alta ligada a paciente, Profesional y turno atendido propio, con nota máxima de 5000 caracteres.
  - Correcciones append-only; Administrador y Recepción no acceden al contenido. Lecturas/escrituras se auditan en modo metadata-only y fallan cerradas ante error de auditoría.
  - SQLite v9 y Alembic `20261102_0010_clinical_history`; backup/restore conserva evoluciones sin exponer notas en manifiestos. Sin datos reales ni preparación productiva.
  - Verificación final: backend **424 OK, 3 omitidos** con PostgreSQL 18.6 local aislado; integración PostgreSQL **41/41**; OpenSpec strict **15/15**; migración y backup/restore clínico reales pasaron.
- **Dependencias**: C-05, C-06, C-13.
- **Governance**: CRITICO — datos clínicos y trazabilidad.
- **Leer antes**:
  - [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) §Fuera de alcance.
  - [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) §Datos y responsabilidad.
  - [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) §Funcionalidades postergadas.
  - [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) §Seguridad y datos.

### [C-16] `gestionar-odontograma-y-plan`

- **Estado**: `[ ]` propuesta OpenSpec lista para Apply, sin implementación; ver `openspec/changes/gestionar-odontograma-y-plan/`.
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

> Ramas independientes de la extensión clínica; el despliegue queda fuera de la entrega. Se ejecutan con dobles/simuladores hasta elegir y autorizar cualquier proveedor externo. Cada change deja instrucciones y evidencia local; no requiere paquete de despliegue.

### [C-17] `programar-recordatorios`

- **Estado**: `[ ]` planificado; canal real pendiente de decisión.
- **Scope**:
  - Modelar preferencia de contacto y `Recordatorio`/outbox ligada al turno; definir anticipación, zona horaria, consentimiento y contenido mínimo sin datos clínicos. Preparar adaptador simulado antes de evaluar email o WhatsApp.
  - Persistir el outbox de recordatorios en PostgreSQL y procesarlo de forma explícita con un worker local y canal simulado; no incorporar una cola externa como dependencia. Redis puede mencionarse como alternativa futura si luego se justifica y aprueba.
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
