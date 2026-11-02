"""Consentimiento y outbox local de recordatorios simulados.

Revision ID: 20261102_0012_appointment_reminders
Revises: 20261102_0011_odontogram_treatment_plans
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0012_appointment_reminders'
down_revision = '20261102_0011_odontogram_treatment_plans'
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
    "'historia.atenciones_listadas', 'evolucion.creada', 'evolucion.corregida', "
    "'odontograma.consultada', 'odontograma.denegada', 'odontograma.version_creada', "
    "'plan.consultado', 'plan.denegado', 'plan.creado', 'plan.estado_actualizado', "
    "'recordatorio.programado', 'recordatorio.invalidado', 'recordatorio.procesado', "
    "'recordatorio.fallo')")

_RECURSOS = (
    "resource_type IN ('turno', 'paciente', 'profesional', 'box', 'prestacion', "
    "'horario', 'excepcion', 'bloqueo', 'cuenta', 'sesion', 'historia', 'evolucion', "
    "'odontograma', 'plan', 'recordatorio')")

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
    "(action = 'plan.estado_actualizado' AND resource_type = 'plan' AND result = 'confirmado') OR "
    "(action = 'recordatorio.programado' AND resource_type = 'recordatorio' AND result = 'confirmado') OR "
    "(action = 'recordatorio.invalidado' AND resource_type = 'recordatorio' AND result = 'confirmado') OR "
    "(action = 'recordatorio.procesado' AND resource_type = 'recordatorio' AND result = 'confirmado') OR "
    "(action = 'recordatorio.fallo' AND resource_type = 'recordatorio' AND result = 'rechazado')")


def upgrade() -> None:
    op.add_column(
        'pacientes',
        sa.Column('acepta_recordatorios', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_check_constraint(
        'ck_pacientes_acepta_recordatorios', 'pacientes', 'acepta_recordatorios IN (true, false)')
    op.create_table(
        'recordatorios_outbox',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('turno_id', sa.BigInteger(), nullable=False),
        sa.Column('turno_version', sa.Integer(), nullable=False),
        sa.Column('generation', sa.Integer(), server_default='1', nullable=False),
        sa.Column('tipo', sa.String(length=32), nullable=False),
        sa.Column('programado_para', sa.DateTime(timezone=True), nullable=False),
        sa.Column('estado', sa.String(length=32), nullable=False),
        sa.Column('intentos', sa.Integer(), server_default='0', nullable=False),
        sa.Column('idempotency_key', sa.String(length=160), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['turno_id'], ['turnos.id'], ondelete='RESTRICT'),
        sa.CheckConstraint('turno_version > 0', name='ck_recordatorios_turno_version'),
        sa.CheckConstraint('generation > 0', name='ck_recordatorios_generation'),
        sa.CheckConstraint("tipo IN ('turno_24h')", name='ck_recordatorios_tipo'),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'procesado_simulado', 'invalidado', 'fallido')",
            name='ck_recordatorios_estado'),
        sa.CheckConstraint('intentos BETWEEN 0 AND 3', name='ck_recordatorios_intentos'),
        sa.UniqueConstraint(
            'turno_id', 'turno_version', 'tipo', 'generation',
            name='uq_recordatorios_turno_version_tipo_generation'),
    )
    op.create_index(
        'ix_recordatorios_estado_programacion', 'recordatorios_outbox',
        ['estado', 'programado_para'])
    op.drop_constraint('ck_eventos_auditoria_action', 'eventos_auditoria', type_='check')
    op.drop_constraint(
        'ck_eventos_auditoria_resource_type', 'eventos_auditoria', type_='check')
    op.drop_constraint(
        'ck_eventos_auditoria_combinacion', 'eventos_auditoria', type_='check')
    op.create_check_constraint(
        'ck_eventos_auditoria_action', 'eventos_auditoria', _ACCIONES)
    op.create_check_constraint(
        'ck_eventos_auditoria_resource_type', 'eventos_auditoria', _RECURSOS)
    op.create_check_constraint(
        'ck_eventos_auditoria_combinacion', 'eventos_auditoria', _COMBINACIONES)


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar consentimiento y recordatorios persistidos.')
