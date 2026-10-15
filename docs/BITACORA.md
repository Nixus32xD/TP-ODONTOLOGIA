# Bitácora del proceso

## 2026-10-15 - Preparación

- **Decisión del usuario:** construir una entrega propia desde cero; usar los dos repositorios proporcionados como referencia.
- **Destino:** [Nixus32xD/TP-ODONTOLOGIA](https://github.com/Nixus32xD/TP-ODONTOLOGIA).
- **Publicación autorizada:** realizar avances con commit y push por hitos, conservando un historial del proceso.
- **Trabajo de esta etapa:** documentación inicial, checklist de la consigna e inventario del entorno. Todavía no hay código de producto ni pruebas.
- **Alcance posterior:** Discovery y fundación para seleccionar una sola funcionalidad verificable. El stack y el change aún no están decididos.
- **Revisión del usuario:** pendiente. No se registra Continuar, Ajustar ni Parar acá hasta recibir una decisión real.

Cada entrada posterior debe indicar qué cambió, evidencia disponible, resultado de la revisión y siguiente paso. Los commits y resultados de ejecución se anotan después de ocurrir.

## 2026-10-15 - Inicialización de OpenSpec

- **Primer hito publicado:** commit `fd8c209`, preparación documental, enviado mediante `git push -u origin main` al repositorio de entrega con resultado exitoso.
- **Comando ejecutado:** `openspec init --tools codex --language es --no-animation`, código de salida 0.
- **Resultado:** `openspec/config.yaml` con esquema `spec-driven` y seis skills en `.agents/skills/`: Explore, Propose, Update Change, Apply Change, Sync Specs y Archive Change.
- **Estado de Active Stack:** versión 4, `step: discovery`. Es la siguiente fase pendiente; no acredita investigación realizada ni revisión humana aprobada.
- **Validación:** `openspec list --json`, código de salida 0, devolvió `changes: []` para `N:/Nueva carpeta/TP-ODONTOLOGIA`.
- **Comprobaciones adicionales:** `openspec validate --all --json`, código de salida 0, validó 0 elementos porque todavía no hay specs ni changes. El JSON del estado se parseó correctamente. Estas comprobaciones no son tests de producto; todavía no existe implementación.
- **Pendientes:** revisión del usuario, disponibilidad de `discovery-research`, Go, evidencia del modo Full y capturas. El video y la evidencia de recuperación de memoria corresponden a etapas posteriores.
- Este hito se versiona junto a configuración, estado y skills; la publicación se comprueba contra el SHA remoto después del commit.

## 2026-10-15 - Continuar a Discovery

- **Revisión del usuario:** después de los dos avances publicados, respondió «Dale» a continuar con Discovery e incorporar `discovery-research` solamente en este proyecto.
- **Hito anterior publicado:** `00eaa9b99442598cb90c40f349501171c222080a`; SHA local/remoto comprobado y carpeta limpia antes de este avance.
- **Skill incorporada:** `Group-Active-IA/discovery-research`, commit `dd7efb7d044ea3a683b6665a3df9d949856b417f`, bajo `.agents/skills/discovery-research`, sin instalación global.
- **Ajuste:** el proveedor todavía usa `jr-orchestrator`; se sustituyó mecánicamente por `active-orchestrator` para conservar un único estado. Se conserva la licencia y se documenta la procedencia en la skill.
- **Método:** lectura pública de fuentes oficiales; no se ejecutó `web-scraper`, no se contactan proveedores ni se crean cuentas. Las fichas y el informe serán material para revisión, no pruebas de ejecución del producto.
- **Pendiente:** revisar el informe y confirmar los once puntos antes de escribir `discovery/discovery.md` y la sección `state.discovery`. La aprobación de inicio no equivale a aprobación de resultados ni a verificación personal de fuentes.

### Enfoque confirmado durante la investigación

- El usuario confirmó: «Sí, consultorio pequeño y primer change de turnos».
- Recepción gestionará turnos de varios profesionales y boxes; se propone como primer change crear un turno evitando solapamientos por profesional y por box.
- WhatsApp, pagos e historia clínica quedan para etapas posteriores. La propuesta del agente y la confirmación se registraron antes de sintetizar el MVP.
- No se decidió todavía stack, API frente a módulo, persistencia ni una garantía de concurrencia. Estos puntos deben quedar explícitos para la fundación y el diseño.

### Investigación documental y revisión cruzada

- Se redactaron quince fichas de producto en `docs/discovery/fuentes/`, más las referencias del marco argentino, con fecha 2026-10-15 y fuentes públicas oficiales.
- Se añadieron seis comprobaciones documentales del agente en `docs/discovery/verificacion-fuentes.md`; la comprobación personal del estudiante sigue pendiente.
- La revisión cruzada corrigió motivos y puntajes de integraciones: WhatsApp y oferta local no se deducen de Google Calendar, APIs genéricas ni integraciones de otros países. Los totales se calculan desde los siete puntajes registrados, no a partir de estimaciones previas.
- Se distinguieron GESDEN ONE/G5, anuncios en prelanzamiento, doble reserva advertida frente a rechazada y pagos de suscripción frente a cobros clínicos.
- Las lecturas divergentes de condiciones Denteo se conservaron como incertidumbre; no se decidió arbitrariamente qué versión era definitiva.
- **Estado:** investigación e informe para revisión. No se ha aprobado el resumen final ni se escribió la sección `state.discovery`.
