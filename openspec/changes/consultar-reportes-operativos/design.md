# Design

## Context

C-08 consulta agenda por instantes offset-aware y C-07 conserva horarios locales, excepciones y bloqueos. C-09 distingue estados que ocupan recursos de estados terminales. C-19 ya mantiene importes exactos como centavos y movimientos con `created_at`; el reporte debe derivar sus totales del ledger sin exponer filas individuales.

## Goals / Non-Goals

**Goals:** ofrecer agregados diarios de agenda y finanzas para rangos locales acotados, con una sola fuente de cálculo para JSON, CSV y la vista React. Mantener autenticación/roles actuales y no añadir tablas ni servicios.

**Non-Goals:** exportar filas de pacientes o movimientos, modificar turnos/ledger, calcular productividad clínica, añadir recomendaciones, conectar pagos/fiscalidad, registrar auditoría de lectura nueva o modificar el esquema.

## Decisions

1. **Rango como fechas locales semiabiertas.** Recibir fechas canónicas `YYYY-MM-DD`, interpretar el comienzo y el límite exclusivo en `America/Argentina/Mendoza`, exigir de 1 a 31 días. Esto conserva agrupación diaria y evita offsets fijos en límites de día.
2. **Un servicio de consulta como fuente de JSON y CSV.** `reportes.py` valida el rango, consulta tablas existentes y devuelve sólo valores agregados. Los endpoints CSV serializan ese resultado con columnas y orden fijos; la interfaz usa esos endpoints y no vuelve a calcular métricas.
3. **Ocupación sobre ventanas locales disponibles.** Para cada fecha y recurso activo, elegir la excepción fechada si existe; de lo contrario usar tramos del día semanal. Restar la unión de bloqueos intersectados con los tramos y medir la unión de intervalos `reservado`/`confirmado` dentro de esa disponibilidad. Reportar por separado minutos y porcentajes para profesionales y boxes; sin capacidad, el porcentaje es `null`. Las atenciones muestran duración planificada, no duración real.
4. **Fecha de turno y fecha de movimiento separadas.** Conteos de agenda se asignan a la fecha local del inicio programado actual del turno. Los movimientos financieros se asignan a la fecha local de su `created_at`. El saldo inicial incluye el ledger anterior al inicio; cada saldo de cierre aplica cargos, cobros y reversiones anteriores al límite local exclusivo del día.
5. **Usar centavos y permisos existentes.** Sumar los montos C-19 como enteros Python, formatear con `centavos_a_importe_ars`, no pasar montos por float. `personal_operativo` protege agenda; `administrador` protege finanzas. Profesional/Paciente no reciben reportes globales.
6. **CSV seguro y agregado.** Usar `csv.writer` con terminadores CRLF, UTF-8, cabeceras fijas, columnas explícitas y neutralización de celdas textuales iniciadas con `=`, `+`, `-` o `@`. No incluir nombres, teléfonos, IDs de pacientes, conceptos, motivos, historia clínica ni datos de tratamientos. Los únicos identificadores permitidos son IDs opacos de recursos de agenda para poder distinguir capacidad por recurso.

Alternativas consideradas: aceptar instantes UTC como C-08 y repartirlos entre días locales (más propenso a errores de límites); calcular cada formato en rutas distintas (arriesga divergencia); mostrar métricas por nombres (innecesario para el reporte agregado y menos privado); sumar montos mediante `float` (pierde exactitud).

## Risks / Trade-offs

- **Capacidad en una fecha histórica con cambio horario** → usar el calendario y zona IANA configurados, mantener las horas de disponibilidad como minutos locales y probar los límites de fechas y conversiones; no fijar `-03:00`.
- **Datos legacy con turnos fuera de horario** → contar sus estados y minutos programados en la sección de agenda; limitar el numerador de capacidad a los intervalos disponibles para que una métrica de ocupación no supere la capacidad.
- **Muchas filas históricas financieras** → las sumas se hacen con enteros Python y consultan sólo movimientos anteriores al fin del rango; es suficiente para la demo local, sin añadir agregados persistidos.
- **CSV abierto en hojas de cálculo** → neutralizar campos textuales potencialmente interpretables como fórmulas y probar su representación exacta.

## Migration Plan

No requiere migración de base de datos. Añadir rutas JSON/CSV y una vista local; conservar compatibilidad con SQLite y PostgreSQL. La restauración/backup no cambia porque el reporte es de sólo lectura y no crea tablas.

## Open Questions

Ninguna para el alcance aprobado. El porcentaje informa capacidad reservada según agenda; no estima productividad ni utilización clínica.
