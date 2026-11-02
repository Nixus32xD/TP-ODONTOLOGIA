"""Adaptador HTTP local de C-01; el dominio conserva reglas y transacciones."""
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
import os

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator

from odontologia import ErrorAgenda, Turno, crear_turno
from odontologia.core.config import cargar_configuracion
from odontologia.auth.almacenamiento import crear_engine_autenticacion, validar_esquema_autenticacion
from odontologia.auth.limitador_login import LimitadorIntentosLogin
from odontologia.auth.sesiones import ErrorSesiones, autenticar, cerrar_sesion, validar_sesion
from odontologia.auth.tokens import validar_secreto_jwt
from odontologia.db.readiness import comprobar_conectividad
from odontologia.auth.usuarios import (
    ErrorUsuarios, actualizar_usuario, crear_usuario, listar_usuarios,
)
from odontologia.audit import listar_eventos
from odontologia.catalogos import (
    ErrorCatalogos, actualizar_recurso, crear_recurso, listar_recursos, obtener_recurso,
)
from odontologia.consulta_turnos import ErrorConsultaTurnos, listar_turnos
from odontologia.observability import MiddlewareObservabilidad
from odontologia.consulta_disponibilidad import (
    ErrorConsultaDisponibilidad, calcular_opciones_disponibilidad,
)
from odontologia.disponibilidad import (
    ErrorDisponibilidad,
    crear_bloqueo,
    eliminar_bloqueo,
    eliminar_excepcion,
    guardar_excepcion,
    guardar_horario,
    listar_bloqueos,
    obtener_excepcion,
    obtener_horario,
)
from odontologia.pacientes import ErrorPacientes, actualizar_paciente, crear_paciente, listar_pacientes, obtener_paciente
from odontologia.historia_clinica import (
    ErrorHistoriaClinica,
    consultar_historia,
    corregir_evolucion,
    crear_evolucion,
)
from odontologia.odontograma import (
    cambiar_estado_plan_tratamiento,
    consultar_odontograma,
    consultar_planes_tratamiento,
    crear_odontograma,
    crear_plan_tratamiento,
    listar_atenciones_atendidas,
)
from odontologia.turnos import transicionar_estado_turno
from odontologia.portal_paciente import (
    ErrorPortalPaciente,
    cancelar_turno_portal,
    consultar_disponibilidad_portal,
    listar_turnos_portal,
    reprogramar_turno_portal,
    reservar_turno_paciente,
)


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


class RespuestaTurno(BaseModel):
    id: int
    paciente_id: str
    profesional_id: str
    box_id: str
    inicio: datetime
    fin: datetime
    estado: str


class SolicitudReprogramacion(BaseModel):
    model_config = ConfigDict(extra='forbid', json_schema_extra={
        'examples': [{
            'version': 1,
            'inicio': '2026-11-02T10:00:00-03:00',
            'fin': '2026-11-02T10:30:00-03:00',
            'profesional_id': 'profesional-B',
            'box_id': 'box-B',
        }],
    })
    version: StrictInt = Field(gt=0, description='Versión actual devuelta al consultar el turno.')
    inicio: datetime = Field(description='ISO 8601 con offset explícito y minuto exacto.')
    fin: datetime = Field(description='ISO 8601 con offset explícito y minuto exacto.')
    profesional_id: StrictStr
    box_id: StrictStr

    @field_validator('inicio', 'fin', mode='before')
    @classmethod
    def fecha_iso(cls, valor):
        if not isinstance(valor, str) or 'T' not in valor:
            raise ValueError('Se requiere fecha-hora ISO con T y offset explícito.')
        return valor


class RespuestaReprogramacion(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        'examples': [{
            'id': 42,
            'paciente_id': 'paciente-A',
            'profesional_id': 'profesional-B',
            'box_id': 'box-B',
            'inicio': '2026-11-02T13:00:00Z',
            'fin': '2026-11-02T13:30:00Z',
            'estado': 'reservado',
            'version': 2,
        }],
    })
    id: int
    paciente_id: str
    profesional_id: str
    box_id: str
    inicio: datetime
    fin: datetime
    estado: str
    version: int


class RespuestaEstadoTurno(BaseModel):
    id: int
    estado: str


class RespuestaListaTurnos(BaseModel):
    items: list[dict[str, object]]
    limit: int
    offset: int


class SolicitudReservaPortal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    inicio: StrictStr


class SolicitudReprogramacionPortal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: StrictInt = Field(gt=0)
    inicio: StrictStr


class RespuestaTurnoPortal(BaseModel):
    turno_id: StrictInt
    inicio: datetime
    fin: datetime
    estado: StrictStr
    version: StrictInt


class RespuestaListaTurnosPortal(BaseModel):
    items: list[RespuestaTurnoPortal]


class FranjaPortal(BaseModel):
    inicio: datetime
    fin: datetime


class RespuestaDisponibilidadPortal(BaseModel):
    fecha: StrictStr
    items: list[FranjaPortal]


class RespuestaListaDisponibilidad(BaseModel):
    fecha: str
    items: list[dict[str, datetime]]


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
    profesional_id: StrictStr | None = None
    paciente_id: StrictStr | None = None


class ActualizacionUsuario(BaseModel):
    model_config = ConfigDict(extra='forbid')
    rol: StrictStr | None = None
    activo: StrictBool | None = None
    profesional_id: StrictStr | None = None
    paciente_id: StrictStr | None = None


class SolicitudPaciente(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: StrictStr
    telefono: StrictStr | None = None
    acepta_recordatorios: StrictBool = False


class ActualizacionPaciente(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: StrictStr | None = None
    telefono: StrictStr | None = None
    activo: StrictBool | None = None
    acepta_recordatorios: StrictBool | None = None


class RespuestaPaciente(BaseModel):
    id: StrictStr
    nombre: StrictStr
    telefono: StrictStr | None
    activo: StrictBool
    acepta_recordatorios: StrictBool


class RespuestaListaPacientes(BaseModel):
    items: list[RespuestaPaciente]
    limit: int
    offset: int


class SolicitudEvolucion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    turno_id: StrictInt = Field(gt=0)
    nota: StrictStr = Field(min_length=1, max_length=5000)


class SolicitudCorreccion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nota: StrictStr = Field(min_length=1, max_length=5000)


class RespuestaEvolucion(BaseModel):
    id: StrictStr
    paciente_id: StrictStr
    profesional_id: StrictStr
    turno_id: StrictInt
    nota: StrictStr
    created_at: datetime
    corrige_a_id: StrictStr | None


class RespuestaListaEvoluciones(BaseModel):
    items: list[RespuestaEvolucion]
    limit: int
    offset: int


class RespuestaAtencionAtendida(BaseModel):
    turno_id: StrictInt
    paciente_id: StrictStr
    paciente_nombre: StrictStr
    inicio: datetime
    fin: datetime


class RespuestaListaAtencionesAtendidas(BaseModel):
    items: list[RespuestaAtencionAtendida]
    limit: int
    offset: int


class SolicitudHallazgoOdontograma(BaseModel):
    model_config = ConfigDict(extra='forbid')
    pieza_fdi: StrictStr = Field(min_length=2, max_length=2)
    superficies: list[StrictStr] = Field(min_length=1)
    observacion: StrictStr | None = Field(default=None, max_length=500)


class SolicitudOdontograma(BaseModel):
    model_config = ConfigDict(extra='forbid', json_schema_extra={
        'examples': [{
            'hallazgos': [
                {'pieza_fdi': '11', 'superficies': ['M', 'V'],
                 'observacion': 'Observación sintética de ejemplo.'},
            ],
        }],
    })
    hallazgos: list[SolicitudHallazgoOdontograma]


class RespuestaHallazgoOdontograma(BaseModel):
    pieza_fdi: StrictStr
    superficie_fdi: StrictStr
    observacion: StrictStr | None


class RespuestaVersionOdontograma(BaseModel):
    id: StrictStr
    paciente_id: StrictStr
    profesional_id: StrictStr
    version: StrictInt
    created_at: datetime
    hallazgos: list[RespuestaHallazgoOdontograma]


class RespuestaListaVersionesOdontograma(BaseModel):
    items: list[RespuestaVersionOdontograma]
    version_vigente: StrictInt | None


class SolicitudPlanTratamiento(BaseModel):
    model_config = ConfigDict(extra='forbid', json_schema_extra={
        'examples': [{'prestaciones_ids': ['prestacion-sintetica-A', 'prestacion-sintetica-B']}],
    })
    prestaciones_ids: list[StrictStr] = Field(min_length=1)


class SolicitudEstadoPlan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    estado: StrictStr


class RespuestaEtapaPlan(BaseModel):
    orden: StrictInt
    prestacion_id: StrictStr


class RespuestaPlanTratamiento(BaseModel):
    id: StrictStr
    paciente_id: StrictStr
    profesional_id: StrictStr
    estado: StrictStr
    created_at: datetime
    etapas: list[RespuestaEtapaPlan]


class RespuestaListaPlanesTratamiento(BaseModel):
    items: list[RespuestaPlanTratamiento]


class SolicitudRecurso(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: StrictStr = Field(min_length=1, max_length=120)


class SolicitudPrestacion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: StrictStr = Field(min_length=1, max_length=120)
    duracion_minutos: StrictInt = Field(ge=1, le=2_147_483_647)


class ActualizacionRecurso(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: StrictStr | None = Field(default=None, min_length=1, max_length=120)
    activo: StrictBool | None = None


class ActualizacionPrestacion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: StrictStr | None = Field(default=None, min_length=1, max_length=120)
    duracion_minutos: StrictInt | None = Field(
        default=None, ge=1, le=2_147_483_647)
    activo: StrictBool | None = None


class RespuestaRecurso(BaseModel):
    id: StrictStr
    nombre: StrictStr
    activo: StrictBool


class RespuestaPrestacion(RespuestaRecurso):
    duracion_minutos: StrictInt


class RespuestaListaRecursos(BaseModel):
    items: list[RespuestaRecurso]
    limit: int
    offset: int


class RespuestaListaPrestaciones(BaseModel):
    items: list[RespuestaPrestacion]
    limit: int
    offset: int


class TramoHorario(BaseModel):
    model_config = ConfigDict(extra='forbid')
    inicio: StrictStr
    fin: StrictStr


class SolicitudHorario(BaseModel):
    model_config = ConfigDict(extra='forbid', json_schema_extra={
        'examples': [{'dias': {'1': [
            {'inicio': '09:00', 'fin': '12:00'},
            {'inicio': '13:00', 'fin': '17:00'},
        ]}}],
    })
    dias: dict[str, list[TramoHorario]]


class RespuestaHorario(SolicitudHorario):
    tipo_recurso: StrictStr
    recurso_id: StrictStr


class SolicitudExcepcion(BaseModel):
    model_config = ConfigDict(extra='forbid', json_schema_extra={
        'examples': [{'tramos': [{'inicio': '09:00', 'fin': '12:00'}]}],
    })
    tramos: list[TramoHorario]


class RespuestaExcepcion(SolicitudExcepcion):
    id: StrictStr
    tipo_recurso: StrictStr
    recurso_id: StrictStr
    fecha: date


class SolicitudBloqueo(BaseModel):
    model_config = ConfigDict(extra='forbid', json_schema_extra={
        'examples': [{
            'tipo_recurso': 'profesional', 'recurso_id': 'profesional-A',
            'inicio': '2026-11-02T12:00:00Z', 'fin': '2026-11-02T13:00:00Z',
        }],
    })
    tipo_recurso: StrictStr
    recurso_id: StrictStr
    inicio: datetime
    fin: datetime

    @field_validator('inicio', 'fin', mode='before')
    @classmethod
    def fecha_iso_con_offset(cls, valor):
        if not isinstance(valor, str) or 'T' not in valor:
            raise ValueError('Se requiere fecha-hora ISO con T y offset explícito.')
        return valor


class RespuestaBloqueo(BaseModel):
    id: StrictStr
    tipo_recurso: StrictStr
    recurso_id: StrictStr
    inicio: datetime
    fin: datetime


class RespuestaListaBloqueos(BaseModel):
    items: list[RespuestaBloqueo]
    limit: int
    offset: int


ESTADOS_ERROR = {'entrada_invalida': 422, 'recurso_desconocido': 404,
                 'turno_no_encontrado': 404, 'transicion_invalida': 409,
                 'version_desactualizada': 409, 'turno_no_reprogramable': 409,
                 'recurso_inactivo': 409,
                 'fuera_de_disponibilidad': 409, 'turnos_afectados': 409,
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

    documentacion_habilitada = os.environ.get('ODONTOLOGIA_ENTORNO') == 'desarrollo'
    app = FastAPI(
        title='Agenda odontológica', version='1.1.0', lifespan=lifespan,
        docs_url='/docs' if documentacion_habilitada else None,
        redoc_url='/redoc' if documentacion_habilitada else None,
        openapi_url='/openapi.json' if documentacion_habilitada else None,
    )
    app.add_middleware(MiddlewareObservabilidad)
    app.state.persistencia = persistencia
    app.state.auth_engine = auth_engine
    app.state.limitador_login = LimitadorIntentosLogin()
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
        headers = {'Retry-After': str(exc.retry_after)} if exc.retry_after is not None else None
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)}, headers=headers)

    @app.exception_handler(ErrorUsuarios)
    async def error_usuario(request: Request, exc: ErrorUsuarios):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorPacientes)
    async def error_paciente(request: Request, exc: ErrorPacientes):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorHistoriaClinica)
    async def error_historia_clinica(request: Request, exc: ErrorHistoriaClinica):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorCatalogos)
    async def error_catalogo(request: Request, exc: ErrorCatalogos):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorDisponibilidad)
    async def error_disponibilidad(request: Request, exc: ErrorDisponibilidad):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorConsultaTurnos)
    async def error_consulta_turnos(request: Request, exc: ErrorConsultaTurnos):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorConsultaDisponibilidad)
    async def error_consulta_disponibilidad(request: Request, exc: ErrorConsultaDisponibilidad):
        return JSONResponse(status_code=exc.estado, content={
            'codigo': exc.codigo, 'campo': None, 'mensaje': str(exc)})

    @app.exception_handler(ErrorPortalPaciente)
    async def error_portal_paciente(request: Request, exc: ErrorPortalPaciente):
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

    def paciente_portal(identidad=Depends(identidad_actual)):
        if identidad['rol'] != 'paciente' or not identidad.get('paciente_id'):
            try:
                from sqlalchemy.orm import Session

                from odontologia.audit import registrar_evento_session

                with Session(auth_engine) as session, session.begin():
                    registrar_evento_session(
                        session, action='portal.acceso.denegado', resource_type='portal',
                        actor_id=identidad['usuario_id'], result='rechazado')
            except Exception as exc:
                raise ErrorPortalPaciente(
                    'almacenamiento_error', 'No se pudo registrar el acceso.', 503) from exc
            raise ErrorSesiones('permiso_denegado', 'No tiene permiso para esta operación.', 403)
        return identidad

    respuestas_auth = {
        401: {'model': ErrorHTTP, 'description': 'Autenticación requerida o sesión inválida.'},
        403: {'model': ErrorHTTP, 'description': 'Permiso insuficiente.'},
        503: {'model': ErrorHTTP, 'description': 'Autenticación o almacenamiento no disponible.'},
    }

    @app.get('/portal/disponibilidad', response_model=RespuestaDisponibilidadPortal,
             responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                        422: {'model': ErrorHTTP}, 503: respuestas_auth[503]})
    def disponibilidad_portal(fecha: str = Query(..., description='Fecha local dentro de los próximos 31 días.'),
                              identidad=Depends(paciente_portal)):
        asegurar_esquema()
        return consultar_disponibilidad_portal(
            auth_engine, paciente_id=identidad['paciente_id'],
            actor_id=identidad['usuario_id'], fecha=fecha)

    @app.get('/mis-turnos', response_model=RespuestaListaTurnosPortal,
             responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                        503: respuestas_auth[503]})
    def turnos_portal(identidad=Depends(paciente_portal)):
        asegurar_esquema()
        return listar_turnos_portal(
            auth_engine, paciente_id=identidad['paciente_id'],
            actor_id=identidad['usuario_id'])

    @app.post('/mis-turnos', status_code=201, response_model=RespuestaTurnoPortal,
              responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                         409: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                         503: respuestas_auth[503]})
    def reservar_portal(
            solicitud: SolicitudReservaPortal,
            clave: str = Header(..., alias='Idempotency-Key', min_length=1, max_length=128),
            identidad=Depends(paciente_portal)):
        asegurar_esquema()
        return reservar_turno_paciente(
            auth_engine, paciente_id=identidad['paciente_id'],
            actor_id=identidad['usuario_id'], inicio=solicitud.inicio, clave=clave)

    @app.post('/mis-turnos/{turno_id}/cancelacion', response_model=RespuestaTurnoPortal,
              responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                         404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP},
                         422: {'model': ErrorHTTP}, 503: respuestas_auth[503]})
    def cancelar_portal(
            turno_id: int,
            clave: str = Header(..., alias='Idempotency-Key', min_length=1, max_length=128),
            identidad=Depends(paciente_portal)):
        asegurar_esquema()
        return cancelar_turno_portal(
            auth_engine, paciente_id=identidad['paciente_id'],
            actor_id=identidad['usuario_id'], turno_id=turno_id, clave=clave)

    @app.post('/mis-turnos/{turno_id}/reprogramacion', response_model=RespuestaTurnoPortal,
              responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                         404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP},
                         422: {'model': ErrorHTTP}, 503: respuestas_auth[503]})
    def reprogramar_portal(
            turno_id: int, solicitud: SolicitudReprogramacionPortal,
            clave: str = Header(..., alias='Idempotency-Key', min_length=1, max_length=128),
            identidad=Depends(paciente_portal)):
        asegurar_esquema()
        return reprogramar_turno_portal(
            auth_engine, paciente_id=identidad['paciente_id'],
            actor_id=identidad['usuario_id'], turno_id=turno_id,
            version=solicitud.version, inicio=solicitud.inicio, clave=clave)

    @app.get('/turnos', response_model=RespuestaListaTurnos, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def consulta_turnos(
            desde: datetime = Query(..., description='ISO 8601 con offset explícito.'),
            hasta: datetime = Query(..., description='ISO 8601 con offset explícito.'),
            profesional_id: str | None = None, box_id: str | None = None,
            estado: str | None = None, limit: int = Query(default=50, ge=1, le=100),
            offset: int = Query(default=0, ge=0), identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return listar_turnos(
            auth_engine, desde=desde, hasta=hasta, profesional_id=profesional_id,
            box_id=box_id, estado=estado, limit=limit, offset=offset,
            profesional_vinculado_id=(identidad['profesional_id']
                                      if identidad['rol'] == 'profesional' else None))

    @app.get('/disponibilidad', response_model=RespuestaListaDisponibilidad, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def consulta_disponibilidad(
            fecha: str = Query(..., description='Fecha local YYYY-MM-DD.'),
            profesional_id: str = Query(...), box_id: str = Query(...),
            duracion_minutos: int = Query(..., gt=0),
            identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return calcular_opciones_disponibilidad(
            auth_engine, fecha=fecha, profesional_id=profesional_id,
            box_id=box_id, duracion_minutos=duracion_minutos,
            profesional_vinculado_id=(identidad['profesional_id']
                                      if identidad['rol'] == 'profesional' else None))

    @app.post('/turnos', status_code=201, response_model=RespuestaTurno,
              responses={**{estado: {'model': ErrorHTTP}
                           for estado in set(ESTADOS_ERROR.values())}, **respuestas_auth})
    def alta(solicitud: SolicitudTurno, _identidad=Depends(personal_operativo)):
        if engine is not None:
            from odontologia.db.postgresql import crear_turno_postgresql

            turno = crear_turno_postgresql(
                engine, **solicitud.model_dump(), timeout_segundos=timeout_segundos,
                actor_id=_identidad['usuario_id'])
        else:
            turno = crear_turno(
                ruta, **solicitud.model_dump(), timeout_segundos=timeout_segundos,
                actor_id=_identidad['usuario_id'])
        return RespuestaTurno(
            id=turno.id, paciente_id=turno.paciente_id,
            profesional_id=turno.profesional_id, box_id=turno.box_id,
            inicio=turno.inicio, fin=turno.fin, estado='reservado')

    @app.post('/turnos/{turno_id}/reprogramacion',
              response_model=RespuestaReprogramacion, responses={
                  404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP},
                  422: {'model': ErrorHTTP}, 500: {'model': ErrorHTTP},
                  **respuestas_auth,
              })
    def reprogramar(turno_id: int, solicitud: SolicitudReprogramacion,
                    identidad=Depends(personal_operativo)):
        from odontologia.reprogramacion import reprogramar_turno

        asegurar_esquema()
        resultado = reprogramar_turno(
            engine or auth_engine, turno_id,
            version_esperada=solicitud.version,
            inicio=solicitud.inicio, fin=solicitud.fin,
            profesional_id=solicitud.profesional_id, box_id=solicitud.box_id,
            actor_id=identidad['usuario_id'], timeout_segundos=timeout_segundos)
        return RespuestaReprogramacion(**resultado.__dict__)

    def cambiar_estado(turno_id: int, destino: str, identidad):
        return transicionar_estado_turno(
            engine or auth_engine, turno_id, destino,
            actor_id=identidad['usuario_id'], timeout_segundos=timeout_segundos)

    @app.post('/turnos/{turno_id}/confirmacion', response_model=RespuestaEstadoTurno,
              responses={404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP}, **respuestas_auth})
    def confirmar_turno(turno_id: int, identidad=Depends(personal_operativo)):
        return cambiar_estado(turno_id, 'confirmado', identidad)

    @app.post('/turnos/{turno_id}/cancelacion', response_model=RespuestaEstadoTurno,
              responses={404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP}, **respuestas_auth})
    def cancelar_turno(turno_id: int, identidad=Depends(personal_operativo)):
        return cambiar_estado(turno_id, 'cancelado', identidad)

    @app.post('/turnos/{turno_id}/atencion', response_model=RespuestaEstadoTurno,
              responses={404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP}, **respuestas_auth})
    def atender_turno(turno_id: int, identidad=Depends(personal_operativo)):
        return cambiar_estado(turno_id, 'atendido', identidad)

    @app.post('/turnos/{turno_id}/ausencia', response_model=RespuestaEstadoTurno,
              responses={404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP}, **respuestas_auth})
    def marcar_ausente(turno_id: int, identidad=Depends(personal_operativo)):
        return cambiar_estado(turno_id, 'ausente', identidad)

    @app.post('/sesiones', response_model=RespuestaLogin, responses={
        401: {'model': ErrorHTTP, 'description': 'Credenciales inválidas.'},
        422: {'model': ErrorHTTP}, 429: {'model': ErrorHTTP}, 503: {'model': ErrorHTTP},
    })
    def iniciar_sesion(solicitud: SolicitudLogin, request: Request):
        secreto = verificar_configuracion()
        asegurar_esquema()
        origen = request.client.host if request.client is not None else 'desconocido'
        token = autenticar(
            auth_engine, solicitud.identificador, solicitud.password, secreto,
            duracion_segundos=expiracion_jwt,
            limitador=app.state.limitador_login, origen=origen)
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
                profesional_id=solicitud.profesional_id,
                paciente_id=solicitud.paciente_id,
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
        if not solicitud.model_fields_set:
            raise ErrorUsuarios('entrada_invalida', 'Debe informar al menos un cambio.', 422)
        cambios = {
            campo: getattr(solicitud, campo)
            for campo in solicitud.model_fields_set
        }
        return actualizar_usuario(
            auth_engine, usuario_id, **cambios,
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
            solicitud.acepta_recordatorios,
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

    @app.get('/pacientes/{paciente_id}/historia', response_model=RespuestaListaEvoluciones,
             responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                        404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                        503: respuestas_auth[503]})
    def consulta_historia_clinica(
            paciente_id: str, limit: int = Query(default=50, ge=1, le=100),
            offset: int = Query(default=0, ge=0), identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return consultar_historia(
            auth_engine, paciente_id, identidad=identidad, limit=limit, offset=offset)

    @app.post('/pacientes/{paciente_id}/evoluciones', status_code=201,
              response_model=RespuestaEvolucion,
              responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                         404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                         503: respuestas_auth[503]})
    def alta_evolucion_clinica(
            paciente_id: str, solicitud: SolicitudEvolucion,
            identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return crear_evolucion(
            auth_engine, paciente_id=paciente_id, turno_id=solicitud.turno_id,
            nota=solicitud.nota, identidad=identidad)

    @app.post('/evoluciones/{evolucion_id}/correcciones', status_code=201,
              response_model=RespuestaEvolucion,
              responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                         404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                         503: respuestas_auth[503]})
    def correccion_evolucion_clinica(
            evolucion_id: str, solicitud: SolicitudCorreccion,
            identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return corregir_evolucion(
            auth_engine, evolucion_id=evolucion_id, nota=solicitud.nota,
            identidad=identidad)

    @app.get('/profesional/atenciones-atendidas',
             response_model=RespuestaListaAtencionesAtendidas,
             responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                        422: {'model': ErrorHTTP}, 503: respuestas_auth[503]})
    def consulta_atenciones_atendidas(
            limit: int = Query(default=25, ge=1, le=100),
            offset: int = Query(default=0, ge=0), identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return listar_atenciones_atendidas(
            auth_engine, identidad=identidad, limit=limit, offset=offset)

    @app.get('/pacientes/{paciente_id}/odontograma',
             response_model=RespuestaListaVersionesOdontograma,
             responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                        404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                        503: respuestas_auth[503]})
    def consulta_odontograma(
            paciente_id: str, identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return consultar_odontograma(auth_engine, paciente_id, identidad=identidad)

    @app.post('/pacientes/{paciente_id}/odontograma', status_code=201,
              response_model=RespuestaVersionOdontograma,
              responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                         404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                         503: respuestas_auth[503]})
    def alta_version_odontograma(
            paciente_id: str, solicitud: SolicitudOdontograma,
            identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return crear_odontograma(
            auth_engine, paciente_id=paciente_id,
            hallazgos=[hallazgo.model_dump() for hallazgo in solicitud.hallazgos],
            identidad=identidad)

    @app.get('/pacientes/{paciente_id}/planes',
             response_model=RespuestaListaPlanesTratamiento,
             responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                        404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                        503: respuestas_auth[503]})
    def consulta_planes_tratamiento(
            paciente_id: str, identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return consultar_planes_tratamiento(auth_engine, paciente_id, identidad=identidad)

    @app.post('/pacientes/{paciente_id}/planes', status_code=201,
              response_model=RespuestaPlanTratamiento,
              responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                         404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                         503: respuestas_auth[503]})
    def alta_plan_tratamiento(
            paciente_id: str, solicitud: SolicitudPlanTratamiento,
            identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return crear_plan_tratamiento(
            auth_engine, paciente_id=paciente_id,
            prestaciones_ids=solicitud.prestaciones_ids, identidad=identidad)

    @app.patch('/planes/{plan_id}/estado', response_model=RespuestaPlanTratamiento,
               responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                          404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP},
                          422: {'model': ErrorHTTP}, 503: respuestas_auth[503]})
    def cambio_estado_plan(
            plan_id: str, solicitud: SolicitudEstadoPlan,
            identidad=Depends(identidad_actual)):
        asegurar_esquema()
        return cambiar_estado_plan_tratamiento(
            auth_engine, plan_id=plan_id, estado=solicitud.estado, identidad=identidad)

    @app.get('/profesionales', response_model=RespuestaListaRecursos, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 422: {'model': ErrorHTTP},
        503: respuestas_auth[503],
    })
    def consulta_profesionales(limit: int = Query(default=50, ge=1, le=100),
                               offset: int = Query(default=0, ge=0),
                               _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return {'items': listar_recursos(auth_engine, 'profesionales', limit=limit, offset=offset),
                'limit': limit, 'offset': offset}

    @app.post('/profesionales', status_code=201, response_model=RespuestaRecurso, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 422: {'model': ErrorHTTP},
        503: respuestas_auth[503],
    })
    def alta_profesional(solicitud: SolicitudRecurso,
                         _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return crear_recurso(
            auth_engine, 'profesionales', solicitud.model_dump(),
            actor_id=_identidad['usuario_id'])

    @app.get('/profesionales/{profesional_id}', response_model=RespuestaRecurso, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def profesional(profesional_id: str, _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return obtener_recurso(auth_engine, 'profesionales', profesional_id)

    @app.patch('/profesionales/{profesional_id}', response_model=RespuestaRecurso, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def modificar_profesional(profesional_id: str, solicitud: ActualizacionRecurso,
                              _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        cambios = solicitud.model_dump(exclude_unset=True)
        if not cambios:
            raise ErrorCatalogos('entrada_invalida', 'Debe indicar al menos un cambio.', 422)
        if 'activo' in cambios and _identidad['rol'] != 'administrador':
            raise ErrorSesiones('permiso_denegado', 'Sólo Administrador puede cambiar el estado.', 403)
        return actualizar_recurso(
            auth_engine, 'profesionales', profesional_id, cambios,
            actor_id=_identidad['usuario_id'])

    @app.get('/boxes', response_model=RespuestaListaRecursos, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 422: {'model': ErrorHTTP},
        503: respuestas_auth[503],
    })
    def consulta_boxes(limit: int = Query(default=50, ge=1, le=100),
                       offset: int = Query(default=0, ge=0),
                       _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return {'items': listar_recursos(auth_engine, 'boxes', limit=limit, offset=offset),
                'limit': limit, 'offset': offset}

    @app.post('/boxes', status_code=201, response_model=RespuestaRecurso, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 422: {'model': ErrorHTTP},
        503: respuestas_auth[503],
    })
    def alta_box(solicitud: SolicitudRecurso, _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return crear_recurso(
            auth_engine, 'boxes', solicitud.model_dump(), actor_id=_identidad['usuario_id'])

    @app.get('/boxes/{box_id}', response_model=RespuestaRecurso, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def box(box_id: str, _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return obtener_recurso(auth_engine, 'boxes', box_id)

    @app.patch('/boxes/{box_id}', response_model=RespuestaRecurso, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def modificar_box(box_id: str, solicitud: ActualizacionRecurso,
                      _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        cambios = solicitud.model_dump(exclude_unset=True)
        if not cambios:
            raise ErrorCatalogos('entrada_invalida', 'Debe indicar al menos un cambio.', 422)
        if 'activo' in cambios and _identidad['rol'] != 'administrador':
            raise ErrorSesiones('permiso_denegado', 'Sólo Administrador puede cambiar el estado.', 403)
        return actualizar_recurso(
            auth_engine, 'boxes', box_id, cambios, actor_id=_identidad['usuario_id'])

    @app.get('/prestaciones', response_model=RespuestaListaPrestaciones, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 422: {'model': ErrorHTTP},
        503: respuestas_auth[503],
    })
    def consulta_prestaciones(limit: int = Query(default=50, ge=1, le=100),
                              offset: int = Query(default=0, ge=0),
                              _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return {'items': listar_recursos(auth_engine, 'prestaciones', limit=limit, offset=offset),
                'limit': limit, 'offset': offset}

    @app.post('/prestaciones', status_code=201, response_model=RespuestaPrestacion, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 422: {'model': ErrorHTTP},
        503: respuestas_auth[503],
    })
    def alta_prestacion(solicitud: SolicitudPrestacion,
                        _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return crear_recurso(
            auth_engine, 'prestaciones', solicitud.model_dump(), actor_id=_identidad['usuario_id'])

    @app.get('/prestaciones/{prestacion_id}', response_model=RespuestaPrestacion, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def prestacion(prestacion_id: str, _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return obtener_recurso(auth_engine, 'prestaciones', prestacion_id)

    @app.patch('/prestaciones/{prestacion_id}', response_model=RespuestaPrestacion, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def modificar_prestacion(prestacion_id: str, solicitud: ActualizacionPrestacion,
                             _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        cambios = solicitud.model_dump(exclude_unset=True)
        if not cambios:
            raise ErrorCatalogos('entrada_invalida', 'Debe indicar al menos un cambio.', 422)
        if 'activo' in cambios and _identidad['rol'] != 'administrador':
            raise ErrorSesiones('permiso_denegado', 'Sólo Administrador puede cambiar el estado.', 403)
        return actualizar_recurso(
            auth_engine, 'prestaciones', prestacion_id, cambios,
            actor_id=_identidad['usuario_id'])

    @app.get('/horarios/{tipo_recurso}/{recurso_id}', response_model=RespuestaHorario,
             responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                        404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                        503: respuestas_auth[503]})
    def consulta_horario(tipo_recurso: str, recurso_id: str,
                         _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return obtener_horario(auth_engine, tipo_recurso, recurso_id)

    @app.put('/horarios/{tipo_recurso}/{recurso_id}', response_model=RespuestaHorario,
             responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                        404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP},
                        422: {'model': ErrorHTTP}, 503: respuestas_auth[503]})
    def reemplazar_horario(tipo_recurso: str, recurso_id: str, solicitud: SolicitudHorario,
                           _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        dias = {dia: [tramo.model_dump() for tramo in tramos]
                for dia, tramos in solicitud.dias.items()}
        return guardar_horario(
            auth_engine, tipo_recurso, recurso_id, dias,
            actor_id=_identidad['usuario_id'])

    @app.get(
        '/horarios/{tipo_recurso}/{recurso_id}/excepciones/{fecha}',
        response_model=RespuestaExcepcion,
        responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                   404: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP},
                   503: respuestas_auth[503]},
    )
    def consulta_excepcion(tipo_recurso: str, recurso_id: str, fecha: str,
                           _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        resultado = obtener_excepcion(auth_engine, tipo_recurso, recurso_id, fecha)
        if resultado is None:
            raise ErrorDisponibilidad('recurso_desconocido', 'La excepción no existe.', 404)
        return resultado

    @app.put(
        '/horarios/{tipo_recurso}/{recurso_id}/excepciones/{fecha}',
        response_model=RespuestaExcepcion,
        responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                   404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP},
                   422: {'model': ErrorHTTP}, 503: respuestas_auth[503]},
    )
    def reemplazar_excepcion(tipo_recurso: str, recurso_id: str, fecha: str,
                             solicitud: SolicitudExcepcion,
                             _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        tramos = [tramo.model_dump() for tramo in solicitud.tramos]
        return guardar_excepcion(
            auth_engine, tipo_recurso, recurso_id, fecha, tramos,
            actor_id=_identidad['usuario_id'])

    @app.delete(
        '/horarios/{tipo_recurso}/{recurso_id}/excepciones/{fecha}', status_code=204,
        responses={401: respuestas_auth[401], 403: respuestas_auth[403],
                   404: {'model': ErrorHTTP}, 409: {'model': ErrorHTTP},
                   422: {'model': ErrorHTTP}, 503: respuestas_auth[503]},
    )
    def borrar_excepcion(tipo_recurso: str, recurso_id: str, fecha: str,
                         _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        eliminar_excepcion(
            auth_engine, tipo_recurso, recurso_id, fecha,
            actor_id=_identidad['usuario_id'])
        return None

    @app.get('/bloqueos', response_model=RespuestaListaBloqueos, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403],
        422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def consulta_bloqueos(limit: int = Query(default=50, ge=1, le=100),
                          offset: int = Query(default=0, ge=0),
                          _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return {'items': listar_bloqueos(auth_engine, limit=limit, offset=offset),
                'limit': limit, 'offset': offset}

    @app.post('/bloqueos', status_code=201, response_model=RespuestaBloqueo, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        409: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def alta_bloqueo(solicitud: SolicitudBloqueo,
                     _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        return crear_bloqueo(
            auth_engine, solicitud.tipo_recurso, solicitud.recurso_id,
            solicitud.inicio, solicitud.fin, actor_id=_identidad['usuario_id'])

    @app.delete('/bloqueos/{bloqueo_id}', status_code=204, responses={
        401: respuestas_auth[401], 403: respuestas_auth[403], 404: {'model': ErrorHTTP},
        409: {'model': ErrorHTTP}, 422: {'model': ErrorHTTP}, 503: respuestas_auth[503],
    })
    def baja_bloqueo(bloqueo_id: str, _identidad=Depends(personal_operativo)):
        asegurar_esquema()
        eliminar_bloqueo(auth_engine, bloqueo_id, actor_id=_identidad['usuario_id'])
        return None

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

    @app.get('/ready')
    def ready():
        try:
            comprobar_conectividad(persistencia, ruta, auth_engine)
        except Exception:
            return JSONResponse(status_code=503, content={'codigo': 'base_no_disponible'})
        return {'status': 'ready'}

    return app
