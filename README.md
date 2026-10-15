# TP - Gestión de turnos odontológicos

Entrega propia de Metodología I: investigar y desarrollar una funcionalidad de agenda y turnos de pacientes para consultorios odontológicos del mercado argentino, usando Active Stack, OpenSpec y el ciclo OPSX.

Repositorio: [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).

## Estado actual

OpenSpec inicializado y Discovery en revisión: quince sistemas relevados, matriz ponderada y propuesta para un consultorio pequeño. El usuario confirmó como primer change crear turnos evitando solapamientos por profesional y box. Todavía no hay código de producto ni pruebas de comportamiento; el stack y la persistencia se decidirán durante la fundación.

Se ejecutó `openspec init --tools codex --language es --no-animation`: configuración `spec-driven` y seis skills OPSX. Se incorporó `discovery-research` sólo en este proyecto. El estado de Active Stack conserva `version: 4` y `step: discovery`: el informe está para revisar, sin aprobación final ni cierre de la fase.

Para consultar el estado desde PowerShell con OpenSpec disponible en PATH:

```powershell
Set-Location -LiteralPath 'N:\Nueva carpeta\TP-ODONTOLOGIA'
openspec list --json
```

La consulta actual devuelve `changes: []`. Sigue la revisión del informe y de sus once puntos antes de completar el resultado canónico de Discovery y pasar a la base de conocimiento. Los pendientes del entorno y de evidencia quedan documentados para la entrega.

Esta entrega comienza desde cero. El alcance inicial es una funcionalidad terminada de agenda, con datos ficticios y sin integraciones clínicas reales.

## Recorrido de la entrega

0. Preparar el entorno y registrar evidencia real.
1. Iniciar la fundación con Active Stack y OpenSpec.
2. Investigar el mercado y verificar fuentes del Discovery.
3. Generar y revisar la base de conocimiento.
4. Generar y revisar el roadmap.
5. Elegir skills y revisar las reglas del agente.
6. Completar un change: Explore, Propose, Apply, Verify y Archive.
7. Demostrar memoria y recuperación de contexto con Engram.

Se registrarán avances mediante commits y push por hitos. Las revisiones humanas y las decisiones Continuar / Ajustar / Parar acá se documentarán cuando ocurran; no se darán por realizadas automáticamente.

## Documentación

- [Consigna y checklist de entregables](docs/CONSIGNA.md).
- [Bitácora del proceso](docs/BITACORA.md).
- [Inventario y pendientes del entorno](docs/evidencia/entorno.md).
- [Informe Discovery](docs/discovery/informe-discovery.md) y [PDF](docs/discovery/informe-discovery.pdf).
- [Once puntos para revisión](docs/discovery/resumen-para-revision.md).
- [Comprobaciones documentales y revisión personal pendiente](docs/discovery/verificacion-fuentes.md).

## Regenerar el informe PDF

Con Python 3, `reportlab`, `pypdf` y las fuentes Arial de Windows disponibles:

```powershell
python tools/render_discovery.py
```

El comando consolida tablas, calcula los totales y genera el PDF y `matriz-evidencia.json` desde las fichas. No consulta servicios externos ni modifica el estado de Active Stack. La revisión personal de al menos cinco fuentes continúa pendiente.

El README incorporará los pasos de instalación y ejecución de la suite cuando exista la implementación. Todos los ejemplos y pruebas usarán datos ficticios, sin secretos ni datos reales de pacientes.
