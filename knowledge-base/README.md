# TP-ODONTOLOGIA — Base de conocimiento

Generada el 2026-10-15 mediante `kb-creator`, modo de ingestión de documentos. El [Discovery canónico](../discovery/discovery.md) y su [resumen confirmado](../docs/discovery/resumen-para-revision.md) fijan el alcance. La confirmación de los once puntos conserva las preguntas abiertas; no aprueba automáticamente respuestas técnicas.

## Índice de archivos

| Archivo | Contenido |
| --- | --- |
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos, alcance y criterios de éxito |
| [02_descripcion_general.md](02_descripcion_general.md) | Estado actual, stack pendiente e integraciones |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, entidades y permisos conceptuales |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Modelo conceptual y datos ficticios |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas confirmadas y propuestas temporales |
| [06_funcionalidades.md](06_funcionalidades.md) | Historias del primer change y aceptación candidata |
| [07_flujos_principales.md](07_flujos_principales.md) | Alta, conflictos, entradas inválidas y bordes |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Estructura mínima propuesta y límites de seguridad |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Procedencia, estado y riesgos de cada decisión |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Decisiones pendientes y lagunas de evidencia |

## Lectura para continuar

1. Entender el objetivo y los actores: archivos 01 y 03.
2. Revisar el modelo y las reglas: archivos 04 y 05.
3. Resolver las decisiones indispensables para Propose: archivo 10.
4. Revisar funcionalidades y flujos candidatos: archivos 06 y 07.
5. Definir tecnología y diseño mínimo: archivos 02, 08 y 09.

## Resumen ejecutivo

La entrega propia parte de cero y se limita a registrar turnos de un consultorio pequeño con varios profesionales y boxes, rechazando solapamientos de cualquiera de esos dos recursos. WhatsApp, pagos, historia clínica y una interfaz completa quedan para después.

La KB describe requisitos y contrato aplicado; la implementación y sus pruebas se acreditan en el código y la evidencia, no por la mera existencia de estos documentos. La revisión personal de las seis fuentes quedó confirmada por el estudiante el 2026-10-15. C-01 ya implementa módulo Python, SQLite local y exclusión con procesos reales. Ver [evidencia](../docs/evidencia/implementacion-turnos.md). Archive y la entrega académica final siguen pendientes.

## Fuentes y límites

- [Consigna y checklist](../docs/CONSIGNA.md), [bitácora](../docs/BITACORA.md) e [inventario del entorno](../docs/evidencia/entorno.md).
- [Informe Discovery](../docs/discovery/informe-discovery.md), [matriz de evidencia](../docs/discovery/matriz-evidencia.json) y quince fichas con sus referencias públicas.
- [Comprobaciones del agente](../docs/discovery/verificacion-fuentes.md): la revisión personal de las seis fuentes quedó confirmada por el estudiante el 2026-10-15.
- Los PDFs son presentaciones de la consigna y el informe; no agregan aceptación de decisiones ni evidencias de ejecución.

`Confirmado` significa acordado por el usuario o exigido por la consigna. `Propuesta` requiere revisión antes de ser contrato de implementación. `No evidenciado` describe límites de la investigación y no demuestra ausencia de una función.

## Corrección FastAPI — C-01

El usuario corrigió expresamente el stack a FastAPI y autorizó commit/push tras validar, manteniendo sólo C-01. Adaptador POST /turnos, GET /health y OpenAPI reutilizan SQLite. Dependencias fijadas, instaladas en .venv (sin cambios globales); HTTPX para TestClient. Estado previo sin HTTP conserva valor histórico, no describe el producto actual. Baseline43; suite actual53 tests. No se modifica PDF, datos reales ni proveedores externos. Archive y evidencias personales pendientes.
