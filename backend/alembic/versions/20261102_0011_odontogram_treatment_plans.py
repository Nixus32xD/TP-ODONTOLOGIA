"""Odontograma versionado y planes manuales sintéticos.

Revision ID: 20261102_0011_odontogram_treatment_plans
Revises: 20261102_0010_clinical_history
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0011_odontogram_treatment_plans'
down_revision = '20261102_0010_clinical_history'
branch_labels = None
depends_on = None


_ACCIONES = (
    "action IN ('turno.creado', 'turno.estado_actualizado', 'turno.reprogramado', "
    "'paciente.creado', 'paciente.actualizado', 'paciente.desactivado', "
    "'paciente.reactivado', 'profesional.creado', 'profesional.actualizado', "
    "'profesional.desactivado', 'profesional.reactivado', 'box.creado', "
    "'box.actualizado', 'box.desactivado', 'box.reactivado', 'prestacion.creada', "
    "'prestacion.actualizada', 'prestacion.desactivada', 'prestacion.reactivada', "
    "'horario.actualizado', 'excepcion.creada', 'excepcion.actualizada', "
    "'excepcion.eliminada', 'bloqueo.creado', 'bloqueo.eliminado', "
    "'cuenta.bootstrap', 'cuenta.creada', 'cuenta.actualizada', 'sesion.iniciada', "
    "'sesion.cerrada', 'sesion.rechazada', 'historia.consultada', 'historia.denegada', "
    "'historia.atenciones_listadas', "
    "'evolucion.creada', 'evolucion.corregida', 'odontograma.consultada', "
    "'odontograma.denegada', 'odontograma.version_creada', 'plan.consultado', "
    "'plan.denegado', 'plan.creado', 'plan.estado_actualizado')")

_RECURSOS = (
    "resource_type IN ('turno', 'paciente', 'profesional', 'box', 'prestacion', "
    "'horario', 'excepcion', 'bloqueo', 'cuenta', 'sesion', 'historia', 'evolucion', "
    "'odontograma', 'plan')")

_COMBINACIONES = (
    "(action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR "
    "(action = 'turno.estado_actualizado' AND resource_type = 'turno' AND result = 'confirmado') OR "
    "(action = 'turno.reprogramado' AND resource_type = 'turno' AND result = 'confirmado') OR "
    "(action = 'paciente.creado' AND resource_type = 'paciente' AND result = 'confirmado') OR "
    "(action = 'paciente.actualizado' AND resource_type = 'paciente' AND result = 'confirmado') OR "
    "(action = 'paciente.desactivado' AND resource_type = 'paciente' AND result = 'confirmado') OR "
    "(action = 'paciente.reactivado' AND resource_type = 'paciente' AND result = 'confirmado') OR "
    "(action = 'profesional.creado' AND resource_type = 'profesional' AND result = 'confirmado') OR "
    "(action = 'profesional.actualizado' AND resource_type = 'profesional' AND result = 'confirmado') OR "
    "(action = 'profesional.desactivado' AND resource_type = 'profesional' AND result = 'confirmado') OR "
    "(action = 'profesional.reactivado' AND resource_type = 'profesional' AND result = 'confirmado') OR "
    "(action = 'box.creado' AND resource_type = 'box' AND result = 'confirmado') OR "
    "(action = 'box.actualizado' AND resource_type = 'box' AND result = 'confirmado') OR "
    "(action = 'box.desactivado' AND resource_type = 'box' AND result = 'confirmado') OR "
    "(action = 'box.reactivado' AND resource_type = 'box' AND result = 'confirmado') OR "
    "(action = 'prestacion.creada' AND resource_type = 'prestacion' AND result = 'confirmado') OR "
    "(action = 'prestacion.actualizada' AND resource_type = 'prestacion' AND result = 'confirmado') OR "
    "(action = 'prestacion.desactivada' AND resource_type = 'prestacion' AND result = 'confirmado') OR "
    "(action = 'prestacion.reactivada' AND resource_type = 'prestacion' AND result = 'confirmado') OR "
    "(action = 'horario.actualizado' AND resource_type = 'horario' AND result = 'confirmado') OR "
    "(action = 'excepcion.creada' AND resource_type = 'excepcion' AND result = 'confirmado') OR "
    "(action = 'excepcion.actualizada' AND resource_type = 'excepcion' AND result = 'confirmado') OR "
    "(action = 'excepcion.eliminada' AND resource_type = 'excepcion' AND result = 'confirmado') OR "
    "(action = 'bloqueo.creado' AND resource_type = 'bloqueo' AND result = 'confirmado') OR "
    "(action = 'bloqueo.eliminado' AND resource_type = 'bloqueo' AND result = 'confirmado') OR "
    "(action = 'cuenta.bootstrap' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
    "(action = 'cuenta.creada' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
    "(action = 'cuenta.actualizada' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
    "(action = 'sesion.iniciada' AND resource_type = 'sesion' AND result = 'confirmado') OR "
    "(action = 'sesion.cerrada' AND resource_type = 'sesion' AND result = 'confirmado') OR "
    "(action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado') OR "
    "(action = 'historia.consultada' AND resource_type = 'historia' AND result = 'confirmado') OR "
    "(action = 'historia.denegada' AND resource_type = 'historia' AND result = 'rechazado') OR "
    "(action = 'historia.atenciones_listadas' AND resource_type = 'historia' AND result = 'confirmado') OR "
    "(action = 'evolucion.creada' AND resource_type = 'evolucion' AND result = 'confirmado') OR "
    "(action = 'evolucion.corregida' AND resource_type = 'evolucion' AND result = 'confirmado') OR "
    "(action = 'odontograma.consultada' AND resource_type = 'odontograma' AND result = 'confirmado') OR "
    "(action = 'odontograma.denegada' AND resource_type = 'odontograma' AND result = 'rechazado') OR "
    "(action = 'odontograma.version_creada' AND resource_type = 'odontograma' AND result = 'confirmado') OR "
    "(action = 'plan.consultado' AND resource_type = 'plan' AND result = 'confirmado') OR "
    "(action = 'plan.denegado' AND resource_type = 'plan' AND result = 'rechazado') OR "
    "(action = 'plan.creado' AND resource_type = 'plan' AND result = 'confirmado') OR "
    "(action = 'plan.estado_actualizado' AND resource_type = 'plan' AND result = 'confirmado')")


def _crear_append_only(tabla: str) -> None:
    funcion = f'impedir_cambio_{tabla}'
    op.execute(f'''
        CREATE FUNCTION {funcion}() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION '{tabla} es append-only';
        END;
        $$ LANGUAGE plpgsql
    ''')
    op.execute(f'''
        CREATE TRIGGER {tabla}_append_only
        BEFORE UPDATE OR DELETE ON {tabla}
        FOR EACH ROW EXECUTE FUNCTION {funcion}()
    ''')


def upgrade() -> None:
    op.create_table(
        'versiones_odontograma',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('paciente_id', sa.String(length=64),
                  sa.ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('profesional_id', sa.String(length=64),
                  sa.ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('version > 0', name='ck_versiones_odontograma_version_positiva'),
        sa.UniqueConstraint(
            'paciente_id', 'profesional_id', 'version',
            name='uq_versiones_odontograma_paciente_profesional_version'),
    )
    op.create_index(
        'ix_versiones_odontograma_paciente_profesional_version', 'versiones_odontograma',
        ['paciente_id', 'profesional_id', 'version'])
    op.create_table(
        'hallazgos_odontograma',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('version_id', sa.String(length=36),
                  sa.ForeignKey('versiones_odontograma.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('pieza_fdi', sa.String(length=2), nullable=False),
        sa.Column('superficie_fdi', sa.String(length=1), nullable=False),
        sa.Column('observacion', sa.Text(), nullable=True),
        sa.CheckConstraint('length(pieza_fdi) = 2', name='ck_hallazgos_odontograma_pieza_largo'),
        sa.CheckConstraint(
            "superficie_fdi IN ('M', 'D', 'O', 'I', 'B', 'V', 'L')",
            name='ck_hallazgos_odontograma_superficie'),
        sa.CheckConstraint(
            'observacion IS NULL OR length(observacion) <= 500',
            name='ck_hallazgos_odontograma_observacion_largo'),
        sa.UniqueConstraint(
            'version_id', 'pieza_fdi', 'superficie_fdi',
            name='uq_hallazgos_odontograma_version_pieza_superficie'),
    )
    op.create_index(
        'ix_hallazgos_odontograma_version_pieza', 'hallazgos_odontograma',
        ['version_id', 'pieza_fdi'])
    op.create_table(
        'planes_tratamiento',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('paciente_id', sa.String(length=64),
                  sa.ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('profesional_id', sa.String(length=64),
                  sa.ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('estado', sa.String(length=16), server_default='propuesto', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "estado IN ('propuesto', 'en_curso', 'completado', 'cancelado')",
            name='ck_planes_tratamiento_estado'),
    )
    op.create_index(
        'ix_planes_tratamiento_paciente_profesional_creacion', 'planes_tratamiento',
        ['paciente_id', 'profesional_id', 'created_at', 'id'])
    op.create_table(
        'etapas_plan_tratamiento',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('plan_id', sa.String(length=36),
                  sa.ForeignKey('planes_tratamiento.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('prestacion_id', sa.String(length=64),
                  sa.ForeignKey('prestaciones.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.CheckConstraint('orden > 0', name='ck_etapas_plan_tratamiento_orden_positiva'),
        sa.UniqueConstraint('plan_id', 'orden', name='uq_etapas_plan_tratamiento_plan_orden'),
    )
    op.create_index(
        'ix_etapas_plan_tratamiento_plan_orden', 'etapas_plan_tratamiento', ['plan_id', 'orden'])
    for tabla in ('versiones_odontograma', 'hallazgos_odontograma', 'etapas_plan_tratamiento'):
        _crear_append_only(tabla)

    op.drop_constraint('ck_eventos_auditoria_action', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_resource_type', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_combinacion', 'eventos_auditoria', type_='check')
    op.create_check_constraint('ck_eventos_auditoria_action', 'eventos_auditoria', _ACCIONES)
    op.create_check_constraint(
        'ck_eventos_auditoria_resource_type', 'eventos_auditoria', _RECURSOS)
    op.create_check_constraint(
        'ck_eventos_auditoria_combinacion', 'eventos_auditoria', _COMBINACIONES)


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar odontogramas, planes y auditoría persistidos.')
