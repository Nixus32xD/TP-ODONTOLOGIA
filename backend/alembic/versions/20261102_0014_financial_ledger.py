"""Ledger financiero sintético e idempotencia de comandos.

Revision ID: 20261102_0014_financial_ledger
Revises: 20261102_0013_patient_self_service
"""
from alembic import op
import sqlalchemy as sa


revision = '20261102_0014_financial_ledger'
down_revision = '20261102_0013_patient_self_service'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from odontologia.db.models import EventoAuditoria

    for nombre in ('ck_eventos_auditoria_action', 'ck_eventos_auditoria_resource_type',
                   'ck_eventos_auditoria_combinacion'):
        op.drop_constraint(nombre, 'eventos_auditoria', type_='check')
    for constraint in EventoAuditoria.__table__.constraints:
        if isinstance(constraint, sa.CheckConstraint) and constraint.name in {
            'ck_eventos_auditoria_action', 'ck_eventos_auditoria_resource_type',
            'ck_eventos_auditoria_combinacion',
        }:
            op.create_check_constraint(constraint.name, 'eventos_auditoria',
                                       str(constraint.sqltext))

    op.create_table(
        'cargos_financieros',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('paciente_id', sa.String(64), nullable=False),
        sa.Column('monto_centavos', sa.BigInteger(), nullable=False),
        sa.Column('concepto', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ondelete='RESTRICT',
                                name='fk_cargos_financieros_paciente_id'),
        sa.CheckConstraint('monto_centavos BETWEEN 1 AND 99999999999',
                           name='ck_cargos_financieros_monto'),
        sa.CheckConstraint('length(trim(concepto)) BETWEEN 1 AND 200',
                           name='ck_cargos_financieros_concepto'),
    )
    op.create_index('ix_cargos_financieros_paciente_fecha_id', 'cargos_financieros',
                    ['paciente_id', 'created_at', 'id'])
    op.create_table(
        'cobros_financieros',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('cargo_id', sa.String(36), nullable=False),
        sa.Column('monto_centavos', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cargo_id'], ['cargos_financieros.id'], ondelete='RESTRICT',
                                name='fk_cobros_financieros_cargo_id'),
        sa.CheckConstraint('monto_centavos BETWEEN 1 AND 99999999999',
                           name='ck_cobros_financieros_monto'),
    )
    op.create_index('ix_cobros_financieros_cargo_fecha_id', 'cobros_financieros',
                    ['cargo_id', 'created_at', 'id'])
    op.create_table(
        'reversiones_cobros',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('cobro_id', sa.String(36), nullable=False),
        sa.Column('monto_centavos', sa.BigInteger(), nullable=False),
        sa.Column('motivo', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cobro_id'], ['cobros_financieros.id'], ondelete='RESTRICT',
                                name='fk_reversiones_cobros_cobro_id'),
        sa.CheckConstraint('monto_centavos BETWEEN 1 AND 99999999999',
                           name='ck_reversiones_cobros_monto'),
        sa.CheckConstraint('length(trim(motivo)) BETWEEN 1 AND 500',
                           name='ck_reversiones_cobros_motivo'),
    )
    op.create_index('ix_reversiones_cobros_cobro_fecha_id', 'reversiones_cobros',
                    ['cobro_id', 'created_at', 'id'])
    op.create_table(
        'idempotencia_financiera',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('actor_id', sa.String(36), nullable=False),
        sa.Column('operacion', sa.String(16), nullable=False),
        sa.Column('clave', sa.String(128), nullable=False),
        sa.Column('fingerprint', sa.String(64), nullable=False),
        sa.Column('respuesta_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['usuarios.id'], ondelete='RESTRICT',
                                name='fk_idempotencia_financiera_actor_id'),
        sa.CheckConstraint("operacion IN ('cargo', 'cobro', 'reversion')",
                           name='ck_idempotencia_financiera_operacion'),
        sa.CheckConstraint('length(clave) BETWEEN 1 AND 128',
                           name='ck_idempotencia_financiera_clave'),
        sa.CheckConstraint('length(fingerprint) = 64',
                           name='ck_idempotencia_financiera_fingerprint'),
        sa.UniqueConstraint('actor_id', 'operacion', 'clave',
                            name='uq_idempotencia_financiera_actor_operacion_clave'),
    )
    op.execute('''
        CREATE FUNCTION impedir_cambio_ledger_financiero() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'ledger financiero es append-only';
        END;
        $$ LANGUAGE plpgsql
    ''')
    for tabla in ('cargos_financieros', 'cobros_financieros', 'reversiones_cobros'):
        op.execute(f'''CREATE TRIGGER {tabla}_append_only
            BEFORE UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION impedir_cambio_ledger_financiero()''')


def downgrade() -> None:
    raise RuntimeError('Downgrade destructivo bloqueado; conservar ledger y idempotencia.')
