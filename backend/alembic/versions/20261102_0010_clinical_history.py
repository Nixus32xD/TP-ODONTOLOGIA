"""Historia clínica de demostración con evoluciones inmutables.

Revision ID: 20261102_0010_clinical_history
Revises: 20261102_0009_turn_rescheduling
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0010_clinical_history'
down_revision = '20261102_0009_turn_rescheduling'
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
    "'evolucion.creada', 'evolucion.corregida')")

_RECURSOS = (
    "resource_type IN ('turno', 'paciente', 'profesional', 'box', 'prestacion', "
    "'horario', 'excepcion', 'bloqueo', 'cuenta', 'sesion', 'historia', 'evolucion')")

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
    "(action = 'evolucion.creada' AND resource_type = 'evolucion' AND result = 'confirmado') OR "
    "(action = 'evolucion.corregida' AND resource_type = 'evolucion' AND result = 'confirmado')")


def upgrade() -> None:
    op.create_table(
        'evoluciones_clinicas',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('paciente_id', sa.String(length=64),
                  sa.ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('profesional_id', sa.String(length=64),
                  sa.ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('turno_id', sa.BigInteger(),
                  sa.ForeignKey('turnos.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('nota', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('corrige_a_id', sa.String(length=36),
                  sa.ForeignKey('evoluciones_clinicas.id', ondelete='RESTRICT'), nullable=True),
        sa.CheckConstraint(
            'length(trim(nota)) BETWEEN 1 AND 5000', name='ck_evoluciones_clinicas_nota'),
    )
    op.create_index(
        'ix_evoluciones_paciente_profesional_creacion', 'evoluciones_clinicas',
        ['paciente_id', 'profesional_id', 'created_at', 'id'])
    op.create_index('ix_evoluciones_turno', 'evoluciones_clinicas', ['turno_id'])
    op.execute('''
        CREATE FUNCTION impedir_cambio_evoluciones_clinicas() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'evoluciones_clinicas es append-only';
        END;
        $$ LANGUAGE plpgsql
    ''')
    op.execute('''
        CREATE TRIGGER evoluciones_clinicas_append_only
        BEFORE UPDATE OR DELETE ON evoluciones_clinicas
        FOR EACH ROW EXECUTE FUNCTION impedir_cambio_evoluciones_clinicas()
    ''')

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
        'Downgrade destructivo bloqueado; conservar evoluciones clínicas y auditoría persistidas.')
