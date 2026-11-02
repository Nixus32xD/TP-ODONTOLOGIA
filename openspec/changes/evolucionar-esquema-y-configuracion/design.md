# Design

## Context

`backend/odontologia/agenda.py` implementa C-01 sobre SQLite con una transacción `BEGIN IMMEDIATE`; el esquema usa tres catálogos ficticios y turnos con minutos UTC. `crear_app` recibe SQLite y no conecta al crear la aplicación. La especificación principal `alta-turnos` es el contrato vigente y no se modifica en este change.

## Goals / Non-Goals

**Goals:**
- Incorporar un adapter PostgreSQL con los mismos resultados de C-01.
- Versionar el esquema y ofrecer una importación explícita de la agenda SQLite, sin tocar la fuente.
- Mantener SQLite predeterminado hasta probar la implementación PostgreSQL en un motor de prueba aislado.

**Non-Goals:**
- Autenticación/autorización, cambios de modelo de negocio, doble escritura, migración automática, eliminación de SQLite o cambio del contrato C-01.
- Conectarse a la instancia PostgreSQL preexistente de la máquina, usar datos reales o desplegar servicios externos.

## Decisions

### Selección explícita del backend

Agregar `ODONTOLOGIA_PERSISTENCIA` con valores `sqlite` y `postgresql`. La ausencia del valor mantiene SQLite; la selección PostgreSQL exige `DATABASE_URL` y nunca cae silenciosamente a SQLite. Construir el engine no abrirá una conexión; la app no hará upgrade, seed o importación al crearse ni al iniciar.

**Alternativas:** elegir por la mera presencia de `DATABASE_URL` mezcla configuración con disponibilidad de secretos y cambiaría el comportamiento de Compose inadvertidamente; reemplazar SQLite por defecto rompe las pruebas y herramientas existentes. La selección explícita mantiene compatibilidad mientras se valida PG.

### Versionado del esquema con Alembic

Alembic registra revisiones incrementales y crea las tablas PostgreSQL de pacientes, profesionales, boxes y turnos. Los minutos UTC se mantienen como enteros; el ID de turno es `BIGINT` identity. La primera revisión agrega una fila única de sincronización para serializar altas. Las revisiones se aplican únicamente mediante un comando explícito.

**Alternativas:** una tabla de versión casera duplica herramientas de revisión, orden, estado y upgrade; inicializar tablas en `create_app` mezcla cambios de esquema con la vida del proceso.

### Exclusión concurrente equivalente a C-01

Cada alta PostgreSQL abre una transacción, fija `lock_timeout`, bloquea `agenda_mutex` con `SELECT ... FOR UPDATE`, valida referencias y conflictos en el orden profesional/box, inserta y confirma. El bloqueo global conserva la serialización que SQLite obtiene con `BEGIN IMMEDIATE` y simplifica el orden de errores para el consultorio pequeño. Los fallos anteriores al commit se revierten; el agotamiento de espera se mapea a `agenda_ocupada`.

**Alternativas:** bloqueos por recurso permiten más concurrencia, pero exigen un protocolo de orden estable para evitar interbloqueos y ampliar pruebas. Una restricción GiST requiere extensión/tipos específicos y aún debe preservar la prioridad determinista de errores. La fila singleton reduce concurrencia de escrituras, acorde con el scope actual.

### Importación manual y no destructiva

La operación de importación abre SQLite en modo sólo lectura, comprueba el esquema y la integridad referencial de C-01, requiere que Alembic esté en la revisión vigente y que las tablas de negocio del destino estén vacías, y copia todas las filas dentro de una única transacción PostgreSQL. Conserva los IDs; actualiza la secuencia de turnos antes del commit. No elimina ni renombra archivos y nunca sobrescribe datos del destino. El esquema (DDL) se prepara con `alembic upgrade head` como paso separado y explícito.

**Alternativas:** migrar al inicio de la API puede duplicar filas o ejecutarse con credenciales de runtime; reemplazar el archivo SQLite o hacer dual-write deja ambiguo qué fuente es autoritativa. Se conservan SQLite y los datos originales como rollback operativo.

### Pruebas de PostgreSQL

Las pruebas unitarias y de API existentes continúan sobre SQLite. Las pruebas de migración y multiproceso PostgreSQL usarán una URL de base dedicada a tests, exigirán un esquema temporal de nombre único y eliminarán únicamente ese esquema al terminar. Si no se configura esa URL, las pruebas de integración se omiten con motivo visible; su omisión no demuestra compatibilidad ni permite cambiar el backend predeterminado.

**Alternativas:** probar sólo dialecto SQLite no verifica bloqueos `FOR UPDATE`, SQL PostgreSQL ni códigos de error reales. La instancia que actualmente escucha en el puerto 5432 no se usará; se desconoce su dueño funcional y no está autorizada como base de test.

## Risks / Trade-offs

- **[Riesgo]** La serialización global limita throughput. → Mantenerla mientras el producto sea un consultorio pequeño; cambiar a locks por recurso requiere otro diseño y pruebas de interbloqueo.
- **[Riesgo]** Un origen SQLite manipulado o incompatible podría perder filas al importar. → Abrir en modo lectura, validar tablas, claves foráneas y checks; rechazar inconsistencias y comprobar conteos/IDs dentro de la transacción.
- **[Riesgo]** Un usuario puede seleccionar PG antes de preparar el esquema. → Fallar con error público y conservar SQLite sólo cuando esté seleccionado explícitamente; no hacer fallback silencioso.
- **[Riesgo]** La integración real PG puede no estar disponible en todos los equipos. → No afirmar validación PG cuando la prueba de integración se omite y mantener SQLite como modo predeterminado hasta ejecutarla en un motor aislado.

## Migration Plan

1. Hacer copia de seguridad de la agenda SQLite fuera del repositorio y confirmar que contiene sólo datos ficticios. El change no crea esa copia automáticamente.
2. Preparar una base PostgreSQL vacía exclusiva y ejecutar `alembic upgrade head` explícitamente.
3. Ejecutar el comando de importación con la ruta SQLite y la URL PostgreSQL seleccionadas; revisar el resumen de filas importadas.
4. Verificar conteos, IDs e intervalos, ejecutar pruebas de concurrencia PostgreSQL y sólo entonces configurar la aplicación con backend `postgresql`.
5. Ante un resultado dudoso, no repetir sobre el destino poblado; mantener la fuente SQLite y seleccionar explícitamente SQLite. No hay dual-write ni borrado automático.

En este entorno no se habilita el backend PostgreSQL por defecto ni se ejecuta la importación sobre una base preexistente. El paso 4 requiere evidencia en un PostgreSQL de prueba aislado antes de considerar el backend listo para desplazar a SQLite.
