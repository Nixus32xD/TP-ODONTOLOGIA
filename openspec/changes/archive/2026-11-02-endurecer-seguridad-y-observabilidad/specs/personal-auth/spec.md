## ADDED Requirements

### Requirement: Limitar intentos fallidos de inicio de sesión
El sistema SHALL limitar en memoria los fallos de autenticación por dirección de origen y hash de cuenta normalizada. Tras cinco fallos en una ventana móvil de cinco minutos, SHALL responder HTTP 429 con `Retry-After` hasta que expire el fallo más antiguo. Un login exitoso SHALL limpiar los fallos confirmados; los contadores SHALL expirar y SHALL NOT producir bloqueos permanentes.

#### Scenario: Se alcanza el límite de fallos
- **GIVEN** cinco intentos fallidos para la misma dirección de origen y cuenta normalizada durante cinco minutos
- **WHEN** llega otro intento para esa combinación antes de expirar la ventana
- **THEN** responde HTTP 429 con `Retry-After` positivo y no verifica credenciales

#### Scenario: Expira el límite temporal
- **GIVEN** una combinación limitada cuyos cinco minutos ya transcurrieron
- **WHEN** llega un nuevo intento
- **THEN** el intento puede verificarse normalmente y no existe un bloqueo permanente

#### Scenario: Inicio de sesión exitoso limpia fallos previos
- **GIVEN** una combinación con fallos previos pero sin un límite activo
- **WHEN** el usuario inicia sesión correctamente
- **THEN** el contador de fallos de esa combinación se limpia

#### Scenario: No se confía en headers de proxy
- **GIVEN** dos peticiones con valores distintos de `X-Forwarded-For` pero la misma dirección de conexión
- **WHEN** ambas fallan al iniciar sesión para la misma cuenta normalizada
- **THEN** se contabilizan bajo la misma dirección de conexión, sin usar el header reenviado

#### Scenario: Estado temporal no persistido
- **GIVEN** ocurre un fallo de autenticación
- **WHEN** se actualiza el control de intentos
- **THEN** no se persiste la IP ni el identificador de cuenta

### Requirement: Reservar capacidad para verificaciones concurrentes
El sistema SHALL reservar atómicamente hasta cinco verificaciones de credenciales activas por dirección de origen y hash de cuenta normalizada antes del trabajo de contraseña. Un intento concurrente adicional SHALL responder 429 con `Retry-After`. Errores de validación o disponibilidad SHALL liberar su reserva sin contar como fallo. Un login exitoso SHALL limpiar fallos confirmados sin descartar otras verificaciones activas.

#### Scenario: Intentos concurrentes limitados antes de verificar
- **GIVEN** seis intentos con la misma dirección de origen y cuenta normalizada llegan mientras se verifican contraseñas
- **WHEN** el límite reserva espacios de verificación
- **THEN** como máximo cinco llegan a la verificación de credenciales y el restante recibe HTTP 429 con `Retry-After`

#### Scenario: Éxito o indisponibilidad libera reservas correctamente
- **GIVEN** existen verificaciones simultáneas para la misma combinación
- **WHEN** una finaliza correctamente o falla por indisponibilidad de la base
- **THEN** el éxito limpia los fallos confirmados conservando otras verificaciones activas, y el error de base libera su espacio sin contar como fallo

#### Scenario: Límite local al proceso
- **GIVEN** la aplicación ejecutada con la configuración de un solo proceso Uvicorn del proyecto
- **WHEN** ocurren fallos de autenticación
- **THEN** el control se aplica en memoria de ese proceso y no afirma coordinación entre múltiples procesos o instancias
