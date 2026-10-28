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

## Dominio: políticas de esta porción

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

## Excepciones globales y restricciones confirmadas

- RN-EX-01: sólo datos ficticios, sin información clínica real.
- RN-EX-02: ninguna integración externa ni SOAP, credenciales, certificados ni ARCA/AFIP real.
- RN-EX-03: validación explícita, errores claros y ninguna corrección silenciosa.
- RN-EX-04: pruebas por comportamiento y suite verde antes de finalizar/archivar.

Códigos: entrada_invalida, recurso_desconocido, conflicto_profesional, conflicto_box, agenda_ocupada, almacenamiento_error y agenda_existente. Sin SQL/rutas internas en mensaje público.

## Relación con otras fuentes

[Clinic Cloud](../docs/discovery/fuentes/clinic-cloud.md) documenta selección de box sin demostrar exclusión; [Dentrix Ascend](../docs/discovery/fuentes/dentrix-ascend.md) documenta advertencias que permiten guardar. El TP eligió rechazo. Investigación documental no sustituye pruebas ni revisión personal.
