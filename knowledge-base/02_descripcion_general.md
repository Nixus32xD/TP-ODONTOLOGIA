# Descripción general

## Estado actual

C-01 implementa el alta de turnos ficticios mediante FastAPI y un módulo de dominio local. C-02 añade PostgreSQL optativo y migración explícita; C-03 añade autenticación y autorización del personal. C-02 y C-03 están implementados y validados localmente, con Archive pendiente. Ver [evidencia técnica](../docs/evidencia/implementacion-turnos.md). Consultorio pequeño, recepción y múltiples profesionales/boxes; escala funcional team, sin SaaS ni multitenencia.

## Stack tecnológico

**Corrección de la cátedra (2026-10-29):** el sistema se trabaja con el stack siguiente, separado en `backend/` y `frontend/`. Ver [DD-09](09_decisiones_y_supuestos.md).

| Parte | Tecnología | Estado |
| --- | --- | --- |
| Backend | Python 3.12+ y FastAPI + Uvicorn | Implementado en C-01 (FastAPI 0.143.2), en `backend/` |
| Backend | JWT para autenticación | Implementado en C-03; Archive pendiente |
| Backend | ORM SQLAlchemy | Implementado en C-02/C-03 |
| Backend | PostgreSQL para persistencia | Optativo; migraciones C-02/C-03 probadas en PostgreSQL temporal aislado |
| Backend | Redis para funcionalidades asincrónicas | Servicio `redis` y `backend/odontologia/workers/`; cola de recordatorios en C-17 |
| Backend | Docker / Docker Compose | `backend/Dockerfile`, `frontend/Dockerfile` y `docker-compose.yml`; despliegue controlado en C-14 |
| Frontend | React + TypeScript + Vite | Estructura inicial en `frontend/`; interfaz de recepción en C-11 |
| Persistencia disponible | SQLite predeterminada; PostgreSQL optativo | C-01–C-03; DDL explícito |
| Pruebas | unittest, TestClient y multiprocessing | 111 tests SQLite; 121 incluyendo PostgreSQL aislado |
| Especificación y flujo | OpenSpec / Active Stack | C-01 archivado; C-02/C-03 activos, pendientes de Archive |
| Herramienta del informe | Python, ReportLab y pypdf | Dependencias documentales separadas del producto |

La decisión parte del [diseño](../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md) y del alcance acotado, no del renderer. FastAPI fue corregido por instrucción explícita del usuario; dependencias fijadas en `backend/requirements.txt` y `backend/requirements-dev.txt` e instaladas únicamente en .venv; `backend/requirements-stack.txt` agrega las del stack de la cátedra. Ver [inventario](../docs/evidencia/entorno.md).

## Arquitectura general

Validar entrada → abrir agenda existente → BEGIN IMMEDIATE → validar referencias y conflictos → insertar → COMMIT → retornar. Una conexión por operación. Ver [arquitectura](08_arquitectura_propuesta.md) y [modelo](04_modelo_de_datos.md).

## Integraciones externas

Ninguna. WhatsApp, pagos, calendarios, ARCA/AFIP, SOAP, credenciales y certificados reales están fuera del producto. OpenSpec y Engram son herramientas del proceso.

## API (si aplica)

API de dominio: inicializar_agenda(ruta_db) y crear_turno con paciente, profesional, box, inicio, fin y timeout. Retorna Turno o lanza ErrorAgenda con código/campo estables. La API añade `POST /sesiones`, `GET/DELETE /sesiones/actual`, `GET/POST /usuarios` y `PATCH /usuarios/{id}`. `POST /turnos` requiere Bearer vigente de Administrador o Recepción; la gestión de usuarios requiere Administrador. Credenciales, sesiones y permisos se validan en el backend. `GET /health` sólo verifica liveness, no DB. `/docs`, `/redoc` y `/openapi.json` documentan los contratos. Crear la app no migra ni crea DB. Demo: `python -m odontologia.demo`.

## Infraestructura y confianza

needs_infra:false significa sin infraestructura externa; Uvicorn sirve la API sólo en loopback; no ausencia de almacenamiento. El uso de JWT no convierte este proyecto en apto para producción ni habilita datos reales; Profesionales no acceden hasta C-08. Pruebas usan datos ficticios y almacenamiento temporal.

Con el stack de la cátedra, PostgreSQL y Redis corren como servicios locales de Docker Compose publicados sólo en 127.0.0.1. C-02/C-03 validaron PostgreSQL de forma aislada; SQLite sigue como valor predeterminado. Redis y funcionalidades de cola permanecen planificados para C-17.
