import json
import logging
import os
import sqlite3
from contextlib import closing
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi import Request
from fastapi.testclient import TestClient

from odontologia import inicializar_agenda
from odontologia.api import crear_app
from odontologia.db.readiness import comprobar_conectividad


class ObservabilidadTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        with patch.dict(os.environ, {
                'JWT_SECRETO': 'secreto-local-de-prueba-no-reutilizar-2026'}, clear=True):
            self.app = crear_app(os.path.join(self.temporal.name, 'agenda.sqlite3'))

    def cliente(self, app=None):
        return TestClient(app or self.app, raise_server_exceptions=False)

    def test_request_id_valido_se_canonicaliza_y_se_devuelve(self):
        identificador = 'A0B1C2D3-E4F5-4678-9ABC-DEF012345678'
        with self.cliente() as client:
            respuesta = client.get('/health', headers={'X-Request-ID': identificador})
        self.assertEqual(respuesta.headers['X-Request-ID'], str(UUID(identificador)))

    def test_request_id_ausente_o_invalido_se_reemplaza_por_uuid_nuevo(self):
        with self.cliente() as client:
            ausente = client.get('/health')
            invalido = client.get('/health', headers={'X-Request-ID': 'sentinela-invalida'})
            excesivo = client.get('/health', headers={'X-Request-ID': 'x' * 1000})
            duplicado = client.get('/health', headers=[
                ('X-Request-ID', 'A0B1C2D3-E4F5-4678-9ABC-DEF012345678'),
                ('X-Request-ID', 'otro-valor'),
            ])
        UUID(ausente.headers['X-Request-ID'])
        UUID(invalido.headers['X-Request-ID'])
        UUID(excesivo.headers['X-Request-ID'])
        UUID(duplicado.headers['X-Request-ID'])
        self.assertNotEqual(invalido.headers['X-Request-ID'], 'sentinela-invalida')
        self.assertNotEqual(duplicado.headers['X-Request-ID'],
                            'a0b1c2d3-e4f5-4678-9abc-def012345678')

    def test_log_contiene_solo_campos_allowlist_y_no_datos_crudos(self):
        @self.app.post('/sensible/{recurso_id}')
        async def sensible(recurso_id: str, request: Request):
            return {'ok': True}

        secretos = ('ruta-centinela', 'query-centinela', 'body-centinela', 'header-centinela')
        with self.cliente() as client, self.assertLogs('uvicorn.error', level='INFO') as logs:
            respuesta = client.post(
                f'/sensible/{secretos[0]}?dato={secretos[1]}',
                content=secretos[2], headers={'X-Secreto': secretos[3]},
            )
        self.assertEqual(respuesta.status_code, 200)
        evento = json.loads(logs.records[0].getMessage())
        self.assertEqual(set(evento), {
            'request_id', 'method', 'route', 'status', 'duration_ms', 'code'})
        self.assertEqual(evento['route'], '/sensible/{recurso_id}')
        self.assertEqual(evento['status'], 200)
        for secreto in secretos:
            self.assertNotIn(secreto, logs.output[0])
        self.assertNotIn('testclient', logs.output[0])

    def test_log_de_solicitud_no_autorizada_usa_codigo_http_estable(self):
        with self.cliente() as client, self.assertLogs('uvicorn.error', level='INFO') as logs:
            respuesta = client.get('/usuarios')
        self.assertEqual(respuesta.status_code, 401)
        evento = json.loads(logs.records[0].getMessage())
        self.assertEqual(evento['route'], '/usuarios')
        self.assertEqual(evento['status'], 401)
        self.assertEqual(evento['code'], 'unauthorized')

    def test_ruta_no_encontrada_no_registra_path_crudo_y_conserva_id(self):
        ruta_privada = '/no-existe/dato-centinela'
        with self.cliente() as client, self.assertLogs('uvicorn.error', level='INFO') as logs:
            respuesta = client.get(ruta_privada)
        self.assertEqual(respuesta.status_code, 404)
        evento = json.loads(logs.records[0].getMessage())
        self.assertEqual(evento['route'], '<unmatched>')
        self.assertNotIn('dato-centinela', logs.records[0].getMessage())
        self.assertEqual(evento['request_id'], respuesta.headers['X-Request-ID'])

    def test_ready_consulta_db_sin_crearla_y_health_sigue_siendo_liveness(self):
        inicializar_agenda(os.path.join(self.temporal.name, 'agenda.sqlite3'))
        with closing(sqlite3.connect(os.path.join(self.temporal.name, 'agenda.sqlite3'))) as db:
            esquema_antes = db.execute(
                "SELECT name, sql FROM sqlite_master ORDER BY name").fetchall()
        with self.cliente() as client:
            preparada = client.get('/ready')
            health = client.get('/health')
        self.assertEqual(preparada.status_code, 200)
        self.assertEqual(preparada.json(), {'status': 'ready'})
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {'status': 'ok'})
        with closing(sqlite3.connect(os.path.join(self.temporal.name, 'agenda.sqlite3'))) as db:
            self.assertEqual(db.execute(
                "SELECT name, sql FROM sqlite_master ORDER BY name").fetchall(), esquema_antes)

        ruta_ausente = self.temporal.name + '/no-creada.sqlite3'
        with patch.dict(os.environ, {}, clear=True):
            app_sin_db = crear_app(ruta_ausente)
        with self.cliente(app_sin_db) as client:
            no_disponible = client.get('/ready')
            liveness = client.get('/health')
        self.assertEqual(no_disponible.status_code, 503)
        self.assertEqual(no_disponible.json(), {'codigo': 'base_no_disponible'})
        self.assertEqual(liveness.status_code, 200)
        self.assertFalse(os.path.exists(ruta_ausente))

    def test_probe_postgresql_ejecuta_solamente_select_1(self):
        engine = MagicMock()
        conexion = engine.connect.return_value.__enter__.return_value
        conexion.execute.return_value.scalar_one.return_value = 1
        comprobar_conectividad('postgresql', 'no-usado.sqlite3', engine)
        consulta = conexion.execute.call_args.args[0]
        self.assertEqual(str(consulta), 'SELECT 1')
        self.assertEqual(conexion.execute.call_count, 1)

    def test_ready_postgresql_falla_sin_exponer_error_del_driver(self):
        secreto = 'postgresql+psycopg://usuario:secreto@host/base'
        engine = MagicMock()
        engine.connect.side_effect = RuntimeError(secreto)
        with patch.dict(os.environ, {
                'ODONTOLOGIA_PERSISTENCIA': 'postgresql', 'DATABASE_URL': secreto,
                'JWT_SECRETO': 'secreto-local-de-prueba-no-reutilizar-2026'}, clear=True), \
                patch('odontologia.db.postgresql.crear_engine', return_value=engine):
            app = crear_app()
        with self.cliente(app) as client:
            respuesta = client.get('/ready')
        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(respuesta.json(), {'codigo': 'base_no_disponible'})
        self.assertNotIn(secreto, respuesta.text)

    def test_excepcion_inesperada_es_500_generico_sin_detalle_en_respuesta_o_log(self):
        detalle = 'secreto-excepcion-centinela'

        @self.app.get('/fallo')
        async def fallo():
            raise RuntimeError(detalle)

        with self.cliente() as client, self.assertLogs('uvicorn.error', level='INFO') as logs:
            respuesta = client.get('/fallo')
        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(respuesta.json(), {
            'codigo': 'error_interno', 'mensaje': 'Ocurrió un error interno.'})
        UUID(respuesta.headers['X-Request-ID'])
        self.assertNotIn(detalle, respuesta.text)
        self.assertNotIn(detalle, '\n'.join(logs.output))
        self.assertNotIn('RuntimeError', '\n'.join(logs.output))
        evento = json.loads(logs.records[0].getMessage())
        self.assertEqual(evento['status'], 500)
        self.assertEqual(evento['code'], 'error_interno')
        self.assertEqual(evento['request_id'], respuesta.headers['X-Request-ID'])


if __name__ == '__main__':
    unittest.main()
