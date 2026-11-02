"""Adaptador HTTP local de C-01; el dominio conserva reglas y transacciones."""
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
import os

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator

from odontologia import ErrorAgenda, Turno, crear_turno
from odontologia.core.config import cargar_configuracion
from odontologia.auth.almacenamiento import crear_engine_autenticacion, validar_esquema_autenticacion
from odontologia.auth.sesiones import ErrorSesiones, autenticar, cerrar_sesion, validar_sesion
from odontologia.auth.tokens import validar_secreto_jwt
from odontologia.auth.usuarios import (
    ErrorUsuarios, actualizar_usuario, crear_usuario, listar_usuarios,
)
from odontologia.audit import listar_eventos
from odontologia.pacientes import ErrorPacientes, actualizar_paciente, crear_paciente, listar_pacientes, obtener_paciente


class SolicitudTurno(BaseModel):
    model_config = ConfigDict(extra='forbid')
    paciente_id: StrictStr
    profesional_id: StrictStr
    box_id: StrictStr
    inicio: datetime = Field(description='ISO 8601 con T, offset explícito y minuto exacto.')
    fin: datetime = Field(description='ISO 8601 con T, offset explícito, minuto exacto y posterior a inicio.')

    @field_validator('inicio', 'fin', mode='before')
    @classmethod
    def fecha_iso(cls, valor):
        # JSON sólo admite texto ISO; Pydantic acepta epoch numérico por defecto.
        if not isinstance(valor, str) or 'T' not in valor:
            raise ValueError('Se requiere fecha-hora ISO con T y offset explícito.')
        return valor


class ErrorHTTP(BaseModel):
    codigo: str
    campo: str | None
    mensaje: str


class SolicitudLogin(BaseModel):
    model_config = ConfigDict(extra='forbid')
    identificador: StrictStr
    password: StrictStr


class RespuestaLogin(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in: int


class SolicitudUsuario(BaseModel):
    model_config = ConfigDict(extra='forbid')
    identificador: StrictStr
    password: StrictStr
    rol: StrictStr


class ActualizacionUsuario(BaseModel):
    model_config = ConfigDict(extra='forbid')
    rol: StrictStr | None = None
    activo: StrictBool | None = None


class SolicitudPaciente(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: StrictStr
    telefono: StrictStr | None = None


class ActualizacionPaciente(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: StrictStr | None = None
    telefono: StrictStr | None = None
    activo: StrictBool | None = None


class RespuestaPaciente(BaseModel):
    id: StrictStr
    nombre: StrictStr
    telefono: StrictStr | None
    activo: StrictBool


class RespuestaListaPacientes(BaseModel):
    items: list[RespuestaPaciente]
    limit: int
    offset: int


ESTADOS_ERROR = {'entrada_invalida': 422, 'recurso_desconocido': 404,
                 'recurso_inactivo': 409,
                 'conflicto_profesional': 409, 'conflicto_box': 409,
                 'agenda_ocupada': 503, 'almacenamiento_error': 500}


def crear_app(ruta_db: str | Path | None = None, *, timeout_segundos: float = 5.0) -> FastAPI:
    """Crear la API sin abrir conexiones; SQLite sigue siendo el valor predeterminado."""
    engine = None
    secreto_jwt = os.environ.get('JWT_SECRETO')
    algoritmo_jwt = os.environ.get('JWT_ALGORITMO', 'HS256')
    expiracion_jwt = int(os.environ.get('JWT_MINUTOS_EXPIRACION', '30')) * 60
    if ruta_db is not None:
        persistencia = 'sqlite'
        ruta = ruta_db
    else:
        configuracion = cargar_configuracion()
        persistencia = configuracion.persistencia
        ruta = configuracion.odontologia_db
        secreto_jwt = configuracion.jwt_secreto
        algoritmo_jwt = configuracion.jwt_algoritmo
        expiracion_jwt = configuracion.jwt_minutos_expiracion * 60
        if persistencia == 'postgresql':
            from odontologia.db.postgresql import crear_engine

            engine = crear_engine(configuracion.database_url)
    auth_engine = engine or crear_engine_autenticacion('sqlite', None, ruta)

    @asynccontextmanager
    async def lifespan(_app):
        try:
            yield
        finally:
            auth_engine.dispose()

    app = FastAPI(title='Agenda odontológica', version='1.1.0', lifespan=lifespan)
    app.state.persistencia = persistencia
    app.state.auth_engine = auth_engine
    bearer = HTTPBearer(auto_error=False)

    @app.exception_handler(ErrorAgenda)
    async def error_dominio(request: Request, exc: ErrorAgenda):
        return JSONResponse(status_code=ESTADOS_ERROR[exc.codigo], content={
            'codigo': exc.codigo, 'campo': exc.campo, 'mensaje': str(exc)})

    @app.exception_handler(RequestValidationError)
    async def error_entrada(request: Request, exc: RequestValidationError):
        ubicacion = exc.errors()[0]['loc']
        campo = str(ubicacion[-1]) if len(ubicacion) > 1 else None
        return JSONResponse(status_code=422, content={
            'codigo': 'entrada_invalida', 'campo': campo,
            'mensaje': 'El cuerpo JSON no cumple el contrato.'})

    @app.exception_handler(ErrorSesiones)
    async def error_sesion(request: Request, exc: ErrorSesiones):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorUsuarios)
    async def error_usuario(request: Request, exc: ErrorUsuarios):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorPacientes)
    async def error_paciente(request: Request, exc: ErrorPacientes):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    def verificar_configuracion():
        try:
            return validar_secreto_jwt(secreto_jwt, algoritmo_jwt)
        except ValueError as exc:
            raise ErrorSesiones(
                'autenticacion_no_configurada', 'La autenticación no está configurada.', 503) from exc

    def asegurar_esquema() -> None:
        try:
            validar_esquema_autenticacion(
                auth_engine, persistencia, ruta if persistencia == 'sqlite' else None)
        except (RuntimeError, ValueError) as exc:
            raise ErrorSesiones(
                'autenticacion_no_configurada', 'El esquema de autenticación no está preparado.', 503) from exc

    def identidad_actual(credenciales: HTTPAuthorizationCredentials | None = Depends(bearer)):
        secreto = verificar_configuracion()
        if credenciales is None or credenciales.scheme.casefold() != 'bearer':
            raise ErrorSesiones('autenticacion_requerida', 'Se requiere autenticación.', 401)
        asegurar_esquema()
        return validar_sesion(auth_engine, credenciales.credentials, secreto)

    def administrador(identidad=Depends(identidad_actual)):
        if identidad['rol'] != 'administrador':
            raise ErrorSesiones('permiso_denegado', 'No tiene permiso para esta operación.', 403)
        return identidad

    def personal_operativo(identidad=Depends(identidad_actual)):
        if identidad['rol'] not in {'administrador', 'recepcion'}:
            raise ErrorSesiones('permiso_denegado', 'No tiene permiso para esta operación.', 403)
        return identidad

    respuestas_auth = {
        401: {'model': ErrorHTTP, 'description': 'Autenticación requerida o sesión inválida.'},
        403: {'model': ErrorHTTP, 'description': 'Permiso insuficiente.'},
        503: {'model': ErrorHTTP, 'description': 'Autenticación o almacenamiento no disponible.'},
    }

    @app.post('/turnos', status_code=201, response_model=Turno,
              responses={**{estado: {'model': ErrorHTTP}
                           for estado in set(ESTADOS_ERROR.values())}, **respuestas_auth})
    def alta(solicitud: SolicitudTurno, _identidad=Depends(identidad_actual)):
        if engine is not None:
            from odontologia.db.postgresql import crear_turno_postgresql

            return crear_turno_postgresql(
                engine, **solicitud.model_dump(), timeout_segundos=timeout_segundos,
                actor_id=_identidad['usuario_id'])
        return crear_turno(
            ruta, **solicitud.model_dump(), timeout_segundos=timeout_segundos,
            actor_id=_identidad['usuario_id'])

    @app.post('/sesiones', response_model=RespuestaLogin, responses={
        401: {'model': ErrorHTTP, 'description': 'Credenciales inválidas.'},
        422: {'model': ErrorHTTP}, 503: {'model': ErrorHTTP},
    })
    def iniciar_sesion(solicitud: SolicitudLogin):
        secreto = verificar_configuracion()
        asegurar_esquema()
        token = autenticar(
            auth_engine, solicitud.identificador, solicitud.password, secreto,
            duracion_segundos=expiracion_jwt)
        return {'access_token': token, 'expires_in': expiracion_jwt}

    @app.get('/sesiones/actual', responses=respuestas_auth)
    def sesion_actual(identidad=Depends(identidad_actual)):
        return identidad

    @app.delete('/sesiones/actual', status_code=204, responses=respuestas_auth)
    def salir(identidad=Depends(identidad_actual),
              credenciales: HTTPAuthorizationCredentials | None = Depends(bearer)):
        cerrar_sesion(auth_engine, credenciales.credentials, verificar_configuracion())
        return None

    @app.get('/usuarios', responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                                     503: respuestas_auth[503]})
    def usuarios(_identidad=Depends(administrador)):
        asegurar_esquema()
        return listar_usuarios(auth_engine)

    @app.post('/usuarios', status_code=201, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 409: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def alta_usuario(solicitud: SolicitudUsuario, _identidad=Depends(administrador)):
        asegurar_esquema()
        try:
            return crear_usuario(
                auth_engine, solicitud.identificador, solicitud.password, solicitud.rol,
                actor_id=_identidad['usuario_id'])
        except ValueError as exc:
            raise ErrorUsuarios('entrada_invalida', 'Los datos de la cuenta no son válidos.', 422) from exc

    @app.patch('/usuarios/{usuario_id}', responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        409: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def modificar_usuario(usuario_id: str, solicitud: ActualizacionUsuario,
                          _identidad=Depends(administrador)):
        asegurar_esquema()
        if solicitud.rol is None and solicitud.activo is None:
            raise ErrorUsuarios('entrada_invalida', 'Debe informar al menos un cambio.', 422)
        return actualizar_usuario(
            auth_engine, usuario_id, rol=solicitud.rol, activo=solicitud.activo,
            actor_id=_identidad['usuario_id'])

    @app.get('/pacientes', response_model=RespuestaListaPacientes, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403],
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def consulta_pacientes(
            limit: int = Query(default=50, ge=1, le=100),
            offset: int = Query(default=0, ge=0),
            _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return {
            'items': listar_pacientes(auth_engine, limit=limit, offset=offset),
            'limit': limit,
            'offset': offset,
        }

    @app.post('/pacientes', status_code=201, response_model=RespuestaPaciente, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403],
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def alta_paciente(solicitud: SolicitudPaciente,
                      _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return crear_paciente(
            auth_engine, solicitud.nombre, solicitud.telefono,
            actor_id=_identidad['usuario_id'])

    @app.get('/pacientes/{paciente_id}', response_model=RespuestaPaciente, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403],
        404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def ficha_paciente(paciente_id: str, _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return obtener_paciente(auth_engine, paciente_id)

    @app.patch('/pacientes/{paciente_id}', response_model=RespuestaPaciente, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def modificar_paciente(paciente_id: str, solicitud: ActualizacionPaciente,
                            _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        cambios = solicitud.model_dump(exclude_unset=True)
        if not cambios:
            raise ErrorPacientes('entrada_invalida', 'Debe indicar al menos un cambio.', 422)
        if 'activo' in cambios and _identidad['rol'] != 'administrador':
            raise ErrorSesiones('permiso_denegado', 'Sólo Administrador puede cambiar el estado.', 403)
        return actualizar_paciente(
            auth_engine, paciente_id, cambios, actor_id=_identidad['usuario_id'])

    @app.delete('/pacientes/{paciente_id}', response_model=RespuestaPaciente, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403],
        404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def desactivar_paciente(paciente_id: str, _identidad=Depends(administrador)):
        asegurar_esquema()
        return actualizar_paciente(
            auth_engine, paciente_id, {'activo': False}, actor_id=_identidad['usuario_id'])

    @app.get('/auditoria', responses={
        401: respuestas_auth[401], 403: respuestas_auth[403],
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def consulta_auditoria(
            limit: int = Query(default=50, ge=1, le=100),
            offset: int = Query(default=0, ge=0),
            _identidad=Depends(administrador)):
        asegurar_esquema()
        try:
            items = listar_eventos(auth_engine, limit=limit, offset=offset)
        except RuntimeError as exc:
            raise ErrorSesiones(
                'almacenamiento_error', 'La auditoría no está disponible.', 503) from exc
        return {'items': items, 'limit': limit, 'offset': offset}

    @app.get('/health')
    def health() -> dict[str, str]:
        """Liveness del proceso; no afirma disponibilidad de la DB."""
        return {'status': 'ok'}

    return app
