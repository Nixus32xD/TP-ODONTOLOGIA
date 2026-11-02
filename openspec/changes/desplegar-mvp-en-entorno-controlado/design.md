# Design

## Context

Ver `proposal.md` y `specs/controlled-deployment/spec.md`. La configuración actual combina `ODONTOLOGIA_PERSISTENCIA=postgresql` con `ODONTOLOGIA_DB`; el entrypoint inicializa SQLite si falta el archivo. Compose declara PostgreSQL y Redis, pero C-17 todavía no implementa el worker. C-12 sigue en 20/21 y su build de imagen con cliente PostgreSQL 16 no está verificado; el host no tiene engine Docker disponible.

## Goals / Non-Goals

**Goals:**

- Paquete Compose aislado, con PostgreSQL autoritativo y volúmenes persistentes identificables.
- Operaciones explícitas de migración, bootstrap, backup y recuperación, con comprobaciones reproducibles.
- Builds y smoke integrados con datos ficticios antes de declarar el entorno válido.

**Non-Goals:**

- Publicación en Internet, TLS/proxy público, hosting de producción o uso de datos reales.
- Worker de recordatorios, Redis como almacenamiento de agenda o migración automática al arrancar.
- Cambios a contratos de agenda, autenticación, readiness o backup ya especificados.

## Decisions

1. **Compose local y aislado.** Mantener backend y frontend accesibles sólo desde loopback por defecto. No publicar el puerto de Redis al host; mantenerlo en la red interna para C-17. La alternativa de un host público requiere otro change y revisión.
2. **Una sola persistencia activa.** Al elegir PostgreSQL, quitar `ODONTOLOGIA_DB` de la configuración Compose y evitar la inicialización SQLite del entrypoint en ese modo. PostgreSQL 16 guarda los datos en volumen persistente; Redis 7 queda disponible, sin worker ni afirmación de uso funcional. La alternativa de operar ambos motores simultáneamente aumenta ambigüedad y no es necesaria para el MVP.
3. **Preparación y migración explícitas.** Separar levantar servicios, aplicar Alembic y crear la cuenta administradora. El arranque de la API no hace DDL ni bootstrap. Para datos iniciales usar datos ficticios; si se importa una agenda SQLite, usar el flujo explícito C-02 hacia un destino vacío y preservar la fuente.
4. **Secretos sólo locales.** Usar `.env` ignorado y ejemplos con marcadores no utilizables; no copiar secretos a imágenes ni a logs. Alternativas gestionadas externas quedan fuera del entorno de demostración.
5. **Validación en capas.** Antes de smoke, exigir imágenes construidas, PostgreSQL saludable, migraciones aplicadas y `GET /ready` exitoso. Validar luego el recorrido de recepción y, por separado, backup C-12 restaurado a destino aislado con una escritura ficticia. Los tests locales no sustituyen estas pruebas Compose.
6. **Gobernanza ALTO.** Antes de modificar Dockerfiles, Compose, variables o configuración operativa, obtener revisión humana del plan; aplicar sólo tras esa revisión. Esto no es autorización para publicar ni desplegar fuera del host.

## Risks / Trade-offs

- **C-12 incompleto y engine ausente** → bloquear Apply y la validación integrada hasta que el build real pendiente pase y haya Docker disponible.
- **SQLite se inicializa aunque la app use PostgreSQL** → corregir la selección de persistencia y probar en un volumen limpio que no aparece ningún archivo SQLite.
- **Colisión con PostgreSQL local en el puerto host** → permitir configurar el puerto de loopback y documentar cómo elegir uno libre; no abrir el servicio a otras interfaces.
- **Redis puede parecer funcional aunque no haya worker** → documentarlo como infraestructura reservada a C-17 y verificar que C-14 no encola ni reporta recordatorios.
- **La prueba podría confundirse con producción** → utilizar exclusivamente datos sintéticos y declarar el alcance local en README/evidencia.

## Migration Plan

1. Completar C-12 8.1 en un host con Docker; cerrar y archivar C-12 sólo después de sus validaciones correspondientes.
2. Con Docker real disponible y tras revisión HIGH, ajustar configuración manteniendo nombres de volúmenes existentes y corrigiendo persistencia/puertos. No ejecutar el entorno contra bases reales.
3. Crear un entorno aislado de prueba, levantar servicios, aplicar migraciones y bootstrap de forma manual; verificar readiness y smoke ficticio.
4. Ejecutar backup, verificación y restauración a destino nuevo con C-12; hacer una escritura ficticia y guardar evidencia.
5. Ante fallo, detener servicios y preservar volúmenes para diagnóstico. No borrar ni sobrescribir el volumen PostgreSQL; para volver a probar, usar un destino nuevo aislado y el proceso C-12.

La falta de engine Docker es un bloqueo actual para implementar y verificar C-14, no una pregunta diferible dentro de este diseño.
