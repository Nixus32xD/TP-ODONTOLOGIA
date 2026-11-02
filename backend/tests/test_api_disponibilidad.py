from pathlib import Path
from contextlib import closing
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


class ApiDisponibilidadTests(unittest.TestCase):
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
        self.secreto = 'secreto-local-disponibilidad-test-no-reutilizar-2026'
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

    def test_roles_operan_horarios_y_excepciones(self):
        base = '/horarios/profesional/profesional-A'
        self.assertEqual(self.client.get(base, headers=self.admin).status_code, 200)
        payload = {'dias': {'1': [
            {'inicio': '09:00', 'fin': '12:00'},
            {'inicio': '12:00', 'fin': '13:00'},
        ]}}
        guardado = self.client.put(base, headers=self.recepcion, json=payload)
        self.assertEqual(guardado.status_code, 200, guardado.text)
        self.assertEqual(guardado.json()['dias']['1'], payload['dias']['1'])
        self.assertEqual(self.client.get(base, headers=self.recepcion).json(), guardado.json())

        path_excepcion = f'{base}/excepciones/2026-11-03'
        creada = self.client.put(path_excepcion, headers=self.admin, json={
            'tramos': [{'inicio': '10:00', 'fin': '11:00'}]})
        self.assertEqual(creada.status_code, 200, creada.text)
        self.assertEqual(self.client.get(path_excepcion, headers=self.recepcion).json(), creada.json())
        vacia = self.client.put(path_excepcion, headers=self.recepcion, json={'tramos': []})
        self.assertEqual(vacia.status_code, 200, vacia.text)
        self.assertEqual(vacia.json()['tramos'], [])
        self.assertEqual(self.client.delete(path_excepcion, headers=self.admin).status_code, 204)
        self.assertEqual(self.client.get(path_excepcion, headers=self.admin).status_code, 404)

    def test_bloqueos_crear_listar_paginados_y_eliminar(self):
        base = '/bloqueos'
        payload = {
            'tipo_recurso': 'profesional', 'recurso_id': 'profesional-A',
            'inicio': '2026-11-02T09:00:00-03:00',
            'fin': '2026-11-02T10:00:00-03:00',
        }
        primera = self.client.post(base, headers=self.recepcion, json=payload)
        self.assertEqual(primera.status_code, 201, primera.text)
        segunda = self.client.post(base, headers=self.admin, json={
            **payload, 'tipo_recurso': 'box', 'recurso_id': 'box-A',
            'inicio': '2026-11-03T09:00:00-03:00', 'fin': '2026-11-03T10:00:00-03:00',
        })
        self.assertEqual(segunda.status_code, 201, segunda.text)
        self.assertEqual(self.client.get(
            f'{base}?limit=1&offset=0', headers=self.admin).json()['items'][0]['id'],
            primera.json()['id'])
        self.assertEqual(self.client.get(
            f'{base}?limit=1&offset=1', headers=self.recepcion).json()['items'][0]['id'],
            segunda.json()['id'])
        self.assertEqual(self.client.delete(
            f"{base}/{primera.json()['id']}", headers=self.admin).status_code, 204)
        self.assertEqual(self.client.get(base, headers=self.admin).json()['items'][0]['id'],
                         segunda.json()['id'])

    def test_mutaciones_auditan_solo_metadata_y_falla_reversa_cambios(self):
        ruta_horario = '/horarios/profesional/profesional-A'
        horario_inicial = {'dias': {'1': [{'inicio': '09:00', 'fin': '12:00'}]}}
        self.assertEqual(self.client.put(
            ruta_horario, headers=self.admin, json=horario_inicial).status_code, 200)
        excepcion_path = f'{ruta_horario}/excepciones/2026-11-03'
        self.assertEqual(self.client.put(
            excepcion_path, headers=self.admin,
            json={'tramos': [{'inicio': '10:00', 'fin': '11:00'}]}).status_code, 200)
        self.assertEqual(self.client.put(
            excepcion_path, headers=self.admin,
            json={'tramos': [{'inicio': '11:00', 'fin': '12:00'}]}).status_code, 200)
        bloqueo = self.client.post('/bloqueos', headers=self.admin, json={
            'tipo_recurso': 'box', 'recurso_id': 'box-A',
            'inicio': '2026-11-02T09:00:00-03:00', 'fin': '2026-11-02T10:00:00-03:00'})
        self.assertEqual(bloqueo.status_code, 201, bloqueo.text)
        retenido = self.client.post('/bloqueos', headers=self.admin, json={
            'tipo_recurso': 'profesional', 'recurso_id': 'profesional-A',
            'inicio': '2026-11-02T15:00:00-03:00', 'fin': '2026-11-02T16:00:00-03:00'})
        self.assertEqual(retenido.status_code, 201, retenido.text)
        self.assertEqual(self.client.delete(
            f"/bloqueos/{bloqueo.json()['id']}", headers=self.admin).status_code, 204)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            eventos = conexion.execute(
                "SELECT actor_id, action, resource_type, resource_id, result "
                "FROM eventos_auditoria WHERE action IN ('horario.actualizado', "
                "'excepcion.creada', 'excepcion.actualizada', 'bloqueo.creado', "
                "'bloqueo.eliminado') ORDER BY id").fetchall()
        self.assertEqual([fila[1] for fila in eventos], [
            'horario.actualizado', 'excepcion.creada', 'excepcion.actualizada',
            'bloqueo.creado', 'bloqueo.creado', 'bloqueo.eliminado'])
        self.assertTrue(all(fila[0] and fila[3] and fila[4] == 'confirmado' for fila in eventos))
        self.assertEqual([fila[2] for fila in eventos], [
            'horario', 'excepcion', 'excepcion', 'bloqueo', 'bloqueo', 'bloqueo'])
        self.assertNotIn('2026-11-03', str(eventos))
        self.assertNotIn('09:00', str(eventos))
        self.assertNotIn('10:00', str(eventos))

        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('''CREATE TRIGGER falla_auditoria BEFORE INSERT ON eventos_auditoria
                WHEN NEW.action IN ('horario.actualizado', 'excepcion.creada',
                                    'excepcion.actualizada', 'bloqueo.creado')
                BEGIN SELECT RAISE(FAIL, 'fallo inyectado'); END''')
        horario_nuevo = {'dias': {'1': [{'inicio': '14:00', 'fin': '17:00'}]}}
        fallido_horario = self.client.put(ruta_horario, headers=self.admin, json=horario_nuevo)
        fallida_excepcion = self.client.put(excepcion_path, headers=self.admin, json={
            'tramos': [{'inicio': '13:00', 'fin': '14:00'}]})
        fallido_bloqueo = self.client.post('/bloqueos', headers=self.admin, json={
            'tipo_recurso': 'box', 'recurso_id': 'box-A',
            'inicio': '2026-11-04T09:00:00-03:00', 'fin': '2026-11-04T10:00:00-03:00'})
        self.assertEqual((fallido_horario.status_code, fallida_excepcion.status_code,
                          fallido_bloqueo.status_code), (503, 503, 503))
        self.assertEqual(self.client.get(ruta_horario, headers=self.admin).json(), {
            'tipo_recurso': 'profesional', 'recurso_id': 'profesional-A',
            'dias': {**{str(dia): [] for dia in range(1, 8)},
                     '1': [{'inicio': '09:00', 'fin': '12:00'}]}})
        self.assertEqual(self.client.get(excepcion_path, headers=self.admin).json()['tramos'], [
            {'inicio': '11:00', 'fin': '12:00'}])
        self.assertEqual(len(self.client.get('/bloqueos', headers=self.admin).json()['items']), 1)
        self.assertEqual(self.client.delete(excepcion_path, headers=self.admin).status_code, 204)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            acciones = {fila[0] for fila in conexion.execute(
                'SELECT action FROM eventos_auditoria')}
        self.assertIn('excepcion.eliminada', acciones)

    def test_auth_inputs_desconocidos_y_paginas_invalidas(self):
        self.assertEqual(self.client.get('/horarios/profesional/profesional-A').status_code, 401)
        self.assertEqual(self.client.get('/bloqueos').status_code, 401)
        self.assertEqual(self.client.get(
            '/horarios/profesional/inexistente', headers=self.recepcion).status_code, 404)
        self.assertEqual(self.client.get(
            '/bloqueos?limit=101', headers=self.admin).status_code, 422)
        self.assertEqual(self.client.get(
            '/bloqueos?offset=-1', headers=self.recepcion).status_code, 422)
        for dias in (
            {'0': []}, {'1': [{'inicio': '09:00', 'fin': '11:00'},
                              {'inicio': '10:00', 'fin': '12:00'}]},
        ):
            respuesta = self.client.put(
                '/horarios/box/box-A', headers=self.admin, json={'dias': dias})
            self.assertEqual(respuesta.status_code, 422, respuesta.text)
        self.assertEqual(self.client.post('/bloqueos', headers=self.admin, json={
            'tipo_recurso': 'profesional', 'recurso_id': 'no-existe',
            'inicio': '2026-11-02T09:00:00-03:00',
            'fin': '2026-11-02T10:00:00-03:00',
        }).status_code, 404)

    def test_openapi_publica_ejemplos_rutas_y_respuestas_de_disponibilidad(self):
        respuesta = self.client.get('/openapi.json')
        self.assertEqual(respuesta.status_code, 200)
        schema = respuesta.json()
        paths = schema['paths']
        self.assertIn('/horarios/{tipo_recurso}/{recurso_id}', paths)
        self.assertIn('/horarios/{tipo_recurso}/{recurso_id}/excepciones/{fecha}', paths)
        self.assertIn('/bloqueos', paths)
        self.assertIn('/bloqueos/{bloqueo_id}', paths)
        self.assertIn('409', paths['/horarios/{tipo_recurso}/{recurso_id}']['put']['responses'])
        self.assertIn('422', paths['/bloqueos']['post']['responses'])
        self.assertIn('examples', schema['components']['schemas']['SolicitudHorario'])
        self.assertIn('examples', schema['components']['schemas']['SolicitudBloqueo'])
        docs = self.client.get('/docs')
        self.assertEqual(docs.status_code, 200)
        self.assertIn('swagger', docs.text.lower())
        self.assertEqual(self.client.get('/auditoria', headers=self.recepcion).status_code, 403)

    def test_cambio_incompatible_responde_409_sin_evento(self):
        horario = {'dias': {'1': [{'inicio': '09:00', 'fin': '12:00'}]}}
        profesional = '/horarios/profesional/profesional-A'
        self.assertEqual(self.client.put(
            profesional, headers=self.admin, json=horario).status_code, 200)
        self.assertEqual(self.client.put(
            '/horarios/box/box-A', headers=self.admin, json=horario).status_code, 200)
        turno = self.client.post('/turnos', headers=self.admin, json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A', 'box_id': 'box-A',
            'inicio': '2026-10-26T12:00:00Z', 'fin': '2026-10-26T12:30:00Z'})
        self.assertEqual(turno.status_code, 201, turno.text)
        eventos_antes = self.client.get('/auditoria', headers=self.admin).json()['items']
        rechazada = self.client.put(profesional, headers=self.admin, json={
            'dias': {'1': [{'inicio': '10:00', 'fin': '12:00'}]}})
        self.assertEqual(rechazada.status_code, 409, rechazada.text)
        self.assertEqual(rechazada.json()['codigo'], 'turnos_afectados')
        self.assertEqual(self.client.get(profesional, headers=self.admin).json()['dias']['1'],
                         horario['dias']['1'])
        eventos_despues = self.client.get('/auditoria', headers=self.admin).json()['items']
        self.assertEqual(
            sum(evento['action'] == 'horario.actualizado' for evento in eventos_despues),
            sum(evento['action'] == 'horario.actualizado' for evento in eventos_antes))

    def test_api_falla_cerrado_si_falta_tabla_c07_aunque_version_siga_en_v5(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('DROP TABLE horarios_semanales')
            conexion.commit()
        respuesta = self.client.post('/turnos', headers=self.admin, json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A', 'box_id': 'box-A',
            'inicio': '2026-11-02T12:00:00Z', 'fin': '2026-11-02T12:30:00Z'})
        self.assertEqual(respuesta.status_code, 503, respuesta.text)
        self.assertEqual(respuesta.json()['codigo'], 'autenticacion_no_configurada')

    def test_api_falla_cerrado_si_falta_estado_en_turnos_antes_de_mutar(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('DROP TABLE turnos')
            conexion.execute('''CREATE TABLE turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id TEXT NOT NULL,
                profesional_id TEXT NOT NULL,
                box_id TEXT NOT NULL,
                inicio_minuto INTEGER NOT NULL,
                fin_minuto INTEGER NOT NULL
            )''')
            conexion.commit()

        respuesta = self.client.post('/turnos', headers=self.admin, json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A', 'box_id': 'box-A',
            'inicio': '2026-11-02T12:00:00Z', 'fin': '2026-11-02T12:30:00Z'})

        self.assertEqual(respuesta.status_code, 503, respuesta.text)
        self.assertEqual(respuesta.json()['codigo'], 'autenticacion_no_configurada')
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0], 0)
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='turno.creado'"
            ).fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
