"""Adaptador HTTP local de C-01; el dominio conserva reglas y transacciones."""
from datetime import datetime
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from odontologia import ErrorAgenda, Turno, crear_turno


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


ESTADOS_ERROR = {'entrada_invalida': 422, 'recurso_desconocido': 404,
                 'conflicto_profesional': 409, 'conflicto_box': 409,
                 'agenda_ocupada': 503, 'almacenamiento_error': 500}


def crear_app(ruta_db: str | Path | None = None, *, timeout_segundos: float = 5.0) -> FastAPI:
    """No crea DB ni abre conexiones; inicializar_agenda es un paso explícito."""
    ruta = ruta_db if ruta_db is not None else os.environ.get('ODONTOLOGIA_DB', 'agenda.sqlite3')
    app = FastAPI(title='Agenda odontológica — C-01', version='1.0.0')

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

    @app.post('/turnos', status_code=201, response_model=Turno,
              responses={estado: {'model': ErrorHTTP} for estado in set(ESTADOS_ERROR.values())})
    def alta(solicitud: SolicitudTurno):
        return crear_turno(ruta, **solicitud.model_dump(), timeout_segundos=timeout_segundos)

    @app.get('/health')
    def health() -> dict[str, str]:
        """Liveness del proceso; no afirma disponibilidad de la DB."""
        return {'status': 'ok'}

    return app
