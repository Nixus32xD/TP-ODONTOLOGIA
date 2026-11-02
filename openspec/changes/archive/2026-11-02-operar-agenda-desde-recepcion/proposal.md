# Proposal

## Why

El repositorio tiene sólo una pantalla técnica para comprobar `GET /health`; Recepción todavía no puede operar la agenda desde una interfaz. C-08, C-09 y C-10 ya exponen consultas y operaciones protegidas, por lo que este change puede presentar ese contrato sin trasladar reglas del backend al navegador.

## What Changes

- Incorporar una interfaz React, TypeScript y Vite con inicio y cierre de sesión para Administrador, Recepción y Profesional; mantener el bearer token sólo en memoria y revocarlo al cerrar sesión.
- Mostrar la agenda diaria y semanal usando `GET /turnos` con rangos offset-aware, filtros y paginación disponibles. Consultar `GET /disponibilidad` para orientar la elección de horario, dejando explícito que el alta vuelve a validar en el servidor.
- Permitir a Administrador y Recepción alta, confirmación, cancelación, atención, ausencia y reprogramación mediante las rutas existentes; usar la versión del turno en C-10 y, ante conflictos o errores, conservar el resultado del servidor y recargar la consulta afectada.
- Permitir a Profesional consultar sólo su agenda vinculada, en modo de sólo lectura y con la proyección de datos limitada por C-08. No se ofrece disponibilidad desde esa vista porque el catálogo de boxes está restringido a Administrador/Recepción y la interfaz no puede seleccionar un box autorizado para esa cuenta.
- Ofrecer formularios mínimos sobre las APIs existentes para seleccionar/crear pacientes, consultar catálogos y consultar/gestionar horarios, excepciones y bloqueos según permisos ya aplicados por la API.
- Mantener navegación por teclado, foco visible y estados perceptibles de carga, vacío, éxito y error. No incorporar dependencias externas de servicios ni crear una segunda implementación de reglas de agenda.
- Mantener las prestaciones como catálogo independiente. No incluir una prestación en el formulario de turno, inferir su duración ni asociarla al turno: el modelo y la API actuales no persisten esa relación.

## Capabilities

### New Capabilities

- `reception-agenda-ui`: Interfaz autenticada para consultar y operar la agenda del consultorio mediante APIs existentes, con privacidad por rol y estados accesibles.

### Modified Capabilities

Ninguna. El change especifica comportamiento nuevo de la interfaz y no altera contratos de backend existentes.

## Impact

- Afecta `frontend/src/`, actualmente scaffold React 18/TypeScript/Vite con una comprobación de salud y sin cliente de sesión ni pruebas de interfaz.
- Consume `POST/DELETE /sesiones/actual`, `GET /sesiones/actual`, `GET /turnos`, `GET /disponibilidad`, `POST /turnos`, operaciones C-09 de estado, `POST /turnos/{id}/reprogramacion` y rutas ya existentes de pacientes, catálogos y disponibilidad.
- No requiere migraciones ni cambios de backend. La agenda semanal se consulta como un rango soportado por C-08; no agrega reglas temporales al frontend.
