from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from odontologia.agenda import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.bootstrap_admin import crear_primer_administrador
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.disponibilidad import guardar_horario


class ApiReprogramacionTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        crear_primer_administrador(engine, 'admin.reprog', 'frase-larga-segura-2026')
        abierto = {str(dia): [{'inicio': '08:00', 'fin': '18:00'}]
                   for dia in range(1, 8)}
        for tipo in ('profesional', 'box'):
            for recurso in (f'{tipo}-A', f'{tipo}-B'):
                guardar_horario(engine, tipo, recurso, abierto)
        engine.dispose()
        self.secreto_env = patch.dict(
            'os.environ', {
                'JWT_SECRETO': 'secreto-local-de-prueba-no-reutilizar-2026'}, clear=True)
        self.secreto_env.start()
        self.addCleanup(self.secreto_env.stop)
        self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.headers = self._login('admin.reprog', 'frase-larga-segura-2026')

    def _login(self, identificador, password):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': password})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def _alta(self):
        respuesta = self.client.post('/turnos', headers=self.headers, json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A',
            'box_id': 'box-A', 'inicio': '2026-11-02T09:00:00-03:00',
            'fin': '2026-11-02T09:30:00-03:00'})
        self.assertEqual(respuesta.status_code, 201, respuesta.text)
        return respuesta.json()['id']

    def _solicitud(self, **cambios):
        cuerpo = {
            'version': 1, 'inicio': '2026-11-02T10:00:00-03:00',
            'fin': '2026-11-02T10:30:00-03:00',
            'profesional_id': 'profesional-B', 'box_id': 'box-B',
        }
        cuerpo.update(cambios)
        return cuerpo

    def _estado_fila(self, turno_id):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return conexion.execute(
                'SELECT paciente_id, profesional_id, box_id, inicio_minuto, fin_minuto, '
                'estado, version FROM turnos WHERE id=?', (turno_id,)).fetchone()

    def _eventos_reprogramacion(self, turno_id):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return conexion.execute(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='turno.reprogramado' "
                'AND resource_id=?', (str(turno_id),)).fetchone()[0]

    def test_reprogramacion_vigente_responde_datos_y_expone_ruta_openapi(self):
        turno = self._alta()
        respuesta = self.client.post(
            f'/turnos/{turno}/reprogramacion', headers=self.headers,
            json=self._solicitud())
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        self.assertEqual(respuesta.json(), {
            'id': turno, 'paciente_id': 'paciente-A',
            'profesional_id': 'profesional-B', 'box_id': 'box-B',
            'inicio': '2026-11-02T13:00:00Z', 'fin': '2026-11-02T13:30:00Z',
            'estado': 'reservado', 'version': 2,
        })
        openapi = self.client.get('/openapi.json').json()
        operacion = openapi['paths']['/turnos/{turno_id}/reprogramacion']['post']
        self.assertIn('200', operacion['responses'])
        self.assertIn('401', operacion['responses'])
        self.assertIn('403', operacion['responses'])
        self.assertIn('404', operacion['responses'])
        self.assertIn('409', operacion['responses'])
        self.assertIn('422', operacion['responses'])
        componentes = openapi['components']['schemas']
        solicitud = componentes['SolicitudReprogramacion']
        self.assertEqual(set(solicitud['required']), {
            'version', 'inicio', 'fin', 'profesional_id', 'box_id'})
        self.assertFalse(solicitud['additionalProperties'])
        self.assertEqual(solicitud['examples'][0], self._solicitud())
        respuesta_schema = componentes['RespuestaReprogramacion']
        ejemplo_respuesta = respuesta_schema['examples'][0]
        self.assertEqual(set(ejemplo_respuesta), set(respuesta.json()))
        self.assertIsInstance(ejemplo_respuesta['version'], int)
        self.assertGreater(ejemplo_respuesta['version'], 0)

    def test_reprogramacion_rechaza_cuerpo_estricto_version_y_turno_inexistente(self):
        turno = self._alta()
        fila_anterior = self._estado_fila(turno)
        for cuerpo in (
            {k: v for k, v in self._solicitud().items() if k != 'version'},
            self._solicitud(extra='no permitido'),
            self._solicitud(version=True),
            self._solicitud(inicio='2026-11-02T10:00:00'),
        ):
            with self.subTest(cuerpo=cuerpo):
                respuesta = self.client.post(
                    f'/turnos/{turno}/reprogramacion', headers=self.headers, json=cuerpo)
                self.assertEqual(respuesta.status_code, 422, respuesta.text)
                self.assertEqual(respuesta.json()['codigo'], 'entrada_invalida')
                self.assertEqual(self._estado_fila(turno), fila_anterior)
                self.assertEqual(self._eventos_reprogramacion(turno), 0)

        inexistente = self.client.post(
            '/turnos/999999/reprogramacion', headers=self.headers,
            json=self._solicitud())
        self.assertEqual(inexistente.status_code, 404, inexistente.text)
        self.assertEqual(inexistente.json()['codigo'], 'turno_no_encontrado')

    def test_reprogramacion_exige_sesion_y_rol_operativo(self):
        turno = self._alta()
        sin_sesion = self.client.post(
            f'/turnos/{turno}/reprogramacion', json=self._solicitud())
        self.assertEqual(sin_sesion.status_code, 401)
        recepcion_creada = self.client.post('/usuarios', headers=self.headers, json={
            'identificador': 'recepcion.reprog',
            'password': 'otra-frase-larga-segura-2026', 'rol': 'recepcion'})
        self.assertEqual(recepcion_creada.status_code, 201, recepcion_creada.text)
        recepcion = self._login('recepcion.reprog', 'otra-frase-larga-segura-2026')
        autorizada = self.client.post(
            f'/turnos/{turno}/reprogramacion', headers=recepcion,
            json=self._solicitud())
        self.assertEqual(autorizada.status_code, 200, autorizada.text)
        self.assertEqual(autorizada.json()['version'], 2)
        creado = self.client.post('/usuarios', headers=self.headers, json={
            'identificador': 'profesional.reprog',
            'password': 'otra-frase-larga-segura-2026', 'rol': 'profesional',
            'profesional_id': 'profesional-A'})
        self.assertEqual(creado.status_code, 201, creado.text)
        profesional = self._login(
            'profesional.reprog', 'otra-frase-larga-segura-2026')
        with patch('odontologia.api.validar_sesion', return_value={
                'rol': 'profesional', 'usuario_id': creado.json()['id'],
                'profesional_id': 'profesional-A'}):
            denegada = self.client.post(
                f'/turnos/{turno}/reprogramacion', headers=profesional,
                json=self._solicitud(version=2, inicio='2026-11-02T11:00:00-03:00',
                                     fin='2026-11-02T11:30:00-03:00'))
        self.assertEqual(denegada.status_code, 403)
        self.assertEqual(self._estado_fila(turno)[1], 'profesional-B')
        self.assertEqual(self._eventos_reprogramacion(turno), 1)

    def test_version_obsoleta_y_terminal_responden_409_sin_mutar(self):
        turno = self._alta()
        anterior = self._estado_fila(turno)
        respuesta = self.client.post(
            f'/turnos/{turno}/reprogramacion', headers=self.headers,
            json=self._solicitud(version=8))
        self.assertEqual(respuesta.status_code, 409, respuesta.text)
        self.assertEqual(respuesta.json()['codigo'], 'version_desactualizada')
        self.assertEqual(self._estado_fila(turno), anterior)
        self.assertEqual(self._eventos_reprogramacion(turno), 0)

        cancelada = self.client.post(f'/turnos/{turno}/cancelacion', headers=self.headers)
        self.assertEqual(cancelada.status_code, 200, cancelada.text)
        fila_terminal = self._estado_fila(turno)
        terminal = self.client.post(
            f'/turnos/{turno}/reprogramacion', headers=self.headers,
            json=self._solicitud(version=fila_terminal[6]))
        self.assertEqual(terminal.status_code, 409, terminal.text)
        self.assertEqual(terminal.json()['codigo'], 'turno_no_reprogramable')
        self.assertEqual(self._estado_fila(turno), fila_terminal)
        self.assertEqual(self._eventos_reprogramacion(turno), 0)


if __name__ == '__main__':
    unittest.main()
