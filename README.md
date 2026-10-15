# TP - Gestión de turnos odontológicos

Entrega propia de Metodología I: investigar y desarrollar una funcionalidad de agenda y turnos de pacientes para consultorios odontológicos del mercado argentino, usando Active Stack, OpenSpec y el ciclo OPSX.

Repositorio: [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).

## Estado actual

Preparación documental y OpenSpec inicializado con Codex. Todavía no hay código de producto, runtime del proyecto ni pruebas para ejecutar. El stack de la aplicación y una única funcionalidad verificable se elegirán después del Discovery y de la fundación.

Se ejecutó correctamente `openspec init --tools codex --language es --no-animation`: configuración `spec-driven` y seis skills del proyecto para Explore, Propose, Update, Apply, Sync y Archive. El estado de Active Stack tiene `version: 4` y `step: discovery`; indica la siguiente fase pendiente, no un Discovery ejecutado ni una revisión humana aprobada.

Para consultar el estado desde PowerShell con OpenSpec disponible en PATH:

```powershell
Set-Location -LiteralPath 'N:\Nueva carpeta\TP-ODONTOLOGIA'
openspec list --json
```

La consulta actual devuelve `changes: []`. Sigue la revisión humana de la preparación y resolver la disponibilidad de `discovery-research` para iniciar Discovery. Los demás pendientes del entorno y de evidencia quedan documentados para la entrega.

Esta entrega comienza desde cero; los repositorios de referencia sirven para estudiar el proceso. El alcance inicial es una funcionalidad terminada, sin asumir un SaaS completo, autenticación ni facturación fiscal.

Referencias revisadas: [Mateows/TPI-METODOLOGIA](https://github.com/Mateows/TPI-METODOLOGIA) (`20622f44293010d9bd6d8aef5c0a2ea401e55891`, fundación; agenda pendiente) y [Santiago-Btto/TP_ODONTOLOGIA_METODOLOGIA](https://github.com/Santiago-Btto/TP_ODONTOLOGIA_METODOLOGIA) (`438933b193f5b6b9a90e945f634d8315210565f6`, alta de turnos con prevención de solapamientos). No se importan su código, historial ni capturas; las decisiones de producto y tecnología requieren investigación propia.

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

El README incorporará los pasos de instalación y ejecución de la suite cuando exista la implementación. Todos los ejemplos y pruebas usarán datos ficticios, sin secretos ni datos reales de pacientes.
