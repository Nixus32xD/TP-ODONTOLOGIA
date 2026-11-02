"""Eventos append-only para las operaciones aprobadas.

Revision ID: 20261101_0003_audit
Revises: 20261101_0002_auth
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa


revision = '20261101_0003_audit'
down_revision = '20261101_0002_auth'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'eventos_auditoria',
        sa.Column('id', sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor_id', sa.String(length=36),
                  sa.ForeignKey('usuarios.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('resource_type', sa.String(length=16), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=True),
        sa.Column('result', sa.String(length=12), nullable=False),
        sa.CheckConstraint(
            "action IN ('turno.creado', 'cuenta.bootstrap', 'cuenta.creada', "
            "'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada')",
            name='ck_eventos_auditoria_action'),
        sa.CheckConstraint(
            "resource_type IN ('turno', 'cuenta', 'sesion')",
            name='ck_eventos_auditoria_resource_type'),
        sa.CheckConstraint(
            "result IN ('confirmado', 'rechazado')",
            name='ck_eventos_auditoria_result'),
        sa.CheckConstraint(
            "(action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR "
            "(action = 'cuenta.bootstrap' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
            "(action = 'cuenta.creada' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
            "(action = 'cuenta.actualizada' AND resource_type = 'cuenta' AND result = 'confirmado') OR "
            "(action = 'sesion.iniciada' AND resource_type = 'sesion' AND result = 'confirmado') OR "
            "(action = 'sesion.cerrada' AND resource_type = 'sesion' AND result = 'confirmado') OR "
            "(action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado')",
            name='ck_eventos_auditoria_combinacion'),
        sa.CheckConstraint(
            "resource_type != 'sesion' OR resource_id IS NULL",
            name='ck_eventos_auditoria_sin_id_sesion'),
        sa.CheckConstraint(
            "action != 'sesion.rechazada' OR (actor_id IS NULL AND resource_id IS NULL)",
            name='ck_eventos_auditoria_rechazo_generico'),
    )
    op.create_index(
        'ix_eventos_auditoria_fecha_id', 'eventos_auditoria', ['created_at', 'id'])
    op.execute('''
        CREATE FUNCTION impedir_cambio_eventos_auditoria() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'eventos_auditoria es append-only';
        END;
        $$ LANGUAGE plpgsql
    ''')
    op.execute('''
        CREATE TRIGGER eventos_auditoria_append_only
        BEFORE UPDATE OR DELETE ON eventos_auditoria
        FOR EACH ROW EXECUTE FUNCTION impedir_cambio_eventos_auditoria()
    ''')


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar eventos de auditoría persistidos.')
