# Modelo de datos

## Alcance del modelo

El alta de turnos se implementa en [agenda.py](../backend/odontologia/agenda.py); C-05 administra fichas ficticias y C-06 añade los catálogos de recursos. C-04/C-05/C-06 usan una tabla técnica de auditoría, descrita abajo. Sólo se usan datos ficticios, sin información clínica real.

## Entidades propuestas

El encabezado conserva la navegación inicial; estas entidades ya están representadas en el módulo.

| Entidad | Representación | Contrato |
| --- | --- | --- |
| Paciente | pacientes, ID TEXT PRIMARY KEY | paciente-A/B; nombre, teléfono opcional y activo |
| Profesional | profesionales, ID TEXT PRIMARY KEY | profesional-A/B; nombre y estado activo; exclusión por intervalo |
| Box | boxes, ID TEXT PRIMARY KEY | box-A/B; nombre y estado activo; recurso exclusivo |
| Prestación | prestaciones, ID TEXT PRIMARY KEY | nombre, duración positiva en minutos y estado activo; independiente del turno |
| Turno | turnos y valor inmutable Turno | ID INTEGER PRIMARY KEY positivo, tres referencias e inicio/fin |

Cada turno referencia exactamente un paciente, profesional y box; no contiene `prestacion_id`. FK activadas/verificadas por conexión; CHECK inicio anterior a fin. Los catálogos se consultan paginados y se actualizan sin borrar filas; sólo Administrador cambia su estado.

Persistir inicio_minuto/fin_minuto como enteros desde epoch UTC. API recibe datetime con offset y precisión de minuto, retorna UTC, sin float ni redondeo. Índices por profesional/inicio y box/inicio; no son restricciones únicas de intervalo: la exclusión depende del control e inserción dentro de BEGIN IMMEDIATE.

## Seed data inicial propuesto

El bootstrap C-01 crea paciente-A/B, profesional-A/B y box-A/B sin turnos. Al migrar a SQLite v4 o Alembic 0005 se conservan los IDs y se asignan nombres demostrativos estables a profesionales y boxes; el catálogo de prestaciones comienza vacío. La migración es explícita y conserva turnos previos. Demo/tests usan TemporaryDirectory del sistema; las DB no se versionan.

## Límites que afectan el modelo

Sin estados/cancelación de turnos, disponibilidad, asociaciones de prestaciones ni compatibilidad profesional-box/profesional-prestación. La duración de prestación es sólo informativa en C-06 y no cambia el intervalo libre de C-01. Los nuevos turnos rechazan paciente, profesional o box inactivo; los turnos anteriores y referencias históricas se conservan. Cada fila ocupa recursos. Paciente simultáneo permitido si ambos recursos difieren. Sin idempotencia, excepción de sobreturno ni garantías para SQL directo externo. Estos límites académicos no son recomendaciones clínicas.

## Auditoría técnica de C-04

`eventos_auditoria` se agrega mediante migración explícita SQLite versión 2 o Alembic PostgreSQL `20261101_0003_audit`. Sus columnas son `id`, `created_at` UTC, `actor_id` opcional, `action`, `resource_type`, `resource_id` opcional y `result`. Guarda sólo metadatos permitidos; no guarda nombres/identificadores ingresados, datos clínicos, cuerpos, contraseñas, hashes, JWT ni IDs de sesión. `actor_id` puede ser nulo en bootstrap y login rechazado. Los eventos no se editan ni borran por operaciones ordinarias y no hay purga automática.

Las operaciones C-04/C-05/C-06 agregan el evento dentro de la transacción que confirma la mutación de turno, cuenta, sesión, paciente o catálogo. Tanto helper como DDL aplican la misma matriz acción→recurso→resultado. Los eventos de catálogo contienen fecha, actor, acción, tipo, ID opaco y resultado; nunca nombre, duración ni cuerpo. Si la escritura falla, la operación revierte y devuelve error genérico. La consulta paginada sólo la puede realizar Administrador.
