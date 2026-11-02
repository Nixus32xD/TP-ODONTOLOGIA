"""Esquema inicial PostgreSQL para la agenda C-01.

Revision ID: 20261101_0001
Revises:
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa


revision = '20261101_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('pacientes', sa.Column('id', sa.String(length=64), primary_key=True))
    op.create_table('profesionales', sa.Column('id', sa.String(length=64), primary_key=True))
    op.create_table('boxes', sa.Column('id', sa.String(length=64), primary_key=True))
    op.create_table(
        'turnos',
        sa.Column('id', sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column('paciente_id', sa.String(length=64), sa.ForeignKey('pacientes.id'), nullable=False),
        sa.Column('profesional_id', sa.String(length=64), sa.ForeignKey('profesionales.id'), nullable=False),
        sa.Column('box_id', sa.String(length=64), sa.ForeignKey('boxes.id'), nullable=False),
        sa.Column('inicio_minuto', sa.BigInteger(), nullable=False),
        sa.Column('fin_minuto', sa.BigInteger(), nullable=False),
        sa.CheckConstraint('id > 0', name='ck_turnos_id_positivo'),
        sa.CheckConstraint('inicio_minuto < fin_minuto', name='ck_turnos_intervalo'),
    )
    op.create_index('ix_turnos_profesional_inicio', 'turnos', ['profesional_id', 'inicio_minuto'])
    op.create_index('ix_turnos_box_inicio', 'turnos', ['box_id', 'inicio_minuto'])
    op.create_table(
        'agenda_mutex',
        sa.Column('id', sa.SmallInteger(), primary_key=True),
        sa.CheckConstraint('id = 1', name='ck_agenda_mutex_singleton'),
    )
    op.bulk_insert(sa.table('agenda_mutex', sa.column('id', sa.SmallInteger())), [{'id': 1}])


def downgrade() -> None:
    raise RuntimeError('Downgrade destructivo bloqueado; conservar PostgreSQL y recuperar desde SQLite o backup verificado.')
