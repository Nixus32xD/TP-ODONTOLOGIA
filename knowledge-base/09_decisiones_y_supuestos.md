# Decisiones y supuestos

## Decisiones documentadas

### DD-01 — Entrega propia desde cero

**Estado:** confirmado por el usuario. **Decisión:** construir una entrega propia en el repositorio TP-ODONTOLOGIA. **Contexto:** la consigna pide mostrar el proceso desde un repositorio sin código. **Alternativas consideradas:** importar una implementación completa o desarrollar la entrega. **Justificación:** el usuario eligió la segunda. **Trade-off:** exige especificar e implementar; no acredita avance reutilizado.

### DD-02 — Consultorio pequeño y primer change de turnos

**Estado:** confirmado por el usuario. **Decisión:** recepción agenda varios profesionales y boxes; el primer change rechaza solapamientos por profesional y box. **Contexto:** acotar el MVP. **Alternativas consideradas:** múltiples módulos clínicos/administrativos o una operación verificable. **Justificación:** el usuario confirmó este enfoque. **Trade-off:** WhatsApp, pagos e historia clínica se postergan.

### DD-03 — Cierre del resumen Discovery

**Estado:** confirmado el 2026-10-15. **Decisión:** registrar los once puntos y continuar con `discovery-research` y la siguiente etapa pendiente. **Contexto:** había un resumen para revisión. **Alternativas consideradas:** continuar, ajustar o detener la etapa. **Justificación:** confirmación explícita actual. **Trade-off:** conservó preguntas técnicas y revisión personal pendientes en ese hito; esta última fue confirmada posteriormente; no aprueba respuestas por defecto.

### DD-04 — Investigación asistida y verificación personal separadas

**Estado:** restricción confirmada por consigna y usuario. **Decisión:** conservar las seis comprobaciones documentales del agente con su atribución; registrar separadamente la confirmación posterior del estudiante, quien declaró haber visto y considerar correctas las seis fuentes el 2026-10-15. **Contexto:** honestidad de la entrega. **Alternativa descartada:** presentar revisión asistida como revisión personal. **Justificación:** existe ahora confirmación expresa del estudiante en el registro de fuentes; no se inventan notas personales por fuente. **Trade-off:** Discovery documental puede alimentar fundación, pero la evidencia de entrega permanece incompleta.

### DD-05 — Datos ficticios y sin integraciones reales

**Estado:** restricción confirmada. **Decisión:** no usar pacientes reales, historia clínica, SOAP externo, credenciales, certificados ni ARCA/AFIP real en el ejercicio. **Contexto:** alcance académico acotado. **Alternativa descartada:** validar contra proveedores reales. **Justificación:** instrucciones del usuario y Discovery. **Trade-off:** las pruebas no podrán acreditar integración externa ni operación clínica real.

### DD-06 — Autorización Git vigente

**Estado:** preferencia confirmada del usuario. **Decisión:** validar cada petición completada y realizar un commit local descriptivo, separando cambios no relacionados; push y publicación requieren autorización explícita aplicable. **Contexto:** esta preferencia reemplaza la prohibición anterior de commits automáticos, sin extender permisos de publicación. El usuario autorizó ahora publicar los commits locales pendientes y continuar: main llegó a `509307025550d183493b5a56fa2d16fd18d0651f`. Apply se guarda como nuevo commit local validado; no se extiende el permiso de push a avances futuros. **Alternativa descartada:** heredar indefinidamente una prohibición de commit o un permiso de publicación de otra etapa. **Justificación:** instrucciones vigentes y alcance de cada autorización. **Trade-off:** el avance local queda disponible para revisión antes de una publicación futura.

### DD-07 — Contrato técnico aplicado

**Estado:** implementación autorizada por la petición «hazle push y sigamos con lo siguiente» después de presentar Propose. **Decisión:** módulo Python 3.12+, SQLite local, unittest; intervalos [inicio, fin), UTC/minuto exacto y adyacencia; BEGIN IMMEDIATE y sin idempotencia/políticas clínicas adicionales. **Justificación:** porción pequeña sin servicios externos, archivo persistente y evidencia por procesos. **Alternativas:** memoria sin persistencia o framework/servidor adicional, diferidos. **Trade-off:** sólo un archivo en disco local vía módulo. La autorización no acredita lectura personal del spec. [Evidencia](../docs/evidencia/implementacion-turnos.md).

## Supuestos originales y resolución en C-01

### SU-01 — Escala funcional `team`

**Supuesto:** un consultorio con recepción y varios recursos se describe como `team`. **Origen:** Discovery, usuarios y alcance. **Riesgo si es falso:** confundir contexto con soporte multiusuario concurrente. **Cómo validar:** acordar modelo de ejecución antes de prometer concurrencia. No se infiere SaaS ni multitenencia.

### SU-02 — Infraestructura sin necesidad confirmada

**Supuesto:** `needs_infra:false` es una representación provisional de baja confianza de la ausencia de necesidad confirmada. **Origen:** no hay integración ni despliegue exigidos para el primer change. **Riesgo si es falso:** descartar indebidamente una base de datos u otro mecanismo necesario. **Cómo validar:** resolver persistencia y actualizar el campo si corresponde. No se elige memoria por defecto.

### SU-03 — Modelo conceptual mínimo

**Propuesta:** turno con referencias a paciente, profesional y box más inicio/fin, usando identificadores abstractos. **Origen:** datos candidatos de Discovery. **Riesgo:** asumir identidad del paciente, formato temporal o equivalencia box/sillón sin acuerdo. **Cómo validar:** revisar [04](04_modelo_de_datos.md) durante Propose.

### SU-04 — Intervalos y estructura mínima

**Propuesta:** intervalos semiabiertos, adyacencia permitida y lógica de validación/ocupación comprobable con pocos archivos. **Origen:** ejemplos candidatos del informe, no decisión del usuario. **Riesgo:** convertir una conveniencia técnica en regla de negocio aprobada. **Cómo validar:** acordar RN-TU-03/04/05 y elegir stack antes de implementar.

## Decisiones técnicas y pendientes actuales

DD-07 resuelve la implementación técnica de Q01–Q08; los supuestos SU-02/03/04 anteriores documentan el origen histórico, no el estado actual. needs_infra:false significa sin servidor externo, con SQLite local. Q09 quedó resuelta por confirmación personal de fuentes; Q10 y las otras revisiones humanas académicas siguen pendientes; no se infieren de las pruebas. Ver [10](10_preguntas_abiertas.md).

## Procedencia

[Discovery canónico](../discovery/discovery.md), [resumen confirmado](../docs/discovery/resumen-para-revision.md), [consigna](../docs/CONSIGNA.md), [bitácora](../docs/BITACORA.md) e instrucciones actuales del usuario. Las entradas de bitácora anteriores describen el momento en que se escribieron; no se leen como estado vigente por encima de la confirmación actual.

## DD-08 — Corrección explícita a FastAPI dentro de C-01

En el momento de esta decisión, el usuario aclaró que el stack es FastAPI y limitó el avance al change 1. C-01 conservó SQLite y el dominio probado, y añadió el adaptador HTTP local, liveness y documentación; ese change no incluía autenticación, UI ni CRUD adicional. Esta delimitación histórica no describe el estado actual: luego se autorizó e implementó C-03, que añade autenticación JWT y permisos de personal. No hay servicios externos.

## DD-09 — Stack y estructura definidos por la cátedra

**Estado:** confirmado por la cátedra el 2026-10-29 (corrección del profesor comunicada por el estudiante). **Decisión:** el sistema se trabaja con backend en Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis y Docker/Docker Compose, y frontend en React, TypeScript y Vite, en carpetas `backend/` y `frontend/`. **Contexto:** la entrega tenía FastAPI y SQLite en la raíz, sin frontend; el profesor indicó que faltaban esas carpetas y que se debía respetar el stack. **Alternativas consideradas:** migrar ahora toda la lógica de C-01, crear sólo la estructura y la documentación, o sumar funcionalidades nuevas. **Justificación:** el estudiante eligió estructura y documentación; C-01 ya está archivado y su contrato no se reescribe, así que cada tecnología se asigna al change del roadmap que la implementa (C-02 PostgreSQL/SQLAlchemy, C-03 JWT, C-11 React, C-14 Docker, C-17 Redis con cola de recordatorios). **Trade-off:** hasta C-02 conviven el stack preparado y SQLite vigente en C-01; tener servicios y carpetas listos no acredita su implementación.

### DD-10 — Demo académica sin Docker ni Redis

**Estado:** confirmado por el usuario el 2026-11-02. **Decisión:** desarrollar y presentar el proyecto mediante el repositorio, los changes OpenSpec, pruebas y demo local; no es necesario desplegarlo, construir imágenes ni levantar Docker/Compose o Redis. Redis puede mencionarse como tecnología que la cátedra había indicado o como alternativa futura, sin dependencia operativa. C-14 de despliegue queda opcional y fuera de la entrega; C-17 propone persistencia de outbox en PostgreSQL y canal simulado. **Contexto:** la entrega debe mostrar el proyecto y sus changes; no hay requisito actual de ejecutar una infraestructura contenerizada. **Alternativa considerada:** conservar Docker/Redis como criterios obligatorios de aceptación. **Trade-off:** la entrega no acredita despliegue ni integración de mensajería real.

**Estado técnico posterior (2026-11-02):** C-02 PostgreSQL y C-03 JWT están implementados, validados y archivados. C-04 auditoría está implementado y validado localmente en SQLite y PostgreSQL aislado, con Archive pendiente de revisión. React/TypeScript/Vite está implementado en C-11. Docker y Redis no forman parte de los criterios operativos de la entrega; el despliegue se difiere y la cola C-17 se plantea persistida en PostgreSQL con canal simulado.


## DD-10 — Política de auditoría de C-04

**Estado:** aprobada explícitamente por el usuario el 2026-11-01 para continuar el desarrollo global del proyecto. **Decisión:** registrar metadatos de turnos confirmados, bootstrap/alta/cambios de cuentas, login/logout y rechazos de login; no conservar el identificador intentado ni datos personales, clínicos, cuerpos, secretos, hashes o JWT. La mutación y el evento comparten transacción y la operación falla cerrada ante indisponibilidad del registro. Sólo Administrador consulta eventos paginados; no se exponen edición, borrado ordinario ni purga automática en el demo. **Justificación:** trazabilidad sin convertir el registro en una copia de datos sensibles. **Trade-off:** una falla de auditoría bloquea la mutación asociada; la retención indefinida se limita al demo y requerirá una política aprobada antes de operar con datos reales.

## DD-11 — Disponibilidad local de C-07

**Estado:** decisiones de alcance confirmadas por el usuario antes de Apply de C-07; implementación técnica validada en SQLite y PostgreSQL aislado. **Decisión:** usar `America/Argentina/Mendoza`; ventanas semanales para profesional y box con varios tramos por día, sin cruce de medianoche; Administrador y Recepción administran horarios, excepciones y bloqueos; una excepción reemplaza el horario semanal de ese recurso/fecha y una lista vacía cierra; cada bloqueo pertenece exactamente a un profesional o box. Cada nueva reserva debe caber entera en un tramo de ambos recursos y no solaparse con bloqueos. Cambiar un recurso comprueba todos sus turnos, pasados o futuros; si el nuevo horario los excluye, responde 409 sin mutar ni auditar. La validación por recurso permite configurar profesional y box progresivamente al migrar turnos C-01. SQLite v5 y Alembic 0006 inician sin horarios; la API valida versión y tablas y falla cerrada si el esquema falta. El servicio standalone C-01 en una base no migrada conserva su contrato anterior. **Trade-off:** un turno pasado puede impedir reducir el horario del recurso al que pertenece; se eligió preservar su validez.

## DD-12 — Consulta y vínculo Profesional de C-08

**Estado:** decisiones de alcance documentadas y Apply implementado; regresión completa y Archive pendientes. **Decisión:** Admin/Recepción consultan turnos con fechas offset-aware y rango máximo de 31 días; profesional cuenta con vínculo único administrado por Administrador y consulta sólo esa agenda. Su respuesta contiene horarios y nombre del paciente, sin teléfono. Las opciones de disponibilidad son orientativas, en fecha local Mendoza, con inicios cada 15 minutos y filtros de ocupación C-07/C-09; el alta sigue revalidando dentro de su transacción. No se añade reprogramación ni escritura del rol Profesional. SQLite v7 y Alembic 0008 agregan el vínculo; reasignación/cambio de rol revoca sesiones y el JWT se compara con el estado persistido. **Justificación:** habilitar consulta operativa de menor privilegio sin compartir calendarios ni incluir datos de contacto. **Trade-off:** el vínculo profesional pasa a ser obligatorio para iniciar sesión con ese rol; ante columna ausente o inconsistencias, la API falla cerrada.
