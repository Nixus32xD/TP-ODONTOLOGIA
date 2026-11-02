"""Modelo PostgreSQL del contrato de agenda C-01."""

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Identity, Index, Integer, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Paciente(Base):
    __tablename__ = 'pacientes'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)


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
