# Actores y roles

## Actores del sistema

| Actor / entidad | Descripción | Interacción prevista |
| --- | --- | --- |
| Recepción | Actor principal confirmado | Solicita el alta y recibe el resultado |
| Profesional ficticio | Recurso humano de la agenda | Se referencia en turnos; C-08 vincula su ficha a una cuenta con lectura limitada a su agenda |
| Paciente ficticio | Entidad mínima del turno | Se referencia sin acceso propio ni datos clínicos |
| Box/sillón ficticio | Recurso físico | Se asigna al turno; recurso exclusivo del intervalo en C-01 |
| Estudiante | Autor/revisor de la entrega | Revisa artefactos y ejecuta pruebas; autor nominal pendiente |

La matriz de C-03 fue aprobada para el consultorio pequeño. C-08 amplía la cuenta Profesional a consultas de sólo lectura de su propio calendario; no le permite crear, modificar o cambiar turnos ni consultar otras fichas profesionales. Pacientes no tienen acceso propio. Esto no infiere un rol por cada entidad del modelo.

## RBAC — matriz de permisos conceptual

El primer change C-01 no tenía autenticación. C-03 implementa autenticación y autorización; C-04 añade auditoría; C-05 administra fichas; C-06 catálogos; C-07 disponibilidad; C-09 estados y cancelación. C-08 está en Apply con consultas y vínculo profesional. El backend verifica permisos, no sólo la interfaz.

| Actor | Recurso / acción | Estado conceptual |
| --- | --- | --- |
| Administrador | Gestionar cuentas de personal; crear y consultar turnos/disponibilidad | Gestión de cuenta profesional y consultas implementadas en Apply C-08; puede crear turnos |
| Recepción | Crear y consultar turnos/disponibilidad | Consultas en C-08; no administra cuentas |
| Administrador y Recepción | Crear, consultar y editar datos descriptivos de profesionales, boxes y prestaciones | Implementado en C-06; lectura paginada |
| Administrador | Activar y desactivar profesionales, boxes y prestaciones | Implementado en C-06; baja lógica, conserva referencias históricas |
| Administrador y Recepción | Consultar y reemplazar horarios semanales; gestionar excepciones fechadas y bloqueos de recursos | C-07, limitado a disponibilidad ficticia y sujeto a preservar todos los turnos registrados |
| Recepción | Consulta de ocupación necesaria para el alta | Necesidad interna; no exige listado público |
| Recepción | Confirmar/cancelar/atender/marcar ausencia de turnos | Implementado en C-09; no hay reprogramación |
| Profesional | Consultar su agenda y opciones de disponibilidad | C-08 permite lectura limitada al ID profesional vinculado; sin teléfono ni escritura |
| Paciente | Reservar, cancelar o ver historia clínica | Postergado |
| Administrador | Crear/listar cuentas y cambiar rol/estado activo | Implementado en C-03; último Administrador activo protegido; eventos consultables sólo por Administrador en C-04 |
| Estudiante | Ejecutar pruebas y revisar datos ficticios | Actividad del proceso, no permiso de producción |

La matriz no implica CRUD completo de turnos. C-08 sólo añade consulta y no reprogramación. C-05 administra fichas mínimas; C-06 catálogos; C-07 horarios; C-09 estados. La disponibilidad sugerida es orientativa y el alta transaccional vuelve a validar horarios y conflictos.

## Rutas públicas

GET /health y la documentación local son públicas. GET /auditoria requiere Administrador. POST /turnos y `GET /turnos`, `GET /disponibilidad` requieren sesión; Profesionales sólo consultan su vínculo. Las rutas de usuario exigen Administrador. POST /sesiones emite JWT con vínculo de Profesional; GET/DELETE /sesiones/actual consultan y revocan la propia sesión. No hay reserva pública; el servicio no es apto para pacientes reales ni publicación pública. Se mantienen excluidos los proveedores externos.

## Datos y responsabilidad

Sólo se usan identificadores y etiquetas ficticias. El contrato usa paciente-A/B, referencias conocidas y ninguna restricción adicional de compatibilidad profesional-box. La simultaneidad del paciente está permitida si ambos recursos difieren; no es una recomendación clínica. No se agregan DNI, teléfonos, emails ni datos de salud por su presencia en productos comerciales.

## Procedencia

[Discovery, usuarios y alcance](../discovery/discovery.md), [visión](01_vision_y_objetivos.md) y [preguntas pendientes](10_preguntas_abiertas.md).
