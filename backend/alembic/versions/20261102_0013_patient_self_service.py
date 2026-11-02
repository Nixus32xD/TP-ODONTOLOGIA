"""Vínculo sintético de pacientes y comandos idempotentes del portal.

Revision ID: 20261102_0013_patient_self_service
Revises: 20261102_0012_appointment_reminders
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0013_patient_self_service'
down_revision = '20261102_0012_appointment_reminders'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('ck_eventos_auditoria_action', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_resource_type', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_combinacion', 'eventos_auditoria', type_='check')
    op.create_check_constraint(
        'ck_eventos_auditoria_action', 'eventos_auditoria',
        "action IN ('turno.creado', 'turno.estado_actualizado', 'turno.reprogramado', "
        "'paciente.creado', 'paciente.actualizado', 'paciente.desactivado', 'paciente.reactivado', "
        "'profesional.creado', 'profesional.actualizado', 'profesional.desactivado', "
        "'profesional.reactivado', 'box.creado', 'box.actualizado', 'box.desactivado', "
        "'box.reactivado', 'prestacion.creada', 'prestacion.actualizada', 'prestacion.desactivada', "
        "'prestacion.reactivada', 'horario.actualizado', 'excepcion.creada', "
        "'excepcion.actualizada', 'excepcion.eliminada', 'bloqueo.creado', 'bloqueo.eliminado', "
        "'cuenta.bootstrap', 'cuenta.creada', 'cuenta.actualizada', "
        "'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada', 'historia.consultada', "
        "'historia.denegada', 'historia.atenciones_listadas', 'evolucion.creada', "
        "'evolucion.corregida', 'odontograma.consultada', 'odontograma.denegada', "
        "'odontograma.version_creada', 'plan.consultado', 'plan.denegado', 'plan.creado', "
        "'plan.estado_actualizado', 'recordatorio.programado', 'recordatorio.invalidado', "
        "'recordatorio.procesado', 'recordatorio.fallo', 'portal.disponibilidad.consultada', "
        "'portal.turnos.consultados', 'portal.turno.reservado', 'portal.turno.cancelado', "
        "'portal.turno.reprogramado', 'portal.acceso.denegado')")
    op.create_check_constraint(
        'ck_eventos_auditoria_resource_type', 'eventos_auditoria',
        "resource_type IN ('turno', 'paciente', 'profesional', 'box', 'prestacion', "
        "'horario', 'excepcion', 'bloqueo', 'cuenta', 'sesion', 'historia', 'evolucion', "
        "'odontograma', 'plan', 'recordatorio', 'portal')")
    op.create_check_constraint(
        'ck_eventos_auditoria_combinacion', 'eventos_auditoria',
        "(action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR "
        "(action = 'turno.estado_actualizado' AND resource_type = 'turno' AND result = 'confirmado') OR "
        "(action = 'turno.reprogramado' AND resource_type = 'turno' AND result = 'confirmado') OR "
        "(action = 'horario.actualizado' AND resource_type = 'horario' AND result = 'confirmado') OR "
        "(action = 'excepcion.creada' AND resource_type = 'excepcion' AND result = 'confirmado') OR "
        "(action = 'excepcion.actualizada' AND resource_type = 'excepcion' AND result = 'confirmado') OR "
        "(action = 'excepcion.eliminada' AND resource_type = 'excepcion' AND result = 'confirmado') OR "
        "(action = 'bloqueo.creado' AND resource_type = 'bloqueo' AND result = 'confirmado') OR "
        "(action = 'bloqueo.eliminado' AND resource_type = 'bloqueo' AND result = 'confirmado') OR "
        "(action = 'portal.disponibilidad.consultada' AND resource_type = 'portal' AND result = 'confirmado') OR "
        "(action = 'portal.turnos.consultados' AND resource_type = 'portal' AND result = 'confirmado') OR "
        "(action = 'portal.turno.reservado' AND resource_type = 'turno' AND result = 'confirmado') OR "
        "(action = 'portal.turno.cancelado' AND resource_type = 'turno' AND result = 'confirmado') OR "
        "(action = 'portal.turno.reprogramado' AND resource_type = 'turno' AND result = 'confirmado') OR "
        "(action = 'portal.acceso.denegado' AND resource_type = 'portal' AND result = 'rechazado') OR "
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
    op.add_column('usuarios', sa.Column('paciente_id', sa.String(length=64), nullable=True))
    op.create_foreign_key(
        'fk_usuarios_paciente_id_pacientes', 'usuarios', 'pacientes',
        ['paciente_id'], ['id'], ondelete='RESTRICT')
    op.create_unique_constraint('uq_usuarios_paciente_id', 'usuarios', ['paciente_id'])
    op.drop_constraint('ck_usuarios_rol', 'usuarios', type_='check')
    op.create_check_constraint(
        'ck_usuarios_rol', 'usuarios',
        "rol IN ('administrador', 'recepcion', 'profesional', 'paciente')")
    op.drop_constraint('ck_usuarios_vinculo_profesional', 'usuarios', type_='check')
    op.create_check_constraint(
        'ck_usuarios_vinculo_profesional', 'usuarios',
        "(rol = 'profesional' AND profesional_id IS NOT NULL AND paciente_id IS NULL) OR "
        "(rol = 'paciente' AND profesional_id IS NULL AND paciente_id IS NOT NULL) OR "
        "(rol IN ('administrador', 'recepcion') AND profesional_id IS NULL AND paciente_id IS NULL)")
    op.create_table(
        'idempotencia_portal_paciente',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('paciente_id', sa.String(length=64), nullable=False),
        sa.Column('operacion', sa.String(length=20), nullable=False),
        sa.Column('clave', sa.String(length=128), nullable=False),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
        sa.Column('turno_id', sa.BigInteger(), nullable=False),
        sa.Column('respuesta_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['paciente_id'], ['pacientes.id'], ondelete='RESTRICT',
            name='fk_idempotencia_portal_paciente_paciente_id'),
        sa.ForeignKeyConstraint(
            ['turno_id'], ['turnos.id'], ondelete='RESTRICT',
            name='fk_idempotencia_portal_paciente_turno_id'),
        sa.CheckConstraint(
            "operacion IN ('reserva', 'cancelacion', 'reprogramacion')",
            name='ck_idempotencia_portal_paciente_operacion'),
        sa.CheckConstraint('length(clave) BETWEEN 1 AND 128',
                           name='ck_idempotencia_portal_paciente_clave'),
        sa.CheckConstraint('length(fingerprint) = 64',
                           name='ck_idempotencia_portal_paciente_fingerprint'),
        sa.UniqueConstraint(
            'paciente_id', 'operacion', 'clave',
            name='uq_idempotencia_portal_paciente_operacion_clave'),
    )


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar vínculos y claves de idempotencia.')
