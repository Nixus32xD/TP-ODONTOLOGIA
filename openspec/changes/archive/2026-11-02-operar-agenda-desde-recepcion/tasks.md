# Tasks

## 1. Cliente API y pruebas del frontend

- [x] 1.1 Registrar baseline con `npm run build` desde `frontend/` y anotar el resultado en la evidencia del change; agregar Vitest, Testing Library y comandos mínimos de prueba, verificando instalación, detección de tests y build sin cambiar comportamiento.
- [x] 1.2 Escribir primero pruebas RED para el cliente HTTP autenticado (cabecera bearer, respuestas JSON, errores HTTP y 204); implementarlo y triangular respuesta vacía/error sin filtrar datos sensibles, verificando con Vitest.
- [x] 1.3 Actualizar `frontend/README.md` con comandos de desarrollo, pruebas, proxy y límites de almacenamiento de sesión; verificar que cada comando documentado coincide con `package.json`.

## 2. Sesión y consultas de agenda

- [x] 2.1 Escribir pruebas RED de login/logout para Administrador, Recepción y Profesional, carga de identidad, bearer sólo en memoria, expiración/401 y restricciones visuales por rol; implementar el flujo y verificar que no usa almacenamiento del navegador.
- [x] 2.2 Escribir pruebas RED de agenda diaria, rango semanal, filtros, paginación, privacidad del rol Profesional y consulta de disponibilidad para Administrador/Recepción; implementar consulta/renderizado y probar fechas normales, límite del rango y entradas locales ambiguas/inexistentes. No ofrecer disponibilidad a Profesional hasta que la API autorice cargar/seleccionar boxes para ese rol.

## 3. Alta y ciclo de vida de turnos

- [x] 3.1 Escribir pruebas RED para cargar disponibilidad orientativa y crear un turno con duración explícita; implementar formulario/selección y verificar que el payload no contiene `prestacion_id`, el alta usa `POST /turnos` y sólo se muestra éxito tras respuesta confirmada.
- [x] 3.2 Escribir pruebas RED para confirmar, cancelar, marcar atención, registrar ausencia y reprogramar con versión vigente; implementar las cuatro transiciones C-09 y C-10 para Admin/Recepción, y verificar que Profesional no ve acciones de escritura y que 409 recarga sin actualización optimista.

## 4. Fichas, catálogos y disponibilidad configurable

- [x] 4.1 Escribir pruebas RED para elegir/crear ficha de paciente y consultar/administrar campos permitidos de catálogos; implementar formularios mínimos y verificar paginación, filtros de recursos inactivos para altas y permisos según rol.
- [x] 4.2 Escribir pruebas RED para leer/reemplazar horario semanal, crear/eliminar excepción y crear/eliminar bloqueos; implementar formularios sobre rutas C-07 y comprobar que rechazos 409 preservan la configuración mostrada y comunican el error del backend.

## 5. Accesibilidad y validación integrada

- [x] 5.1 Escribir pruebas de navegación por teclado, foco visible, etiquetas, carga/vacío/error y controles pendientes; ajustar la interfaz y verificar los estados sin depender sólo del color.
- [x] 5.2 Configurar recorridos Playwright con datos ficticios y backend/base aislados; probar login, consulta, alta, conflicto desde API, cancelación y reprogramación, y verificar revocación al salir.
- [x] 5.3 Ejecutar `npm test`, `npm run build` y E2E; corregir fallos del change, actualizar README y evidencia con comandos/resultados reales, y confirmar que no se modificó backend ni se agregó prestación a los turnos.

## Workflow follow-up

- Revisar los artefactos y el diff antes de iniciar Apply.
- Archivar C-11 sólo después de implementar, validar y revisar el change.
- Revisión posterior de la implementación: corregidos y probados el aviso de sesión 401, los mensajes seguros de validación de reprogramación y el borrador de horario al cambiar recurso; ver evidencia en `docs/evidencia/implementacion-recepcion.md`.
