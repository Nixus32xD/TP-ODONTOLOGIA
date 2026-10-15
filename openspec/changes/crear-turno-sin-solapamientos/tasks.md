# Tasks

El usuario autorizó continuar con Apply después de presentar la propuesta. Los checkboxes registran ejecución comprobada del agente; no acreditan lectura personal del spec ni Archive. En Apply cada comportamiento sigue RED ejecutado → GREEN mínimo → triangulación con al menos dos casos → refactor verde; registrar baseline y tabla de evidencia en `docs/evidencia/implementacion-turnos.md`. No escribir código de producto en Propose.

## 1. Preparación ficticia y runner

- [x] 1.1 Comprobar el runtime elegido y crear el primer test de bootstrap que falle por implementación inexistente; añadir sólo el paquete mínimo para hacerlo pasar. Verificar con unittest que la nueva agenda contiene seis recursos y cero turnos, y que repetir bootstrap sobre archivo existente preserva sus datos; documentar runtime/comando y evidencia RED/GREEN.
- [x] 1.2 Probar primero la apertura de agenda ausente y fallo de ruta, implementar su rechazo sin creación implícita y comprobar desde disco que no se creó otro archivo. Registrar al menos dos casos, código `almacenamiento_error` y límite de rutas locales; ejecutar suite existente del grupo.

## 2. Alta válida, entradas e instantes

- [x] 2.1 Escribir y ejecutar RED para alta válida/resultado persistido; implementar alta mínima y comprobar referencias, ID positivo, UTC y exactamente una fila, también al reabrir conexión. Añadir segundo intervalo distinto y documentar firma del módulo y retorno; suite verde antes de continuar.
- [x] 2.2 Probar IDs vacíos, espacios extremos, longitud 64/65, tipo incorrecto y referencias desconocidas de paciente/profesional/box; implementar validación y orden de errores sin recortar. Verificar códigos/campos, cero altas ante rechazo y al menos dos entradas distintas por comportamiento; documentar el contrato de errores junto a los tests.
- [x] 2.3 Probar intervalos vacíos/invertidos, fechas sin offset, tipos incorrectos, segundos/microsegundos y offsets equivalentes; implementar normalización UTC/minutos sin float ni redondeo. Verificar inicio/fin exactos persistidos, prioridad de errores temporales y al menos dos casos válidos distintos; actualizar ejemplos con offset explícito y ejecutar suite.
- [x] 2.4 Probar timeout positivo configurable y rechazos de cero, negativos, infinito, NaN, booleano y cadena antes de acceder al archivo; implementar mínimo, verificar `entrada_invalida`/campo timeout y documentar default 5s y que no es deadline global.

## 3. Exclusión de recursos y bordes

- [x] 3.1 Escribir RED para conflictos parciales, intervalos iguales y ambas contenciones del profesional con box distinto; implementar exclusión dentro de la transacción y comprobar `conflicto_profesional` y conservación de filas. Documentar predicado y ejecutar suite, sin una prueba tautológica del mismo código.
- [x] 3.2 Escribir RED para los mismos patrones del box con profesional distinto y conflicto de ambos recursos mediante turnos independientes; implementar exclusión y prioridad profesional. Verificar códigos, ausencia de alta y registros previos intactos; documentar la prioridad y ejecutar suite.
- [x] 3.3 Probar adyacencia anterior/posterior y simultaneidad con ambos recursos distintos; completar comportamiento mínimo, comprobar dos filas válidas y ausencia de falsos conflictos. Añadir cruce de medianoche y mismo paciente con recursos distintos según exclusiones del spec; documentar esos límites y ejecutar suite.

## 4. Transacción, fallos y competencia real

- [x] 4.1 Probar fallo controlado de almacenamiento anterior al commit y reapertura posterior; asegurar rollback y cierre sin ocultar el error original. Usar DB temporal real y condición reproducible de fallo, sin hook público exclusivo del test; comprobar cero filas fallidas y que la agenda siga usable. Registrar comandos y evidencia, y ejecutar suite.
- [x] 4.2 Probar contención mantenida por otra conexión con timeout corto y timeout inválido cubierto en 2.4; verificar `agenda_ocupada`, ninguna alta y alta posible tras liberar el lock. Implementar mapeo BUSY/LOCKED sin reintentos implícitos, documentar alcance y ejecutar suite con esperas acotadas.
- [x] 4.3 Escribir RED multiproceso `spawn` con workers importables y coordinación explícita sobre un mismo archivo local, primero por profesional y luego por box. Completar serialización consulta/registro; verificar un éxito, un conflicto del recurso esperado, códigos de salida y una sola fila en ambos escenarios, con timeout suficiente y joins acotados. Registrar plataforma, repeticiones y resultados; no declarar garantía si se omite/falla el caso.
- [x] 4.4 Probar repetición de una solicitud confirmada y error de archivo no accesible con entradas válidas; comprobar conflicto determinista en el primer caso y `almacenamiento_error` sin archivo alternativo en el segundo. Documentar ausencia de idempotencia, de reconciliación ante fallos extremos y de garantía sobre escritores externos; ejecutar suite.

## 5. Demostración e integración final

- [x] 5.1 Crear demo local con agenda temporal propia que ejercite alta, conflicto de profesional, conflicto de box y adyacencia sin red; verificar su salida y no persistencia fuera de su temporal. Documentar comandos reproducibles `python -m odontologia.demo` y `python -m unittest discover -s tests -v` en README.
- [x] 5.2 Trazar cada escenario del spec a tests concretos, ejecutar toda la suite y la demo desde checkout limpio de datos, y completar tabla TDD/limitaciones reales. Verificar que no haya secretos, DB generadas ni datos reales versionados y que AGENTS/CLAUDE/KB describan el contrato efectivamente aceptado; no marcar tareas con pruebas fallando.

## 6. Corrección FastAPI solicitada por el usuario (mismo C-01)

- [x] 6.1 Exponer POST /turnos mediante FastAPI reutilizando crear_turno, respuesta 201 persistida y validación JSON estricta sin coerción de IDs ni timestamps. Ejecutar RED antes del adaptador y verificar al menos dos solicitudes válidas/invalidas.
- [x] 6.2 Mapear errores de dominio a HTTP 422/404/409/503/500, comprobar conflictos independientes, adyacencia, desconocidos, bloqueo y fallo real de almacenamiento sin insertar ni filtrar detalles internos.
- [x] 6.3 Exponer GET /health de liveness y documentación OpenAPI, fijar dependencias locales, documentar arranque explícito sin crear DB al importar, sincronizar instrucciones/KB y ejecutar suite completa, demo, smoke local y validación estricta. Mantener Archive y evidencias personales pendientes.

## Workflow follow-up

- Conservar revisión humana real de Propose y los ajustes solicitados; no inventar una aprobación ni un error para el video/reflexión.
- Una nueva petición para Apply inicia la implementación; presentar primero cualquier ajuste material requerido al contrato.
- Después de pruebas y revisión, ejecutar Archive mediante OpenSpec, verificar sincronización de la spec principal y marcar C-01 completo sólo con resultado confirmado. Archive no forma parte de los checkboxes de implementación.
- Q09–Q10 y evidencias académicas siguen pendientes: no se sustituyen con tests, memoria o ejecución del agente. Push/publicación requieren autorización explícita aplicable.
