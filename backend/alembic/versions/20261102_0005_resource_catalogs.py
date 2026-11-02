"""Catálogos administrables de profesionales, boxes y prestaciones.

Revision ID: 20261102_0005_resource_catalogs
Revises: 20261102_0004_patient_management
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0005_resource_catalogs'
down_revision = '20261102_0004_patient_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    for tabla, nombre_base, check_nombre, check_activo in (
            ('profesionales', 'Profesional de demostración ',
             'ck_profesionales_nombre', 'ck_profesionales_activo'),
            ('boxes', 'Box de demostración ', 'ck_boxes_nombre', 'ck_boxes_activo')):
        op.add_column(tabla, sa.Column(
            'nombre', sa.String(length=120), nullable=False, server_default=nombre_base.strip()))
        op.add_column(tabla, sa.Column(
            'activo', sa.Boolean(), nullable=False, server_default=sa.true()))
        op.execute(sa.text(f"UPDATE {tabla} SET nombre = :prefijo || id").bindparams(
            prefijo=nombre_base))
        op.alter_column(tabla, 'nombre', server_default=None)
        op.alter_column(tabla, 'activo', server_default=None)
        op.create_check_constraint(
            check_nombre, tabla, 'length(nombre) BETWEEN 1 AND 120')
        op.create_check_constraint(check_activo, tabla, 'activo IN (true, false)')

    op.create_table(
        'prestaciones',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('duracion_minutos', sa.Integer(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.CheckConstraint('length(nombre) BETWEEN 1 AND 120', name='ck_prestaciones_nombre'),
        sa.CheckConstraint('duracion_minutos > 0', name='ck_prestaciones_duracion'),
        sa.CheckConstraint('activo IN (true, false)', name='ck_prestaciones_activo'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.drop_constraint('ck_eventos_auditoria_action', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_resource_type', 'eventos_auditoria', type_='check')
    op.drop_constraint('ck_eventos_auditoria_combinacion', 'eventos_auditoria', type_='check')
    op.create_check_constraint(
        'ck_eventos_auditoria_action', 'eventos_auditoria',
        "action IN ('turno.creado', 'paciente.creado', 'paciente.actualizado', "
        "'paciente.desactivado', 'paciente.reactivado', 'profesional.creado', "
        "'profesional.actualizado', 'profesional.desactivado', 'profesional.reactivado', "
        "'box.creado', 'box.actualizado', 'box.desactivado', 'box.reactivado', "
        "'prestacion.creada', 'prestacion.actualizada', 'prestacion.desactivada', "
        "'prestacion.reactivada', 'cuenta.bootstrap', 'cuenta.creada', "
        "'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada')")
    op.create_check_constraint(
        'ck_eventos_auditoria_resource_type', 'eventos_auditoria',
        "resource_type IN ('turno', 'paciente', 'profesional', 'box', 'prestacion', 'cuenta', 'sesion')")
    op.create_check_constraint(
        'ck_eventos_auditoria_combinacion', 'eventos_auditoria',
        "(action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR "
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
        "(action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado')")


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar catálogos y eventos persistidos.')
