# Reglas de negocio

RN-TU-01/02 provienen del Discovery confirmado. RN-TU-03 a RN-TU-07 se propusieron en Propose y se implementaron al autorizar el usuario continuar con Apply; esto no acredita lectura personal completa del spec. Ver [spec](../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/specs/alta-turnos/spec.md) y [evidencia](../docs/evidencia/implementacion-turnos.md).

## Dominio: turnos — reglas confirmadas

| Código | Regla implementada | Procedencia |
| --- | --- | --- |
| RN-TU-01 | Rechazar solapamiento del profesional aunque cambie box | Discovery |
| RN-TU-02 | Rechazar solapamiento del box aunque cambie profesional | Discovery |

## Dominio: turnos — contrato aplicado

| Código | Contrato implementado | Evidencia |
| --- | --- | --- |
| RN-TU-03 | Intervalos [inicio, fin) | Conflictos y contención |
| RN-TU-04 | Adyacencia en ambos sentidos | BordesTests |
| RN-TU-05 | Inicio anterior a fin, offset explícito, UTC representable y minuto exacto | FechasTests |
| RN-TU-06 | IDs ficticios conocidos, cadena no vacía hasta 64 sin espacios extremos | IdentificadoresTests |
| RN-TU-07 | Sin alta ante validación/conflicto; rollback de fallo controlado previo al commit | RollbackTests |

Solapamiento: existente.inicio < solicitado.fin y existente.fin > solicitado.inicio. Ante ambos conflictos, profesional tiene prioridad. Orden de validación: forma de IDs paciente/profesional/box, fechas/intervalo/timeout, referencias paciente/profesional/box, conflictos y registro.

## Dominio: políticas del contrato inicial C-01

| Tema | Contrato / exclusión |
| --- | --- |
| Duración | Positiva libre, minuto exacto, sin prestaciones |
| Horarios y cruce de día | Sin disponibilidad clínica; cruce permitido |
| Zona y precisión | Offset explícito; comparar/persistir/devolver UTC |
| Estados/cancelación | Sin estados; cada fila ocupa recursos |
| Paciente simultáneo | Permitido con ambos recursos distintos |
| Compatibilidad | Sin restricción profesional-box adicional |
| Sobreturnos | Ninguna excepción a exclusiones |
| Idempotencia | No implementada; repetir alta exitosa produce conflicto |
| Concurrencia | BEGIN IMMEDIATE antes de consultar; mismo archivo local vía módulo |
| Timeout | 5s por defecto; número finito positivo; no deadline global |

El alcance histórico de C-01 no incluye horarios ni estado. C-07 y C-09 amplían sólo la API con el esquema migrado a SQLite v6 o PostgreSQL 0007; esa capa rechaza cruces de medianoche y turnos fuera de horario según las reglas de disponibilidad indicadas abajo.

## Dominio: catálogos — C-06

| Tema | Contrato aplicado |
| --- | --- |
| Profesional y box | ID opaco, nombre obligatorio de hasta 120 caracteres y estado activo; seed IDs se conservan con nombres ficticios |
| Prestación | ID opaco, nombre obligatorio, duración entera positiva en minutos y estado activo; el límite práctico es el máximo de `INTEGER` PostgreSQL |
| Acceso | Administrador y Recepción crean, consultan y editan datos descriptivos; sólo Administrador activa/desactiva |
| Consulta | Orden ascendente por ID; límite predeterminado 50, máximo 100 y offset no negativo; incluye inactivos |
| Baja | Lógica e idempotente; no elimina filas ni referencias históricas |
| Alta de turno | Referencias desconocidas se resuelven antes de los estados; profesional o box inactivo devuelve `recurso_inactivo` antes de conflictos |
| Prestación en C-01 | No se agrega `prestacion_id`, no se calcula la duración del turno ni se crean compatibilidades |
| Auditoría | Sólo metadatos permitidos y transacción conjunta; si falla el evento, se revierte el cambio |

## Dominio: horarios y disponibilidad — C-07

| Tema | Contrato aplicado |
| --- | --- |
| Zona y ventanas | `America/Argentina/Mendoza`; día ISO 1–7, múltiples tramos locales `HH:MM`, sin solaparse ni cruzar medianoche; adyacencia permitida |
| Recursos | Administrador y Recepción administran horario semanal, excepción fechada y bloqueos de un profesional o box |
| Excepciones | Reemplazan el horario semanal para ese recurso y fecha local; lista vacía cierra y borrar restaura la recurrencia |
| Reservas | En SQLite v5 y PostgreSQL 0006 el turno debe caber entero dentro de un tramo de ambos recursos; un recurso sin configuración está cerrado |
| Bloqueos | Intervalo ISO 8601 con offset, comparación UTC; un solapamiento impide nuevas reservas |
| Cambios de configuración | Si el cambio invalida un turno ocupante (`reservado` o `confirmado`) del recurso objetivo, incluso pasado, responder `turnos_afectados`/409 y no alterar configuración ni auditoría; los estados terminales se preservan como historial y no impiden reconfigurar |
| Compatibilidad | API falla cerrada si faltan versión, tablas C-07 o la columna `turnos.estado`; servicio standalone C-01 sin `auth_schema_version` conserva el contrato histórico hasta migración explícita |
| Auditoría | Mutaciones confirmadas guardan actor, acción, tipo, ID opaco y resultado; no fecha, horas, tramos ni cuerpo; fallo revierte la transacción |

## Dominio: ciclo de vida de turnos — C-09

| Tema | Contrato aplicado |
| --- | --- |
| Estados | `reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`; toda alta migrada comienza `reservado` y las filas históricas se inicializan así |
| Transiciones | `reservado`→`confirmado` o `cancelado`; `confirmado`→`atendido`, `ausente` o `cancelado`; los tres últimos son terminales |
| Ocupación | Sólo `reservado` y `confirmado` bloquean profesional/box; estados terminales conservan turno e historial y liberan ambos |
| Operaciones | `POST /turnos/{id}/confirmacion`, `/cancelacion`, `/atencion`, `/ausencia`; Administrador y Recepción, respuesta `{id, estado}` |
| Repetición | Cancelar un turno ya cancelado devuelve 200 con el mismo estado, sin actualizar ni emitir evento adicional; otras transiciones inválidas responden 409 |
| Auditoría | Mutación efectiva y `turno.estado_actualizado` son atómicas; sólo actor, acción, recurso, ID opaco y resultado; sin referencias ni datos del horario |
| Concurrencia | Transición comparte `BEGIN IMMEDIATE` SQLite o `AgendaMutex` PostgreSQL con las altas; C-01 standalone sin migrar conserva su contrato anterior |

## Excepciones globales y restricciones confirmadas

- RN-EX-01: sólo datos ficticios, sin información clínica real.
- RN-EX-02: ninguna integración externa ni SOAP, credenciales, certificados ni ARCA/AFIP real.
- RN-EX-03: validación explícita, errores claros y ninguna corrección silenciosa.
- RN-EX-04: pruebas por comportamiento y suite verde antes de finalizar/archivar.

Códigos: entrada_invalida, recurso_desconocido, conflicto_profesional, conflicto_box, fuera_de_disponibilidad, turnos_afectados, agenda_ocupada, almacenamiento_error y agenda_existente. Sin SQL/rutas internas en mensaje público.

## Relación con otras fuentes

[Clinic Cloud](../docs/discovery/fuentes/clinic-cloud.md) documenta selección de box sin demostrar exclusión; [Dentrix Ascend](../docs/discovery/fuentes/dentrix-ascend.md) documenta advertencias que permiten guardar. El TP eligió rechazo. Investigación documental no sustituye pruebas ni revisión personal.
