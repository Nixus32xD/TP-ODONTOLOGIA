"""Operaciones de cuentas del personal y bootstrap local."""
import time
from uuid import uuid4

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from odontologia.auth.credenciales import (
    derivar_password,
    normalizar_identificador,
    validar_password,
)
from odontologia.db.models import AgendaMutex, Profesional, Sesion, Usuario
from odontologia.audit import ErrorAuditoria


ROLES_HABILITADOS = {'administrador', 'recepcion', 'profesional'}
_SIN_CAMBIO = object()


class ErrorUsuarios(RuntimeError):
    def __init__(self, codigo: str, mensaje: str, estado: int = 422):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado = estado


def _iniciar_escritura(session: Session) -> None:
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
        return
    mutex = session.scalar(
        select(AgendaMutex.id).where(AgendaMutex.id == 1).with_for_update())
    if mutex != 1:
        raise ErrorUsuarios('almacenamiento_error', 'El esquema de agenda no está preparado.', 503)


def _ahora(ahora: int | None) -> int:
    return int(time.time()) if ahora is None else int(ahora)


def _publico(usuario: Usuario) -> dict[str, object]:
    return {
        'id': usuario.id,
        'identificador': usuario.identificador,
        'rol': usuario.rol,
        'activo': usuario.activo,
        'profesional_id': usuario.profesional_id,
    }


def _validar_vinculo_profesional(session: Session, rol: str,
                                 profesional_id: object,
                                 *, excluir_usuario_id: str | None = None) -> str | None:
    if rol != 'profesional':
        if profesional_id is not None:
            raise ErrorUsuarios(
                'vinculo_profesional_incompatible',
                'Sólo una cuenta Profesional puede tener vínculo profesional.', 422)
        return None
    if (not isinstance(profesional_id, str) or not profesional_id
            or len(profesional_id) > 64 or profesional_id.strip() != profesional_id):
        raise ErrorUsuarios(
            'vinculo_profesional_invalido',
            'La cuenta Profesional requiere un identificador de profesional válido.', 422)
    profesional = session.get(Profesional, profesional_id)
    if profesional is None:
        raise ErrorUsuarios(
            'profesional_desconocido', 'El profesional no existe.', 404)
    if not profesional.activo:
        raise ErrorUsuarios(
            'profesional_inactivo', 'El profesional no está activo.', 409)
    consulta_vinculo = select(Usuario.id).where(
        Usuario.profesional_id == profesional_id)
    if excluir_usuario_id is not None:
        consulta_vinculo = consulta_vinculo.where(Usuario.id != excluir_usuario_id)
    vinculado = session.scalar(consulta_vinculo.limit(1))
    if vinculado is not None:
        raise ErrorUsuarios(
            'profesional_vinculado', 'El profesional ya tiene una cuenta vinculada.', 409)
    return profesional_id


def crear_primer_administrador(engine, identificador: str, password: str) -> dict[str, object]:
    normalizado = normalizar_identificador(identificador)
    validar_password(password)
    password_hash = derivar_password(password)
    usuario = Usuario(
        id=str(uuid4()), identificador=normalizado, password_hash=password_hash,
        rol='administrador', activo=True,
    )
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            admin_activo = session.scalar(
                select(func.count()).select_from(Usuario).where(
                    Usuario.rol == 'administrador', Usuario.activo.is_(True)))
            if admin_activo:
                raise ErrorUsuarios(
                    'administrador_existente', 'Ya existe un Administrador activo.', 409)
            session.add(usuario)
            session.flush()
            from odontologia.audit import registrar_evento_session

            registrar_evento_session(
                session, action='cuenta.bootstrap', resource_type='cuenta',
                resource_id=usuario.id, result='confirmado')
            resultado = _publico(usuario)
        return resultado
    except ErrorUsuarios:
        raise
    except ErrorAuditoria as exc:
        raise ErrorUsuarios('almacenamiento_error', 'No se pudo guardar la cuenta.', 503) from exc
    except IntegrityError as exc:
        raise ErrorUsuarios('identificador_duplicado', 'El identificador ya existe.', 409) from exc
    except SQLAlchemyError as exc:
        raise ErrorUsuarios('almacenamiento_error', 'No se pudo guardar la cuenta.', 503) from exc


def crear_usuario(engine, identificador: str, password: str, rol: str,
                  *, profesional_id: str | None = None,
                  actor_id: str | None = None) -> dict[str, object]:
    normalizado = normalizar_identificador(identificador)
    validar_password(password)
    if not isinstance(rol, str) or rol not in ROLES_HABILITADOS:
        raise ErrorUsuarios('rol_invalido', 'El rol solicitado no está habilitado.', 422)
    usuario = Usuario(
        id=str(uuid4()), identificador=normalizado,
        password_hash=derivar_password(password), rol=rol, activo=True,
    )
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            usuario.profesional_id = _validar_vinculo_profesional(
                session, rol, profesional_id)
            session.add(usuario)
            session.flush()
            if actor_id is not None:
                from odontologia.audit import registrar_evento_session

                registrar_evento_session(
                    session, action='cuenta.creada', resource_type='cuenta',
                    resource_id=usuario.id, actor_id=actor_id, result='confirmado')
            resultado = _publico(usuario)
        return resultado
    except ErrorAuditoria as exc:
        raise ErrorUsuarios('almacenamiento_error', 'No se pudo guardar la cuenta.', 503) from exc
    except IntegrityError as exc:
        if 'profesional_id' in str(getattr(exc, 'orig', exc)):
            raise ErrorUsuarios(
                'profesional_vinculado', 'El profesional ya tiene una cuenta vinculada.', 409
            ) from exc
        raise ErrorUsuarios('identificador_duplicado', 'El identificador ya existe.', 409) from exc
    except SQLAlchemyError as exc:
        raise ErrorUsuarios('almacenamiento_error', 'No se pudo guardar la cuenta.', 503) from exc


def listar_usuarios(engine) -> list[dict[str, object]]:
    try:
        with Session(engine) as session:
            usuarios = session.scalars(select(Usuario).order_by(Usuario.identificador)).all()
            return [_publico(usuario) for usuario in usuarios]
    except SQLAlchemyError as exc:
        raise ErrorUsuarios('almacenamiento_error', 'No se pudo consultar las cuentas.', 503) from exc


def actualizar_usuario(engine, usuario_id: str, *, rol: str | None = None,
                       profesional_id: str | None | object = _SIN_CAMBIO,
                       activo: bool | None = None, ahora: int | None = None,
                       actor_id: str | None = None) -> dict[str, object]:
    if rol is not None and (not isinstance(rol, str) or rol not in ROLES_HABILITADOS):
        raise ErrorUsuarios('rol_invalido', 'El rol solicitado no está habilitado.', 422)
    if activo is not None and not isinstance(activo, bool):
        raise ErrorUsuarios('estado_invalido', 'El estado activo debe ser booleano.', 422)
    instante = _ahora(ahora)
    try:
        with Session(engine) as session, session.begin():
            _iniciar_escritura(session)
            usuario = session.get(Usuario, usuario_id)
            if usuario is None:
                raise ErrorUsuarios('usuario_desconocido', 'La cuenta no existe.', 404)
            perdera_ultimo_admin = (
                usuario.rol == 'administrador' and usuario.activo
                and ((rol is not None and rol != 'administrador') or activo is False)
            )
            if perdera_ultimo_admin:
                administradores_activos = session.scalar(
                    select(func.count()).select_from(Usuario).where(
                        Usuario.rol == 'administrador', Usuario.activo.is_(True)))
                if administradores_activos <= 1:
                    raise ErrorUsuarios(
                        'ultimo_administrador',
                        'No se puede quitar el acceso al último Administrador activo.', 409)
            nuevo_rol = usuario.rol if rol is None else rol
            nuevo_profesional_id = usuario.profesional_id
            if nuevo_rol == 'profesional':
                solicitado = (usuario.profesional_id if profesional_id is _SIN_CAMBIO
                              else profesional_id)
                nuevo_profesional_id = _validar_vinculo_profesional(
                    session, nuevo_rol, solicitado,
                    excluir_usuario_id=usuario_id)
            else:
                if profesional_id is not _SIN_CAMBIO and profesional_id is not None:
                    _validar_vinculo_profesional(session, nuevo_rol, profesional_id)
                nuevo_profesional_id = None
            cambio_vinculo = nuevo_profesional_id != usuario.profesional_id
            cambio_rol = nuevo_rol != usuario.rol
            cambio = cambio_rol or cambio_vinculo or (
                activo is not None and activo != usuario.activo)
            usuario.rol = nuevo_rol
            usuario.profesional_id = nuevo_profesional_id
            if activo is not None:
                usuario.activo = activo
            if cambio:
                session.execute(
                    update(Sesion).where(
                        Sesion.usuario_id == usuario_id,
                        Sesion.revocada_en.is_(None),
                    ).values(revocada_en=instante)
                )
                if actor_id is not None:
                    from odontologia.audit import registrar_evento_session

                    registrar_evento_session(
                        session, action='cuenta.actualizada', resource_type='cuenta',
                        resource_id=usuario.id, actor_id=actor_id, result='confirmado')
            session.flush()
            resultado = _publico(usuario)
        return resultado
    except ErrorUsuarios:
        raise
    except ErrorAuditoria as exc:
        raise ErrorUsuarios('almacenamiento_error', 'No se pudo actualizar la cuenta.', 503) from exc
    except IntegrityError as exc:
        if 'profesional_id' in str(getattr(exc, 'orig', exc)):
            raise ErrorUsuarios(
                'profesional_vinculado', 'El profesional ya tiene una cuenta vinculada.', 409
            ) from exc
        raise ErrorUsuarios('almacenamiento_error', 'No se pudo actualizar la cuenta.', 503) from exc
    except SQLAlchemyError as exc:
        raise ErrorUsuarios('almacenamiento_error', 'No se pudo actualizar la cuenta.', 503) from exc
