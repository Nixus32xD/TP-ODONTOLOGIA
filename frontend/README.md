# Frontend — TP-ODONTOLOGIA

Interfaz de recepción. Stack definido por la cátedra: **React + TypeScript + Vite**.

## Estado

Estructura inicial: una página que consulta `GET /health` del backend y lista las pantallas planificadas. Login (JWT) corresponde a **C-03** y la agenda de recepción a **C-11**; ninguna regla de negocio se duplica en la UI: los conflictos los decide el backend.

## Estructura

```text
frontend/
├── src/
│   ├── api/cliente.ts       # Llamadas HTTP al backend (/api → FastAPI)
│   ├── pages/Pendientes.tsx # Pantallas planificadas por change
│   ├── App.tsx
│   └── main.tsx
├── index.html
├── vite.config.ts           # Proxy /api → backend
├── package.json
└── Dockerfile
```

## Ejecutar

```powershell
npm install
npm run dev      # http://localhost:5173 (con el backend levantado en el puerto 8000)
npm run build    # compila TypeScript y genera dist/
```

Con Docker: `docker compose up --build` desde la raíz del repositorio.
