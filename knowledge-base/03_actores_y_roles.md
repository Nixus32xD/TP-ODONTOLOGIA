# Actores y roles

## Actores del sistema

| Actor / entidad | Descripción | Interacción prevista |
| --- | --- | --- |
| Recepción | Actor principal confirmado | Solicita el alta y recibe el resultado |
| Profesional ficticio | Recurso humano de la agenda | Se referencia en el turno; no requiere cuenta |
| Paciente ficticio | Entidad mínima del turno | Se referencia sin acceso propio ni datos clínicos |
| Box/sillón ficticio | Recurso físico | Se asigna al turno; recurso exclusivo del intervalo en C-01 |
| Estudiante | Autor/revisor de la entrega | Revisa artefactos y ejecuta pruebas; autor nominal pendiente |

Un administrador de producción, el acceso propio del profesional y el portal del paciente quedan para después. No se infiere un rol de usuario por cada entidad del modelo.

## RBAC — matriz de permisos conceptual

No existe autenticación ni RBAC implementado o requerido en el primer change. La tabla expresa responsabilidades funcionales, sin prometer autorización segura.

| Actor | Recurso / acción | Estado conceptual |
| --- | --- | --- |
| Recepción | Crear turno y consultar el resultado | Confirmado como caso de uso |
| Recepción | Consulta de ocupación necesaria para el alta | Necesidad interna; no exige listado público |
| Recepción | Editar/cancelar turnos o administrar catálogos | No incluido; estados y cancelación pendientes |
| Profesional | Ingresar con cuenta o administrar agenda propia | Postergado |
| Paciente | Reservar, cancelar o ver historia clínica | Postergado |
| Administrador | Gestionar usuarios/permisos | Postergado |
| Estudiante | Ejecutar pruebas y revisar datos ficticios | Actividad del proceso, no permiso de producción |

CRUD completo de turnos, pacientes, profesionales y boxes no se deriva de esta matriz. El primer change sigue siendo una operación de alta con controles.

## Rutas públicas

No hay rutas públicas definidas ni reserva abierta. Si se elige una API, sus contratos deben especificarse sin tratar la ausencia de autenticación académica como seguridad apta para pacientes reales. La restricción de no ejecutar HTTP/servicios externos del ejercicio conserva vigencia.

## Datos y responsabilidad

Sólo se usan identificadores y etiquetas ficticias. El contrato usa paciente-A/B, referencias conocidas y ninguna restricción adicional de compatibilidad profesional-box. La simultaneidad del paciente está permitida si ambos recursos difieren; no es una recomendación clínica. No se agregan DNI, teléfonos, emails ni datos de salud por su presencia en productos comerciales.

## Procedencia

[Discovery, usuarios y alcance](../discovery/discovery.md), [visión](01_vision_y_objetivos.md) y [preguntas pendientes](10_preguntas_abiertas.md).
