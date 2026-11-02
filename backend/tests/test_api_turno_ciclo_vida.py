from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from odontologia.agenda import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.bootstrap_admin import crear_primer_administrador
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.disponibilidad import guardar_horario


class ApiCicloVidaTurnoTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.secreto = 'secreto-local-de-prueba-no-reutilizar-2026'
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        crear_primer_administrador(engine, 'admin.turnos', 'frase-larga-segura-2026')
        abierto = {str(dia): [{'inicio': '00:00', 'fin': '24:00'}] for dia in range(1, 8)}
        for tipo, recurso in (('profesional', 'profesional-A'), ('box', 'box-A')):
            guardar_horario(engine, tipo, recurso, abierto)
        engine.dispose()
        with patch.dict('os.environ', {'JWT_SECRETO': self.secreto}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        login = self.client.post('/sesiones', json={
            'identificador': 'admin.turnos', 'password': 'frase-larga-segura-2026'})
        self.assertEqual(login.status_code, 200, login.text)
        self.headers = {'Authorization': f"Bearer {login.json()['access_token']}"}

    def _alta(self):
        respuesta = self.client.post('/turnos', headers=self.headers, json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A',
            'box_id': 'box-A', 'inicio': '2026-10-15T09:00:00-03:00',
            'fin': '2026-10-15T09:30:00-03:00'})
        self.assertEqual(respuesta.status_code, 201, respuesta.text)
        self.assertEqual(respuesta.json()['estado'], 'reservado')
        return respuesta.json()['id']

    def _estado_db(self, turno_id):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return conexion.execute(
                'SELECT estado FROM turnos WHERE id=?', (turno_id,)).fetchone()[0]

    def _eventos_estado(self, turno_id):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return conexion.execute(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='turno.estado_actualizado' "
                'AND resource_id=?', (str(turno_id),)).fetchone()[0]

    def _login(self, identificador, password):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': password})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def test_endpoints_de_estado_y_alta_persisten_los_cuatro_destinos(self):
        turno = self._alta()
        confirmacion = self.client.post(
            f'/turnos/{turno}/confirmacion', headers=self.headers)
        self.assertEqual(confirmacion.status_code, 200, confirmacion.text)
        self.assertEqual(confirmacion.json(), {'id': turno, 'estado': 'confirmado'})
        atencion = self.client.post(f'/turnos/{turno}/atencion', headers=self.headers)
        self.assertEqual(atencion.status_code, 200, atencion.text)
        self.assertEqual(atencion.json(), {'id': turno, 'estado': 'atendido'})
        self.assertEqual(self._estado_db(turno), 'atendido')

        cancelado = self._alta()
        cancelar = self.client.post(f'/turnos/{cancelado}/cancelacion', headers=self.headers)
        self.assertEqual(cancelar.status_code, 200, cancelar.text)
        self.assertEqual(cancelar.json(), {'id': cancelado, 'estado': 'cancelado'})
        self.assertEqual(self._estado_db(cancelado), 'cancelado')

        ausente = self._alta()
        self.client.post(f'/turnos/{ausente}/confirmacion', headers=self.headers)
        marcar_ausente = self.client.post(
            f'/turnos/{ausente}/ausencia', headers=self.headers)
        self.assertEqual(marcar_ausente.status_code, 200, marcar_ausente.text)
        self.assertEqual(marcar_ausente.json(), {'id': ausente, 'estado': 'ausente'})
        self.assertEqual(self._estado_db(ausente), 'ausente')

        paths = self.client.get('/openapi.json').json()['paths']
        self.assertTrue({
            '/turnos/{turno_id}/confirmacion', '/turnos/{turno_id}/cancelacion',
            '/turnos/{turno_id}/atencion', '/turnos/{turno_id}/ausencia',
        } <= set(paths))

    def test_autorizacion_sin_sesion_recepcion_y_profesional(self):
        turno = self._alta()
        sin_sesion = self.client.post(f'/turnos/{turno}/cancelacion')
        self.assertEqual(sin_sesion.status_code, 401)
        self.assertEqual(self._estado_db(turno), 'reservado')

        creado = self.client.post('/usuarios', headers=self.headers, json={
            'identificador': 'recepcion.turnos',
            'password': 'otra-frase-larga-segura-2026', 'rol': 'recepcion'})
        self.assertEqual(creado.status_code, 201, creado.text)
        recepcion = self._login('recepcion.turnos', 'otra-frase-larga-segura-2026')
        confirmada = self.client.post(
            f'/turnos/{turno}/confirmacion', headers=recepcion)
        self.assertEqual(confirmada.status_code, 200, confirmada.text)
        self.assertEqual(self._estado_db(turno), 'confirmado')

        with patch('odontologia.api.validar_sesion', return_value={
                'rol': 'profesional', 'usuario_id': creado.json()['id']}):
            denegada = self.client.post(
                f'/turnos/{turno}/cancelacion', headers=recepcion)
        self.assertEqual(denegada.status_code, 403)
        self.assertEqual(self._estado_db(turno), 'confirmado')

    def test_turno_inexistente_es_404_y_transicion_invalida_no_audita(self):
        inexistente = self.client.post('/turnos/999999/confirmacion', headers=self.headers)
        self.assertEqual(inexistente.status_code, 404)
        turno = self._alta()
        invalida = self.client.post(f'/turnos/{turno}/atencion', headers=self.headers)
        self.assertEqual(invalida.status_code, 409)
        self.assertEqual(invalida.json()['codigo'], 'transicion_invalida')
        self.assertEqual(self._estado_db(turno), 'reservado')
        self.assertEqual(self._eventos_estado(turno), 0)

    def test_cancelacion_repetida_es_idempotente_en_api(self):
        turno = self._alta()
        primera = self.client.post(f'/turnos/{turno}/cancelacion', headers=self.headers)
        repetida = self.client.post(f'/turnos/{turno}/cancelacion', headers=self.headers)
        self.assertEqual((primera.status_code, repetida.status_code), (200, 200))
        self.assertEqual(repetida.json(), {'id': turno, 'estado': 'cancelado'})
        self.assertEqual(self._eventos_estado(turno), 1)


if __name__ == '__main__':
    unittest.main()
