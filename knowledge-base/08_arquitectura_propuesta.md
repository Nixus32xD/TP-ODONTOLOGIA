# Arquitectura propuesta

## Estado y objetivo

Propuesta mínima para revisar durante fundación/Propose. No hay arquitectura de producto implementada ni lenguaje elegido. Se prioriza una operación comprensible y comprobable antes de añadir capas, dependencias o módulos posteriores.

## Patrones y responsabilidades propuestos

| Responsabilidad | Dónde se usaría | Motivo / límite |
| --- | --- | --- |
| Validación explícita | Entrada de alta e intervalo | Rechazar datos inválidos con errores comprensibles |
| Lógica de ocupación aislable | Comparación de turnos por profesional y box | Probar reglas con entradas distintas sin servicios externos |
| Coordinación del alta | Consulta y registro | Evitar confundir cálculo de conflicto con garantía concurrente |
| Acceso mínimo a turnos existentes | Mecanismo de almacenamiento por definir | Reutilizar lo que corresponda; interfaz de repositorio sólo si aporta |

No se impone DDD, CQRS, microservicios ni un árbol de capas. La separación lógica puede resolverse con pocos archivos según las convenciones del stack elegido. Un repositorio o adaptador es una opción condicionada a persistencia, no una abstracción obligatoria.

## Estructura de directorios

La estructura documental actual usa `docs/`, `discovery/`, `knowledge-base/`, `openspec/`, `.agents/` y `tools/`. La estructura del producto está pendiente.

Organización **ilustrativa** de responsabilidades, sin carpetas aprobadas ni extensiones elegidas:

```text
producto (ubicación pendiente)
  alta de turno
  validación / ocupación
  acceso a turnos, si hace falta
pruebas (ubicación según runner)
  casos válidos, conflictos y límites acordados
```

No se crean esas carpetas desde esta KB. La decisión API/módulo no se resuelve inventando backend, frontend o endpoints.

## Seguridad y datos

- Autenticación: fuera del primer change; sin promesa de acceso seguro de producción.
- Autorización: responsabilidades conceptuales en [03](03_actores_y_roles.md), sin RBAC implementado.
- Validación: entradas explícitas según contrato; tipos, tamaños y errores exactos pendientes.
- Datos: identificadores/etiquetas ficticios, sin diagnósticos, contactos reales ni adjuntos clínicos.
- Secretos: el ejercicio no requiere credenciales ni certificados de proveedores; no se incorporan.
- Integraciones: no ejecutar HTTP/SOAP ni servicios externos del producto.

La documentación de leyes y afirmaciones de proveedores no certifica el ejercicio. Un despliegue con personas reales requeriría un alcance y revisión diferentes.

## Persistencia, concurrencia y errores

No se seleccionan memoria, archivos ni base de datos. La decisión debe responder qué necesita conservar el TP y cómo observarlo en pruebas.

Si se promete exclusión concurrente, el control y el registro deben coordinarse conforme al mecanismo elegido y probarse en su alcance real. Una prueba unitaria de intervalos o una secuencia de altas no demuestra seguridad entre procesos.

Los errores deben distinguir datos inválidos, conflictos y fallos de registro según el futuro contrato. El comportamiento cuando hay dos conflictos o falla el almacenamiento requiere especificación; no se transforma una excepción en alta exitosa.

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
| --- | --- | --- | --- |
| Ninguna definida | Stack y almacenamiento pendientes; no hay configuración de producto aprobada | No aplica | No aplica |

No se crean variables ficticias para completar una plantilla. `needs_infra:false` sólo expresa que no hay infraestructura confirmada; revisar al elegir persistencia.

## Validación futura

Runner pendiente. Cuando haya implementación se aplicarán el baseline de pruebas existentes, RED/GREEN, casos distintos y suite completa. La KB sólo recibe verificaciones documentales de nombres, enlaces y coherencia; no se presentan como pruebas de producto.
