# Tasks

## 0. Desbloqueo y revisión ALTO

- [ ] 0.1 Completar C-12 8.1 en un host con Docker: construir la imagen backend y verificar clientes PG16; cerrar/archivar C-12 en su propio flujo. Verificar `openspec status --change respaldar-y-restaurar-agenda` completo y evidencia del build.
- [ ] 0.2 Confirmar que `docker info` responde en el host de trabajo y obtener revisión humana del plan ALTO antes de tocar configuración. Registrar el resultado de ambos controles; hasta entonces no aplicar C-14.

## 1. Configuración aislada y secretos

- [ ] 1.1 Ajustar Compose para que PostgreSQL sea la persistencia única y el entrypoint no inicialice SQLite en ese modo; verificar en un volumen aislado que no se crea archivo SQLite y que el backend conserva datos en PostgreSQL.
- [ ] 1.2 Limitar servicios a loopback y Redis a la red interna; hacer configurable el puerto host de PostgreSQL. Verificar `docker compose config` y que la configuración efectiva no publica servicios en otras interfaces.
- [ ] 1.3 Mantener credenciales sólo en `.env` local y marcadores no utilizables en ejemplos; verificar que `.env` está ignorado y que imágenes, logs y respuestas de error no muestran secretos.
- [ ] 1.4 Documentar en README arranque, parada, volúmenes, puertos, limitación local, Redis reservado a C-17 y ausencia de worker; verificar que los comandos se corresponden con Compose y no afirman operación pública.

## 2. Imágenes y preparación de datos

- [ ] 2.1 Construir backend y frontend con `docker compose build`; comprobar que ambas imágenes terminan correctamente y que el backend incluye clientes PostgreSQL 16 compatibles con el servidor usado por C-12.
- [ ] 2.2 Documentar y ejecutar migraciones Alembic y bootstrap administrativo como pasos explícitos; verificar que un arranque con esquema ausente no ejecuta DDL/bootstrap y no declara la agenda lista.

## 3. Integración y recuperación

- [ ] 3.1 Iniciar Compose con datos ficticios, comprobar PostgreSQL saludable y `GET /ready`, e incorporar una prueba de fallo de DB; verificar 200 listo cuando responde y no-listo cuando está caída, sin mutación implícita.
- [ ] 3.2 Ejecutar smoke/E2E ficticio de recepción: login, alta y consulta de turno; verificar que la API confirma la operación y una nueva consulta la recupera desde PostgreSQL.
- [ ] 3.3 Crear y verificar backup C-12, restaurar a un destino nuevo aislado y hacer una escritura ficticia; comprobar conteos del manifiesto, preservar la base activa y registrar comandos/resultados en evidencia.
- [ ] 3.4 Ejecutar suite y OpenSpec strict, revisar que los volúmenes existentes no se sobrescriben y que no hay puertos públicos; adjuntar evidencia del entorno y resultado de recuperación antes de considerar Archive.

## Workflow follow-up

- Revisar la evidencia y archivar C-14 sólo después de completar todas las tareas y aprobación humana de configuración ALTO.
- La tarea 0.1 pertenece al change C-12; no marcarla completa en C-14 hasta que C-12 registre el build real y cierre su propio flujo.
