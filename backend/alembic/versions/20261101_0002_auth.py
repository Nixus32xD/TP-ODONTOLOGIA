"""Cuentas del personal y sesiones revocables.

Revision ID: 20261101_0002_auth
Revises: 20261101_0001
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa


revision = '20261101_0002_auth'
down_revision = '20261101_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'usuarios',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('identificador', sa.String(length=64), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=300), nullable=False),
        sa.Column('rol', sa.String(length=20), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint(
            "rol IN ('administrador', 'recepcion')", name='ck_usuarios_rol'),
    )
    op.create_table(
        'sesiones',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('usuario_id', sa.String(length=36),
                  sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jti', sa.String(length=36), nullable=False),
        sa.Column('expira_en', sa.BigInteger(), nullable=False),
        sa.Column('revocada_en', sa.BigInteger(), nullable=True),
        sa.Column('creado_en', sa.BigInteger(), nullable=False),
    )
    op.create_index('ix_sesiones_usuario_id', 'sesiones', ['usuario_id'])
    op.create_index('ix_sesiones_jti', 'sesiones', ['jti'], unique=True)


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar cuentas y sesiones persistidas.')
