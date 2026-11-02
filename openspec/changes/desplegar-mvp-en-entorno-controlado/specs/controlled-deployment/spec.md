# Spec Delta

## Purpose

Define cómo ejecutar la agenda en una red local aislada para una clínica, con configuración explícita, datos ficticios y recuperación comprobable, sin habilitar acceso público.

## ADDED Requirements

### Requirement: Limitar el entorno de demostración a una red local controlada
El paquete SHALL exponer la interfaz y la API sólo en interfaces locales por defecto y SHALL NOT habilitar acceso público, túneles ni servicios externos.

#### Scenario: Inicio local por defecto
- **GIVEN** se inicia el paquete con la configuración de ejemplo
- **WHEN** los servicios publican sus puertos
- **THEN** la interfaz y la API sólo aceptan conexiones desde el host local

#### Scenario: No habilitar publicación pública
- **GIVEN** el paquete está configurado para la demostración de una clínica
- **WHEN** se revisan sus endpoints, dependencias y rutas de red
- **THEN** no hay endpoints accesibles desde Internet ni integración con proveedores externos

### Requirement: Usar PostgreSQL como almacenamiento único en el paquete
El paquete SHALL seleccionar explícitamente PostgreSQL 16 como almacenamiento de agenda y SHALL NOT inicializar ni usar una base SQLite cuando PostgreSQL está seleccionado. Redis 7 SHALL permanecer en la red interna como servicio preparado, sin afirmar que exista un worker de recordatorios.

#### Scenario: Persistencia en PostgreSQL
- **GIVEN** los servicios están iniciados y PostgreSQL tiene el esquema vigente
- **WHEN** se registra un turno ficticio
- **THEN** el turno persiste en PostgreSQL y no se crea una base SQLite de agenda

#### Scenario: Redis disponible sin worker
- **GIVEN** se inicia el entorno de C-14 antes de implementar C-17
- **WHEN** se comprueba Redis y el procesamiento de recordatorios
- **THEN** Redis está accesible sólo dentro de la red del paquete y no se informa ningún recordatorio como encolado o enviado

### Requirement: Aplicar esquema de forma explícita
El sistema SHALL requerir que el operador aplique las migraciones al PostgreSQL de destino y SHALL NOT ejecutar DDL, migraciones ni bootstrap de cuentas automáticamente al iniciar los servicios.

#### Scenario: Arranque con esquema vigente
- **GIVEN** el operador preparó PostgreSQL y aplicó las migraciones documentadas
- **WHEN** inicia la API
- **THEN** la aplicación conserva el esquema y los datos sin ejecutar migraciones implícitas

#### Scenario: Esquema aún no preparado
- **GIVEN** PostgreSQL no tiene el esquema vigente
- **WHEN** se inicia la aplicación antes de aplicar las migraciones
- **THEN** el entorno no declara la agenda lista para operar ni crea o sustituye el esquema por sí mismo

### Requirement: Mantener secretos fuera del repositorio y de las salidas
El entorno SHALL obtener credenciales de operadores, PostgreSQL y JWT de configuración local no versionada. SHALL NOT incluir valores secretos en imágenes, archivos de ejemplo, logs, respuestas de salud o documentación de entrega.

#### Scenario: Configuración de ejemplo
- **GIVEN** se prepara la configuración desde los archivos de ejemplo
- **WHEN** se inspeccionan los valores distribuidos
- **THEN** sólo hay marcadores no utilizables y el usuario debe proporcionar sus valores locales

#### Scenario: Error de configuración
- **GIVEN** falta una credencial requerida o una conexión falla
- **WHEN** el servicio registra o responde al error
- **THEN** no expone contraseñas, URLs con credenciales ni secretos JWT

### Requirement: Verificar operación y recuperación con datos ficticios
Antes de declarar el entorno operativo, el operador SHALL comprobar builds, inicio, readiness, migraciones, un smoke del flujo de recepción y una restauración C-12 en un destino aislado con una escritura ficticia posterior.

#### Scenario: Smoke de recepción
- **GIVEN** el entorno está migrado, listo y configurado con cuentas y datos ficticios
- **WHEN** recepción inicia sesión y registra un turno válido mediante la interfaz
- **THEN** la API confirma el turno y una nueva consulta de agenda lo muestra

#### Scenario: Recuperación aislada
- **GIVEN** existe un backup válido generado por C-12
- **WHEN** se restaura en un destino aislado y se realiza una escritura ficticia
- **THEN** la restauración conserva recuentos y datos del manifiesto, la nueva escritura es observable y no se altera la base activa

#### Scenario: Validación integrada sin Docker
- **GIVEN** no hay un engine Docker disponible o C-12 aún no completó su build de imagen pendiente
- **WHEN** se intenta verificar el paquete integrado
- **THEN** la validación queda pendiente y no se declara el despliegue verificado
