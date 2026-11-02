# Design

## Context

El frontend existente es una aplicación React 18/TypeScript/Vite con una única vista de salud, un `fetch` aislado y proxy `/api` hacia FastAPI. No tiene enrutamiento, estado de sesión ni runner de pruebas. El backend ya expone las operaciones de C-08 a C-10 y C-07, con validación, permisos y persistencia en la API. Ver [proposal.md](proposal.md) y [spec](specs/reception-agenda-ui/spec.md).

## Goals / Non-Goals

**Goals:**

- Añadir una capa de cliente API autenticado, componentes de agenda y formularios pequeños sobre el scaffold sin modificar servicios de dominio.
- Dar la misma semántica a día y semana mediante rangos existentes de `GET /turnos`.
- Mantener autenticación, privacidad por rol, disponibilidad consultiva y respuestas del servidor como autoridad.
- Incorporar pruebas de cliente/componentes y E2E con datos ficticios, más navegación accesible.

**Non-Goals:**

- Cambiar endpoints, contratos, permisos, esquema, decisiones de horarios o reglas de solapamiento.
- Persistir el bearer en `localStorage`, `sessionStorage`, IndexedDB o cookies.
- Crear cuentas, gestionar usuarios del personal, historia clínica, pagos, notificaciones ni datos reales.
- Asociar prestaciones o su duración a turnos, ni replicar cálculo de disponibilidad en el navegador.

## Decisions

1. **Cliente API central y token en estado de aplicación.** Las llamadas protegidas pasan por un módulo tipado que agrega `Authorization: Bearer`, decodifica la respuesta pública de error y notifica 401 a la sesión. Un proveedor/contexto React mantiene token e identidad en memoria; recargar la pestaña exige volver a iniciar sesión. Se eligió esto sobre almacenamiento persistente para cumplir el límite de exposición y el ciclo revocable ya existente. El rol `profesional` también puede iniciar sesión, pero la UI limita su acceso a su agenda C-08 de sólo lectura. No se muestra consulta de disponibilidad al rol porque `/boxes` sólo está habilitado para personal operativo; no se pide ingresar IDs manualmente.

2. **Agenda diaria primero y semana como rango de consulta.** La pantalla diaria será la vista inicial; la semanal enviará a `GET /turnos` un intervalo de siete días, dentro del máximo de 31 días de C-08. Filtros y paginación se envían a la API. Se eligió ampliar a semana porque la API soporta el rango sin añadir una regla de dominio ni reconstruir ocupaciones.

3. **Fecha local y disponibilidad provistas por el contrato de agenda.** Mostrar horarios con `America/Argentina/Mendoza`; serializar cada intervalo a ISO 8601 con offset antes de enviarlo. Usar `Intl` y una función pequeña de conversión local/offset, con pruebas de round-trip; entradas locales inexistentes o ambiguas se rechazan con mensaje, sin corrección silenciosa. Administrador/Recepción seleccionan recursos activos desde catálogos permitidos y consultan `GET /disponibilidad`; `POST /turnos` sigue siendo la validación autoritativa. Professional no recibe esa consulta en la UI: el rol no puede listar boxes, y permitir IDs manuales sería un flujo difícil de usar.

4. **Mutaciones sin optimismo.** Alta, confirmación, cancelación y reprogramación mantienen el estado anterior mientras esperan al servidor, bloquean duplicación del control accionado y sólo después de respuesta exitosa actualizan el estado visible y recargan la consulta. En 409 se conserva la versión renderizada hasta recibir la recarga; la reprogramación siempre envía la versión que devolvió C-08.

5. **Formularios acotados por endpoint y rol.** Reutilizar listas paginadas existentes para seleccionar recursos; permitir alta de ficha mínima de paciente y pantallas simples de catálogo/horarios que correspondan a rutas actuales. Administrador y Recepción comparten las operaciones C-09/C-10 que la API ya autoriza; los controles de escritura, incluidos catálogos y horarios, no aparecen en la vista Profesional. Prestaciones pueden consultarse/administrarse como catálogo separado; el formulario de turno no las incluye ni usa su duración.

6. **Pruebas acordes al scaffold.** Agregar pruebas unitarias/componentes con Vitest 4.1.12 y Testing Library y recorridos E2E con Playwright contra el backend y una base de pruebas aislada con datos ficticios. Vitest 4 requiere Vite 6 y Node 20 o superior; el entorno tiene Node 22.18, por lo que Vite se actualiza a la línea 6 compatible y parcheada y `@vitejs/plugin-react` a 5.0.4, que declara compatibilidad con Vite 6. Esta elección mantiene React 18/TypeScript y el mismo modo Vite; la auditoría tras actualizar las herramientas quedó en cero vulnerabilidades.

7. **Accesibilidad mediante HTML semántico y estados explícitos.** Controles con etiquetas visibles, orden de foco estable, foco visible, errores ligados a campos y región `aria-live` para carga/resultado/error. No se incorporará un sistema de componentes adicional al scaffold.

## Risks / Trade-offs

- [La sesión en memoria termina al recargar] → Solicitar un nuevo inicio de sesión; no ampliar persistencia del token.
- [La disponibilidad puede quedar desactualizada] → Mostrarla como sugerencia y tratar respuesta/conflicto de `POST /turnos` como definitiva.
- [La zona horaria del equipo puede diferir de Mendoza] → Formatear e interpretar fechas usando explícitamente la zona IANA del contrato; rechazar valores locales ambiguos o inexistentes.
- [Las formas de gestión pueden ampliar la superficie operativa] → Limitarse a rutas C-06/C-07 existentes y no introducir permisos ni operaciones de cuenta nuevos.
- [E2E requiere backend y base aislados] → Usar únicamente cuentas y registros ficticios, configuración de prueba y puertos loopback; no apuntar a bases de trabajo ni servicios externos.

## Migration Plan

No hay cambio de esquema ni despliegue de backend. Para desarrollo, conservar el proxy Vite `/api`; configurar la URL existente sólo cuando el entorno difiera. La reversión consiste en revertir el cambio del frontend y sus dependencias de desarrollo. No se cambia la sesión de servidor ni se invalida la compatibilidad de C-01.

## Open Questions

Ninguna. Los formularios son de operación local sobre la API existente; la prestación permanece sin asociación a turnos.
