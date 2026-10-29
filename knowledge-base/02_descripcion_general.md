# Descripción general

## Estado actual

C-01 implementa el alta de turnos ficticios mediante FastAPI y un módulo de dominio local. El usuario pidió publicar la propuesta y continuar con Apply; esa autorización no acredita lectura personal completa del spec. Ver [evidencia](../docs/evidencia/implementacion-turnos.md). Consultorio pequeño, recepción y múltiples profesionales/boxes; escala funcional team, sin SaaS ni multitenencia.

## Stack tecnológico

**Corrección de la cátedra (2026-10-29):** el sistema se trabaja con el stack siguiente, separado en `backend/` y `frontend/`. Ver [DD-09](09_decisiones_y_supuestos.md).

| Parte | Tecnología | Estado |
| --- | --- | --- |
| Backend | Python 3.12+ y FastAPI + Uvicorn | Implementado en C-01 (FastAPI 0.143.2), en `backend/` |
| Backend | JWT para autenticación | Estructura en `backend/odontologia/auth/`; C-03 |
| Backend | ORM SQLAlchemy | Estructura en `backend/odontologia/db/`; C-02 |
| Backend | PostgreSQL para persistencia | Servicio `db` en Docker Compose; C-02 migra C-01 |
| Backend | Redis para funcionalidades asincrónicas | Servicio `redis` y `backend/odontologia/workers/`; cola de recordatorios en C-17 |
| Backend | Docker / Docker Compose | `backend/Dockerfile`, `frontend/Dockerfile` y `docker-compose.yml`; despliegue controlado en C-14 |
| Frontend | React + TypeScript + Vite | Estructura inicial en `frontend/`; interfaz de recepción en C-11 |
| Vigente en C-01 | SQLite mediante sqlite3 estándar | Verificado con SQLite 3.53.1; se conserva hasta C-02 |
| Pruebas de C-01 | unittest, TestClient y multiprocessing | 53 tests en `backend/tests/` |
| Especificación y flujo | OpenSpec / Active Stack | C-01 archivado el 2026-10-28 |
| Herramienta del informe | Python, ReportLab y pypdf | Dependencias documentales separadas del producto |

La decisión parte del [diseño](../openspec/changes/archive/2026-10-28-crear-turno-sin-solapamientos/design.md) y del alcance acotado, no del renderer. FastAPI fue corregido por instrucción explícita del usuario; dependencias fijadas en `backend/requirements.txt` y `backend/requirements-dev.txt` e instaladas únicamente en .venv; `backend/requirements-stack.txt` agrega las del stack de la cátedra. Ver [inventario](../docs/evidencia/entorno.md).

## Arquitectura general

Validar entrada → abrir agenda existente → BEGIN IMMEDIATE → validar referencias y conflictos → insertar → COMMIT → retornar. Una conexión por operación. Ver [arquitectura](08_arquitectura_propuesta.md) y [modelo](04_modelo_de_datos.md).

## Integraciones externas

Ninguna. WhatsApp, pagos, calendarios, ARCA/AFIP, SOAP, credenciales y certificados reales están fuera del producto. OpenSpec y Engram son herramientas del proceso.

## API (si aplica)

API de módulo: inicializar_agenda(ruta_db) y crear_turno con paciente, profesional, box, inicio, fin y timeout. Retorna Turno o lanza ErrorAgenda con código/campo estables. POST /turnos devuelve 201; errores 422/404/409/503/500. GET /health sólo verifica liveness, no DB. /docs, /redoc y /openapi.json documentan la API. crear_app recibe la ruta de una agenda previamente inicializada; no crea DB al importar. Demo: python -m odontologia.demo.

## Infraestructura y confianza

needs_infra:false significa sin infraestructura externa; Uvicorn sirve la API sólo en loopback; no ausencia de almacenamiento. Garantía limitada al mismo archivo SQLite local y escritores que usen el módulo, sin red compartida ni varios archivos/equipos. Pruebas con temporales locales y procesos reales; no acredita operación clínica o producción.

Con el stack de la cátedra, PostgreSQL y Redis corren como servicios locales de Docker Compose publicados sólo en 127.0.0.1. C-01 todavía no los usa: su garantía sigue limitada a SQLite hasta que C-02 migre la persistencia y vuelva a demostrar la exclusión concurrente.
