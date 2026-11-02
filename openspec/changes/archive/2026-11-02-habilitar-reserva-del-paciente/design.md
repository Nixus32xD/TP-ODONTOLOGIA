# Design

## Context

La autenticación persiste `Usuario`/`Sesion` y emite identidad con rol y `profesional_id`. Las reservas operativas están en `turnos`; C-08 calcula disponibilidad por profesional/box y C-10 reprograma con versión, exclusión y auditoría atómica. SQLite usa migraciones explícitas de autenticación; PostgreSQL usa Alembic. Backup/restore valida una lista cerrada de tablas y una versión exacta del esquema. La UI React presenta pantallas según el rol.

## Goals / Non-Goals

**Goals:** añadir identidad sintética de paciente, operaciones propias con mínimo de datos, comandos idempotentes y un portal integrado en la UI actual; conservar auditoría fail-closed, compatibilidad SQLite/PostgreSQL y backup/restore.

**Non-Goals:** registrar pacientes públicamente, verificar identidad real, contactar por canales externos, exponer servicios/profesionales/boxes, ofrecer clínica, pagos o uso productivo.

## Decisions

1. **Vínculo de cuenta en el esquema actual.** Agregar `paciente_id` único a `usuarios`, con FK a una ficha activa y restricción de compatibilidad rol-vínculo; reconstruir `usuarios` sólo en la migración SQLite necesaria para ampliar los `CHECK`. PostgreSQL recibirá migración Alembic aditiva equivalente. Se conserva `profesional_id` y sus contratos archivados. Como alternativa, una tabla de vínculos separada evita reconstruir SQLite, pero duplica reglas de integridad entre roles.

2. **Aprovisionamiento administrativo local.** Reutilizar el flujo de cuentas y política de contraseña; permitir `rol=paciente` sólo con un `paciente_id` activo y no vinculado, bajo sesión Administrador. La respuesta no contiene contraseña ni token. No habrá invitación, auto-registro ni canal externo.

3. **Disponibilidad opaca y duración demostrativa fija.** La consulta del portal combina los horarios activos de profesionales y boxes mediante el cálculo C-08 con duración fija de 30 minutos, y devuelve únicamente `inicio`/`fin`. La reserva acepta el inicio elegido; en una transacción bajo el mutex vigente el servidor vuelve a calcular candidatos y selecciona determinísticamente una pareja libre de recursos, sin confiar en IDs del cliente. Alternativas como publicar IDs de agenda o nombres de prestaciones ampliarían la información expuesta; duración variable requeriría primero un contrato de catálogo para pacientes.

4. **Comandos y titularidad en servicios de dominio.** Crear módulo de autoservicio sobre una misma sesión/transacción SQLAlchemy para SQLite y PostgreSQL, reutilizando las validaciones C-01/C-08/C-10 y la política de zona Mendoza. Todos los recursos se cargan y comprueban contra `identidad.paciente_id` antes de buscar una clave idempotente o formar respuestas. Desconocido y ajeno se traducen al mismo 404.

5. **Idempotencia persistida y serializada.** Una tabla registra paciente, operación, clave, SHA-256 del payload canónico y respuesta mínima JSON. La unicidad `(paciente_id, operación, clave)` impide duplicados; un mutex compartido serializa inserción de turno, clave, auditoría y efectos de recordatorio. La misma huella devuelve la respuesta registrada y otra huella produce 409. La tabla viaja en backup/restore junto a turnos y cuentas.

6. **Restringir reservas a una franja común ficticia.** Para evitar exponer catálogo, la demo ofrece slots genéricos de 30 minutos alineados a 15 minutos. El paciente envía sólo inicio ISO con offset; la API deriva fin y recursos. Se limita la consulta a los siguientes 31 días locales y a tres turnos futuros activos. La hora del servidor se inyecta en pruebas y se convierte a `America/Argentina/Mendoza`.

7. **Cancelación y reprogramación como comandos propios.** Reusar transiciones y reprogramación de dominio sólo después de validar dueño, estado, versión y anticipación; exigir 24 horas o más antes del turno actual y destino futuro elegible. El comando de reprogramación conserva paciente, duración y estado; C-17 invalida/recalcula outbox dentro de la misma transacción. Se añade actor paciente a las acciones de auditoría sin incluir datos del turno.

8. **Migración y presentación local.** Aumentar SQLite a v12 y Alembic a `20261102_0013_patient_self_service`; ajustar versión esperada y lista cerrada del backup. La UI muestra el portal sólo a `paciente` autenticado y mantiene vistas existentes para los demás roles. La demo usa credenciales sintéticas creadas expresamente.

## Risks / Trade-offs

- [La búsqueda de disponibilidad sobre muchas parejas puede aumentar consultas] → limitar rango a 31 días, duración fija y deduplicar intervalos candidatos.
- [La selección de recursos puede competir con altas simultáneas] → volver a validar bajo el mutex compartido y confirmar reserva, idempotencia, auditoría y outbox juntos.
- [El portal podría confundirse con servicio clínico real] → etiqueta visible de demostración sintética, sin datos reales ni canales externos; documentar que no está preparado para producción.
- [El historial de idempotencia conserva referencias de turnos] → almacenar sólo identificadores y respuesta mínima requerida para reintento; incluirlo en control de acceso, backup/restore y sin endpoints de consulta genéricos.

## Migration Plan

1. Baseline suites backend/frontend y crear pruebas RED antes de código de producción.
2. Añadir migraciones SQLite v12 y Alembic 0013 con nuevos vínculos/tabla; validar upgrades desde versiones soportadas y conservar filas previas.
3. Implementar provisioning/autenticación, servicio transaccional y rutas protegidas; luego integrar portal UI y cuenta sintética.
4. Probar backup/restore SQLite y PostgreSQL reales en entorno aislado con el puerto de test autorizado; ejecutar suites completas.
5. Sincronizar specs y archivar sólo con validación estricta y evidencia completa.

Rollback: no se promete downgrade de datos. Para volver a la versión anterior se restaura un backup previo a la migración; nunca se elimina `paciente_id` ni el historial idempotente automáticamente.

## Open Questions

Ninguna para el alcance sintético aprobado. La duración fija de 30 minutos define sólo los slots de demostración, no la duración clínica de una prestación.
