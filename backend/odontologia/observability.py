"""Middleware local con correlación y eventos HTTP de campos permitidos."""
import json
import logging
from time import perf_counter
from uuid import UUID, uuid4


_LOGGER = logging.getLogger('uvicorn.error')
_CODIGOS_HTTP = {
    200: 'ok', 201: 'created', 204: 'no_content', 400: 'bad_request',
    401: 'unauthorized', 403: 'forbidden', 404: 'not_found', 409: 'conflict',
    422: 'validation_error', 429: 'rate_limited', 500: 'error_interno',
    503: 'unavailable',
}


def _request_id(scope) -> str:
    valores = [
        contenido.decode('latin-1')
        for nombre, contenido in scope.get('headers', [])
        if nombre.lower() == b'x-request-id'
    ]
    if len(valores) != 1:
        return str(uuid4())
    valor = valores[0]
    try:
        if len(valor) > 36:
            raise ValueError('identificador excesivo')
        return str(UUID(valor))
    except (ValueError, AttributeError):
        return str(uuid4())


def _ruta_template(scope) -> str:
    ruta = scope.get('route')
    plantilla = getattr(ruta, 'path', None)
    return plantilla if isinstance(plantilla, str) else '<unmatched>'


class MiddlewareObservabilidad:
    """Agrega X-Request-ID, respuesta interna genérica y logging allowlisted."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get('type') != 'http':
            await self.app(scope, receive, send)
            return

        request_id = _request_id(scope)
        scope.setdefault('state', {})['request_id'] = request_id
        inicio = perf_counter()
        estado = 500
        respuesta_iniciada = False

        async def enviar_con_id(mensaje):
            nonlocal estado, respuesta_iniciada
            if mensaje['type'] == 'http.response.start':
                estado = mensaje['status']
                respuesta_iniciada = True
                cabeceras = [
                    (nombre, valor) for nombre, valor in mensaje.get('headers', [])
                    if nombre.lower() != b'x-request-id'
                ]
                cabeceras.append((b'x-request-id', request_id.encode('ascii')))
                mensaje = {**mensaje, 'headers': cabeceras}
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar_con_id)
        except Exception:
            if not respuesta_iniciada:
                cuerpo = json.dumps({
                    'codigo': 'error_interno',
                    'mensaje': 'Ocurrió un error interno.',
                }, ensure_ascii=False).encode('utf-8')
                await enviar_con_id({
                    'type': 'http.response.start', 'status': 500,
                    'headers': [(b'content-type', b'application/json; charset=utf-8'),
                                (b'content-length', str(len(cuerpo)).encode('ascii'))],
                })
                await enviar_con_id({
                    'type': 'http.response.body', 'body': cuerpo, 'more_body': False,
                })

        evento = {
            'request_id': request_id,
            'method': scope.get('method', ''),
            'route': _ruta_template(scope),
            'status': estado,
            'duration_ms': round((perf_counter() - inicio) * 1000, 3),
            'code': _CODIGOS_HTTP.get(estado, 'http_response'),
        }
        _LOGGER.info(json.dumps(evento, ensure_ascii=True, separators=(',', ':')))
