# Evidencia técnica — C-12 respaldar y restaurar agenda

Fecha: 2026-11-02. Esta evidencia registra verificaciones técnicas con fixtures/base aislada y datos ficticios. No constituye validación humana, recuperación de datos reales ni preparación para producción.

## Contrato aplicado

- Respaldo completo, manual y local para SQLite; PostgreSQL es optativo según la selección ya configurada en C-02.
- SQLite usa Online Backup API y deriva `table_counts` del archivo snapshot. PostgreSQL obtiene sus 14 recuentos y ejecuta `pg_dump --snapshot` desde la misma vista MVCC, manteniendo abierta una transacción `REPEATABLE READ`.
- El manifiesto declara formato, fecha UTC, versión de aplicación/esquema, payload, SHA-256 y recuentos enteros no negativos para las tablas del esquema vigente. No guarda URL, rutas de origen, secretos ni valores/IDs de filas.
- SHA-256 permite detectar corrupción o cambios accidentales del payload; no autentica el manifiesto cuando un atacante puede reemplazar ambos archivos. Los recuentos agregados no ofrecen confidencialidad. El backup contiene datos operativos, cuentas y auditoría y se debe tratar como sensible.
- La restauración requiere un destino nuevo explícito, verifica esquema, integridad, claves foráneas y recuentos en staging, y no sobrescribe la agenda activa ni destinos existentes. No hay copia remota, cifrado gestionado ni purga automática.

## Pruebas automatizadas

Desde `backend/`:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_backup_*.py' -v
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
..\.venv\Scripts\python.exe -m pip check
```

Resultados registrados:

- Suite C-12 enfocada inicial: **57 tests, OK; 1 omitido**. El omitido es el test de symlink; Windows devolvió `WinError 1314` al crear el enlace. El rechazo tiene implementación, pero ese caso no tiene ejecución automatizada en este host.
- Suite completa backend inicial: **328 tests, OK; 2 omitidos**. Esta ejecución no tuvo `ODONTOLOGIA_TEST_DATABASE_URL`, por lo que el módulo de integración PostgreSQL fue omitido; su ejecución aislada se hizo después y se registra abajo.
- `pip check`: `No broken requirements found.`

La suite enfocada cubre esquema/privacidad del manifiesto, campos `table_counts` inválidos, snapshots y escrituras concurrentes SQLite/WAL, herramientas PostgreSQL faltantes/errores/versiones, snapshot exportado, CLI, verificación offline, rechazo de destinos existentes y restauración con post-escritura ficticia.

## Integración PostgreSQL aislada

Se inició un clúster PostgreSQL 18.6 propio, limitado a `127.0.0.1:55432`, con cliente 18.6 (misma major), y se usó sólo la base `odontologia_test` con filas ficticias. No se conectó a la instancia existente de 5432 ni a servicios externos. La suite de integración PostgreSQL se ejecutó con `ODONTOLOGIA_TEST_DATABASE_URL` dirigido exclusivamente a esa base: **41/41 tests OK**. El harness creó y eliminó sus schemas únicos de prueba.

La integración específica C-12 comprobó:

- `crear` produjo un dump custom PostgreSQL de **37.173 bytes**; `pg_restore --list` reconoció **80 entradas**.
- Se insertó una fila ficticia después de exportar el snapshot y antes de `pg_dump`. Tras restaurar en una base nueva, sus **14 recuentos** coincidieron con `table_counts`; la fila posterior al snapshot no apareció en el dump.
- `restaurar` publicó una base nueva con revisión `20261102_0009_turn_rescheduling`; una conexión nueva encontró los datos ficticios y confirmó una inserción ficticia adicional.
- Repetir la restauración hacia el mismo destino fue rechazado como destino existente y la base publicada siguió accesible.
- Un bundle temporal corrompido (con hash actualizado para que la verificación criptográfica simple no bastara) falló al restaurarse; el destino final no se publicó ni quedó staging propio.
- Se restauró `pg_hba.conf` a SCRAM al terminar. `pg_ctl` confirmó que el cluster quedó detenido y el puerto 55432 libre; se eliminó sólo el directorio temporal creado para esta prueba.

Este ensayo demuestra el flujo de software y la compatibilidad del adapter con PostgreSQL 18/cliente 18; no demuestra recuperación ante pérdida real, revisión por el estudiante o compatibilidad del contenedor PG16.

## Alcance del build de imagen

Se intentó desde la raíz del repositorio:

```powershell
docker build -f backend/Dockerfile backend
```

En la fecha de esa verificación, la shell informó que `docker` no era un comando reconocido y no se encontraron Docker, Podman ni Buildah en Windows o WSL. No se ejecutó ni verificó un build PG16. El 2026-11-02 el usuario aclaró que la entrega se demuestra mediante changes y no requiere Docker; por tanto, ese build queda fuera del alcance y no es un pendiente de aceptación. La evidencia de integración PostgreSQL real sigue limitada al cluster ficticio PG18.6 con cliente 18.6.

## OpenSpec y estado

- `openspec validate --specs`: **13/13** pasó tras sincronizar la nueva capability principal `agenda-backup-restore`.
- `openspec validate --all --strict`: **14/14** pasó después de crear la spec principal y completar los documentos de evidencia.
- OpenSpec continúa activo, **16/17 tareas** en ese punto histórico; la única tarea pendiente exigía el build de imagen que el usuario luego quitó del alcance. No se presentó ese build como exitoso.

## Seguimiento de revisión independiente — permisos y aviso CLI

La revisión encontró que con `umask 022` el directorio publicado quedaba `0755`, payload/manifiesto SQLite `0644` y el payload PostgreSQL no se precreaba antes de `pg_dump`. También faltaba un aviso sensible en la salida exitosa de `crear`.

RED se reprodujo en WSL Ubuntu, con los tests usando `tempfile` bajo `/tmp` y `umask 022`: SQLite observó staging `0700` y payload/manifiesto `0644`; PostgreSQL observó staging `0700` y payload ausente al iniciar el dump. Los tests CLI fallaron porque `crear` sólo confirmaba el éxito y no advertía sensibilidad ni ubicación fuera del repositorio.

GREEN: el helper usa creación exclusiva `0600` y `chmod` condicional sólo en POSIX; staging y bundle publicado quedan `0700`, archivos `0600`. Los payloads se crean antes de copiar/dumpear y se vuelven a restringir antes de publicar. En Windows no se cambia el ACL heredado. WSL Ubuntu ejecutó los tests POSIX **2/2 OK** bajo `/tmp` con `umask 022` y de nuevo **2/2 OK** con `umask 0777`; el focused Windows quedó **59 tests, OK; 3 omitidos** (symlink `WinError 1314` y los dos tests POSIX). Los tests CLI pasaron **8/8** y ahora advierten que el bundle contiene datos sensibles y debe guardarse fuera del repositorio sin compartirse.

La suite completa previa a la corrección de publicación pasó **330 tests, OK; 4 omitidos** en 78.178 s. PostgreSQL aislado repitió **41/41 OK** en un clúster nuevo 18.6, cliente de la misma major, loopback 55432. El CLI real creó y verificó un bundle de 37.036 bytes, luego restauró en una base nueva; una consulta confirmó la fila ficticia. Eso confirma que `pg_dump` escribe sobre el payload 0600 precreado. El primer intento CLI no encontró el cliente porque `PATH` del host no lo incluía; al añadir sólo el directorio PG18 al `PATH` de ese proceso, crear/verificar/restaurar pasaron. El cluster se apagó, el puerto se verificó libre y sólo su directorio propio se eliminó.

## Seguimiento de revisión independiente — publicación atómica sin reemplazo

La revisión encontró que crear el destino final antes de moverle payload y manifiesto podía dejar un bundle parcial si el proceso se interrumpía, y que no se había cubierto una colisión concurrente de directorio vacío POSIX. RED se reprodujo con cinco pruebas focalizadas: una excepción después de preparar staging para cada adapter, una colisión tardía con directorio vacío para cada adapter y la primitiva no-replace; inicialmente fallaron las cinco.

GREEN prepara todo el bundle dentro del staging privado del mismo volumen y publica el directorio entero de una vez. Windows usa `os.rename`, validado por la prueba de colisión; Linux invoca `renameat2(RENAME_NOREPLACE)` y falla cerrado si esa primitiva no existe. WSL Ubuntu ejecutó los cinco casos: **5/5 OK**, incluidos ambos adapters, la preservación del directorio vacío y la ausencia de destino tras excepción; la prueba directa confirma que `renameat2` no reemplaza un directorio vacío. Windows focused de C-12: **64 tests OK, 3 omitidos**. Suite completa Windows: **335 tests OK, 4 omitidos**. Los modos POSIX permanecen en staging y tras publicar, sin modificar ACL de Windows.

También se intentó ejecutar toda la batería `test_backup_*.py` con el Python del sistema de WSL: **58 tests, 4 errores**, por dependencias no instaladas en ese intérprete (`sqlalchemy` ausente, además de un atributo de módulo PostgreSQL no cargado al faltar esa dependencia). No es un fallo de las pruebas de publicación, que pasan con ese mismo Python (5/5), ni de permisos POSIX (2/2). La suite enfocada completa se validó en el entorno virtual de Windows, donde sus dependencias están instaladas.

OpenSpec reportó **20/21 tareas completadas** en ese punto histórico. 9.4 quedó marcada tras RED/GREEN y ambas validaciones de publicación. Luego, el usuario aclaró que la entrega no requiere Docker; se retiró esa tarea y C-12 se cerró en 20/20 y se archivó, sin afirmar que el build haya ocurrido.

**Cierre posterior (2026-11-02):** se retiró la tarea de build de imagen del alcance acordado; la validación final local pasó con 361 tests backend y 4 omitidos, PostgreSQL aislado 41/41 previamente, `pip check` limpio y OpenSpec strict 15/15. C-12 quedó 20/20 y fue archivado mediante OpenSpec. No se construyó una imagen Docker; la entrega no requiere contenedores ni despliegue.

## Aclaración de alcance — 2026-11-02

El usuario definió que la entrega consiste en construir el proyecto y presentar sus changes, sin desplegar ni levantar Docker. El build de la imagen PostgreSQL 16 se conserva aquí como antecedente no ejecutado, pero no bloquea la entrega. Las pruebas realizadas corresponden a suites locales, WSL y un PostgreSQL temporal PG18.6; no acreditan un contenedor ni operación real.

**Almacenamiento y control de versiones:** se recomienda una ruta fuera del repositorio (`N:\copias`). El CLI no puede impedir que se indique otra ruta: si el bundle se crea dentro del repositorio, no queda ignorado automáticamente; el operador debe evitar añadirlo al control de versiones. No se añadió un patrón amplio a `.gitignore`.
