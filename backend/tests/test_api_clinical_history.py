from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from odontologia import crear_turno, inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario


class ApiHistoriaClinicaTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        self.secreto = 'secreto-local-pruebas-historia-clinica-2026'
        inicializar_agenda(self.ruta)
        self.turno = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))
        migrar_sqlite(self.ruta)
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.admin = crear_primer_administrador(
            engine, 'admin.historia', 'frase-larga-segura-2026')
        self.profesional = crear_usuario(
            engine, 'profesional.historia', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A', actor_id=self.admin['id'])
        self.recepcion = crear_usuario(
            engine, 'recepcion.historia', 'frase-larga-segura-2026', 'recepcion',
            actor_id=self.admin['id'])
        engine.dispose()
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute("UPDATE turnos SET estado='atendido' WHERE id=?", (self.turno.id,))
            conexion.commit()
        with patch.dict('os.environ', {
                'JWT_SECRETO': self.secreto, 'ODONTOLOGIA_ENTORNO': 'desarrollo'}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.admin_headers = self.login('admin.historia')
        self.profesional_headers = self.login('profesional.historia')
        self.recepcion_headers = self.login('recepcion.historia')

    def login(self, identificador):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': 'frase-larga-segura-2026'})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def test_profesional_consulta_y_registra_nota_sin_exponer_campos_de_contacto(self):
        alta = self.client.post('/pacientes/paciente-A/evoluciones',
                                headers=self.profesional_headers,
                                json={'turno_id': self.turno.id, 'nota': 'Control ficticio.'})
        self.assertEqual(alta.status_code, 201, alta.text)
        self.assertEqual(alta.json()['nota'], 'Control ficticio.')

        historia = self.client.get(
            '/pacientes/paciente-A/historia', headers=self.profesional_headers)
        self.assertEqual(historia.status_code, 200, historia.text)
        self.assertEqual(len(historia.json()['items']), 1)
        self.assertNotIn('telefono', historia.json()['items'][0])
        self.assertNotIn('nombre', historia.json()['items'][0])

    def test_admin_y_recepcion_no_leen_ni_escriben_clinica_y_denegaciones_se_auditan(self):
        for headers in (self.admin_headers, self.recepcion_headers):
            with self.subTest(role=headers == self.admin_headers):
                lectura = self.client.get('/pacientes/paciente-A/historia', headers=headers)
                escritura = self.client.post('/pacientes/paciente-A/evoluciones', headers=headers,
                                             json={'turno_id': self.turno.id, 'nota': 'No guardar.'})
                self.assertEqual(lectura.status_code, 403)
                self.assertEqual(escritura.status_code, 403)
        auditoria = self.client.get('/auditoria', headers=self.admin_headers)
        self.assertEqual(auditoria.status_code, 200, auditoria.text)
        self.assertTrue(any(
            evento['action'] == 'historia.denegada' and evento['result'] == 'rechazado'
            for evento in auditoria.json()['items']))
        self.assertNotIn('No guardar.', str(auditoria.json()))

    def test_nota_excesiva_o_campos_extra_se_rechazan(self):
        excesiva = self.client.post('/pacientes/paciente-A/evoluciones',
                                    headers=self.profesional_headers,
                                    json={'turno_id': self.turno.id, 'nota': 'x' * 5001})
        extra = self.client.post('/pacientes/paciente-A/evoluciones',
                                 headers=self.profesional_headers,
                                 json={'turno_id': self.turno.id, 'nota': 'Texto ficticio',
                                       'diagnostico': 'caries'})
        self.assertEqual(excesiva.status_code, 422)
        self.assertEqual(extra.status_code, 422)

    def test_limite_de_nota_y_paginacion_de_historia(self):
        primera = self.client.post('/pacientes/paciente-A/evoluciones',
                                   headers=self.profesional_headers,
                                   json={'turno_id': self.turno.id, 'nota': 'x' * 5000})
        segunda = self.client.post('/pacientes/paciente-A/evoluciones',
                                   headers=self.profesional_headers,
                                   json={'turno_id': self.turno.id, 'nota': 'Segunda nota ficticia.'})
        self.assertEqual(primera.status_code, 201, primera.text)
        self.assertEqual(len(primera.json()['nota']), 5000)
        self.assertEqual(segunda.status_code, 201, segunda.text)

        pagina_1 = self.client.get('/pacientes/paciente-A/historia?limit=1&offset=0',
                                   headers=self.profesional_headers)
        pagina_2 = self.client.get('/pacientes/paciente-A/historia?limit=1&offset=1',
                                   headers=self.profesional_headers)
        self.assertEqual(pagina_1.status_code, 200, pagina_1.text)
        self.assertEqual(pagina_2.status_code, 200, pagina_2.text)
        self.assertEqual(len(pagina_1.json()['items']), 1)
        self.assertEqual(len(pagina_2.json()['items']), 1)
        self.assertNotEqual(pagina_1.json()['items'][0]['id'], pagina_2.json()['items'][0]['id'])
        self.assertEqual(self.client.post('/pacientes/paciente-A/evoluciones',
                                          headers=self.profesional_headers,
                                          json={'turno_id': self.turno.id, 'nota': '   '}).status_code,
                         422)

    def test_correccion_append_only_solo_por_profesional_autor(self):
        original = self.client.post('/pacientes/paciente-A/evoluciones',
                                     headers=self.profesional_headers,
                                     json={'turno_id': self.turno.id,
                                           'nota': 'Nota original ficticia.'})
        self.assertEqual(original.status_code, 201, original.text)
        original_id = original.json()['id']

        correccion = self.client.post(f'/evoluciones/{original_id}/correcciones',
                                      headers=self.profesional_headers,
                                      json={'nota': 'Nota corregida ficticia.'})
        self.assertEqual(correccion.status_code, 201, correccion.text)
        self.assertEqual(correccion.json()['corrige_a_id'], original_id)
        historia = self.client.get('/pacientes/paciente-A/historia',
                                   headers=self.profesional_headers)
        self.assertEqual([item['nota'] for item in historia.json()['items']],
                         ['Nota original ficticia.', 'Nota corregida ficticia.'])

        ajena = self.client.post(f'/evoluciones/{original_id}/correcciones',
                                 headers=self.recepcion_headers,
                                 json={'nota': 'Texto no autorizado.'})
        self.assertEqual(ajena.status_code, 403)
        self.assertNotIn('Nota corregida ficticia.', str(ajena.json()))

    def test_lectura_anonima_y_paciente_sin_atencion_propia_se_deniegan(self):
        self.assertEqual(self.client.get('/pacientes/paciente-A/historia').status_code, 401)
        desconocida = self.client.get(
            '/pacientes/paciente-no-existe/historia', headers=self.profesional_headers)
        self.assertEqual(desconocida.status_code, 404)


if __name__ == '__main__':
    unittest.main()
