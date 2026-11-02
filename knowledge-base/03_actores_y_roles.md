# Actores y roles

## Actores del sistema

| Actor / entidad | Descripción | Interacción prevista |
| --- | --- | --- |
| Recepción | Actor principal confirmado | Solicita el alta y recibe el resultado |
| Profesional ficticio | Recurso humano de la agenda | Se referencia en el turno; no tiene cuenta API habilitada hasta C-08 |
| Paciente ficticio | Entidad mínima del turno | Se referencia sin acceso propio ni datos clínicos |
| Box/sillón ficticio | Recurso físico | Se asigna al turno; recurso exclusivo del intervalo en C-01 |
| Estudiante | Autor/revisor de la entrega | Revisa artefactos y ejecuta pruebas; autor nominal pendiente |

La matriz de C-03 fue aprobada para el consultorio pequeño: Administrador gestiona usuarios y usa las operaciones disponibles; Recepción crea turnos y administra datos descriptivos mínimos de catálogos; Profesional no accede a la API hasta que C-08 defina su agenda propia. Pacientes no tienen acceso propio. Esto no infiere un rol por cada entidad del modelo.

## RBAC — matriz de permisos conceptual

El primer change C-01 no tenía autenticación. C-03 implementa y archiva autenticación y autorización en SQLite y PostgreSQL. C-04 añade auditoría de operaciones y está archivado. C-05 administra fichas mínimas de pacientes; C-06 administra catálogos ficticios de profesionales, boxes y prestaciones; C-07 administra disponibilidad. El backend verifica el permiso en cada operación, no sólo en la interfaz.

| Actor | Recurso / acción | Estado conceptual |
| --- | --- | --- |
| Administrador | Gestionar cuentas de Administrador y Recepción; usar operaciones disponibles | Implementado en C-03; puede crear turnos |
| Recepción | Crear turno y consultar el resultado | Implementado en C-03; no administra cuentas |
| Administrador y Recepción | Crear, consultar y editar datos descriptivos de profesionales, boxes y prestaciones | Implementado en C-06; lectura paginada |
| Administrador | Activar y desactivar profesionales, boxes y prestaciones | Implementado en C-06; baja lógica, conserva referencias históricas |
| Administrador y Recepción | Consultar y reemplazar horarios semanales; gestionar excepciones fechadas y bloqueos de recursos | C-07, limitado a disponibilidad ficticia y sujeto a preservar todos los turnos registrados |
| Recepción | Consulta de ocupación necesaria para el alta | Necesidad interna; no exige listado público |
| Recepción | Editar/cancelar turnos o cambiar estado de catálogos | No incluido; estados de turnos y cancelación pendientes, estado de catálogos reservado a Administrador |
| Profesional | Ingresar con cuenta o administrar agenda propia | No habilitado; requiere definición de agenda en C-08 |
| Paciente | Reservar, cancelar o ver historia clínica | Postergado |
| Administrador | Crear/listar cuentas y cambiar rol/estado activo | Implementado en C-03; último Administrador activo protegido; eventos consultables sólo por Administrador en C-04 |
| Estudiante | Ejecutar pruebas y revisar datos ficticios | Actividad del proceso, no permiso de producción |

La matriz no implica CRUD completo de turnos. C-05 administra una ficha mínima del paciente; C-06 permite administrar los datos descriptivos y el estado de los catálogos de profesionales, boxes y prestaciones. C-03 habilita el alta de turnos definida por C-01 y la gestión de cuentas indicada arriba. C-07 suma a Administrador y Recepción la configuración de ventanas de agenda, excepciones y bloqueos; una configuración incompatible con cualquier turno histórico se rechaza.

## Rutas públicas

GET /health y la documentación local son públicas. GET /auditoria requiere rol Administrador y retorna sólo metadatos paginados. POST /turnos exige Bearer vigente de Administrador o Recepción; las rutas de usuario exigen Administrador. POST /sesiones recibe credenciales y emite JWT; GET/DELETE /sesiones/actual consultan y revocan la propia sesión. No hay reserva pública; el servicio no es apto para pacientes reales ni publicación pública. Se mantienen excluidos los proveedores externos.

## Datos y responsabilidad

Sólo se usan identificadores y etiquetas ficticias. El contrato usa paciente-A/B, referencias conocidas y ninguna restricción adicional de compatibilidad profesional-box. La simultaneidad del paciente está permitida si ambos recursos difieren; no es una recomendación clínica. No se agregan DNI, teléfonos, emails ni datos de salud por su presencia en productos comerciales.

## Procedencia

[Discovery, usuarios y alcance](../discovery/discovery.md), [visión](01_vision_y_objetivos.md) y [preguntas pendientes](10_preguntas_abiertas.md).
