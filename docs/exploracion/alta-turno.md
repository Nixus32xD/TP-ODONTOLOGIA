# Exploración del alta de turno

Fecha: 2026-10-15. Relevamiento documental previo a Propose; no implementación ni pruebas de producto.

## Qué existe

- Discovery confirmado para recepción de un consultorio pequeño, con varios profesionales y boxes; exclusión de ambos recursos y datos ficticios.
- Diez documentos de KB, roadmap de un change, registro de skills e instrucciones AGENTS/CLAUDE idénticas.
- OpenSpec `spec-driven`, raíz comprobada `N:/Nueva carpeta/TP-ODONTOLOGIA`, artefactos en español y encabezados estructurales en inglés.
- Antes de crear este change, `openspec list --json` y `openspec list --specs --json` devolvieron inventarios vacíos.
- La búsqueda de código/configuración de producto sólo encontró `tools/render_discovery.py`; no hay paquete, API, servidor, DB, tests ni runner configurado del producto. El renderer no es lógica de agenda.
- Runtime documental observado: Python 3.12.14, SQLite 3.53.1 y módulo unittest importable. Importarlos no ejecuta escenarios ni determina por sí solo el stack del producto.

## Opciones y elección propuesta

| Opción | Ventaja | Costo / decisión |
| --- | --- | --- |
| Python + SQLite + unittest, módulo local | Biblioteca estándar, archivo persistente, pruebas sin servidor y menor preparación para la demo | Propuesta preferida; hay que diseñar transacciones y comprobar exclusión entre procesos |
| Python y memoria | Bootstrap mínimo | Descartada para esta propuesta: no conserva turnos entre ejecuciones ni representa el escenario elegido de conexiones independientes |
| Laravel y DB de servidor | Ecosistema de aplicación web completo | Diferida: añade framework/servicio para una sola operación sin UI ni red requeridas |
| Node/TypeScript | Alternativa válida con buenas herramientas | Diferida: agrega decisiones de compilación y acceso SQLite que no aportan al objetivo inmediato |

La elección responde a la porción académica, persistencia observable y ausencia de servicios externos; no se deduce del lenguaje del PDF. No hay benchmark ni comparación de productividad ejecutados.

## Contrato que falta revisar

La propuesta del agente resuelve Q01–Q08 en [design.md](../../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md): módulo, runtime, archivo local, serialización de escrituras, fechas con offset, intervalos semiabiertos, duración positiva libre, todos los turnos persistidos ocupantes, paciente ficticio y prioridad de conflicto. Son decisiones propuestas para revisar, no confirmaciones personales inventadas.

Se acota expresamente qué no se controla: horarios/descansos, disponibilidad, duración por prestación, estados, cancelación, solapamiento del paciente, compatibilidad profesional-box e idempotencia de reintentos. El spec debe hacer observable ese límite y evitar convertirlo en una garantía de producto clínico.

## Fuentes técnicas y comprobaciones

Consultadas el 2026-10-15:

- [Python 3.12: sqlite3](https://docs.python.org/3.12/library/sqlite3.html): módulo estándar, conexión y control de transacciones explícitas.
- [SQLite: transacciones](https://www.sqlite.org/lang_transaction.html): un escritor simultáneo y comportamiento de `BEGIN IMMEDIATE`/`SQLITE_BUSY`.
- [Python 3.12: unittest](https://docs.python.org/3.12/library/unittest.html): organización y descubrimiento de pruebas.

Se intentó resolver documentación mediante Context7; la consulta falló por conectividad y se consultaron directamente las fuentes oficiales. No se probó todavía el algoritmo ni la garantía concurrente. Las pruebas futuras deberán usar procesos reales sobre el mismo archivo local; dos llamadas secuenciales no bastan.
