"""Estado persistido para el ciclo de vida de los turnos.

Revision ID: 20261102_0007_turn_status
Revises: 20261102_0006_agenda_availability
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0007_turn_status'
down_revision = '20261102_0006_agenda_availability'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'turnos',
        sa.Column('estado', sa.String(length=16), nullable=False, server_default='reservado'),
    )
    op.create_check_constraint(
        'ck_turnos_estado', 'turnos',
        "estado IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",
    )
    op.drop_constraint('ck_eventos_auditoria_action', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_combinacion', 'eventos_auditoria', type_='check')
    op.create_check_constraint(
        'ck_eventos_auditoria_action', 'eventos_auditoria',
        "action IN ('turno.creado', 'turno.estado_actualizado', 'paciente.creado', "
        "'paciente.actualizado', 'paciente.desactivado', 'paciente.reactivado', "
        "'profesional.creado', 'profesional.actualizado', 'profesional.desactivado', "
        "'profesional.reactivado', 'box.creado', 'box.actualizado', 'box.desactivado', "
        "'box.reactivado', 'prestacion.creada', 'prestacion.actualizada', "
        "'prestacion.desactivada', 'prestacion.reactivada', 'horario.actualizado', "
        "'excepcion.creada', 'excepcion.actualizada', 'excepcion.eliminada', "
        "'bloqueo.creado', 'bloqueo.eliminado', 'cuenta.bootstrap', 'cuenta.creada', "
        "'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada')",
    )
    op.create_check_constraint(
        'ck_eventos_auditoria_combinacion', 'eventos_auditoria',
        "(action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR "
        "(action = 'turno.estado_actualizado' AND resource_type = 'turno' AND result = 'confirmado') OR "
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
        "(action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado')",
    )


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar los estados persistidos y corregir hacia delante.')
