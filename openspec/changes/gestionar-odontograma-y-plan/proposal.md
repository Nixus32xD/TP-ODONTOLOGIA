# Proposal

## Why

La historia clínica actual admite notas narrativas, pero no permite registrar de forma estructurada un odontograma versionado ni un plan manual de prestaciones. C-16 amplía la demostración sintética sobre C-15 con conservación histórica, acceso clínico restringido y respaldo recuperable, sin automatizar decisiones odontológicas.

## What Changes

- Agregar `odontogram` para registrar hallazgos por pieza y superficie usando nomenclatura FDI/ISO de dos dígitos y superficies individuales, con observaciones breves y versiones inmutables.
- Agregar `treatment-plans` para crear planes manuales basados en el catálogo existente de prestaciones, con etapas y estados operativos explícitos; sin precios ni asociación automática a turnos.
- Extender las reglas de autorización y auditoría para estas capacidades: sólo un Profesional activo vinculado puede consultar o registrar datos de pacientes con una atención propia en estado `atendido`; Administrador y Recepción no acceden al contenido clínico. La auditoría guarda metadatos y falla cerrada.
- Extender backup/restore de SQLite y PostgreSQL para incluir y validar versiones, referencias y recuentos de las nuevas entidades.
- Mantener uso sólo local y demostrativo con pacientes y contenido sintéticos. No se incorporan Docker, Redis, proveedores externos, datos reales, recomendaciones ni afirmaciones de preparación productiva.

## Capabilities

### New Capabilities

- `odontogram`: registro y consulta versionados de hallazgos sintéticos por pieza y superficie.
- `treatment-plans`: planes manuales sintéticos con prestaciones existentes y etapas operativas.

### Modified Capabilities

- `personal-auth`: aplicar los límites de rol, vínculo profesional, turno atendido, auditoría metadata-only y fallo cerrado también a odontogramas y planes.
- `agenda-backup-restore`: incluir y validar las tablas y referencias de odontograma y planes en bundles SQLite y PostgreSQL.

## Impact

Se prevén cambios en modelos SQLAlchemy, migraciones aditivas SQLite/Alembic, servicios y rutas FastAPI, auditoría, manifiesto/conteos/validación/restauración de backups y una vista clínica mínima en React. La nomenclatura propuesta toma como referencia ISO 3950:2016 para designar dientes con dos dígitos (https://www.iso.org/standard/68292.html) y el CodeSystem de superficies FDI publicado por HL7 (https://terminology.hl7.org/6.5.0/CodeSystem-FDI-surface.html); estas referencias orientan códigos, no representan consenso clínico ni definen diagnóstico. ISO indica que su edición está bajo revisión para reemplazo, por lo que su estado deberá revalidarse antes de Apply.
