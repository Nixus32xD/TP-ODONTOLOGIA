# Reglas de negocio

Los códigos permiten trazar especificaciones y pruebas futuras. **Confirmada** es una regla acordada; **Propuesta pendiente** es una opción aún sin aceptación de contrato. No hay reglas implementadas ni pruebas de producto en esta etapa.

## Dominio: turnos — reglas confirmadas

| Código | Regla | Procedencia |
| --- | --- | --- |
| RN-TU-01 | Rechazar un turno que solape la ocupación del mismo profesional, aunque el box sea distinto | Discovery confirmado, puntos 1, 3 y 7 |
| RN-TU-02 | Rechazar un turno que solape la ocupación del mismo box, aunque el profesional sea distinto | Discovery confirmado, puntos 1, 3 y 7 |

El usuario confirmó la exclusión de ambos recursos. La definición matemática del intervalo y qué ocupaciones cuentan todavía deben especificarse. No se permite asumir una excepción de sobreturno por haberla visto en otro producto.

## Dominio: turnos — propuestas pendientes

| Código | Propuesta para revisar | Pregunta asociada |
| --- | --- | --- |
| RN-TU-03 | Representar la ocupación como intervalo semiabierto `[inicio, fin)` | Q04 |
| RN-TU-04 | Permitir adyacencia: un turno puede empezar al finalizar otro | Q04 |
| RN-TU-05 | Exigir inicio anterior al fin; rechazar intervalo vacío o invertido sin corregirlo | Q04 |
| RN-TU-06 | Validar referencias de paciente, profesional y box contra datos ficticios reconocidos | Q07 y Q08 |
| RN-TU-07 | Rechazar sin registrar el alta cuando falle una validación o haya conflicto | Q03 y contrato de errores |

Si se aprueban RN-TU-03/04, el predicado candidato para intervalos `a` y `b` es `a.inicio < b.fin` y `b.inicio < a.fin`. Sigue siendo una propuesta; no se usa como contrato aprobado ni demuestra exclusión concurrente.

## Dominio: políticas aún por definir

| Tema | Estado |
| --- | --- |
| Duración fija, libre o derivada de prestación | Pendiente; no se asumen 15/30 minutos ni se crea catálogo de prestaciones |
| Horarios habilitados, descansos y cruce de día | Pendiente; no se impone horario comercial |
| Zona horaria y precisión | Pendiente; no se asume formato local/UTC ni redondeo |
| Estados que ocupan recursos y cancelación | Pendiente; no hay máquina de estados aprobada |
| Simultaneidad del paciente | Pendiente; no se deduce de RN-TU-01/02 |
| Disponibilidad y compatibilidad profesional-box | Pendiente; no se presume asociación fija ni capacidad mayor a uno |
| Sobreturnos | Sin política aprobada; no se introduce una excepción |
| Idempotencia/reintentos | Pendiente; no se promete deduplicación de solicitudes |
| Solicitudes concurrentes | Mecanismo y prueba pendientes; pruebas secuenciales no bastan para afirmar atomicidad |

## Excepciones globales y restricciones confirmadas

- **RN-EX-01:** usar exclusivamente datos ficticios, sin información clínica real.
- **RN-EX-02:** no ejecutar integraciones externas, HTTP/SOAP, credenciales, certificados ni ARCA/AFIP real en el ejercicio.
- **RN-EX-03:** validar entradas de forma explícita y producir errores claros; no alterar silenciosamente datos inválidos para aceptarlos.
- **RN-EX-04:** cada cambio de comportamiento exige pruebas y la suite completa deberá pasar antes de considerarlo terminado.

Procedencia: [Discovery](../discovery/discovery.md), [consigna](../docs/CONSIGNA.md) e instrucciones del proyecto proporcionadas por el usuario.

## Relación con otras fuentes

[Clinic Cloud](../docs/discovery/fuentes/clinic-cloud.md) documenta selección de box, pero no prueba exclusividad; [Dentrix Ascend](../docs/discovery/fuentes/dentrix-ascend.md) documenta advertencias que permiten guardar. El TP eligió **rechazo** para profesional y box; esas diferencias justifican especificar el comportamiento en lugar de copiar un formulario o aviso.
