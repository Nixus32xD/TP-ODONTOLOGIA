# Evidencia de implementación C-11 — Interfaz de recepción

## 1. Baseline del frontend

- Checkout inicial sin `frontend/node_modules/` ni `frontend/package-lock.json`.
- Primer `npm run build` en `frontend/`: falló antes de compilar con `"tsc" no se reconoce`, debido a dependencias no instaladas.
- Tras `npm install` de las dependencias existentes: `npm run build` pasó con TypeScript y Vite 5.4.10; 32 módulos transformados.
- La instalación temporal de Vitest 2.1.9 produjo 5 vulnerabilidades de desarrollo (2 moderadas, 1 alta y 2 críticas) según `npm audit`. Se actualizaron las herramientas compatibles a Vite 6.4.5, `@vitejs/plugin-react` 5.0.4 y Vitest 4.1.12; `npm audit` pasó con 0 vulnerabilidades.
- Después de agregar el runner, `npm test -- --passWithNoTests` detectó Vitest 4.1.12 y terminó correctamente sin archivos de prueba, antes de añadir tests de comportamiento.
- Build después de configurar el runner: `npm run build` — Vite 6.4.5, 28 módulos, correcto.

## 2. Pruebas de comportamiento

### Sesión y login

- RED `src/auth/session.test.tsx`: falló al importar `./session`, aún inexistente.
- GREEN/triangulación: sesión para Administrador, Recepción y Profesional; identidad se valida con `GET /sesiones/actual` usando el token sólo antes de guardarlo en estado React. Logout envía `DELETE /sesiones/actual`; una falla igual borra la sesión local y muestra mensaje.
- Se dispara evento de sesión inválida al recibir 401 y el proveedor limpia identidad/token. Prueba asegura que `Storage.prototype.setItem` no se usa y que local/session storage quedan vacíos.
- RED `src/pages/Login.test.tsx`: falló al importar el componente inexistente. GREEN: controles Usuario/Contraseña etiquetados, envío de credenciales a `POST /sesiones`, consulta de identidad y error visible; 2/2 tests.
- RED `src/App.test.tsx`: falló sobre la vista inicial de salud porque no existía login/guardia por rol. GREEN: Administrador/Recepción ven vista operativa; Profesional ve sólo el acceso de consulta, sin controles de alta, transición ni reprogramación. Sesión + login + aplicación: **10/10 tests**; `npm run build` con Vite 6.4.5 pasó.

### Cliente API

- RED: 4/4 pruebas fallaron porque `apiRequest` no existía. GREEN y triangulación añadieron Bearer condicional, JSON/204, error público 409, respuesta de error inválida/503, ausencia de bearer anónimo y error de red neutro: `src/api/cliente.test.ts` **6/6 tests**.

### Consulta de agenda (2.2)

- RED: las pruebas de `src/agenda/Agenda.test.tsx` no resolvían `./Agenda` antes de crear la vista. RED de zona horaria: `tiempo.test.ts` fallaba porque aún no existía `./tiempo`.
- GREEN: `Agenda.tsx` consulta día o semana con límites offset-aware, aplica filtros y paginación mediante `GET /turnos`, presenta los campos operativos o la proyección mínima de Profesional y ofrece consulta orientativa de disponibilidad sólo a Administrador/Recepción con catálogos de recursos.
- Ajuste de alcance verificado: Professional puede iniciar sesión y consultar su calendario propio, sin disponibilidad UI. El endpoint `/boxes` requiere `personal_operativo`; pedirle a Professional IDs de box manualmente no es una interacción adecuada. Se deja esa opción pendiente de una autorización de catálogo en la API, sin cambiar backend.
- `tiempo.test.ts`: día local Mendoza, semana lunes–lunes de exactamente siete días, conversión ISO con `-03:00`, y rechazo de hora inexistente/ambigua en una zona con DST.
- `npm test -- --reporter=dot`: **6 archivos, 25 tests aprobados**; `npm run build`: TypeScript y Vite 6.4.5 correctos (31 módulos).

### Alta de turno (3.1)

- RED: el test de alta no encontró la opción de paciente, porque la pantalla todavía no cargaba fichas activas ni incluía flujo de selección/registro.
- GREEN: la vista carga fichas y recursos activos para Administrador/Recepción, solicita disponibilidad orientativa, permite elegir una opción y registra con `POST /turnos`. El payload contiene únicamente paciente, profesional, box, inicio y fin; no incluye `prestacion_id`.
- La confirmación visual aparece después de recibir respuesta exitosa y recargar agenda. El test deja la respuesta del POST pendiente para demostrar que mientras tanto no se muestra éxito. El caso de conflicto HTTP 409 verifica que no se anuncia alta y se vuelve a consultar la agenda.
- `npm test -- --reporter=dot`: **6 archivos, 27 tests aprobados**; `npm run build`: Vite 6.4.5, correcto (31 módulos). npm se ejecutó con cache/TEMP/logs redirigidos a `N:\CodexTemp` porque C: llegó a cero espacio libre; no se borraron datos.

### Ciclo de vida de turnos y reprogramación (3.2)

- RED: los tests de agenda fallaban al importar la vista/comportamientos que todavía no existían. GREEN: se agregaron confirmar, cancelar, marcar atención, registrar ausencia y reprogramar con la versión vigente del turno.
- Las mutaciones muestran estado pendiente y deshabilitan el control correspondiente; la UI sólo adopta la respuesta confirmada del servidor. En 409 se muestra el error y se recarga la agenda sin aplicar un cambio optimista.
- Recepción y Administrador ven las operaciones; Profesional mantiene su agenda de sólo lectura.

### Pacientes y catálogos (4.1)

- RED: el test de alta no encontraba pacientes ni un flujo de ficha mínima. GREEN: permite seleccionar un paciente activo o crear nombre y teléfono opcional, y selecciona el ID que devuelve la API; no agrega historia clínica.
- Se pueden consultar y administrar campos permitidos de profesionales, boxes y prestaciones conforme al rol. Recepción no puede cambiar estados activos; esa acción queda para Administrador. Los catálogos se recorren con paginación hasta su última página y las altas sólo ofrecen recursos activos.
- Pruebas cubren el payload mínimo, paginación, respuesta del servidor y restricciones por rol.

### Horarios, excepciones y bloqueos (4.2)

- RED: los tests no resolvían la pantalla de disponibilidad. GREEN: la UI consulta/reemplaza los siete días semanales con varios tramos, registra y elimina excepciones (incluido un día cerrado) y registra/elimina bloqueos por las rutas C-07.
- Un 409 por turnos afectados conserva la configuración cargada y muestra el mensaje del backend. Las validaciones de negocio siguen en la API; no se agregó una implementación de disponibilidad en el cliente.

## 3. Accesibilidad, integración y cierre

### Accesibilidad (5.1)

- Vitest verifica navegación de login con Tab, controles etiquetados, anuncio de solicitud pendiente y bloqueo de doble envío; la agenda prueba estado pendiente, 409, recarga y ausencia de actualización optimista. Las vistas informan errores/estados con regiones `role=status` y `role=alert`, además de texto visible sin depender únicamente del color.
- El CSS expone un contorno de foco de 3 px con `:focus-visible`. En Chromium real, Playwright comprobó el ancho computado de 3 px y el orden de foco por teclado; JSDOM por sí solo no demuestra el renderizado visual.

### E2E aislado (5.2)

- Playwright ejecuta Chromium contra Vite y FastAPI en loopback. FastAPI inicia una SQLite temporal aislada con cuentas y registros ficticios; no se conecta a una base de trabajo ni a servicios externos. El teardown elimina sólo directorios temporales con prefijo propio de esta suite.
- Los tres recorridos cubren: navegación/foco; login, agenda, alta, reprogramación, confirmación, cancelación y revocación de sesión (401 tras cerrar); y conflicto de solapamiento creado directamente por API, sin anunciar alta exitosa.
- En este equipo el browser se instaló en `N:\CodexTemp\playwright-browsers`; para reproducir E2E con el disco C: lleno se fijan las rutas antes de ejecutar desde `frontend/`:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = 'N:\CodexTemp\playwright-browsers'
$env:ODONTOLOGIA_E2E_TEMP_ROOT = 'N:\CodexTemp\tp-odontologia-e2e'
$env:TEMP = 'N:\CodexTemp'
$env:TMP = 'N:\CodexTemp'
npm run test:e2e
```

- Sin `PLAYWRIGHT_BROWSERS_PATH`, Playwright intentó buscar headless Chromium en `%LOCALAPPDATA%\ms-playwright` y no encontró el ejecutable. Con la ruta de instalación indicada, los tres E2E pasaron; es una configuración local del equipo, no un fallo de los casos.

### Verificación final (5.3)

- `npm test -- --run`: 9 archivos, **50/50 tests aprobados** (incluye 3 regresiones añadidas tras la revisión).
- `npm run build`: TypeScript y Vite 6.4.5 correctos; **35 módulos transformados**.
- E2E con las variables anteriores: **3/3 pasaron** (7,5 s).
- `npm audit --audit-level=low`: **0 vulnerabilidades**; `npm ls --depth=0`: dependencias directas resueltas sin errores.
- `git diff --check`: sin errores. Backend sin cambios y alta de turno sin `prestacion_id`.
- Estas comprobaciones son locales; no equivalen a despliegue, validación con usuarios ni integración con proveedores externos.

### Correcciones posteriores a la revisión

- RED: al emitir el evento de sesión inválida, la sesión se borraba pero no aparecía mensaje. GREEN: el proveedor ahora comunica que la sesión expiró o dejó de ser válida y pide iniciar sesión de nuevo; la prueba confirma que el aviso accesible acompaña el retorno al login.
- RED: errores locales seguros de fecha inexistente/ambigua, fecha inválida y cruce de medianoche se convertían en un mensaje genérico de agenda. GREEN: se muestran sólo esos mensajes de validación conocidos; los errores desconocidos siguen usando el mensaje neutro para no filtrar detalles internos. Pruebas de reprogramación cubren hora inexistente en `America/Argentina/Mendoza` y cruce de medianoche, y verifican que no se llama a la API.
- RED: al cambiar el profesional/box, mientras respondía el GET de horario el borrador anterior seguía editable y guardar estaba habilitado. GREEN: al cambiar recurso se limpia de inmediato el horario vigente y borrador; Guardar sólo se habilita cuando la respuesta cargada corresponde al tipo e ID seleccionados. La prueba deja la segunda carga pendiente y verifica que no se ve ni puede enviarse el borrador anterior.
- Los tres archivos de pruebas afectados pasaron **28/28 tests**; luego la suite completa pasó **50/50**, el build pasó (35 módulos), E2E pasó **3/3** y la auditoría quedó en **0 vulnerabilidades**. Sin cambios de backend.
