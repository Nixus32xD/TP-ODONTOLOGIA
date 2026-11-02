# Modelo de datos

## Alcance del modelo

El alta standalone de C-01 se implementa en [agenda.py](../backend/odontologia/agenda.py); C-05 administra fichas ficticias, C-06 los catálogos, C-07 la disponibilidad y C-09 el ciclo de vida. La API migrada conserva estados de turno y C-04 a C-09 usan una tabla técnica de auditoría. Sólo se usan datos ficticios, sin información clínica real.

## Entidades propuestas

El encabezado conserva la navegación inicial; estas entidades ya están representadas en el módulo.

| Entidad | Representación | Contrato |
| --- | --- | --- |
| Paciente | pacientes, ID TEXT PRIMARY KEY | paciente-A/B; nombre, teléfono opcional y activo |
| Profesional | profesionales, ID TEXT PRIMARY KEY | profesional-A/B; nombre y estado activo; exclusión por intervalo |
| Box | boxes, ID TEXT PRIMARY KEY | box-A/B; nombre y estado activo; recurso exclusivo |
| Prestación | prestaciones, ID TEXT PRIMARY KEY | nombre, duración positiva en minutos y estado activo; independiente del turno |
| Turno | turnos y valor inmutable Turno | ID INTEGER PRIMARY KEY positivo, tres referencias, inicio/fin y estado restringido en la API migrada |
| Horario semanal | horarios_semanales | Profesional o box (exactamente uno), día ISO y tramo local de minutos; SQLite v5+ / PostgreSQL 0006+ |
| Excepción | excepciones_horario y tramos_excepcion | Fecha local por recurso; cabecera presente con cero tramos significa día cerrado |
| Bloqueo | bloqueos_agenda | ID opaco, exactamente profesional o box, intervalo positivo en minutos UTC |
| Cuenta Profesional | usuarios.profesional_id | FK única a profesionales; el rol Profesional requiere vínculo y Administrador/Recepción no lo admiten |

Cada turno referencia exactamente un paciente, profesional y box; no contiene `prestacion_id`. FK activadas/verificadas por conexión; CHECK inicio anterior a fin. Los catálogos se consultan paginados y se actualizan sin borrar filas; sólo Administrador cambia su estado.

Persistir inicio_minuto/fin_minuto como enteros desde epoch UTC. API recibe datetime con offset y precisión de minuto, retorna UTC, sin float ni redondeo. Índices por profesional/inicio y box/inicio; no son restricciones únicas de intervalo: la exclusión depende del control e inserción dentro de BEGIN IMMEDIATE.

## Seed data inicial propuesto

El bootstrap C-01 crea paciente-A/B, profesional-A/B y box-A/B sin turnos. Al migrar a SQLite v5 o Alembic 0006 se conservan los IDs y se asignan nombres demostrativos estables a profesionales y boxes; el catálogo de prestaciones comienza vacío y la disponibilidad inicia cerrada. La migración es explícita y conserva turnos previos. Demo/tests usan TemporaryDirectory del sistema; las DB no se versionan.

## Estado y ocupación — C-09

En la API con SQLite v6 o PostgreSQL Alembic `20261102_0007_turn_status`, `turnos.estado` sólo admite `reservado`, `confirmado`, `atendido`, `ausente` o `cancelado`. Filas previas reciben `reservado` sin cambiar ID, referencias ni intervalo. `reservado` y `confirmado` ocupan profesional y box; los tres estados terminales permanecen como historial y liberan ambos recursos. Las transiciones permitidas son reservado→confirmado/cancelado y confirmado→atendido/ausente/cancelado. La cancelación repetida devuelve el estado actual sin mutar ni volver a auditar. La transición comparte la exclusión transaccional de las altas: `BEGIN IMMEDIATE` en SQLite y la fila `AgendaMutex` en PostgreSQL.

La migración SQLite reconstruye `eventos_auditoria` para aceptar `turno.estado_actualizado` y copia las filas históricas conservando sus IDs, índice y protecciones append-only. PostgreSQL actualiza las constraints de acción y combinación en Alembic 0007. Cada transición efectiva registra sólo actor, acción, tipo `turno`, ID opaco y resultado; estado e historial se confirman juntos.

## Consulta y vínculo de Profesional — C-08

SQLite v7 y PostgreSQL Alembic `20261102_0008_professional_accounts` agregan `usuarios.profesional_id` como FK única con `ON DELETE RESTRICT` y CHECK rol/vínculo. El Administrador asigna una ficha activa al crear o actualizar una cuenta; cambiar el rol o vínculo revoca sesiones. JWT e identidad validada contienen el ID asociado y se comparan con el vínculo actual para fallar cerrado. Las filas existentes Administrador/Recepción migran sin vínculo.

`GET /turnos` consulta intervalos semiabiertos `[desde,hasta)`, hasta 31 días, con filtros y paginación estable. La proyección operativa no contiene teléfono; Profesional sólo recibe inicio, fin y nombre del paciente de su propio vínculo. `GET /disponibilidad` propone inicios de 15 minutos dentro de horarios/excepciones locales y excluye recursos inactivos, bloqueos y turnos `reservado`/`confirmado`; es de sólo lectura y no sustituye la validación de `POST /turnos`. C-01 standalone continúa sin requerir el campo `estado` ni la migración de autenticación.

## Límites que afectan el modelo

Sin asociaciones de prestaciones/compatibilidad profesional-box/profesional-prestación, reprogramación, excepción de sobreturno ni garantías para SQL directo externo. La duración de prestación es sólo informativa en C-06. En C-01 standalone el intervalo conserva su libertad original y no requiere estado; la API C-07/C-09, tras migrar, exige disponibilidad de ambos recursos y considera ocupantes sólo `reservado`/`confirmado`. Los turnos anteriores y referencias históricas se conservan; si un cambio afecta a un turno ocupante se rechaza, mientras los estados terminales no impiden configurar horarios, excepciones ni bloqueos futuros. Paciente simultáneo permitido si ambos recursos difieren. Estos límites académicos no son recomendaciones clínicas.

## Auditoría técnica de C-04

`eventos_auditoria` se agrega mediante migración explícita SQLite versión 2 o Alembic PostgreSQL `20261101_0003_audit`. Sus columnas son `id`, `created_at` UTC, `actor_id` opcional, `action`, `resource_type`, `resource_id` opcional y `result`. Guarda sólo metadatos permitidos; no guarda nombres/identificadores ingresados, datos clínicos, cuerpos, contraseñas, hashes, JWT ni IDs de sesión. `actor_id` puede ser nulo en bootstrap y login rechazado. Los eventos no se editan ni borran por operaciones ordinarias y no hay purga automática.

Las operaciones C-04/C-05/C-06/C-07/C-09 agregan el evento dentro de la transacción que confirma la mutación de turno, cuenta, sesión, paciente, catálogo, agenda o estado de turno. Tanto helper como DDL aplican la misma matriz acción→recurso→resultado. `turno.estado_actualizado` no incluye referencias de agenda ni intervalos. Los eventos de catálogo y disponibilidad contienen fecha, actor, acción, tipo, ID opaco y resultado; nunca nombre, duración, fechas de excepción, horarios, intervalos ni cuerpos. Si la escritura falla, la operación revierte y devuelve error genérico. La consulta paginada sólo la puede realizar Administrador.
