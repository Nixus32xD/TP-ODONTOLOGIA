# Proposal

## Why

El sistema conserva turnos atendidos, pero todavía no dispone de un registro clínico separado y trazable para las evoluciones de una atención. Esta capacidad prepara una demostración local con datos exclusivamente ficticios, manteniendo la ficha mínima de paciente y las operaciones generales de agenda fuera del alcance clínico.

## What Changes

- Agregar una capacidad de historia clínica basada en evoluciones narrativas vinculadas a un paciente, un turno atendido y el profesional asociado.
- Permitir a un Profesional activo consultar y agregar sólo evoluciones de sus propias atenciones; Recepción y Administrador no podrán leer contenido clínico.
- Conservar las evoluciones originales y registrar correcciones como nuevas entradas vinculadas a la evolución corregida, sin edición ni borrado ordinario.
- Auditar lecturas y escrituras clínicas con metadatos mínimos y fallar cerrado si la auditoría no puede confirmarse.
- Incorporar la tabla clínica nueva a las migraciones incrementales SQLite/Alembic y al backup/restore local existente.
- Limitar el change a texto narrativo acotado y datos sintéticos. No agregar diagnósticos estructurados, recetas, adjuntos, odontograma, integraciones externas ni preparación para uso productivo.

## Capabilities

### New Capabilities
- `clinical-history`: consulta, registro y corrección append-only de evoluciones clínicas vinculadas a turnos atendidos, con acceso de mínimo privilegio.

### Modified Capabilities
- `personal-auth`: habilitar una excepción clínica estrecha para Profesionales activos, sin modificar sus permisos generales de agenda, pacientes, catálogos o cuentas.
- `audit-trail`: registrar accesos y operaciones clínicas con metadatos que excluyan contenido clínico y nombres, bajo política fail-closed.
- `agenda-backup-restore`: incluir las nuevas filas clínicas en los snapshots, recuentos y validaciones de restauración.

## Impact

El Apply requerirá endpoints protegidos de historia y evoluciones, persistencia clínica separada de `Paciente`, una migración aditiva compatible con SQLite y Alembic, y la extensión de auditoría y backup/restore existentes. No modifica el contrato de la ficha mínima ni los endpoints de agenda; se apoya en el estado terminal `atendido`. La propuesta no incorpora datos reales, servicios externos, Redis ni Docker y no afirma preparación clínica o productiva.
