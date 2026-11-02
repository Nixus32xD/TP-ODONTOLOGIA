from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from odontologia import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.usuarios import crear_primer_administrador
from odontologia.disponibilidad import guardar_horario


class ApiAutenticacionTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        self.secreto = 'secreto-local-de-prueba-no-reutilizar-2026'
        migrar_sqlite(self.ruta)
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        crear_primer_administrador(engine, 'admin.one', 'frase-larga-segura-2026')
        abierto = {str(dia): [{'inicio': '00:00', 'fin': '24:00'}] for dia in range(1, 8)}
        for tipo, recursos in (('profesional', ('profesional-A', 'profesional-B')),
                               ('box', ('box-A', 'box-B'))):
            for recurso in recursos:
                guardar_horario(engine, tipo, recurso, abierto)
        engine.dispose()
        with patch.dict('os.environ', {'JWT_SECRETO': self.secreto}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.admin = self.login('admin.one', 'frase-larga-segura-2026')

    def login(self, identificador, password):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': password})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def filas_turno(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0]

    def test_health_publica_y_turnos_requiere_identidad_sin_mutar(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        respuesta = self.client.post('/turnos', json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A',
            'box_id': 'box-A', 'inicio': '2026-10-15T09:00:00-03:00',
            'fin': '2026-10-15T09:30:00-03:00'})
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(self.filas_turno(), 0)

    def test_recepcion_y_administrador_pueden_crear_turno_profesional_no_se_habilita(self):
        self.client.post('/usuarios', headers=self.admin, json={
            'identificador': 'recepcion.a', 'password': 'otra-frase-larga-segura-2026',
            'rol': 'recepcion'})
        recepcion = self.login('recepcion.a', 'otra-frase-larga-segura-2026')
        turno = {'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A',
                 'box_id': 'box-A', 'inicio': '2026-10-15T09:00:00-03:00',
                 'fin': '2026-10-15T09:30:00-03:00'}
        self.assertEqual(self.client.post('/turnos', headers=recepcion, json=turno).status_code, 201)
        turno['inicio'] = '2026-10-15T10:00:00-03:00'
        turno['fin'] = '2026-10-15T10:30:00-03:00'
        self.assertEqual(self.client.post('/turnos', headers=self.admin, json=turno).status_code, 201)

    def test_gestion_usuarios_es_solo_admin_y_no_expone_password_hash(self):
        payload = {'identificador': 'recepcion.a', 'password': 'otra-frase-larga-segura-2026',
                   'rol': 'recepcion'}
        self.assertEqual(self.client.get('/usuarios').status_code, 401)
        creada = self.client.post('/usuarios', headers=self.admin, json=payload)
        self.assertEqual(creada.status_code, 201, creada.text)
        self.assertNotIn('password_hash', creada.json())
        recepcion = self.login('recepcion.a', payload['password'])
        identidad = self.client.get('/sesiones/actual', headers=recepcion).json()
        self.assertIn('expira_en', identidad)
        self.assertEqual(self.client.get('/usuarios', headers=recepcion).status_code, 403)
        actualizada = self.client.patch(
            f"/usuarios/{creada.json()['id']}", headers=self.admin, json={'activo': False})
        self.assertEqual(actualizada.status_code, 200, actualizada.text)
        self.assertEqual(self.client.get('/sesiones/actual', headers=recepcion).status_code, 401)
        login_baja = self.client.post('/sesiones', json={
            'identificador': 'recepcion.a', 'password': payload['password']})
        self.assertEqual(login_baja.status_code, 401)
        self.assertEqual(login_baja.json()['codigo'], 'credenciales_invalidas')

    def test_logout_revoca_token_y_documenta_contrato(self):
        self.assertEqual(self.client.get('/sesiones/actual', headers=self.admin).status_code, 200)
        self.assertEqual(self.client.delete('/sesiones/actual', headers=self.admin).status_code, 204)
        self.assertEqual(self.client.get('/sesiones/actual', headers=self.admin).status_code, 401)
        esquema = self.client.get('/openapi.json').json()
        self.assertTrue({'/sesiones', '/sesiones/actual', '/usuarios', '/usuarios/{usuario_id}'}
                        <= set(esquema['paths']))

    def test_sin_secreto_liveness_sigue_publica_y_operaciones_fallan_cerradas(self):
        with patch.dict('os.environ', {}, clear=True):
            app = crear_app(self.ruta)
        with TestClient(app) as client:
            self.assertEqual(client.get('/health').status_code, 200)
            respuesta = client.post('/sesiones', json={
                'identificador': 'admin.one', 'password': 'frase-larga-segura-2026'})
            self.assertEqual(respuesta.status_code, 503)
            self.assertEqual(respuesta.json()['codigo'], 'autenticacion_no_configurada')

    def test_esquema_sqlite_no_migrado_falla_cerrado_sin_ddl(self):
        ruta = Path(self.temporal.name) / 'sin-auth.sqlite3'
        inicializar_agenda(ruta)
        with patch.dict('os.environ', {'JWT_SECRETO': self.secreto}, clear=True):
            app = crear_app(ruta)
        with TestClient(app) as client:
            respuesta = client.post('/sesiones', json={
                'identificador': 'admin.one', 'password': 'frase-larga-segura-2026'})
        self.assertEqual(respuesta.status_code, 503)
        with closing(sqlite3.connect(ruta)) as conexion:
            tablas = {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertFalse({'usuarios', 'sesiones', 'auth_schema_version'} & tablas)


if __name__ == '__main__':
    unittest.main()
