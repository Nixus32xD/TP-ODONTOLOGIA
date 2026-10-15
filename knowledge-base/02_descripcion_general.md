# Descripción general

## Estado actual

C-01 implementa el alta de turnos ficticios mediante FastAPI y un módulo de dominio local. El usuario pidió publicar la propuesta y continuar con Apply; esa autorización no acredita lectura personal completa del spec. Ver [evidencia](../docs/evidencia/implementacion-turnos.md). Consultorio pequeño, recepción y múltiples profesionales/boxes; escala funcional team, sin SaaS ni multitenencia.

## Stack tecnológico

| Capa | Tecnología | Versión mínima / estado |
| --- | --- | --- |
| Lenguaje y runtime del producto | Python | 3.12+; verificado con 3.12.14 |
| Forma de exposición | FastAPI + Uvicorn | FastAPI 0.143.2; HTTP local, sin proveedores externos |
| Almacenamiento | SQLite mediante sqlite3 estándar | Archivo en disco local; verificado con SQLite 3.53.1 |
| Pruebas del producto | unittest, TestClient y multiprocessing | 53 tests; procesos spawn reales y contrato HTTP |
| Interfaz gráfica | Fuera de C-01 | Demo por consola |
| Especificación y flujo | OpenSpec / Active Stack | Change activo; Archive pendiente |
| Herramienta del informe | Python, ReportLab y pypdf | Dependencias documentales separadas del producto |

La decisión parte del [diseño](../openspec/changes/crear-turno-sin-solapamientos/design.md) y del alcance acotado, no del renderer. FastAPI fue corregido por instrucción explícita del usuario; dependencias fijadas en requirements.txt y requirements-dev.txt e instaladas únicamente en .venv. Ver [inventario](../docs/evidencia/entorno.md).

## Arquitectura general

Validar entrada → abrir agenda existente → BEGIN IMMEDIATE → validar referencias y conflictos → insertar → COMMIT → retornar. Una conexión por operación. Ver [arquitectura](08_arquitectura_propuesta.md) y [modelo](04_modelo_de_datos.md).

## Integraciones externas

Ninguna. WhatsApp, pagos, calendarios, ARCA/AFIP, SOAP, credenciales y certificados reales están fuera del producto. OpenSpec y Engram son herramientas del proceso.

## API (si aplica)

API de módulo: inicializar_agenda(ruta_db) y crear_turno con paciente, profesional, box, inicio, fin y timeout. Retorna Turno o lanza ErrorAgenda con código/campo estables. POST /turnos devuelve 201; errores 422/404/409/503/500. GET /health sólo verifica liveness, no DB. /docs, /redoc y /openapi.json documentan la API. crear_app recibe la ruta de una agenda previamente inicializada; no crea DB al importar. Demo: python -m odontologia.demo.

## Infraestructura y confianza

needs_infra:false significa sin infraestructura externa; Uvicorn sirve la API sólo en loopback; no ausencia de almacenamiento. Garantía limitada al mismo archivo SQLite local y escritores que usen el módulo, sin red compartida ni varios archivos/equipos. Pruebas con temporales locales y procesos reales; no acredita operación clínica o producción.
