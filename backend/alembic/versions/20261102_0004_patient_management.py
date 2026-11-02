"""Campos mínimos de paciente y eventos de auditoría de pacientes.

Revision ID: 20261102_0004_patient_management
Revises: 20261101_0003_audit
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0004_patient_management'
down_revision = '20261101_0003_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'pacientes', sa.Column('nombre', sa.String(length=120), nullable=False,
                               server_default=''))
    op.add_column('pacientes', sa.Column('telefono', sa.String(length=32), nullable=True))
    op.add_column(
        'pacientes', sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute("UPDATE pacientes SET nombre = 'Paciente de demostración ' || id WHERE nombre = ''")
    op.alter_column('pacientes', 'nombre', server_default=None)
    op.alter_column('pacientes', 'activo', server_default=None)
    op.create_check_constraint(
        'ck_pacientes_nombre', 'pacientes', 'length(nombre) BETWEEN 1 AND 120')
    op.create_check_constraint('ck_pacientes_activo', 'pacientes', 'activo IN (true, false)')

    op.drop_constraint('ck_eventos_auditoria_action', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_resource_type', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_combinacion', 'eventos_auditoria', type_='check')
    op.create_check_constraint(
        'ck_eventos_auditoria_action', 'eventos_auditoria',
        "action IN ('turno.creado', 'paciente.creado', 'paciente.actualizado', "
        "'paciente.desactivado', 'paciente.reactivado', 'cuenta.bootstrap', "
        "'cuenta.creada', 'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada', "
        "'sesion.rechazada')")
    op.create_check_constraint(
        'ck_eventos_auditoria_resource_type', 'eventos_auditoria',
        "resource_type IN ('turno', 'paciente', 'cuenta', 'sesion')")
    op.create_check_constraint(
        'ck_eventos_auditoria_combinacion', 'eventos_auditoria',
        "(action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR "
        "(action = 'paciente.creado' AND resource_type = 'paciente' AND result = 'confirmado') OR "
        "(action = 'paciente.actualizado' AND resource_type = 'paciente' AND result = 'confirmado') OR "
        "(action = 'paciente.desactivado' AND resource_type = 'paciente' AND result = 'confirmado') OR "
        "(action = 'paciente.reactivado' AND resource_type = 'paciente' AND result = 'confirmado') OR "
        "(action = 'cuenta.bootstrap' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
        "(action = 'cuenta.creada' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
        "(action = 'cuenta.actualizada' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
        "(action = 'sesion.iniciada' AND resource_type = 'sesion' AND result = 'confirmado') OR "
        "(action = 'sesion.cerrada' AND resource_type = 'sesion' AND result = 'confirmado') OR "
        "(action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado')")


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar fichas y eventos de auditoría persistidos.')
