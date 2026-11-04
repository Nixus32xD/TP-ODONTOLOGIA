---
name: odontologia-openspec
description: Revisa, propone y verifica cambios OpenSpec para el sistema odontológico de este repositorio. Usala cuando se trabaje en changes, endpoints, agenda, pacientes, clínica, finanzas, reportes o sus pruebas; aplica las reglas del proyecto y conserva la trazabilidad entre contrato, implementación, evidencia y roadmap.
---

# Changes OpenSpec para el sistema odontológico

## Objetivo

Ayudar a evolucionar este sistema respetando los contratos aprobados, el roadmap y la separación entre evidencia técnica y aceptación humana. Esta skill guía el trabajo; no reemplaza OpenSpec CLI, los tests ni las decisiones del equipo.

## Procedimiento

1. Lee `AGENTS.md`, `CHANGES.md` y los documentos de Knowledge Base indicados por el change. Comprueba el estado del checkout antes de editar.
2. Consulta `openspec list --json` y el estado del change con `openspec status --change "<nombre>" --json`. No infieras estados por nombres de carpetas.
3. Identifica dependencias, alcance, exclusiones y nivel de governance. Para políticas CRÍTICAS o ALTAS aún no acordadas, presenta la decisión material antes de implementarla; no amplíes el contrato por conveniencia.
4. Conserva backend en `backend/` y UI en `frontend/`. Reutiliza adaptadores y servicios existentes; nunca agregues datos clínicos reales, credenciales o llamadas a proveedores externos.
5. Sigue el ciclo de pruebas del proyecto: baseline, prueba que falle para el comportamiento nuevo, cambio mínimo, casos límite y suite relevante. No marques tareas ni afirmes ejecuciones que no observaste.
6. Al verificar, relaciona cada escenario con código, prueba y resultado. Una carpeta archivada o un checklist marcado no sustituye la ejecución.
7. Antes del commit, revisa diff y estado Git; separa cambios ajenos. Push sólo si la instrucción vigente lo autoriza explícitamente.

## Salida al revisar o planificar

- Estado observado y comando/fuente usado.
- Alcance incluido y excluido.
- Contratos o decisiones que requieren resolución.
- Archivos/componentes afectados y pruebas que demostrarían el resultado.
- Evidencia realizada y limitaciones, sin atribuirla al estudiante si la ejecutó el agente.

## Reglas específicas

- En agenda, conserva intervalos `[inicio, fin)`, zona horaria documentada y rechazo de conflictos de profesional/box.
- En auditoría y datos clínicos, limita registros a metadata cuando lo exige el contrato y conserva autorización por rol.
- En importes, usa el ledger existente y precisión entera/decimal estricta; no derives cargos desde turnos.
- En CSV, neutraliza fórmulas y no exportes PII ni contenido clínico.
- Docker y Redis están fuera del alcance operativo actual; no los agregues como dependencias.
