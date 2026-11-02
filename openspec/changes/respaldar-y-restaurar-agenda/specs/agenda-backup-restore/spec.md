# Spec Delta

## Purpose

Permite copiar y recuperar una agenda local de forma coherente y verificable, conservando los datos operativos y de auditoría sin sobrescribir el almacenamiento activo.

## ADDED Requirements

### Requirement: Crear una copia coherente de la base seleccionada
El sistema SHALL crear, a pedido explícito, una copia completa y consistente de la base del motor seleccionado. La copia SHALL conservar las filas confirmadas y el historial de auditoría; SHALL NOT incluir archivos de entorno, secretos JWT ni datos fuera de la base.

#### Scenario: Copia SQLite mientras hay escrituras
- **GIVEN** una base SQLite válida con una transacción concurrente en curso
- **WHEN** se solicita una copia manual
- **THEN** la copia contiene un snapshot consistente de transacciones confirmadas, excluye cambios incompletos y la agenda de origen conserva su estado

#### Scenario: Copia PostgreSQL de una versión compatible
- **GIVEN** PostgreSQL está seleccionado, el esquema tiene una revisión soportada y las herramientas de copia requeridas están disponibles
- **WHEN** se solicita una copia manual
- **THEN** se genera un artefacto consistente que conserva los datos y la revisión declarada, sin modificar la base de origen

#### Scenario: Motor o herramientas no disponibles
- **GIVEN** el motor seleccionado no es compatible o falta una herramienta PostgreSQL requerida
- **WHEN** se solicita una copia
- **THEN** se informa un error claro antes de declarar creada una copia utilizable y no se modifica la agenda de origen

### Requirement: Acompañar la copia con un manifiesto verificable
Cada copia SHALL incluir un manifiesto con formato, fecha UTC, motor, versión de aplicación, versión de esquema, recuentos de filas por tabla e integridad SHA-256 del artefacto. El sistema SHALL validar estos datos antes de aceptar una copia para restauración.

#### Scenario: Verificación de una copia íntegra
- **GIVEN** el artefacto y manifiesto corresponden y declaran un formato y esquema soportados
- **WHEN** se verifica la copia
- **THEN** se confirma la integridad y compatibilidad sin modificar el archivo

#### Scenario: Artefacto alterado o incompatible
- **GIVEN** el hash no coincide, falta el manifiesto o el formato/esquema no se soporta
- **WHEN** se verifica o intenta restaurar la copia
- **THEN** se rechaza antes de publicar datos en el destino y se conserva intacto el artefacto original

### Requirement: Vincular recuentos de filas al mismo snapshot respaldado
Cada manifiesto SHALL incluir `table_counts`, un mapa de nombres de tablas del esquema vigente a recuentos enteros no negativos. Los recuentos SHALL representar exactamente el snapshot del payload y no incluir valores de filas, identificadores personales ni otros datos de fichas. PostgreSQL SHALL obtenerlos y ejecutar el dump desde el mismo snapshot MVCC; SQLite SHALL derivarlos del archivo snapshot ya creado. Los recuentos SHALL permitir validar una restauración antes de publicarla.

#### Scenario: Recuentos SQLite corresponden al payload
- **GIVEN** una copia SQLite generada desde una base con cambios concurrentes
- **WHEN** se crea su manifiesto
- **THEN** `table_counts` se calcula leyendo el archivo de snapshot y coincide con las filas confirmadas contenidas, sin leer valores personales

#### Scenario: Recuentos PostgreSQL corresponden al dump
- **GIVEN** una transacción PostgreSQL `REPEATABLE READ` exporta un snapshot y obtiene los recuentos
- **WHEN** `pg_dump` importa ese mismo snapshot mientras la transacción sigue abierta
- **THEN** el mapa y el dump representan la misma vista MVCC, incluso si se confirman nuevas filas en paralelo

#### Scenario: Recuento inválido o distinto al restaurar
- **GIVEN** un manifiesto con nombres ajenos al esquema, valores no enteros o recuentos distintos a los del destino de staging
- **WHEN** se verifica o restaura la copia
- **THEN** se rechaza antes de publicar el destino

### Requirement: Restaurar sólo a un destino nuevo y explícito
El sistema SHALL requerir que la persona identifique el artefacto y un destino que no exista y no corresponda a la agenda activa. SHALL NOT sobrescribir, vaciar ni reemplazar un archivo, base o almacenamiento existente.

#### Scenario: Restauración válida a destino nuevo
- **GIVEN** una copia íntegra y compatible y un destino nuevo explícito
- **WHEN** se solicita su restauración
- **THEN** el sistema prepara y valida el destino antes de dejarlo disponible, sin mutar la fuente ni la base activa

#### Scenario: Destino existente o activo
- **GIVEN** el destino ya existe o resuelve a la agenda actualmente seleccionada
- **WHEN** se solicita la restauración
- **THEN** la operación se rechaza sin alterar el destino, el origen ni la agenda activa

#### Scenario: Fallo durante la restauración
- **GIVEN** una restauración falla antes de completar validación
- **WHEN** termina la operación
- **THEN** no se publica un destino parcialmente restaurado, la copia fuente permanece intacta y se informa que la recuperación no se completó

### Requirement: Validar la agenda restaurada antes de declararla recuperada
El sistema SHALL comprobar integridad del motor, compatibilidad de esquema, restricciones referenciales y recuentos de datos respaldados antes de informar éxito. La verificación SHALL permitir una nueva alta de prueba con datos ficticios en el destino restaurado.

#### Scenario: Integridad y referencias válidas
- **GIVEN** una restauración completada en staging
- **WHEN** se ejecutan las comprobaciones del motor y de datos
- **THEN** las verificaciones de integridad, claves foráneas, versión y recuentos coinciden con el manifiesto antes de publicar el destino

#### Scenario: Prueba posterior de escritura
- **GIVEN** el destino restaurado superó las verificaciones estructurales
- **WHEN** se registra un turno de prueba con datos ficticios en una ejecución aislada
- **THEN** la nueva conexión confirma la fila y la evidencia distingue esta prueba técnica de una restauración real revisada por el estudiante

### Requirement: Tratar las copias como datos sensibles sin purga automática
El sistema SHALL mantener los artefactos en una ruta local explícita, informar que contienen datos sensibles y SHALL NOT transmitirlos a servicios externos ni eliminar copias anteriores automáticamente.

#### Scenario: Copia local protegida
- **GIVEN** se crea una copia de agenda que contiene cuentas, pacientes y auditoría
- **WHEN** se informa su ubicación y estado
- **THEN** se advierte su sensibilidad y no se copian secretos de entorno ni se afirma que cuenta con cifrado gestionado

#### Scenario: Permisos owner-only en POSIX
- **GIVEN** el sistema ejecuta el CLI en un sistema POSIX
- **WHEN** el bundle se prepara y se publica
- **THEN** el directorio del bundle y el staging tienen modo `0700`, y el payload y el manifiesto tienen modo `0600` antes y después de la publicación

#### Scenario: Sin política automática de borrado
- **GIVEN** hay copias locales anteriores
- **WHEN** se ejecuta otro backup o restauración
- **THEN** las copias previas permanecen intactas y no se activa borrado por antigüedad
