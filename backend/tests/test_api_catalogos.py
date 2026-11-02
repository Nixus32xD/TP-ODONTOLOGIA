from pathlib import Path
import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from odontologia import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario
from odontologia.disponibilidad import guardar_horario


class ApiCatalogosTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        crear_primer_administrador(self.engine, 'admin.one', 'frase-larga-segura-2026')
        crear_usuario(self.engine, 'recepcion.a', 'otra-frase-larga-segura-2026', 'recepcion')
        abierto = {str(dia): [{'inicio': '00:00', 'fin': '24:00'}] for dia in range(1, 8)}
        for tipo, recursos in (('profesional', ('profesional-A', 'profesional-B')),
                               ('box', ('box-A', 'box-B'))):
            for recurso in recursos:
                guardar_horario(self.engine, tipo, recurso, abierto)
        self.secreto = 'secreto-local-catalogos-test-no-reutilizar-2026'
        with patch.dict(os.environ, {'JWT_SECRETO': self.secreto}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.admin = self._login('admin.one', 'frase-larga-segura-2026')
        self.recepcion = self._login('recepcion.a', 'otra-frase-larga-segura-2026')

    def _login(self, identificador, password):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': password})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def test_recepcion_administra_los_tres_catalogos_y_solo_admin_cambia_estado(self):
        casos = (
            ('profesionales', {'nombre': 'Dra. Ejemplo'}, 'profesional'),
            ('boxes', {'nombre': 'Box sur'}, 'box'),
            ('prestaciones', {'nombre': 'Consulta ficticia', 'duracion_minutos': 20}, 'prestacion'),
        )
        for ruta, datos, tipo in casos:
            with self.subTest(ruta=ruta):
                creada = self.client.post(f'/{ruta}', headers=self.recepcion, json=datos)
                self.assertEqual(creada.status_code, 201, creada.text)
                recurso = creada.json()
                self.assertTrue(recurso['id'])
                self.assertTrue(recurso['activo'])
                self.assertEqual(self.client.get(
                    f'/{ruta}/{recurso["id"]}', headers=self.recepcion).json(), recurso)
                listado = self.client.get(f'/{ruta}?limit=1&offset=0', headers=self.recepcion)
                self.assertEqual(listado.status_code, 200, listado.text)
                self.assertEqual((listado.json()['limit'], listado.json()['offset']), (1, 0))
                self.assertEqual(len(listado.json()['items']), 1)
                modificada = self.client.patch(
                    f'/{ruta}/{recurso["id"]}', headers=self.recepcion,
                    json={'nombre': 'Nombre corregido'})
                self.assertEqual(modificada.status_code, 200, modificada.text)
                self.assertEqual(modificada.json()['nombre'], 'Nombre corregido')
                self.assertEqual(self.client.patch(
                    f'/{ruta}/{recurso["id"]}', headers=self.recepcion,
                    json={'activo': False}).status_code, 403)
                baja = self.client.patch(
                    f'/{ruta}/{recurso["id"]}', headers=self.admin, json={'activo': False})
                self.assertEqual(baja.status_code, 200, baja.text)
                self.assertFalse(baja.json()['activo'])
                alta = self.client.patch(
                    f'/{ruta}/{recurso["id"]}', headers=self.admin, json={'activo': True})
                self.assertTrue(alta.json()['activo'])

    def test_auth_paginacion_referencias_y_validaciones(self):
        for ruta, payloads in (
                ('profesionales', [{'nombre': '   '}, {'nombre': 'x' * 121},
                                   {'nombre': 'Dra.', 'activo': False}]),
                ('boxes', [{'nombre': ''}, {'nombre': 'x' * 121},
                           {'nombre': 'Box', 'prestacion': 'no'}]),
                ('prestaciones', [
                    {'nombre': 'Servicio', 'duracion_minutos': duracion}
                    for duracion in (None, 0, -1, 1.5, True, '20', 2_147_483_648)]
                    + [{'nombre': 'Servicio', 'duracion_minutos': 20, 'box_id': 'box-A'}]),
        ):
            for payload in payloads:
                with self.subTest(ruta=ruta, payload=payload):
                    self.assertEqual(self.client.post(f'/{ruta}', headers=self.admin,
                                                       json=payload).status_code, 422)
        self.assertEqual(self.client.get('/profesionales').status_code, 401)
        self.assertEqual(self.client.get('/boxes?limit=101', headers=self.admin).status_code, 422)
        self.assertEqual(self.client.get('/prestaciones?offset=-1', headers=self.admin).status_code, 422)
        self.assertEqual(self.client.get('/boxes/no-existe', headers=self.admin).status_code, 404)
        prestacion = self.client.post('/prestaciones', headers=self.admin, json={
            'nombre': 'Servicio', 'duracion_minutos': 30}).json()
        self.assertEqual(self.client.patch(
            f"/prestaciones/{prestacion['id']}", headers=self.admin,
            json={'duracion_minutos': False}).status_code, 422)

    def test_openapi_documenta_rutas_y_turno_c01_no_recibe_prestacion(self):
        esquema = self.client.get('/openapi.json').json()
        self.assertTrue({
            '/profesionales', '/profesionales/{profesional_id}',
            '/boxes', '/boxes/{box_id}', '/prestaciones', '/prestaciones/{prestacion_id}',
        } <= set(esquema['paths']))
        self.assertNotIn('prestacion_id', esquema['components']['schemas']['SolicitudTurno']['properties'])
        props = esquema['components']['schemas']['SolicitudPrestacion']['properties']
        self.assertEqual((props['nombre']['minLength'], props['nombre']['maxLength']), (1, 120))
        self.assertEqual((props['duracion_minutos']['minimum'],
                          props['duracion_minutos']['maximum']), (1, 2_147_483_647))
        alta = self.client.post('/turnos', headers=self.recepcion, json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A', 'box_id': 'box-A',
            'inicio': '2026-11-02T09:00:00-03:00', 'fin': '2026-11-02T09:30:00-03:00'})
        self.assertEqual(alta.status_code, 201, alta.text)

    def test_turnos_rechazan_catalogos_inactivos_y_priorizan_referencias_desconocidas(self):
        def solicitar(paciente_id, profesional_id, box_id, hora):
            return self.client.post('/turnos', headers=self.recepcion, json={
                'paciente_id': paciente_id, 'profesional_id': profesional_id, 'box_id': box_id,
                'inicio': f'2026-11-02T{hora}:00:00-03:00',
                'fin': f'2026-11-02T{hora}:30:00-03:00',
            })

        inicial = solicitar('paciente-A', 'profesional-A', 'box-A', '08')
        self.assertEqual(inicial.status_code, 201, inicial.text)
        self.assertEqual(self.client.patch(
            '/profesionales/profesional-A', headers=self.admin,
            json={'activo': False}).status_code, 200)
        inactivo_profesional = solicitar('paciente-A', 'profesional-A', 'box-B', '09')
        self.assertEqual(inactivo_profesional.status_code, 409, inactivo_profesional.text)
        self.assertEqual(inactivo_profesional.json()['codigo'], 'recurso_inactivo')
        self.assertEqual(inactivo_profesional.json()['campo'], 'profesional')

        self.assertEqual(self.client.patch(
            '/boxes/box-A', headers=self.admin, json={'activo': False}).status_code, 200)
        inactivo_box = solicitar('paciente-B', 'profesional-B', 'box-A', '09')
        self.assertEqual(inactivo_box.status_code, 409, inactivo_box.text)
        self.assertEqual(inactivo_box.json()['campo'], 'box')

        self.assertEqual(self.client.delete('/pacientes/paciente-A', headers=self.admin).status_code, 200)
        desconocido = solicitar('paciente-A', 'profesional-inexistente', 'box-A', '10')
        self.assertEqual(desconocido.status_code, 404, desconocido.text)
        self.assertEqual(desconocido.json()['codigo'], 'recurso_desconocido')
        self.assertEqual(desconocido.json()['campo'], 'profesional')

        self.assertEqual(self.client.get('/auditoria', headers=self.admin).json()['items'][0]['action'],
                         'paciente.desactivado')


if __name__ == '__main__':
    unittest.main()
