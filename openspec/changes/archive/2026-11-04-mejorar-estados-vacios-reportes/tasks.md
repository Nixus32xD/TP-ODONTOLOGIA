# Tasks

## 1. Panel y pruebas

- [x] 1.1 Ejecutar baseline de `Reportes.test.tsx` (2/2); agregar casos RED para agenda/finanzas vacías, reporte con datos y error; 2 casos fallaron al faltar `role="status"` y los otros 3 pasaron.
- [x] 1.2 Implementar mensajes `role="status"` por dataset vacío; 5/5 tests focales pasan y error conserva `role="alert"`.
- [x] 1.3 Suite frontend 77/77 en 13 archivos y `npm run build` pasa; los tests de C-20 conservan roles, rutas y CSV.

## 2. Integración y evidencia

- [x] 2.1 Actualizar CHANGES.md, instrucciones/registro de la skill y documentación MCP; incluir consulta Context7 real, comparación de servidores y revisión crítica reproducible.
- [x] 2.2 Actualizar documentación de aplicación/entrega y validar `openspec validate mejorar-estados-vacios-reportes --strict` y `git diff --check`.

## Workflow follow-up

- Archivar el change tras completar las tareas y sincronizar la delta `operational-reporting`.
- Verificar `openspec list --json` y el resultado archivado.
