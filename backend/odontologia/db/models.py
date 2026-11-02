"""Modelo PostgreSQL del contrato de agenda C-01."""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Paciente(Base):
    __tablename__ = 'pacientes'
    __table_args__ = (
        CheckConstraint('length(nombre) BETWEEN 1 AND 120', name='ck_pacientes_nombre'),
        CheckConstraint('activo IN (true, false)', name='ck_pacientes_activo'),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(32), nullable=True)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)


class Profesional(Base):
    __tablename__ = 'profesionales'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)


class Box(Base):
    __tablename__ = 'boxes'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)


class Turno(Base):
    __tablename__ = 'turnos'
    __table_args__ = (
        CheckConstraint('id > 0', name='ck_turnos_id_positivo'),
        CheckConstraint('inicio_minuto < fin_minuto', name='ck_turnos_intervalo'),
        Index('ix_turnos_profesional_inicio', 'profesional_id', 'inicio_minuto'),
        Index('ix_turnos_box_inicio', 'box_id', 'inicio_minuto'),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, 'sqlite'), Identity(), primary_key=True)
    paciente_id: Mapped[str] = mapped_column(String(64), ForeignKey('pacientes.id'), nullable=False)
    profesional_id: Mapped[str] = mapped_column(String(64), ForeignKey('profesionales.id'), nullable=False)
    box_id: Mapped[str] = mapped_column(String(64), ForeignKey('boxes.id'), nullable=False)
    inicio_minuto: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fin_minuto: Mapped[int] = mapped_column(BigInteger, nullable=False)


class AgendaMutex(Base):
    __tablename__ = 'agenda_mutex'
    __table_args__ = (CheckConstraint('id = 1', name='ck_agenda_mutex_singleton'),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)

class Usuario(Base):
    __tablename__ = 'usuarios'
    __table_args__ = (
        CheckConstraint("rol IN ('administrador', 'recepcion')", name='ck_usuarios_rol'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identificador: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)


class Sesion(Base):
    __tablename__ = 'sesiones'
    __table_args__ = (
        Index('ix_sesiones_usuario_id', 'usuario_id'),
        Index('ix_sesiones_jti', 'jti', unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    usuario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    jti: Mapped[str] = mapped_column(String(36), nullable=False)
    expira_en: Mapped[int] = mapped_column(BigInteger, nullable=False)
    revocada_en: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    creado_en: Mapped[int] = mapped_column(BigInteger, nullable=False)


class EventoAuditoria(Base):
    __tablename__ = 'eventos_auditoria'
    __table_args__ = (
        CheckConstraint(
            "action IN ('turno.creado', 'paciente.creado', 'paciente.actualizado', "
            "'paciente.desactivado', 'paciente.reactivado', 'cuenta.bootstrap', 'cuenta.creada', "
            "'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada')",
            name='ck_eventos_auditoria_action'),
        CheckConstraint(
            "resource_type IN ('turno', 'paciente', 'cuenta', 'sesion')",
            name='ck_eventos_auditoria_resource_type'),
        CheckConstraint(
            "result IN ('confirmado', 'rechazado')",
            name='ck_eventos_auditoria_result'),
        CheckConstraint(
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
            "(action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado')",
            name='ck_eventos_auditoria_combinacion'),
        CheckConstraint(
            "resource_type != 'sesion' OR resource_id IS NULL",
            name='ck_eventos_auditoria_sin_id_sesion'),
        CheckConstraint(
            "action != 'sesion.rechazada' OR (actor_id IS NULL AND resource_id IS NULL)",
            name='ck_eventos_auditoria_rechazo_generico'),
        Index('ix_eventos_auditoria_fecha_id', 'created_at', 'id'),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, 'sqlite'),
                                    Identity(), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey('usuarios.id', ondelete='RESTRICT'), nullable=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(16), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    result: Mapped[str] = mapped_column(String(12), nullable=False)
