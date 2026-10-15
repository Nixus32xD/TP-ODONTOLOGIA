# Descripción general

## Estado actual

El repositorio contiene documentación del TP, Discovery, herramientas para producir el informe y configuración de OpenSpec/Active Stack. No hay implementación de agenda ni suite de comportamiento del producto. Las herramientas de documentación no determinan el stack del producto.

El alcance es un consultorio pequeño con recepción y múltiples profesionales/boxes. La clasificación de escala `team` describe ese contexto funcional; no demuestra soporte multiusuario concurrente ni implica multitenencia.

## Stack tecnológico

| Capa | Tecnología | Versión mínima / estado |
| --- | --- | --- |
| Lenguaje y runtime del producto | Pendiente de definición en fundación | Sin decisión |
| Forma de exposición | Pendiente: módulo de dominio o API | Sin contrato ni transporte definidos |
| Almacenamiento | Pendiente | No se seleccionó motor, memoria ni formato de archivo |
| Pruebas del producto | Pendiente del stack | No existe runner del producto confirmado |
| Interfaz gráfica | No obligatoria para el primer change | No seleccionada |
| Especificación y flujo | OpenSpec / Active Stack | Inventario observado, no mínimo de runtime |
| Herramienta del informe | Python, ReportLab y pypdf | Uso documental existente, no elección de stack |

Las versiones observadas de Git, Node y OpenSpec están en el [inventario](../docs/evidencia/entorno.md). Disponibilidad local no equivale a requisito tecnológico aprobado.

## Arquitectura general

Propuesta para revisión: una operación de alta recibe datos, valida el contrato, consulta ocupaciones de los recursos y registra o rechaza el turno. El diseño debe definir si consulta y registro necesitan una operación indivisible según el modelo de ejecución acordado.

```text
Recepción (actor conceptual)
          |
          v
Alta de turno -> validación -> control de ocupación -> registro / error
                                  |
                                  v
                         turnos existentes
```

Este diagrama es funcional; no afirma que existan frontend, servidor, base de datos ni interfaces implementadas. La estructura técnica propuesta se desarrolla en [08](08_arquitectura_propuesta.md).

## Integraciones externas

| Servicio | Propósito | Estado en el primer change |
| --- | --- | --- |
| WhatsApp, pagos y calendarios | Capacidades contrastadas en Discovery | Postergadas; sin conexión |
| ARCA/AFIP | Fuera de alcance | No usar HTTP, SOAP, credenciales ni certificados reales |
| OpenSpec, Active Stack y Engram | Herramientas del proceso académico | No son integraciones clínicas |

No se ejecutan servicios externos del producto. La opción de API no autoriza por sí sola transporte HTTP en este ejercicio: su alcance debe aclararse antes de elegirla.

## API (si aplica)

No hay API, rutas ni endpoints aprobados. Se describen entradas y resultados conceptuales en [04](04_modelo_de_datos.md) y [07](07_flujos_principales.md). Elegir módulo o API sigue pendiente, sin inventar URLs ni contratos REST.

## Infraestructura y confianza

No hay necesidad de infraestructura confirmada para esta porción. Por eso `kb.discovery.needs_infra` usa `false` como valor provisional de baja confianza: **no decide usar memoria ni descarta una base de datos futura**. La elección de persistencia podría cambiarlo. No se seleccionaron Docker, colas, caché, hosting, despliegue ni tareas programadas.

Los campos `system_type`, `stack` y `needs_infra` se mantienen como incertidumbres explícitas en [10](10_preguntas_abiertas.md).
