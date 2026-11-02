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
from odontologia.audit import ErrorAuditoria


class ApiOdontogramaTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        self.turno_a = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))
        self.turno_b = crear_turno(
            self.ruta, paciente_id='paciente-B', profesional_id='profesional-B',
            box_id='box-B', inicio=datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T10:30:00-03:00'))
        self.turno_c = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-B',
            box_id='box-B', inicio=datetime.fromisoformat('2026-11-02T11:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T11:30:00-03:00'))
        migrar_sqlite(self.ruta)
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.admin = crear_primer_administrador(
            engine, 'admin.odontograma', 'frase-larga-segura-2026')
        self.profesional = crear_usuario(
            engine, 'profesional.odontograma', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A', actor_id=self.admin['id'])
        self.profesional_b = crear_usuario(
            engine, 'profesional.odontograma.b', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-B', actor_id=self.admin['id'])
        self.recepcion = crear_usuario(
            engine, 'recepcion.odontograma', 'frase-larga-segura-2026', 'recepcion',
            actor_id=self.admin['id'])
        engine.dispose()
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute("UPDATE turnos SET estado='atendido' WHERE id=?",
                               (self.turno_a.id,))
            connection.execute("UPDATE turnos SET estado='atendido' WHERE id=?",
                               (self.turno_c.id,))
            connection.commit()
        with patch.dict('os.environ', {
                'JWT_SECRETO': 'secreto-local-pruebas-odontograma-2026',
                'ODONTOLOGIA_ENTORNO': 'desarrollo'}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.admin_headers = self.login('admin.odontograma')
        self.profesional_headers = self.login('profesional.odontograma')
        self.profesional_b_headers = self.login('profesional.odontograma.b')
        self.recepcion_headers = self.login('recepcion.odontograma')

    def login(self, identificador):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': 'frase-larga-segura-2026'})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def test_profesional_consulta_y_crea_versiones_completas(self):
        payload = {'hallazgos': [
            {'pieza_fdi': '11', 'superficies': ['M', 'V'], 'observacion': 'hallazgo sintético'}]}
        alta = self.client.post('/pacientes/paciente-A/odontograma',
                                headers=self.profesional_headers, json=payload)
        self.assertEqual(alta.status_code, 201, alta.text)
        self.assertEqual(alta.json()['version'], 1)
        self.assertEqual(len(alta.json()['hallazgos']), 2)
        historial = self.client.get('/pacientes/paciente-A/odontograma',
                                    headers=self.profesional_headers)
        self.assertEqual(historial.status_code, 200, historial.text)
        self.assertEqual(historial.json()['version_vigente'], 1)
        self.assertEqual(len(historial.json()['items']), 1)

    def test_lista_atenciones_atendidas_solo_propias_con_respuesta_minima(self):
        propia = self.client.get('/profesional/atenciones-atendidas?limit=1&offset=0',
                                 headers=self.profesional_headers)
        self.assertEqual(propia.status_code, 200, propia.text)
        self.assertEqual((propia.json()['limit'], propia.json()['offset']), (1, 0))
        self.assertEqual(len(propia.json()['items']), 1)
        self.assertEqual(set(propia.json()['items'][0]), {
            'turno_id', 'paciente_id', 'paciente_nombre', 'inicio', 'fin',
        })
        self.assertEqual(propia.json()['items'][0]['paciente_id'], 'paciente-A')
        propia_completa = self.client.get('/profesional/atenciones-atendidas',
                                          headers=self.profesional_headers)
        ajena = self.client.get('/profesional/atenciones-atendidas',
                                headers=self.profesional_b_headers)
        self.assertEqual(propia_completa.json()['items'][0]['turno_id'], self.turno_a.id)
        self.assertEqual(ajena.json()['items'][0]['turno_id'], self.turno_c.id)
        self.assertEqual(self.client.get(
            '/profesional/atenciones-atendidas?limit=101',
            headers=self.profesional_headers).status_code, 422)
        self.assertEqual(self.client.get('/profesional/atenciones-atendidas',
                                         headers=self.admin_headers).status_code, 403)
        self.assertEqual(self.client.get('/profesional/atenciones-atendidas',
                                         headers=self.recepcion_headers).status_code, 403)

        with closing(sqlite3.connect(self.ruta)) as connection:
            action = connection.execute(
                "SELECT action, resource_type, resource_id, result FROM eventos_auditoria "
                "WHERE action='historia.atenciones_listadas'").fetchone()
        self.assertEqual(action, ('historia.atenciones_listadas', 'historia', None, 'confirmado'))

    def test_rol_y_atencion_restringen_lectura_y_escritura(self):
        payload = {'hallazgos': []}
        for headers in (self.admin_headers, self.recepcion_headers):
            lectura = self.client.get('/pacientes/paciente-A/odontograma', headers=headers)
            escritura = self.client.post(
                '/pacientes/paciente-A/odontograma', headers=headers, json=payload)
            self.assertEqual(lectura.status_code, 403, lectura.text)
            self.assertEqual(escritura.status_code, 403, escritura.text)
        no_atendido = self.client.post(
            '/pacientes/paciente-B/odontograma', headers=self.profesional_headers, json=payload)
        self.assertEqual(no_atendido.status_code, 404, no_atendido.text)
        lectura_sin_atencion = self.client.get(
            '/pacientes/paciente-B/odontograma', headers=self.profesional_headers)
        self.assertEqual(lectura_sin_atencion.status_code, 404, lectura_sin_atencion.text)
        self.assertEqual(self.client.get('/pacientes/paciente-A/odontograma').status_code, 401)

    def test_profesionales_aislan_sus_versiones_aunque_compartan_paciente(self):
        alta = self.client.post(
            '/pacientes/paciente-A/odontograma', headers=self.profesional_headers,
            json={'hallazgos': [{'pieza_fdi': '11', 'superficies': ['M'],
                                 'observacion': None}]})
        lectura_ajena = self.client.get(
            '/pacientes/paciente-A/odontograma', headers=self.profesional_b_headers)

        self.assertEqual(alta.status_code, 201, alta.text)
        self.assertEqual(lectura_ajena.status_code, 200, lectura_ajena.text)
        self.assertEqual(lectura_ajena.json()['items'], [])
        self.assertIsNone(lectura_ajena.json()['version_vigente'])

    def test_entrada_invalida_no_crea_version_y_esquema_openapi_existe(self):
        invalida = self.client.post('/pacientes/paciente-A/odontograma',
                                    headers=self.profesional_headers,
                                    json={'hallazgos': [{
                                        'pieza_fdi': '11', 'superficies': ['O'],
                                        'observacion': 'inválido'}]})
        self.assertEqual(invalida.status_code, 422, invalida.text)
        with closing(sqlite3.connect(self.ruta)) as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM versiones_odontograma').fetchone()[0], 0)
        paths = self.client.get('/openapi.json').json()['paths']
        self.assertIn('/pacientes/{paciente_id}/odontograma', paths)
        self.assertIn('get', paths['/pacientes/{paciente_id}/odontograma'])
        self.assertIn('post', paths['/pacientes/{paciente_id}/odontograma'])

    def test_ejemplo_openapi_es_sintetico_y_no_agrega_diagnosticos(self):
        openapi = self.client.get('/openapi.json').json()
        ejemplo = openapi['components']['schemas']['SolicitudOdontograma']['examples'][0]
        self.assertEqual(ejemplo['hallazgos'][0]['pieza_fdi'], '11')
        self.assertIn('sintética', ejemplo['hallazgos'][0]['observacion'])
        self.assertNotIn('diagnostico', str(ejemplo).lower())

    def test_cuenta_y_profesional_vigentes_se_revalidan_en_cada_operacion(self):
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute(
                "UPDATE profesionales SET activo=0 WHERE id='profesional-A'")
            connection.commit()
        leer = self.client.get('/pacientes/paciente-A/odontograma',
                               headers=self.profesional_headers)
        escribir = self.client.post('/pacientes/paciente-A/odontograma',
                                    headers=self.profesional_headers,
                                    json={'hallazgos': []})
        self.assertEqual(leer.status_code, 403, leer.text)
        self.assertEqual(escribir.status_code, 403, escribir.text)

    def test_cuenta_profesional_desactivada_no_consulta_ni_escribe(self):
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute("UPDATE usuarios SET activo=0 WHERE id=?",
                               (self.profesional['id'],))
            connection.commit()
        leer = self.client.get('/pacientes/paciente-A/odontograma',
                               headers=self.profesional_headers)
        escribir = self.client.post('/pacientes/paciente-A/odontograma',
                                    headers=self.profesional_headers,
                                    json={'hallazgos': []})
        self.assertEqual(leer.status_code, 401, leer.text)
        self.assertEqual(escribir.status_code, 401, escribir.text)

    def test_vinculo_profesional_actual_se_revalida_ante_token_previo(self):
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-C', 'Profesional sintético C', 1)")
            connection.execute(
                "UPDATE usuarios SET profesional_id='profesional-C' WHERE id=?",
                (self.profesional['id'],))
            connection.commit()
        leer = self.client.get('/pacientes/paciente-A/odontograma',
                               headers=self.profesional_headers)
        escribir = self.client.post('/pacientes/paciente-A/odontograma',
                                    headers=self.profesional_headers,
                                    json={'hallazgos': []})
        self.assertIn(leer.status_code, (401, 403, 404), leer.text)
        self.assertIn(escribir.status_code, (401, 403, 404), escribir.text)

    def test_fallo_auditoria_api_revierte_version_y_responde_503(self):
        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            respuesta = self.client.post(
                '/pacientes/paciente-A/odontograma', headers=self.profesional_headers,
                json={'hallazgos': []})
        self.assertEqual(respuesta.status_code, 503, respuesta.text)
        with closing(sqlite3.connect(self.ruta)) as connection:
            cantidad = connection.execute(
                'SELECT COUNT(*) FROM versiones_odontograma').fetchone()[0]
        self.assertEqual(cantidad, 0)

    def test_auditoria_odontograma_guarda_metadata_sin_hallazgos(self):
        self.client.post('/pacientes/paciente-A/odontograma',
                         headers=self.profesional_headers,
                         json={'hallazgos': [{
                             'pieza_fdi': '11', 'superficies': ['M'],
                             'observacion': 'texto-clinico-sintetico-no-auditar'}]})
        self.client.get('/pacientes/paciente-A/odontograma',
                        headers=self.profesional_headers)
        auditoria = self.client.get('/auditoria', headers=self.admin_headers)
        eventos = [evento for evento in auditoria.json()['items']
                   if evento['action'].startswith('odontograma.')]
        self.assertEqual({evento['action'] for evento in eventos}, {
            'odontograma.version_creada', 'odontograma.consultada'})
        for evento in eventos:
            self.assertEqual(set(evento), {
                'id', 'created_at', 'actor_id', 'action', 'resource_type', 'resource_id', 'result'})
        self.assertNotIn('texto-clinico-sintetico-no-auditar', str(auditoria.json()))


if __name__ == '__main__':
    unittest.main()
