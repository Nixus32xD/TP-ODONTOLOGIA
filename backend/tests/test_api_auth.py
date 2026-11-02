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

    def filas_auditoria(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return conexion.execute('SELECT COUNT(*) FROM eventos_auditoria').fetchone()[0]

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

    def test_administrador_asigna_vinculo_profesional_al_crear_y_actualizar_cuenta(self):
        alta = self.client.post('/usuarios', headers=self.admin, json={
            'identificador': 'profesional.a',
            'password': 'otra-frase-larga-segura-2026',
            'rol': 'profesional', 'profesional_id': 'profesional-A'})
        self.assertEqual(alta.status_code, 201, alta.text)
        self.assertEqual(alta.json()['profesional_id'], 'profesional-A')

        recepcion = self.client.post('/usuarios', headers=self.admin, json={
            'identificador': 'recepcion.vinculo',
            'password': 'frase-distinta-segura-2026', 'rol': 'recepcion'})
        self.assertEqual(recepcion.status_code, 201, recepcion.text)
        actualizado = self.client.patch(
            f"/usuarios/{recepcion.json()['id']}", headers=self.admin,
            json={'rol': 'profesional', 'profesional_id': 'profesional-B'})
        self.assertEqual(actualizado.status_code, 200, actualizado.text)
        self.assertEqual((actualizado.json()['rol'], actualizado.json()['profesional_id']),
                         ('profesional', 'profesional-B'))

    def test_profesional_autenticado_expone_solo_su_vinculo_y_no_puede_escribir(self):
        alta = self.client.post('/usuarios', headers=self.admin, json={
            'identificador': 'profesional.a',
            'password': 'otra-frase-segura-2026',
            'rol': 'profesional', 'profesional_id': 'profesional-A'})
        self.assertEqual(alta.status_code, 201, alta.text)
        token = self.login('profesional.a', 'otra-frase-segura-2026')
        identidad = self.client.get('/sesiones/actual', headers=token)
        self.assertEqual(identidad.status_code, 200, identidad.text)
        self.assertEqual(identidad.json()['profesional_id'], 'profesional-A')

        turno = self.client.post('/turnos', headers=token, json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A',
            'box_id': 'box-A', 'inicio': '2026-10-15T09:00:00-03:00',
            'fin': '2026-10-15T09:30:00-03:00'})
        self.assertEqual(turno.status_code, 403, turno.text)
        self.assertEqual(self.filas_turno(), 0)

    def test_consulta_turnos_paginada_por_personal_y_limitada_al_vinculo_profesional(self):
        for profesional_id, hora_inicio, hora_fin in (
                ('profesional-A', '09:00', '09:30'),
                ('profesional-B', '10:00', '10:30')):
            inicio = f'2026-10-15T{hora_inicio}:00-03:00'
            fin = f'2026-10-15T{hora_fin}:00-03:00'
            creada = self.client.post('/turnos', headers=self.admin, json={
                'paciente_id': 'paciente-A', 'profesional_id': profesional_id,
                'box_id': 'box-A' if profesional_id.endswith('A') else 'box-B',
                'inicio': inicio, 'fin': fin})
            self.assertEqual(creada.status_code, 201, creada.text)
        creada_cuenta = self.client.post('/usuarios', headers=self.admin, json={
            'identificador': 'profesional.a',
            'password': 'otra-frase-segura-2026',
            'rol': 'profesional', 'profesional_id': 'profesional-A'})
        self.assertEqual(creada_cuenta.status_code, 201, creada_cuenta.text)
        profesional = self.login('profesional.a', 'otra-frase-segura-2026')
        rango = ('?desde=2026-10-15T09:00:00-03:00'
                 '&hasta=2026-10-15T11:00:00-03:00&limit=1&offset=0')
        auditoria_antes = self.filas_auditoria()
        personal = self.client.get('/turnos' + rango, headers=self.admin)
        self.assertEqual(personal.status_code, 200, personal.text)
        self.assertEqual((personal.json()['limit'], personal.json()['offset']), (1, 0))
        self.assertEqual(len(personal.json()['items']), 1)
        self.assertIn('profesional_nombre', personal.json()['items'][0])
        self.assertNotIn('telefono', personal.json()['items'][0])

        agenda_propia = self.client.get('/turnos' + rango, headers=profesional)
        self.assertEqual(agenda_propia.status_code, 200, agenda_propia.text)
        self.assertEqual(len(agenda_propia.json()['items']), 1)
        self.assertEqual(set(agenda_propia.json()['items'][0]),
                         {'inicio', 'fin', 'paciente_nombre'})
        ajeno = self.client.get('/turnos' + rango + '&profesional_id=profesional-B',
                                headers=profesional)
        self.assertEqual(ajeno.status_code, 403, ajeno.text)
        self.assertEqual(self.client.get(
            '/turnos?desde=2026-10-15T09:00:00&hasta=2026-10-15T11:00:00-03:00',
            headers=self.admin).status_code, 422)
        self.assertEqual(self.client.get(
            '/turnos' + rango + '&profesional_id=no-existe',
            headers=self.admin).status_code, 404)
        self.assertEqual(self.client.get(
            '/turnos' + rango + '&limit=101', headers=self.admin).status_code, 422)
        self.assertEqual(self.filas_auditoria(), auditoria_antes)

    def test_disponibilidad_consultiva_solo_admite_profesional_vinculado_y_no_mutar(self):
        alta = self.client.post('/usuarios', headers=self.admin, json={
            'identificador': 'profesional.a',
            'password': 'otra-frase-segura-2026',
            'rol': 'profesional', 'profesional_id': 'profesional-A'})
        self.assertEqual(alta.status_code, 201, alta.text)
        profesional = self.login('profesional.a', 'otra-frase-segura-2026')
        recepcion_alta = self.client.post('/usuarios', headers=self.admin, json={
            'identificador': 'recepcion.consulta',
            'password': 'frase-distinta-segura-2026', 'rol': 'recepcion'})
        self.assertEqual(recepcion_alta.status_code, 201, recepcion_alta.text)
        recepcion = self.login('recepcion.consulta', 'frase-distinta-segura-2026')
        url = ('/disponibilidad?fecha=2026-10-15&profesional_id=profesional-A'
               '&box_id=box-A&duracion_minutos=30')
        self.assertEqual(self.client.get(url).status_code, 401)
        turnos_antes, auditoria_antes = self.filas_turno(), self.filas_auditoria()
        administrador = self.client.get(url, headers=self.admin)
        self.assertEqual(administrador.status_code, 200, administrador.text)
        self.assertTrue(administrador.json()['items'])
        propio = self.client.get(url, headers=profesional)
        self.assertEqual(propio.status_code, 200, propio.text)
        ajeno = self.client.get(url.replace('profesional-A', 'profesional-B'),
                                headers=profesional)
        self.assertEqual(ajeno.status_code, 403, ajeno.text)
        self.assertEqual(self.client.get(
            url.replace('duracion_minutos=30', 'duracion_minutos=0'),
            headers=self.admin).status_code, 422)
        self.assertEqual(self.client.get(
            url.replace('fecha=2026-10-15', 'fecha=2026-02-30'),
            headers=self.admin).status_code, 422)
        self.assertEqual(self.client.get(url, headers=recepcion).status_code, 200)
        self.assertEqual(self.client.get(
            '/disponibilidad?fecha=2026-10-15&profesional_id=inexistente'
            '&box_id=box-A&duracion_minutos=30', headers=self.admin).status_code, 404)
        self.assertEqual(self.client.get(
            '/disponibilidad?fecha=2026-10-15&profesional_id=profesional-A'
            '&box_id=box-A', headers=self.admin).status_code, 422)
        esquema = self.client.get('/openapi.json').json()
        self.assertIn('/disponibilidad', esquema['paths'])
        self.assertEqual(self.filas_turno(), turnos_antes)
        self.assertEqual(self.filas_auditoria(), auditoria_antes)

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
