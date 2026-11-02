"""Modelo PostgreSQL del contrato de agenda C-01."""

from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Identity, Index, Integer, SmallInteger, String, UniqueConstraint
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
    __table_args__ = (
        CheckConstraint('length(nombre) BETWEEN 1 AND 120', name='ck_profesionales_nombre'),
        CheckConstraint('activo IN (true, false)', name='ck_profesionales_activo'),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)


class Box(Base):
    __tablename__ = 'boxes'
    __table_args__ = (
        CheckConstraint('length(nombre) BETWEEN 1 AND 120', name='ck_boxes_nombre'),
        CheckConstraint('activo IN (true, false)', name='ck_boxes_activo'),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)


class Prestacion(Base):
    __tablename__ = 'prestaciones'
    __table_args__ = (
        CheckConstraint('length(nombre) BETWEEN 1 AND 120', name='ck_prestaciones_nombre'),
        CheckConstraint('duracion_minutos > 0', name='ck_prestaciones_duracion'),
        CheckConstraint('activo IN (true, false)', name='ck_prestaciones_activo'),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    duracion_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)


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


class HorarioSemanal(Base):
    __tablename__ = 'horarios_semanales'
    __table_args__ = (
        CheckConstraint(
            '(profesional_id IS NOT NULL AND box_id IS NULL) OR '
            '(profesional_id IS NULL AND box_id IS NOT NULL)',
            name='ck_horarios_semanales_un_recurso'),
        CheckConstraint('dia_iso BETWEEN 1 AND 7', name='ck_horarios_semanales_dia'),
        CheckConstraint(
            'inicio_minuto_local >= 0 AND inicio_minuto_local < 1440 AND '
            'fin_minuto_local > 0 AND fin_minuto_local <= 1440 AND '
            'inicio_minuto_local < fin_minuto_local',
            name='ck_horarios_semanales_intervalo'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profesional_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=True)
    box_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey('boxes.id', ondelete='RESTRICT'), nullable=True)
    dia_iso: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    inicio_minuto_local: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fin_minuto_local: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class ExcepcionHorario(Base):
    __tablename__ = 'excepciones_horario'
    __table_args__ = (
        CheckConstraint(
            '(profesional_id IS NOT NULL AND box_id IS NULL) OR '
            '(profesional_id IS NULL AND box_id IS NOT NULL)',
            name='ck_excepciones_horario_un_recurso'),
        UniqueConstraint('profesional_id', 'fecha_local', name='uq_excepciones_horario_profesional_fecha'),
        UniqueConstraint('box_id', 'fecha_local', name='uq_excepciones_horario_box_fecha'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profesional_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=True)
    box_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey('boxes.id', ondelete='RESTRICT'), nullable=True)
    fecha_local: Mapped[date] = mapped_column(Date, nullable=False)


class TramoExcepcion(Base):
    __tablename__ = 'tramos_excepcion'
    __table_args__ = (
        CheckConstraint(
            'inicio_minuto_local >= 0 AND inicio_minuto_local < 1440 AND '
            'fin_minuto_local > 0 AND fin_minuto_local <= 1440 AND '
            'inicio_minuto_local < fin_minuto_local',
            name='ck_tramos_excepcion_intervalo'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    excepcion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('excepciones_horario.id', ondelete='CASCADE'), nullable=False)
    inicio_minuto_local: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fin_minuto_local: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class BloqueoAgenda(Base):
    __tablename__ = 'bloqueos_agenda'
    __table_args__ = (
        CheckConstraint(
            '(profesional_id IS NOT NULL AND box_id IS NULL) OR '
            '(profesional_id IS NULL AND box_id IS NOT NULL)',
            name='ck_bloqueos_agenda_un_recurso'),
        CheckConstraint('inicio_minuto < fin_minuto', name='ck_bloqueos_agenda_intervalo'),
        Index('ix_bloqueos_profesional_intervalo', 'profesional_id', 'inicio_minuto', 'fin_minuto'),
        Index('ix_bloqueos_box_intervalo', 'box_id', 'inicio_minuto', 'fin_minuto'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profesional_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=True)
    box_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey('boxes.id', ondelete='RESTRICT'), nullable=True)
    inicio_minuto: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fin_minuto: Mapped[int] = mapped_column(BigInteger, nullable=False)

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
            "'paciente.desactivado', 'paciente.reactivado', 'profesional.creado', "
            "'profesional.actualizado', 'profesional.desactivado', 'profesional.reactivado', "
            "'box.creado', 'box.actualizado', 'box.desactivado', 'box.reactivado', "
            "'prestacion.creada', 'prestacion.actualizada', 'prestacion.desactivada', "
            "'prestacion.reactivada', 'cuenta.bootstrap', 'cuenta.creada', "
            "'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada')",
            name='ck_eventos_auditoria_action'),
        CheckConstraint(
            "resource_type IN ('turno', 'paciente', 'profesional', 'box', 'prestacion', 'cuenta', 'sesion')",
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
