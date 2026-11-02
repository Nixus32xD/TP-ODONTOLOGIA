# Proposal

## Why

El proyecto permite que el personal administre turnos, pero todavía no ofrece a un paciente una forma autenticada y acotada de reservar o administrar únicamente sus propios turnos. Un portal local con cuentas ficticias permite demostrar autoservicio sin publicar pacientes, profesionales, agendas identificadas ni canales externos.

## What Changes

- Incorporar el rol `paciente`, con vínculo único a una ficha y alta exclusiva por Administrador para datos sintéticos.
- Agregar API y portal autenticado para consultar turnos propios, reservar en franjas disponibles y cancelar o reprogramar turnos elegibles.
- Aplicar límite de tres turnos futuros activos, claves idempotentes persistidas, límites de anticipación de 24 horas en Mendoza y control de versión al reprogramar.
- Registrar auditoría metadata-only de accesos y mutaciones, y recalcular recordatorios existentes al cancelar o reprogramar.
- No habilitar autorregistro, mensajería, activación externa, pagos ni uso con datos reales. El change no convierte el sistema en apto para producción.

## Capabilities

### New Capabilities
- `patient-self-service`: reservas, consulta mínima y gestión de turnos propios mediante un portal autenticado.

### Modified Capabilities
- `personal-auth`: agregar cuentas sintéticas de paciente con vínculo único y permisos restringidos.
- `audit-trail`: auditar acciones del paciente sin datos personales, clínicos ni horarios.

## Impact

Afecta modelos de cuenta y persistencia, autenticación/autorización, servicios de agenda y reprogramación, auditoría, API FastAPI, migraciones SQLite/Alembic para PostgreSQL, backup/restore y la aplicación React/TypeScript. Reutiliza disponibilidad y transacciones existentes; no agrega dependencias externas ni cambia los contratos archivados de C-01, C-08 o C-10.
