# Modelo de datos

## Alcance del modelo

Modelo **conceptual propuesto**, derivado del alta acordada; todavía no es esquema de almacenamiento. Los tipos `Identificador`, `Etiqueta` y `ValorTemporal` son abstractos. No se eligieron SQL, UUID, formato de fecha, zona horaria, precisión ni serialización.

## Dominios

- Agenda: turno e intervalo ocupado.
- Recursos: profesional y box/sillón.
- Identificación mínima: paciente ficticio, sin historia clínica.

Prestación, horarios, disponibilidad y estados sólo se incorporarán si se acuerdan para esta porción. No se crean entidades para funciones postergadas.

## ERD conceptual

```text
Paciente     1 ---- 0..* Turno 0..* ---- 1 Profesional
                         |
                        0..*
                         |
                         1
                        Box
```

Propuesta: cada turno referencia un paciente, un profesional y un box; cada recurso puede tener varios turnos en momentos compatibles. La cardinalidad y obligación exacta del paciente deben concretarse con su identidad mínima. `Box` representa provisionalmente el recurso físico; no define que sala y sillón sean equivalentes en todos los consultorios.

## Entidades propuestas

### Turno

| Atributo | Tipo conceptual | Estado |
| --- | --- | --- |
| identificador | Identificador | Mecanismo de generación pendiente |
| paciente | Referencia a Paciente | Datos mínimos y validación pendientes |
| profesional | Referencia a Profesional | Recurso confirmado |
| box | Referencia a Box | Recurso confirmado |
| inicio | ValorTemporal | Representación y límites pendientes |
| fin | ValorTemporal | Relación con inicio pendiente de especificación |

Relaciones: un profesional y un box por turno; vínculo mínimo al paciente propuesto. Constraints confirmados: no solapar profesional ni box. Predicado exacto de solapamiento, estados que ocupan y garantía concurrente pendientes. No hay atributo `estado` aprobado ni catálogo de estados supuesto.

Índices: no definidos; dependen del almacenamiento y consultas reales. No se propone un índice SQL antes de elegir persistencia.

### Profesional

- Atributos propuestos: `identificador: Identificador`, `etiqueta: Etiqueta` ficticia.
- Relación: cero o más turnos.
- Constraints propuestos: referencia reconocida en los ejemplos; sin login, matrícula real ni especialidad obligatoria.
- Índices: pendientes del almacenamiento; no hay esquema físico.

### Box

- Atributos propuestos: `identificador: Identificador`, `etiqueta: Etiqueta` ficticia.
- Relación: cero o más turnos.
- Constraints: exclusión temporal confirmada; capacidad, equivalencia sala/sillón y compatibilidad con profesionales pendientes.
- Índices: pendientes; no se decide duplicar recursos ni asignar capacidad múltiple.

### Paciente

- Atributos propuestos: `identificador: Identificador`; etiqueta ficticia sólo si aporta al ejemplo.
- Relación: cero o más turnos; prohibición de simultaneidad del paciente no acordada.
- Constraints: no almacenar datos personales reales, información clínica ni adjuntos.
- Índices: pendientes; no se necesita una búsqueda por DNI/contacto para el alcance confirmado.

## Seed data inicial propuesto

Dos profesionales `profesional-A` y `profesional-B`, dos boxes `box-A` y `box-B` y dos pacientes `paciente-A` y `paciente-B` bastan como etiquetas de ejemplos para separar conflictos. Son nombres didácticos, no formato de identificador implementado ni cantidad fija de recursos del producto.

Los fixtures deberán incluir agenda vacía y un turno existente en un intervalo ilustrativo 09:00–09:30 de una fecha ficticia, cuando se acuerde la representación temporal. No se fija una prestación de treinta minutos: ese intervalo sólo ejemplifica una ocupación.

## Pendientes que afectan el modelo

Persistencia, concurrencia, identidad del paciente, duración por prestación, horarios, estados/cancelación, zona horaria y compatibilidad de recursos. Ver [reglas](05_reglas_de_negocio.md) y [preguntas](10_preguntas_abiertas.md) antes de convertir este modelo en código.
