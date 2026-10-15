# Modelo de datos

## Alcance del modelo

Modelo implementado en [agenda.py](../odontologia/agenda.py) según el [diseño](../openspec/changes/crear-turno-sin-solapamientos/design.md). Sólo datos ficticios, sin información clínica ni contactos.

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
