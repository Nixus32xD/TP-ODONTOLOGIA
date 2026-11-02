# Frontend — TP-ODONTOLOGIA

Interfaz en React 18 + TypeScript + Vite. C-11 consume las APIs FastAPI a través del prefijo `/api`; las reglas de agenda y permisos siguen siendo responsabilidad del backend.

## Desarrollo local

Desde `frontend/`, con Node.js instalado:

```powershell
npm install
npm run dev       # http://localhost:5173
npm test          # Vitest, ejecución única
npm run test:watch
npm run build     # TypeScript y bundle de producción en dist/
npx playwright install chromium # una vez para los E2E
npm run test:e2e  # Playwright + API y SQLite ficticias aisladas
```

El servidor Vite espera FastAPI en `http://127.0.0.1:8000`. Para cambiar el destino del proxy:

```powershell
$env:VITE_PROXY_TARGET = 'http://127.0.0.1:8001'
npm run dev
```

El proxy de desarrollo usa el backend local configurado por Vite. No se usa un host distinto configurando las llamadas de la UI: todas pasan por `/api`. Docker/Compose no son necesarios para la entrega.

## Sesión y seguridad del cliente

El bearer de sesión se conserva sólo en memoria de la aplicación. Al recargar la página se debe iniciar sesión otra vez. No guardar tokens ni contraseñas en `localStorage`, `sessionStorage`, IndexedDB, archivos ni logs. Los errores y conflictos deben mostrarse desde la respuesta pública del backend, sin presentar como confirmado un cambio pendiente.

Las pruebas usan datos ficticios. No conectar E2E a una base de trabajo ni a servicios externos.
El comando E2E levanta FastAPI y Vite sólo en loopback, genera una SQLite temporal con cuentas y registros ficticios y elimina esos datos al terminar. Si se necesita reubicar el temporal por espacio en disco, se puede definir `ODONTOLOGIA_E2E_TEMP_ROOT` antes de ejecutar `npm run test:e2e`. `PLAYWRIGHT_BROWSERS_PATH` permite elegir dónde instalar Chromium.

Para instalar Chromium y ejecutar E2E en otra unidad desde PowerShell:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = 'N:\CodexTemp\playwright-browsers'
$env:ODONTOLOGIA_E2E_TEMP_ROOT = 'N:\CodexTemp\tp-odontologia-e2e'
$env:TEMP = 'N:\CodexTemp'
$env:TMP = 'N:\CodexTemp'
npx playwright install chromium
npm run test:e2e
```
