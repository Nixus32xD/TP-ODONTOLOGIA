"""Horarios, excepciones y bloqueos de agenda.

Revision ID: 20261102_0006_agenda_availability
Revises: 20261102_0005_resource_catalogs
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0006_agenda_availability'
down_revision = '20261102_0005_resource_catalogs'
branch_labels = None
depends_on = None


def _crear_recurso_constraints(tabla: str) -> None:
    op.create_check_constraint(
        f'ck_{tabla}_un_recurso', tabla,
        '(profesional_id IS NOT NULL AND box_id IS NULL) OR '
        '(profesional_id IS NULL AND box_id IS NOT NULL)')


def upgrade() -> None:
    # La revisión actual supera el VARCHAR(32) predeterminado de Alembic.
    op.alter_column(
        'alembic_version', 'version_num',
        existing_type=sa.String(length=32), type_=sa.String(length=64),
        existing_nullable=False,
    )

    op.create_table(
        'horarios_semanales',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('profesional_id', sa.String(length=64), nullable=True),
        sa.Column('box_id', sa.String(length=64), nullable=True),
        sa.Column('dia_iso', sa.SmallInteger(), nullable=False),
        sa.Column('inicio_minuto_local', sa.SmallInteger(), nullable=False),
        sa.Column('fin_minuto_local', sa.SmallInteger(), nullable=False),
        sa.CheckConstraint('dia_iso BETWEEN 1 AND 7', name='ck_horarios_semanales_dia'),
        sa.CheckConstraint(
            'inicio_minuto_local >= 0 AND inicio_minuto_local < 1440 AND '
            'fin_minuto_local > 0 AND fin_minuto_local <= 1440 AND '
            'inicio_minuto_local < fin_minuto_local',
            name='ck_horarios_semanales_intervalo'),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['box_id'], ['boxes.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    _crear_recurso_constraints('horarios_semanales')

    op.create_table(
        'excepciones_horario',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('profesional_id', sa.String(length=64), nullable=True),
        sa.Column('box_id', sa.String(length=64), nullable=True),
        sa.Column('fecha_local', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['box_id'], ['boxes.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profesional_id', 'fecha_local', name='uq_excepciones_horario_profesional_fecha'),
        sa.UniqueConstraint('box_id', 'fecha_local', name='uq_excepciones_horario_box_fecha'),
    )
    _crear_recurso_constraints('excepciones_horario')

    op.create_table(
        'tramos_excepcion',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('excepcion_id', sa.String(length=36), nullable=False),
        sa.Column('inicio_minuto_local', sa.SmallInteger(), nullable=False),
        sa.Column('fin_minuto_local', sa.SmallInteger(), nullable=False),
        sa.CheckConstraint(
            'inicio_minuto_local >= 0 AND inicio_minuto_local < 1440 AND '
            'fin_minuto_local > 0 AND fin_minuto_local <= 1440 AND '
            'inicio_minuto_local < fin_minuto_local',
            name='ck_tramos_excepcion_intervalo'),
        sa.ForeignKeyConstraint(['excepcion_id'], ['excepciones_horario.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'bloqueos_agenda',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('profesional_id', sa.String(length=64), nullable=True),
        sa.Column('box_id', sa.String(length=64), nullable=True),
        sa.Column('inicio_minuto', sa.BigInteger(), nullable=False),
        sa.Column('fin_minuto', sa.BigInteger(), nullable=False),
        sa.CheckConstraint('inicio_minuto < fin_minuto', name='ck_bloqueos_agenda_intervalo'),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['box_id'], ['boxes.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    _crear_recurso_constraints('bloqueos_agenda')
    op.create_index(
        'ix_bloqueos_profesional_intervalo', 'bloqueos_agenda',
        ['profesional_id', 'inicio_minuto', 'fin_minuto'])
    op.create_index(
        'ix_bloqueos_box_intervalo', 'bloqueos_agenda',
        ['box_id', 'inicio_minuto', 'fin_minuto'])

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
        "'prestacion.reactivada', 'horario.actualizado', 'excepcion.creada', "
        "'excepcion.actualizada', 'excepcion.eliminada', 'bloqueo.creado', "
        "'bloqueo.eliminado', 'cuenta.bootstrap', 'cuenta.creada', 'cuenta.actualizada', "
        "'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada')")
    op.create_check_constraint(
        'ck_eventos_auditoria_resource_type', 'eventos_auditoria',
        "resource_type IN ('turno', 'paciente', 'profesional', 'box', 'prestacion', "
        "'horario', 'excepcion', 'bloqueo', 'cuenta', 'sesion')")
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
        "(action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado')")


def downgrade() -> None:
    raise RuntimeError(
        'Downgrade destructivo bloqueado; conservar configuración y eventos persistidos.')
