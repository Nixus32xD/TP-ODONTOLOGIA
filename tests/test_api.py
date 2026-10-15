"""Contrato HTTP C-01; TestClient ejecuta ASGI sin red externa."""
from pathlib import Path
from contextlib import closing
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
from odontologia import inicializar_agenda
from odontologia.api import crear_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.datos = dict(paciente_id='paciente-A', profesional_id='profesional-A',
                          box_id='box-A', inicio='2026-10-15T09:00:00-03:00',
                          fin='2026-10-15T09:30:00-03:00')

    def filas(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0]

    def test_alta_201_y_persistencia(self):
        respuesta = self.client.post('/turnos', json=self.datos)
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json(), dict(self.datos, id=1,
                         inicio='2026-10-15T12:00:00Z', fin='2026-10-15T12:30:00Z'))
        self.assertEqual(self.filas(), 1)

    def test_adyacencia_y_recursos_independientes(self):
        self.assertEqual(self.client.post('/turnos', json=self.datos).status_code, 201)
        for cambios in [dict(inicio='2026-10-15T12:30:00Z', fin='2026-10-15T13:00:00Z'),
                        dict(profesional_id='profesional-B', box_id='box-B')]:
            self.assertEqual(self.client.post('/turnos', json=dict(self.datos, **cambios)).status_code, 201)
        self.assertEqual(self.filas(), 3)

    def test_conflictos_independientes_y_prioridad(self):
        self.client.post('/turnos', json=self.datos)
        for cambios, codigo in [(dict(box_id='box-B'), 'conflicto_profesional'),
                               (dict(profesional_id='profesional-B'), 'conflicto_box'),
                               ({}, 'conflicto_profesional')]:
            respuesta = self.client.post('/turnos', json=dict(self.datos, **cambios))
            self.assertEqual(respuesta.status_code, 409)
            self.assertEqual(respuesta.json()['codigo'], codigo)
        self.assertEqual(self.filas(), 1)

    def test_recurso_desconocido_404(self):
        for campo in ['paciente_id', 'profesional_id', 'box_id']:
            with self.subTest(campo=campo):
                respuesta = self.client.post('/turnos', json=dict(self.datos, **{campo: 'ausente'}))
                self.assertEqual(respuesta.status_code, 404)
                self.assertEqual(respuesta.json()['codigo'], 'recurso_desconocido')
        self.assertEqual(self.filas(), 0)

    def test_entrada_invalida_sin_coercion(self):
        for cambios in [dict(paciente_id=1), dict(box_id=True), dict(paciente_id=' paciente-A'),
                        dict(inicio=1792065600), dict(inicio='2026-10-15'),
                        dict(inicio='2026-10-15T09:00:00'),
                        dict(inicio='2026-10-15T09:00:01-03:00'),
                        dict(fin=self.datos['inicio']), dict(extra='ignorar')]:
            with self.subTest(cambios=cambios):
                respuesta = self.client.post('/turnos', json=dict(self.datos, **cambios))
                self.assertEqual(respuesta.status_code, 422)
                self.assertEqual(respuesta.json()['codigo'], 'entrada_invalida')
        self.assertEqual(self.filas(), 0)

    def test_cuerpo_faltante_malformado_y_no_objeto(self):
        for kwargs in [{}, {'content': '{'}, {'json': []}, {'json': {}}]:
            with self.subTest(kwargs=kwargs):
                respuesta = self.client.post('/turnos', **kwargs)
                self.assertEqual(respuesta.status_code, 422)
                self.assertEqual(respuesta.json()['codigo'], 'entrada_invalida')
                self.assertNotIn('input', respuesta.text)
        self.assertEqual(self.filas(), 0)

    def test_agenda_ausente_y_no_sqlite_500_sin_fuga(self):
        for nombre in ['ausente.sqlite3', 'invalida.sqlite3']:
            ruta = Path(self.temporal.name) / nombre
            if nombre.startswith('invalida'):
                ruta.write_text('contenido ajeno')
            with TestClient(crear_app(ruta)) as client:
                respuesta = client.post('/turnos', json=self.datos)
            self.assertEqual(respuesta.status_code, 500)
            self.assertEqual(respuesta.json()['codigo'], 'almacenamiento_error')
            self.assertNotIn(self.temporal.name, respuesta.text)
            if nombre.startswith('ausente'):
                self.assertFalse(ruta.exists())
            else:
                self.assertEqual(ruta.read_text(), 'contenido ajeno')

    def test_lock_real_503_y_recuperacion(self):
        with closing(sqlite3.connect(self.ruta, autocommit=True)) as escritor:
            escritor.execute('BEGIN IMMEDIATE')
            with TestClient(crear_app(self.ruta, timeout_segundos=0.05)) as client:
                respuesta = client.post('/turnos', json=self.datos)
                self.assertEqual(respuesta.status_code, 503)
                self.assertEqual(respuesta.json()['codigo'], 'agenda_ocupada')
            escritor.execute('ROLLBACK')
        self.assertEqual(self.filas(), 0)
        self.assertEqual(self.client.post('/turnos', json=self.datos).status_code, 201)

    def test_health_no_crea_agenda_ni_afirma_readiness(self):
        ruta = Path(self.temporal.name) / 'no-creada.sqlite3'
        with TestClient(crear_app(ruta)) as client:
            self.assertEqual(client.get('/health').json(), {'status': 'ok'})
            self.assertEqual(client.get('/health').status_code, 200)
        self.assertFalse(ruta.exists())

    def test_openapi_y_docs(self):
        esquema = self.client.get('/openapi.json')
        self.assertEqual(esquema.status_code, 200)
        rutas = esquema.json()['paths']
        self.assertEqual(set(rutas), {'/turnos', '/health'})
        self.assertEqual(set(rutas['/turnos']), {'post'})
        self.assertEqual(set(rutas['/turnos']['post']['responses']),
                         {'201', '422', '404', '409', '503', '500'})
        modelo = esquema.json()['components']['schemas']['SolicitudTurno']
        self.assertFalse(modelo['additionalProperties'])
        self.assertEqual(modelo['properties']['inicio']['format'], 'date-time')
        self.assertEqual(self.client.get('/docs').status_code, 200)
        self.assertEqual(self.client.get('/redoc').status_code, 200)


if __name__ == '__main__':
    unittest.main()
