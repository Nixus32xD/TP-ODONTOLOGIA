from contextlib import closing
from pathlib import Path
import os
import sqlite3
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
from odontologia.audit import ErrorAuditoria


class ApiPacientesTests(unittest.TestCase):
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
        self.secreto = 'secreto-local-pacientes-test-no-reutilizar-2026'
        with patch.dict(os.environ, {
                'JWT_SECRETO': self.secreto, 'ODONTOLOGIA_ENTORNO': 'desarrollo'}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.admin = self._login('admin.one', 'frase-larga-segura-2026')
        self.recepcion = self._login('recepcion.a', 'otra-frase-larga-segura-2026')

    def _login(self, identificador, password):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': password})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def test_recepcion_administra_ficha_y_solo_admin_cambia_estado(self):
        payload = {'nombre': '  Ana   Pérez ', 'telefono': '+54 261 555-0101'}
        creada = self.client.post('/pacientes', headers=self.recepcion, json=payload)
        self.assertEqual(creada.status_code, 201, creada.text)
        paciente = creada.json()
        self.assertEqual(paciente['nombre'], 'Ana Pérez')
        self.assertTrue(paciente['activo'])
        listado = self.client.get('/pacientes?limit=1&offset=0', headers=self.recepcion)
        self.assertEqual(listado.status_code, 200, listado.text)
        self.assertEqual((listado.json()['limit'], listado.json()['offset']), (1, 0))
        self.assertEqual(len(listado.json()['items']), 1)
        self.assertEqual(self.client.get(
            f"/pacientes/{paciente['id']}", headers=self.recepcion).json(), paciente)
        modificada = self.client.patch(
            f"/pacientes/{paciente['id']}", headers=self.recepcion,
            json={'telefono': None, 'nombre': 'Ana P.'})
        self.assertEqual(modificada.status_code, 200, modificada.text)
        self.assertEqual(modificada.json()['telefono'], None)
        self.assertEqual(self.client.delete(
            f"/pacientes/{paciente['id']}", headers=self.recepcion).status_code, 403)
        baja = self.client.delete(f"/pacientes/{paciente['id']}", headers=self.admin)
        self.assertEqual(baja.status_code, 200, baja.text)
        self.assertFalse(baja.json()['activo'])
        reactivada = self.client.patch(
            f"/pacientes/{paciente['id']}", headers=self.admin, json={'activo': True})
        self.assertEqual(reactivada.status_code, 200, reactivada.text)
        self.assertTrue(reactivada.json()['activo'])

    def test_validacion_auth_y_datos_no_permitidos(self):
        self.assertEqual(self.client.get('/pacientes').status_code, 401)
        self.assertEqual(self.client.post('/pacientes', json={'nombre': 'Ana'}).status_code, 401)
        for payload in (
                {'nombre': '   '}, {'nombre': 'A' * 121},
                {'nombre': 'Ana', 'telefono': 'texto no válido'},
                {'nombre': 'Ana', 'documento': '12345678'},
                {'nombre': 'Ana', 'historia_clinica': 'no debe guardarse'}):
            with self.subTest(payload=payload):
                respuesta = self.client.post('/pacientes', headers=self.admin, json=payload)
                self.assertEqual(respuesta.status_code, 422, respuesta.text)
        self.assertEqual(self.client.get('/pacientes/no-existe', headers=self.admin).status_code, 404)
        self.assertEqual(self.client.get('/pacientes?limit=101', headers=self.admin).status_code, 422)

    def test_consentimiento_paciente_por_admin_y_recepcion_y_denegacion_profesional(self):
        creada = self.client.post('/pacientes', headers=self.recepcion,
                                  json={'nombre': 'Paciente sintético C17'})
        self.assertEqual(creada.status_code, 201, creada.text)
        paciente = creada.json()
        self.assertFalse(paciente['acepta_recordatorios'])

        habilitada = self.client.patch(
            f"/pacientes/{paciente['id']}", headers=self.recepcion,
            json={'acepta_recordatorios': True})
        self.assertEqual(habilitada.status_code, 200, habilitada.text)
        self.assertTrue(habilitada.json()['acepta_recordatorios'])
        deshabilitada = self.client.patch(
            f"/pacientes/{paciente['id']}", headers=self.admin,
            json={'acepta_recordatorios': False})
        self.assertEqual(deshabilitada.status_code, 200, deshabilitada.text)
        self.assertFalse(deshabilitada.json()['acepta_recordatorios'])

        crear_usuario(
            self.engine, 'profesional.c17', 'frase-larga-profesional-2026',
            'profesional', profesional_id='profesional-A', actor_id=None)
        profesional = self._login('profesional.c17', 'frase-larga-profesional-2026')
        denegada = self.client.patch(
            f"/pacientes/{paciente['id']}", headers=profesional,
            json={'acepta_recordatorios': True})
        self.assertEqual(denegada.status_code, 403, denegada.text)
        self.assertEqual(self.client.patch(
            f"/pacientes/{paciente['id']}", headers=self.admin,
            json={'acepta_recordatorios': 'sí'}).status_code, 422)
        self.assertEqual(self.client.patch(
            f"/pacientes/{paciente['id']}", headers=self.admin,
            json={'acepta_recordatorios': True, 'canal': 'whatsapp'}).status_code, 422)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            eventos = conexion.execute(
                "SELECT action, resource_type, resource_id FROM eventos_auditoria "
                "WHERE resource_id=? ORDER BY id", (paciente['id'],)).fetchall()
        self.assertEqual([evento[0] for evento in eventos], [
            'paciente.creado', 'paciente.actualizado', 'paciente.actualizado'])
        self.assertTrue(all(evento[1:] == ('paciente', paciente['id']) for evento in eventos))

    def test_openapi_publica_consentimiento_en_ficha_con_default_false(self):
        esquema = self.client.get('/openapi.json').json()['components']['schemas']

        self.assertIn('acepta_recordatorios', esquema['RespuestaPaciente']['properties'])
        self.assertEqual(
            esquema['SolicitudPaciente']['properties']['acepta_recordatorios']['default'], False)
        self.assertIn(
            'acepta_recordatorios', esquema['ActualizacionPaciente']['properties'])

    def test_turnos_rechaza_paciente_inactivo_y_conserva_historial(self):
        creada = self.client.post('/pacientes', headers=self.admin,
                                  json={'nombre': 'Paciente de prueba'})
        paciente_id = creada.json()['id']
        self.client.delete(f'/pacientes/{paciente_id}', headers=self.admin)
        respuesta = self.client.post('/turnos', headers=self.recepcion, json={
            'paciente_id': paciente_id, 'profesional_id': 'profesional-A', 'box_id': 'box-A',
            'inicio': '2026-11-02T09:00:00-03:00', 'fin': '2026-11-02T09:30:00-03:00'})
        self.assertEqual(respuesta.status_code, 409, respuesta.text)
        self.assertEqual(respuesta.json()['codigo'], 'recurso_inactivo')
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0], 0)

    def test_falla_auditoria_revierte_alta_y_openapi_publica_rutas(self):
        with patch('odontologia.pacientes.registrar_evento_session', side_effect=ErrorAuditoria):
            respuesta = self.client.post(
                '/pacientes', headers=self.admin, json={'nombre': 'No persistir'})
        self.assertEqual(respuesta.status_code, 503)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM pacientes').fetchone()[0], 2)
        esquema = self.client.get('/openapi.json').json()
        self.assertTrue({
            '/pacientes', '/pacientes/{paciente_id}', '/turnos', '/auditoria'
        } <= set(esquema['paths']))
        self.assertEqual(esquema['paths']['/pacientes']['post']['responses']['201']['description'], 'Successful Response')
        self.assertIn(
            'RespuestaPaciente', esquema['paths']['/pacientes']['post']['responses']['201']
            ['content']['application/json']['schema']['$ref'])


if __name__ == '__main__':
    unittest.main()
