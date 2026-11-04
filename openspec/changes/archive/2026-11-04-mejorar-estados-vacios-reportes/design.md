# Design

## Context

C-20 provee agregados y el panel React conserva resultados o errores. El componente no muestra una señal cuando un response exitoso trae `dias` vacío. El contrato nuevo se limita al feedback de UI; React maneja el resultado con estado declarativo (`useState`) y WAI-ARIA `role="status"` comunica avisos no urgentes sin mover el foco.

## Goals / Non-Goals

**Goals:** hacer visible y anunciable el estado vacío por reporte; conservar el comportamiento de los reportes con datos y los errores actuales.

**Non-Goals:** cambiar API, agregaciones, roles, rangos, exportación CSV, layout general o instalación de una biblioteca de accesibilidad.

## Decisions

1. Usar el estado de respuesta existente (`agenda` y `finanzas`) para decidir por separado entre tabla y mensaje vacío. No crear una segunda fuente de estado.
2. Renderizar el mensaje como `role="status"`; WAI-ARIA define anuncio polite/atómico por defecto. Mantener errores en `role="alert"`, con su semántica más urgente.
3. No añadir `aria-live` redundante ni enfocar el mensaje: el rol basta y el foco permanece en el control que inició la consulta.
4. Context7 se eligió frente a GitHub MCP para este change porque la consulta necesitaba documentación vigente de React. Context7 devolvió el ejemplo oficial de React.dev para estados declarativos de una acción asíncrona; GitHub serviría para consultar código/issues pero el checkout local ya ofrece ese código.

## Risks / Trade-offs

- [Una lista vacía puede confundirse con un error] → distinguir explícitamente `role="status"` del `role="alert"` existente y probar ambos.
- [Una agenda vacía junto con finanzas con días] → decidir el estado por cada dataset y cubrirlo en tests.

## Migration Plan

Sin migración ni cambio de API. Actualizar el panel localmente y mantener respuestas anteriores compatibles.
