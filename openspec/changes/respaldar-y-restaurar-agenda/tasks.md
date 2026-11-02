# Tasks

## 1. Versión del producto y formato del manifiesto

- [x] 1.1 Escribir primero pruebas RED para timestamp UTC, versión de formato/app/esquema, nombre y tamaño del payload, hash SHA-256, campos ausentes o extraños y hash alterado; implementar una fuente única de versión de backend (`0.1.0` inicial) y serialización/lectura estricta del manifiesto, triangulando errores incompatibles y documentando su esquema en `backend/README.md`.
- [x] 1.2 Probar con datos ficticios que el manifiesto no contiene URL, ruta origen, contraseña, JWT ni contenido de fichas; ajustar la superficie pública del CLI y verificar mediante inspección del JSON generado y tests que sólo expone metadatos permitidos.
- [x] 1.3 Agregar y validar `table_counts` estricto con tablas del esquema vigente y enteros no negativos; probar campos inválidos y actualizar las pruebas de privacidad y el README del formato.

## 2. Backup coherente de SQLite

- [x] 2.1 Ejecutar pruebas RED con una escritura concurrente confirmada/no confirmada, WAL y transacción fallida; implementar snapshot usando SQLite Online Backup API y triangular que el origen sigue igual, documentando comando y alcance en `backend/README.md`.
- [x] 2.2 Probar archivo ausente, esquema incompatible, integridad o claves foráneas inválidas, ruta de salida existente y fallo a mitad de copia; implementar validaciones fail-closed y staging exclusivo, derivar recuentos desde el snapshot SQLite creado, limpiar sólo staging propio y documentar códigos públicos/resultados esperados.

## 3. Detección y runtime de herramientas PostgreSQL

- [x] 3.1 Escribir pruebas RED para `pg_dump`/`pg_restore` ausentes, error de ejecución, versión mayor discordante con `server_version_num` y argumento malicioso; implementar detección/versionado con `subprocess` sin shell ni exposición de URL/secretos, y documentar prerrequisitos de host.
- [x] 3.2 Incorporar cliente PostgreSQL 16 compatible en la imagen backend sin instalar un servidor, verificar versiones durante build y añadir una comprobación de configuración/runtime que falla antes de abrir salidas; validar el Dockerfile y dejar documentada la diferencia entre adapter y binarios instalados.

## 4. Backup PostgreSQL

- [x] 4.1 Escribir primero pruebas RED de backup custom con esquema vigente, actividad concurrente y rechazo de revisión incompatible; implementar conteos y `pg_dump -Fc` con el mismo snapshot exportado MVCC en staging con proceso seguro, preservar origen/auditoría y actualizar instrucciones de backup PostgreSQL.
- [x] 4.2 Ejecutar integración sólo contra PostgreSQL temporal permitido en loopback; confirmar por restauración aislada que conteos y dump coinciden aunque se confirme una fila concurrente, comprobar `pg_restore --list`, manifiesto/hash, fallos de cliente/major y documentar versiones y límites realmente observados.

## 5. Verificación común de bundles

- [x] 5.1 Escribir pruebas RED para bundle incompleto, manifiesto inválido, hash/tamaño distintos, formato desconocido y revisión de esquema no soportada; implementar `verificar` sin mutaciones y documentar cómo interpretar cada resultado.
- [x] 5.2 Probar hash correcto con payload corrupto/incompatible y `table_counts` inválido; validar SQLite con `integrity_check`, `foreign_key_check` y recuentos del payload, y PostgreSQL en base temporal aislada; registrar que SHA-256 detecta corrupción pero no autentica al creador.

## 6. Restauración segura SQLite

- [x] 6.1 Escribir pruebas RED para destino existente, alias de la base activa, enlace/symlink al origen, ruta inválida y copia incompatible; implementar preflight por ruta normalizada y rechazo sin modificar bytes, origen ni destino, documentando los rechazos.
- [x] 6.2 Implementar restauración a archivo de staging nuevo, verificar integridad, referencias, versión y recuentos antes de publicarlo sólo si el destino sigue ausente; probar fallos inyectados/limpieza y documentar que no se sobrescribe la agenda activa.
- [x] 6.3 Restaurar una copia ficticia en carpeta temporal, abrir una conexión nueva, comprobar filas y ejecutar una alta ficticia; actualizar README y evidencia separando recuperación técnica automatizada de validación humana.

## 7. Restauración segura PostgreSQL

- [x] 7.1 Escribir pruebas RED para base objetivo ya existente/activa, falta de permiso, archivo corrupto, error parcial de `pg_restore` y destino de staging; implementar restore a base staging nueva con `--exit-on-error`, evitar cerrar conexiones externas y no modificar bases preexistentes.
- [x] 7.2 Validar revisión y comparar recuentos de staging con `table_counts`; publicar renombrando a un nombre objetivo previamente ausente sólo tras éxito; en fallo eliminar únicamente staging propio. Probar con cluster temporal aislado y clientes de la misma major, nueva conexión y alta ficticia; documentar permisos/límites y separar evidencia de build PG16.

## 8. Integración y evidencia final

- [ ] 8.1 Ejecutar suite completa de backend, pruebas PostgreSQL aisladas, comandos CLI crear/verificar/restaurar, `pip check`, build de Docker cliente y `openspec validate --all --strict`; corregir sólo defectos de C-12, registrar resultados exactos y confirmar que los datos temporales se limpiaron sin tocar la instancia local.

## 9. Correctivos posteriores a revisión independiente

- [x] 9.1 Agregar primero pruebas RED en POSIX para permisos `0700` del staging y bundle, y `0600` del payload/manifest SQLite y PostgreSQL, observando payload bajo staging y después de publicar; aplicar permisos privados desde la creación sólo en POSIX y conservar ACL heredado en Windows.
- [x] 9.2 Agregar primero prueba RED de la salida exitosa de `crear`; emitir un aviso accionable de datos sensibles y de ubicación fuera del repositorio sin imprimir rutas, URLs ni secretos; mantener la recomendación concreta en README.
- [x] 9.3 Ejecutar las pruebas de permisos en WSL bajo `/tmp` además de las suites Windows; actualizar evidencia con resultados reales, ejecutar focused/full, y conservar 8.1 pendiente si no hay engine para construir Docker.
- [x] 9.4 Probar primero crash/excepción tras preparar staging y colisión que aparece al publicar, incluso un directorio POSIX vacío; publicar el directorio completo atómicamente sin reemplazo en Windows/Linux, conservar intacto destino ocupado, limpiar sólo staging propio y validar ambos adapters en WSL.

## Workflow follow-up

- Revisar el diff y la evidencia de los dos adapters antes de sincronizar la spec.
- Archivar C-12 después de las validaciones y la revisión del change; comprobar el estado archivado.
