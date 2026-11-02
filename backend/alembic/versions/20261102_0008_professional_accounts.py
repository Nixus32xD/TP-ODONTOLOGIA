"""Vínculo único de cuentas de Profesional con su recurso de agenda.

Revision ID: 20261102_0008_professional_accounts
Revises: 20261102_0007_turn_status
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0008_professional_accounts'
down_revision = '20261102_0007_turn_status'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('profesional_id', sa.String(length=64), nullable=True))
    op.create_foreign_key(
        'fk_usuarios_profesional_id_profesionales',
        'usuarios', 'profesionales', ['profesional_id'], ['id'], ondelete='RESTRICT')
    op.create_unique_constraint('uq_usuarios_profesional_id', 'usuarios', ['profesional_id'])
    op.drop_constraint('ck_usuarios_rol', 'usuarios', type_='check')
    op.create_check_constraint(
        'ck_usuarios_rol', 'usuarios',
        "rol IN ('administrador', 'recepcion', 'profesional')")
    op.create_check_constraint(
        'ck_usuarios_vinculo_profesional', 'usuarios',
        "(rol = 'profesional' AND profesional_id IS NOT NULL) OR "
        "(rol IN ('administrador', 'recepcion') AND profesional_id IS NULL)")


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar vínculos y corregir hacia delante.')
