# Modelo de datos

## Alcance del modelo

El dominio de agenda se implementa en [agenda.py](../backend/odontologia/agenda.py). C-04 agrega una tabla técnica de auditoría, descrita abajo. Sólo se usan datos ficticios, sin información clínica ni contactos.

## Entidades propuestas

El encabezado conserva la navegación inicial; estas entidades ya están representadas en el módulo.

| Entidad | Representación | Contrato |
| --- | --- | --- |
| Paciente | pacientes, ID TEXT PRIMARY KEY | paciente-A/B; sin exclusión de simultaneidad |
| Profesional | profesionales, ID TEXT PRIMARY KEY | profesional-A/B; exclusión por intervalo |
| Box | boxes, ID TEXT PRIMARY KEY | box-A/B; recurso exclusivo |
| Turno | turnos y valor inmutable Turno | ID INTEGER PRIMARY KEY positivo, tres referencias e inicio/fin |

Cada turno referencia exactamente un paciente, profesional y box. FK activadas/verificadas por conexión; CHECK inicio anterior a fin. Catálogos sin CRUD.

Persistir inicio_minuto/fin_minuto como enteros desde epoch UTC. API recibe datetime con offset y precisión de minuto, retorna UTC, sin float ni redondeo. Índices por profesional/inicio y box/inicio; no son restricciones únicas de intervalo: la exclusión depende del control e inserción dentro de BEGIN IMMEDIATE.

## Seed data inicial propuesto

Bootstrap implementado: paciente-A/B, profesional-A/B, box-A/B y cero turnos. Reserva sólo un archivo nuevo, sin crear padres ni reemplazar archivos. Demo/tests usan TemporaryDirectory del sistema; las DB no se versionan.

## Límites que afectan el modelo

Sin estados/cancelación, disponibilidad, prestaciones ni compatibilidad profesional-box. Cada fila ocupa recursos. Paciente simultáneo permitido si ambos recursos difieren. Sin idempotencia, excepción de sobreturno ni garantías para SQL directo externo. Estos límites académicos no son recomendaciones clínicas.

## Auditoría técnica de C-04

`eventos_auditoria` se agrega mediante migración explícita SQLite versión 2 o Alembic PostgreSQL `20261101_0003_audit`. Sus columnas son `id`, `created_at` UTC, `actor_id` opcional, `action`, `resource_type`, `resource_id` opcional y `result`. Guarda sólo metadatos permitidos; no guarda nombres/identificadores ingresados, datos clínicos, cuerpos, contraseñas, hashes, JWT ni IDs de sesión. `actor_id` puede ser nulo en bootstrap y login rechazado. Los eventos no se editan ni borran por operaciones ordinarias y no hay purga automática.

Las operaciones C-04 agregan el evento dentro de la transacción que confirma la mutación de turno, cuenta o sesión. Tanto helper como DDL aplican la misma matriz acción→recurso→resultado: turno creado→turno/confirmado; bootstrap, alta o actualización→cuenta/confirmado; inicio o cierre de sesión→sesión/confirmado; rechazo de sesión→sesión/rechazado. Si la escritura falla, la operación revierte y devuelve error genérico. La consulta paginada sólo la puede realizar Administrador.
