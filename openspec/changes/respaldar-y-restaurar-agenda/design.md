# Design

## Context

Ver `proposal.md` para la motivación y `specs/agenda-backup-restore/spec.md` para el contrato. El backend permite SQLite por defecto y PostgreSQL optativo; SQLite llega hasta `auth_schema_version=8` y PostgreSQL hasta Alembic `20261102_0009_turn_rescheduling`. No hay módulo de backup ni restauración. El contenedor actual es `python:3.12-slim` y no instala `pg_dump` ni `pg_restore`.

La agenda contiene turnos, fichas con nombre/teléfono opcional, cuentas, estado de sesiones y eventos de auditoría. Las copias incluyen esas tablas y se consideran sensibles. Los secretos de configuración viven fuera de la base, en variables de entorno/`.env`, y no forman parte del respaldo.

## Goals / Non-Goals

**Goals:**
- Ofrecer comandos locales explícitos para copiar, verificar y restaurar SQLite o PostgreSQL compatibles.
- Evitar snapshots inconsistentes, publicación parcial y sobrescritura de cualquier almacenamiento existente.
- Validar formato, checksum, esquema, integridad y referencias antes de declarar una restauración disponible.
- Probar la operación con bases temporales y datos exclusivamente ficticios.

**Non-Goals:**
- Programar backups, definir retención automática, transmitirlos o administrarlos en un servicio remoto.
- Respaldar `.env`, secretos JWT, logs generales, adjuntos clínicos o ficheros arbitrarios.
- Restaurar encima de una base existente, migrar automáticamente el esquema recuperado o afirmar recuperación productiva.
- Proveer cifrado gestionado, firma criptográfica o protección contra alguien que modifique a la vez el payload y su manifiesto.

## Decisions

1. **CLI manual, separado de HTTP y del arranque.** Añadir un módulo de operaciones de backup invocable desde `backend/`; las órdenes crear/verificar/restaurar reciben rutas y destinos explícitos. La importación de la app y el startup no realizan copias, DDL ni restauraciones. Se eligió un comando local para preservar la superficie API y el control explícito ya usado por las migraciones.

2. **Adapters por motor bajo un contrato común.** Un coordinador valida opciones, genera manifiesto y maneja staging; un adapter SQLite usa `sqlite3.Connection.backup` desde una conexión de lectura para obtener un snapshot consistente incluso cuando hay WAL/escrituras. El adapter PostgreSQL invoca `pg_dump` en formato custom y `pg_restore`, sin interpolar comandos en un shell, y transmite errores mediante mensajes públicos que no exponen URL, credenciales ni consultas. No se copia el archivo SQLite con `shutil.copy` ni se serializan tablas mediante ORM: ambas alternativas omiten garantías de snapshot o de fidelidad del esquema.

3. **Formato versionado y manifiesto junto al payload.** Cada operación genera un directorio bundle nuevo que contiene un payload de motor (`agenda.sqlite3` o `agenda.dump`) y `manifest.json`. El manifiesto registra `format_version`, timestamp UTC, `backend`, `application_version`, `schema_version`, nombre/formato del payload, tamaño, SHA-256 y `table_counts`, un mapa de nombres de tablas actuales a enteros no negativos. Los conteos agregados no contienen valores de filas ni identificadores personales. No incluye URL, ruta de origen, contraseñas ni datos personales. Se define un único `__version__` de backend, con valor inicial `0.1.0` alineado al frontend actual; futuras versiones actualizarán esa fuente explícita. El hash detecta corrupción accidental, no autentica al emisor; el mapa de conteos tampoco ofrece confidencialidad.

4. **Rechazo cerrado para origen, esquema y herramientas.** Antes de leer o escribir, resolver rutas y rechazar formato, versión de esquema o destino no admitidos. SQLite sólo acepta la revisión vigente `8`; PostgreSQL sólo `20261102_0009_turn_rescheduling` hasta que un change posterior amplíe compatibilidad. PostgreSQL consulta la versión mayor del servidor y exige `pg_dump`/`pg_restore` de esa misma versión mayor; detecta binarios y versiones antes de crear artefactos. No aplica Alembic ni repara bases durante backup o restore.

5. **Publicación atómica del bundle sin reemplazar.** Crear payload y manifiesto dentro de staging privado en el mismo volumen, validar ambos y publicar el directorio completo con una primitiva atómica de no-reemplazo. Windows usa `os.rename`, que falla si el destino ya existe; Linux usa `renameat2(RENAME_NOREPLACE)`, que también rechaza un directorio destino vacío. No hay fallback a `os.rename` en POSIX, donde puede sustituir un destino vacío; si la primitiva no está disponible, fallar cerrado. No crear/reservar el directorio final ni mover payload y manifiesto individualmente. Una excepción anterior al rename limpia únicamente staging propio y deja el destino ausente; una colisión concurrente preserva intacto el destino y elimina sólo staging propio. La verificación posterior reabre SQLite en sólo lectura y ejecuta `integrity_check`, `foreign_key_check`, revisión y recuentos; para PostgreSQL inspecciona el archivo custom, verifica hash y restaura en una base aislada antes de declarar el bundle usable.

6. **Restore en staging y destino nuevo.** SQLite restaura el payload a un fichero temporal junto al destino, valida esquema, `integrity_check`, claves foráneas y recuentos, cierra conexiones y publica sólo cuando la ruta objetivo sigue ausente; el origen no se altera. PostgreSQL exige una base objetivo ausente en un cluster explícito. Crea una base de staging con nombre aleatorio, restaura mediante `pg_restore --exit-on-error`, comprueba revisión y recuentos, cierra conexiones y renombra la base de staging al nombre solicitado. Ante fallo, elimina únicamente el staging propio; no termina conexiones ni modifica ni elimina bases existentes. Se requiere permiso explícito para crear bases en el cluster; si no está disponible, rechazar sin fallback.

7. **Runtime de PostgreSQL como requisito separado del adapter.** El adapter comprueba `pg_dump` y `pg_restore`, pero eso no instala los binarios. El Dockerfile debe instalar las herramientas cliente de PostgreSQL 16 compatibles con el servicio Compose actual y verificar versión durante build o test; la guía local exige instalar el cliente de la misma major que el servidor. Si están ausentes o son incompatibles, la operación se detiene antes de abrir salida. Esto evita que las pruebas del adapter den por probada disponibilidad en host/imagen.

8. **Permisos y sensibilidad sin inventar custodia.** Las copias quedan en una ubicación local solicitada por la persona, recomendada fuera del repositorio (por ejemplo, `N:\copias`). Una ruta arbitraria dentro del repositorio no queda excluida automáticamente del control de versiones; quien opera el CLI conserva la responsabilidad de elegir y proteger el destino. No se añade un patrón amplio a `.gitignore`. En POSIX, staging y bundle publicado deben quedar en `0700`; payload y manifiesto, en `0600`, desde la creación hasta después de publicar. Usar modos de creación privados antes de chmod para que staging no se abra a otros usuarios; no cambiar ACL de Windows y no afirmar que se verificó el control de acceso de cada volumen. La salida de `crear` advierte que el bundle contiene datos sensibles y recomienda guardarlo fuera del repositorio, no compartirlo ni subirlo. No se añaden envío, cifrado, claves o purga; retención y borrado quedan bajo control manual.

9. **Mismos conteos y snapshot PostgreSQL.** En SQLite, crear primero el archivo con Online Backup API y derivar `table_counts` leyendo exclusivamente ese snapshot. En PostgreSQL, abrir una transacción `REPEATABLE READ`, comprobar revisión y contar tablas, exportar con `pg_export_snapshot()`, y mantener abierta esa transacción mientras `pg_dump --snapshot=<id>` importa la misma vista. Confirmar/cerrar la transacción después de finalizar el proceso. Así, los conteos y el archivo no divergen por escrituras confirmadas entre ambos pasos. PostgreSQL documenta la exportación/importación de snapshots en [snapshot synchronization](https://www.postgresql.org/docs/16/functions-admin.html#FUNCTIONS-SNAPSHOT-SYNCHRONIZATION) y la opción de snapshot de `pg_dump` en [pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html).

## Risks / Trade-offs

- [Un hash sin firma puede ser recalculado por quien modifique el bundle] → presentarlo como control de integridad accidental, no como autenticidad; cifrado/firma quedan fuera.
- [Instalar cliente PostgreSQL aumenta la imagen y su superficie] → instalar sólo el cliente, fijar major 16 y probar que coincide con Compose; no agregar un servidor PostgreSQL al backend.
- [Permisos insuficientes para crear/renombrar la base PostgreSQL] → comprobarlos y abortar; conservar staging limpio y no degradar a sobrescritura.
- [Una copia local puede extraviarse o ser leída por otro usuario del equipo] → avisar que es sensible y que la protección del medio/ACL debe verificarse en el entorno; no prometer protección gestionada.
- [Restauración técnica en fixture no acredita recuperación humana ni continuidad productiva] → registrar comandos y resultados reproducibles, separar prueba automatizada de prueba personal y no habilitar uso de datos reales.

## Migration Plan

No hay migraciones de esquema ni cambios al arranque. Implementar adapters y CLI sin invocación automática; validar primero en directorios y clusters temporales. Para usar localmente: instalar cliente PostgreSQL compatible sólo si ese motor está seleccionado; generar y verificar un bundle; restaurar a una nueva ruta SQLite o una nueva base aislada PostgreSQL; probar una escritura ficticia posterior. Rollback del ensayo consiste en eliminar exclusivamente el destino temporal de prueba. No se modifica la base activa durante ningún paso.
