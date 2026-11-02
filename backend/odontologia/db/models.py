"""Modelo PostgreSQL del contrato de agenda C-01."""

from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Identity, Index, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Paciente(Base):
    __tablename__ = 'pacientes'
    __table_args__ = (
        CheckConstraint('length(nombre) BETWEEN 1 AND 120', name='ck_pacientes_nombre'),
        CheckConstraint('activo IN (true, false)', name='ck_pacientes_activo'),
        CheckConstraint('acepta_recordatorios IN (true, false)',
                        name='ck_pacientes_acepta_recordatorios'),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(32), nullable=True)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    acepta_recordatorios: Mapped[bool] = mapped_column(
        default=False, server_default='false', nullable=False)


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
        CheckConstraint(
            "estado IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",
            name='ck_turnos_estado'),
        CheckConstraint('version > 0', name='ck_turnos_version_positiva'),
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
    estado: Mapped[str] = mapped_column(
        String(16), default='reservado', server_default='reservado', nullable=False)
    version: Mapped[int] = mapped_column(
        Integer, default=1, server_default='1', nullable=False)


class RecordatorioOutbox(Base):
    __tablename__ = 'recordatorios_outbox'
    __table_args__ = (
        CheckConstraint('turno_version > 0', name='ck_recordatorios_turno_version'),
        CheckConstraint('generation > 0', name='ck_recordatorios_generation'),
        CheckConstraint("tipo = 'turno_24h'", name='ck_recordatorios_tipo'),
        CheckConstraint(
            "estado IN ('pendiente', 'procesado_simulado', 'invalidado', 'fallido')",
            name='ck_recordatorios_estado'),
        CheckConstraint('intentos BETWEEN 0 AND 3', name='ck_recordatorios_intentos'),
        UniqueConstraint(
            'turno_id', 'turno_version', 'tipo', 'generation',
            name='uq_recordatorios_turno_version_tipo_generation'),
        Index('ix_recordatorios_estado_programacion', 'estado', 'programado_para'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    turno_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, 'sqlite'),
        ForeignKey('turnos.id', ondelete='RESTRICT'), nullable=False)
    turno_version: Mapped[int] = mapped_column(Integer, nullable=False)
    generation: Mapped[int] = mapped_column(
        Integer, default=1, server_default='1', nullable=False)
    tipo: Mapped[str] = mapped_column(String(32), nullable=False)
    programado_para: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(String(32), nullable=False)
    intentos: Mapped[int] = mapped_column(Integer, default=0, server_default='0', nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvolucionClinica(Base):
    __tablename__ = 'evoluciones_clinicas'
    __table_args__ = (
        CheckConstraint(
            'length(trim(nota)) BETWEEN 1 AND 5000', name='ck_evoluciones_clinicas_nota'),
        Index('ix_evoluciones_paciente_profesional_creacion',
              'paciente_id', 'profesional_id', 'created_at', 'id'),
        Index('ix_evoluciones_turno', 'turno_id'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paciente_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False)
    profesional_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=False)
    turno_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, 'sqlite'),
        ForeignKey('turnos.id', ondelete='RESTRICT'), nullable=False)
    nota: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    corrige_a_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey('evoluciones_clinicas.id', ondelete='RESTRICT'), nullable=True)


class OdontogramaVersion(Base):
    __tablename__ = 'versiones_odontograma'
    __table_args__ = (
        CheckConstraint('version > 0', name='ck_versiones_odontograma_version_positiva'),
        UniqueConstraint(
            'paciente_id', 'profesional_id', 'version',
            name='uq_versiones_odontograma_paciente_profesional_version'),
        Index('ix_versiones_odontograma_paciente_profesional_version',
              'paciente_id', 'profesional_id', 'version'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paciente_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False)
    profesional_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class HallazgoOdontograma(Base):
    __tablename__ = 'hallazgos_odontograma'
    __table_args__ = (
        CheckConstraint('length(pieza_fdi) = 2', name='ck_hallazgos_odontograma_pieza_largo'),
        CheckConstraint(
            "superficie_fdi IN ('M', 'D', 'O', 'I', 'B', 'V', 'L')",
            name='ck_hallazgos_odontograma_superficie'),
        CheckConstraint(
            'observacion IS NULL OR length(observacion) <= 500',
            name='ck_hallazgos_odontograma_observacion_largo'),
        UniqueConstraint(
            'version_id', 'pieza_fdi', 'superficie_fdi',
            name='uq_hallazgos_odontograma_version_pieza_superficie'),
        Index('ix_hallazgos_odontograma_version_pieza', 'version_id', 'pieza_fdi'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('versiones_odontograma.id', ondelete='RESTRICT'), nullable=False)
    pieza_fdi: Mapped[str] = mapped_column(String(2), nullable=False)
    superficie_fdi: Mapped[str] = mapped_column(String(1), nullable=False)
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlanTratamiento(Base):
    __tablename__ = 'planes_tratamiento'
    __table_args__ = (
        CheckConstraint(
            "estado IN ('propuesto', 'en_curso', 'completado', 'cancelado')",
            name='ck_planes_tratamiento_estado'),
        Index('ix_planes_tratamiento_paciente_profesional_creacion',
              'paciente_id', 'profesional_id', 'created_at', 'id'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paciente_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False)
    profesional_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=False)
    estado: Mapped[str] = mapped_column(
        String(16), default='propuesto', server_default='propuesto', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EtapaPlanTratamiento(Base):
    __tablename__ = 'etapas_plan_tratamiento'
    __table_args__ = (
        CheckConstraint('orden > 0', name='ck_etapas_plan_tratamiento_orden_positiva'),
        UniqueConstraint('plan_id', 'orden', name='uq_etapas_plan_tratamiento_plan_orden'),
        Index('ix_etapas_plan_tratamiento_plan_orden', 'plan_id', 'orden'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('planes_tratamiento.id', ondelete='RESTRICT'), nullable=False)
    prestacion_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('prestaciones.id', ondelete='RESTRICT'), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)


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
        CheckConstraint("rol IN ('administrador', 'recepcion', 'profesional')", name='ck_usuarios_rol'),
        CheckConstraint(
            "(rol = 'profesional' AND profesional_id IS NOT NULL) OR "
            "(rol IN ('administrador', 'recepcion') AND profesional_id IS NULL)",
            name='ck_usuarios_vinculo_profesional'),
        UniqueConstraint('profesional_id', name='uq_usuarios_profesional_id'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    identificador: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    profesional_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey('profesionales.id', ondelete='RESTRICT'), nullable=True)


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
            "action IN ('turno.creado', 'turno.estado_actualizado', 'turno.reprogramado', "
            "'paciente.creado', 'paciente.actualizado', "
            "'paciente.desactivado', 'paciente.reactivado', 'profesional.creado', "
            "'profesional.actualizado', 'profesional.desactivado', 'profesional.reactivado', "
            "'box.creado', 'box.actualizado', 'box.desactivado', 'box.reactivado', "
            "'prestacion.creada', 'prestacion.actualizada', 'prestacion.desactivada', "
            "'prestacion.reactivada', 'cuenta.bootstrap', 'cuenta.creada', "
            "'cuenta.actualizada', 'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada', "
            "'historia.consultada', 'historia.denegada', 'historia.atenciones_listadas', "
            "'evolucion.creada', 'evolucion.corregida', "
            "'odontograma.consultada', 'odontograma.denegada', 'odontograma.version_creada', "
            "'plan.consultado', 'plan.denegado', 'plan.creado', 'plan.estado_actualizado', "
            "'recordatorio.programado', 'recordatorio.invalidado', "
            "'recordatorio.procesado', 'recordatorio.fallo')",
            name='ck_eventos_auditoria_action'),
        CheckConstraint(
            "resource_type IN ('turno', 'paciente', 'profesional', 'box', 'prestacion', "
            "'cuenta', 'sesion', 'historia', 'evolucion', 'odontograma', 'plan', 'recordatorio')",
            name='ck_eventos_auditoria_resource_type'),
        CheckConstraint(
            "result IN ('confirmado', 'rechazado')",
            name='ck_eventos_auditoria_result'),
        CheckConstraint(
            "(action = 'turno.creado' AND resource_type = 'turno' AND result = 'confirmado') OR "
            "(action = 'turno.estado_actualizado' AND resource_type = 'turno' AND result = 'confirmado') OR "
            "(action = 'turno.reprogramado' AND resource_type = 'turno' AND result = 'confirmado') OR "
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
            "(action = 'sesion.rechazada' AND resource_type = 'sesion' AND result = 'rechazado') OR "
            "(action = 'historia.consultada' AND resource_type = 'historia' AND result = 'confirmado') OR "
            "(action = 'historia.denegada' AND resource_type = 'historia' AND result = 'rechazado') OR "
            "(action = 'historia.atenciones_listadas' AND resource_type = 'historia' AND result = 'confirmado') OR "
            "(action = 'evolucion.creada' AND resource_type = 'evolucion' AND result = 'confirmado') OR "
            "(action = 'evolucion.corregida' AND resource_type = 'evolucion' AND result = 'confirmado') OR "
            "(action = 'odontograma.consultada' AND resource_type = 'odontograma' AND result = 'confirmado') OR "
            "(action = 'odontograma.denegada' AND resource_type = 'odontograma' AND result = 'rechazado') OR "
            "(action = 'odontograma.version_creada' AND resource_type = 'odontograma' AND result = 'confirmado') OR "
            "(action = 'plan.consultado' AND resource_type = 'plan' AND result = 'confirmado') OR "
            "(action = 'plan.denegado' AND resource_type = 'plan' AND result = 'rechazado') OR "
            "(action = 'plan.creado' AND resource_type = 'plan' AND result = 'confirmado') OR "
            "(action = 'plan.estado_actualizado' AND resource_type = 'plan' AND result = 'confirmado') OR "
            "(action = 'recordatorio.programado' AND resource_type = 'recordatorio' AND result = 'confirmado') OR "
            "(action = 'recordatorio.invalidado' AND resource_type = 'recordatorio' AND result = 'confirmado') OR "
            "(action = 'recordatorio.procesado' AND resource_type = 'recordatorio' AND result = 'confirmado') OR "
            "(action = 'recordatorio.fallo' AND resource_type = 'recordatorio' AND result = 'rechazado')",
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
