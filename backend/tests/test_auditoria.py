from contextlib import closing
from datetime import datetime
from pathlib import Path
import os
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import ErrorUsuarios, crear_primer_administrador, crear_usuario
from odontologia.disponibilidad import guardar_horario
from fastapi.testclient import TestClient


class AuditoriaEsquemaSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)

    def test_migracion_crea_tabla_append_only_y_versiona_schema(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            tablas = {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn('eventos_auditoria', tablas)
            columnas = {fila[1] for fila in conexion.execute(
                'PRAGMA table_info(eventos_auditoria)')}
            self.assertEqual(columnas, {
                'id', 'created_at', 'actor_id', 'action', 'resource_type', 'resource_id', 'result'})
            self.assertEqual(
                conexion.execute('SELECT version FROM auth_schema_version').fetchone(), (7,))

    def test_auditoria_no_guarda_payload_ni_identificador_intentado(self):
        from odontologia.audit import registrar_evento_sqlite

        with closing(sqlite3.connect(self.ruta, isolation_level=None)) as conexion:
            conexion.execute('PRAGMA foreign_keys=ON')
            conexion.execute('BEGIN IMMEDIATE')
            registrar_evento_sqlite(
                conexion, action='sesion.rechazada', resource_type='sesion', result='rechazado')
            conexion.execute('COMMIT')
        with closing(sqlite3.connect(self.ruta)) as conexion:
            fila = conexion.execute(
                'SELECT actor_id, action, resource_type, resource_id, result '
                'FROM eventos_auditoria').fetchone()
            self.assertEqual(fila, (None, 'sesion.rechazada', 'sesion', None, 'rechazado'))
            self.assertNotIn('payload', {col[1] for col in conexion.execute(
                'PRAGMA table_info(eventos_auditoria)')})

    def test_rechazo_no_acepta_identificador_en_recurso(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "INSERT INTO eventos_auditoria(created_at, action, resource_type, "
                    "resource_id, result) VALUES ('2026-11-01T00:00:00+00:00', "
                    "'sesion.rechazada', 'sesion', 'dato-intentado', 'rechazado')")

    def test_helper_acepta_todos_los_eventos_reales(self):
        from odontologia.audit import registrar_evento_sqlite

        eventos_validos = (
            ('turno.creado', 'turno', 'confirmado'),
            ('paciente.creado', 'paciente', 'confirmado'),
            ('paciente.actualizado', 'paciente', 'confirmado'),
            ('paciente.desactivado', 'paciente', 'confirmado'),
            ('paciente.reactivado', 'paciente', 'confirmado'),
            ('profesional.creado', 'profesional', 'confirmado'),
            ('profesional.actualizado', 'profesional', 'confirmado'),
            ('profesional.desactivado', 'profesional', 'confirmado'),
            ('profesional.reactivado', 'profesional', 'confirmado'),
            ('box.creado', 'box', 'confirmado'),
            ('box.actualizado', 'box', 'confirmado'),
            ('box.desactivado', 'box', 'confirmado'),
            ('box.reactivado', 'box', 'confirmado'),
            ('prestacion.creada', 'prestacion', 'confirmado'),
            ('prestacion.actualizada', 'prestacion', 'confirmado'),
            ('prestacion.desactivada', 'prestacion', 'confirmado'),
            ('prestacion.reactivada', 'prestacion', 'confirmado'),
            ('horario.actualizado', 'horario', 'confirmado'),
            ('excepcion.creada', 'excepcion', 'confirmado'),
            ('excepcion.actualizada', 'excepcion', 'confirmado'),
            ('excepcion.eliminada', 'excepcion', 'confirmado'),
            ('bloqueo.creado', 'bloqueo', 'confirmado'),
            ('bloqueo.eliminado', 'bloqueo', 'confirmado'),
            ('cuenta.bootstrap', 'cuenta', 'confirmado'),
            ('cuenta.creada', 'cuenta', 'confirmado'),
            ('cuenta.actualizada', 'cuenta', 'confirmado'),
            ('sesion.iniciada', 'sesion', 'confirmado'),
            ('sesion.cerrada', 'sesion', 'confirmado'),
            ('sesion.rechazada', 'sesion', 'rechazado'),
        )
        with closing(sqlite3.connect(self.ruta, isolation_level=None)) as conexion:
            conexion.execute('PRAGMA foreign_keys=ON')
            conexion.execute('BEGIN IMMEDIATE')
            for action, resource_type, result in eventos_validos:
                registrar_evento_sqlite(
                    conexion, action=action, resource_type=resource_type, result=result)
            conexion.execute('COMMIT')
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT action, resource_type, result FROM eventos_auditoria ORDER BY id'
            ).fetchall(), list(eventos_validos))

    def test_helper_rechaza_combinaciones_no_permitidas(self):
        from odontologia.audit import _normalizar_evento

        combinaciones_invalidas = (
            ('turno.creado', 'cuenta', 'rechazado'),
            ('cuenta.creada', 'cuenta', 'rechazado'),
            ('sesion.iniciada', 'turno', 'confirmado'),
            ('prestacion.creada', 'profesional', 'confirmado'),
        )
        for action, resource_type, result in combinaciones_invalidas:
            with self.subTest(action=action, resource_type=resource_type, result=result):
                with self.assertRaises(ValueError):
                    _normalizar_evento(
                        action=action, resource_type=resource_type, result=result,
                        actor_id=None, resource_id=None, instante=None)

    def test_ddl_sqlite_rechaza_combinaciones_no_permitidas(self):
        combinaciones_invalidas = (
            ('turno.creado', 'cuenta', 'rechazado'),
            ('paciente.creado', 'cuenta', 'confirmado'),
            ('cuenta.creada', 'cuenta', 'rechazado'),
            ('sesion.iniciada', 'turno', 'confirmado'),
        )
        with closing(sqlite3.connect(self.ruta)) as conexion:
            for action, resource_type, result in combinaciones_invalidas:
                with self.subTest(action=action, resource_type=resource_type, result=result):
                    with self.assertRaises(sqlite3.IntegrityError):
                        conexion.execute(
                            'INSERT INTO eventos_auditoria '
                            '(created_at, action, resource_type, result) '
                            'VALUES (?, ?, ?, ?)',
                            ('2026-11-02T00:00:00+00:00', action, resource_type, result))

    def test_eventos_no_se_pueden_editar_ni_borrar_directamente(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute(
                "INSERT INTO eventos_auditoria(created_at, action, resource_type, result) "
                "VALUES ('2026-11-01T00:00:00+00:00', 'sesion.rechazada', 'sesion', 'rechazado')")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute("UPDATE eventos_auditoria SET result='confirmado'")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute('DELETE FROM eventos_auditoria')

    def test_consulta_rechaza_paginacion_fuera_de_limites(self):
        from odontologia.audit import listar_eventos_sqlite

        with closing(sqlite3.connect(self.ruta)) as conexion:
            for params in ({'limit': 101}, {'limit': 0}, {'offset': -1}):
                with self.subTest(params=params), self.assertRaises(ValueError):
                    listar_eventos_sqlite(conexion, **params)
    def test_consulta_usa_orden_estable_y_limite(self):
        from odontologia.audit import listar_eventos_sqlite

        with closing(sqlite3.connect(self.ruta, isolation_level=None)) as conexion:
            conexion.execute('PRAGMA foreign_keys=ON')
            for _ in range(3):
                conexion.execute('BEGIN IMMEDIATE')
                from odontologia.audit import registrar_evento_sqlite
                registrar_evento_sqlite(
                    conexion, action='sesion.rechazada', resource_type='sesion', result='rechazado',
                    instante=datetime.fromisoformat('2026-11-01T12:00:00+00:00'))
                conexion.execute('COMMIT')
            registros = listar_eventos_sqlite(conexion, limit=2, offset=0)
        self.assertEqual(len(registros), 2)
        self.assertGreater(registros[0]['id'], registros[1]['id'])

    def test_migracion_v1_a_v3_conserva_usuarios_existentes(self):
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        crear_primer_administrador(engine, 'admin.one', 'frase-larga-segura-2026')
        engine.dispose()
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('DROP TRIGGER eventos_auditoria_no_update')
            conexion.execute('DROP TRIGGER eventos_auditoria_no_delete')
            conexion.execute('DROP TABLE eventos_auditoria')
            conexion.execute('UPDATE auth_schema_version SET version=1')
            conexion.commit()
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT COUNT(*) FROM usuarios').fetchone()[0], 1)
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone()[0], 7)
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
                "AND name='eventos_auditoria'").fetchone()[0], 1)


class AuditoriaApiTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        self.admin = crear_primer_administrador(
            self.engine, 'admin.one', 'frase-larga-segura-2026')
        abierto = {str(dia): [{'inicio': '00:00', 'fin': '24:00'}] for dia in range(1, 8)}
        for tipo, recursos in (('profesional', ('profesional-A', 'profesional-B')),
                               ('box', ('box-A', 'box-B'))):
            for recurso in recursos:
                guardar_horario(self.engine, tipo, recurso, abierto)
        self.secreto = 'secreto-local-auditoria-pruebas-2026'
        with patch.dict(os.environ, {'JWT_SECRETO': self.secreto}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.admin_headers = self._login('admin.one', 'frase-larga-segura-2026')

    def _login(self, identificador, password):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': password})
        if respuesta.status_code != 200:
            return {}
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def test_auditoria_solo_admin_paginada_y_con_metadata(self):
        respuesta = self.client.get('/auditoria?limit=1&offset=0', headers=self.admin_headers)
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        self.assertEqual(respuesta.json()['limit'], 1)
        self.assertEqual(len(respuesta.json()['items']), 1)
        self.assertEqual(respuesta.json()['items'][0]['action'], 'sesion.iniciada')
        self.assertEqual(self.client.get('/auditoria').status_code, 401)
        crear_usuario(self.engine, 'recepcion.a', 'otra-frase-larga-segura-2026', 'recepcion')
        recepcion = self._login('recepcion.a', 'otra-frase-larga-segura-2026')
        self.assertEqual(self.client.get('/auditoria', headers=recepcion).status_code, 403)
        self.assertEqual(
            self.client.get('/auditoria?limit=101', headers=self.admin_headers).status_code, 422)

    def test_alta_turno_es_atomica_con_evento_sin_referencias_clinicas(self):
        payload = {'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A',
                   'box_id': 'box-A', 'inicio': '2026-10-15T09:00:00-03:00',
                   'fin': '2026-10-15T09:30:00-03:00'}
        respuesta = self.client.post('/turnos', headers=self.admin_headers, json=payload)
        self.assertEqual(respuesta.status_code, 201, respuesta.text)
        eventos = self.client.get('/auditoria', headers=self.admin_headers).json()['items']
        evento = next(item for item in eventos if item['action'] == 'turno.creado')
        self.assertEqual(evento['actor_id'], self.admin['id'])
        self.assertEqual(evento['resource_id'], str(respuesta.json()['id']))
        self.assertNotIn('paciente-A', str(evento))

    def test_fallo_al_auditar_turno_reversa_la_mutacion_y_falla_cerrado(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('''CREATE TRIGGER falla_auditoria BEFORE INSERT ON eventos_auditoria
                BEGIN SELECT RAISE(FAIL, 'fallo inyectado'); END''')
        respuesta = self.client.post('/turnos', headers=self.admin_headers, json={
            'paciente_id': 'paciente-A', 'profesional_id': 'profesional-A', 'box_id': 'box-A',
            'inicio': '2026-10-15T09:00:00-03:00', 'fin': '2026-10-15T09:30:00-03:00'})
        self.assertEqual(respuesta.status_code, 500, respuesta.text)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0], 0)
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='turno.creado'").fetchone()[0], 0)

    def test_cuentas_sesiones_y_rechazos_registran_solo_metadata(self):
        login_inexistente = self.client.post('/sesiones', json={
            'identificador': 'dato-que-no-debe-quedar', 'password': 'frase-larga-segura-2026'})
        login_incorrecto = self.client.post('/sesiones', json={
            'identificador': 'admin.one', 'password': 'otra-frase-larga-segura-2026'})
        self.assertEqual((login_inexistente.status_code, login_incorrecto.status_code), (401, 401))
        self.assertEqual(login_inexistente.json(), login_incorrecto.json())
        with closing(sqlite3.connect(self.ruta)) as conexion:
            rechazos = conexion.execute(
                "SELECT actor_id, action, resource_id, result FROM eventos_auditoria "
                "WHERE action='sesion.rechazada'").fetchall()
        self.assertEqual(rechazos, [(None, 'sesion.rechazada', None, 'rechazado')] * 2)
        self.assertNotIn('dato-que-no-debe-quedar', str(rechazos))

        creada = self.client.post('/usuarios', headers=self.admin_headers, json={
            'identificador': 'recepcion.a', 'password': 'otra-frase-larga-segura-2026',
            'rol': 'recepcion'})
        self.assertEqual(creada.status_code, 201, creada.text)
        actualizada = self.client.patch(
            f"/usuarios/{creada.json()['id']}", headers=self.admin_headers, json={'activo': False})
        self.assertEqual(actualizada.status_code, 200, actualizada.text)
        cerrada = self.client.delete('/sesiones/actual', headers=self.admin_headers)
        self.assertEqual(cerrada.status_code, 204, cerrada.text)
        headers_vigentes = self._login('admin.one', 'frase-larga-segura-2026')
        eventos = self.client.get('/auditoria', headers=headers_vigentes).json()['items']
        acciones = {evento['action'] for evento in eventos}
        self.assertTrue({'cuenta.bootstrap', 'cuenta.creada', 'cuenta.actualizada',
                         'sesion.iniciada', 'sesion.cerrada', 'sesion.rechazada'} <= acciones)
        texto = str(eventos)
        self.assertNotIn('password', texto)
        self.assertNotIn('dato-que-no-debe-quedar', texto)

    def test_fallo_de_auditoria_en_login_rechazado_da_503_generico(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('''CREATE TRIGGER falla_auditoria BEFORE INSERT ON eventos_auditoria
                BEGIN SELECT RAISE(FAIL, 'fallo inyectado'); END''')
        respuesta = self.client.post('/sesiones', json={
            'identificador': 'admin.one', 'password': 'no-es-la-correcta'})
        self.assertEqual(respuesta.status_code, 503, respuesta.text)
        self.assertNotIn('admin.one', respuesta.text)

    def test_fallo_al_auditar_alta_cuenta_revierte_la_cuenta(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('''CREATE TRIGGER falla_auditoria BEFORE INSERT ON eventos_auditoria
                BEGIN SELECT RAISE(FAIL, 'fallo inyectado'); END''')
        respuesta = self.client.post('/usuarios', headers=self.admin_headers, json={
            'identificador': 'recepcion.a', 'password': 'otra-frase-larga-segura-2026',
            'rol': 'recepcion'})
        self.assertEqual(respuesta.status_code, 503, respuesta.text)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM usuarios WHERE identificador='recepcion.a'").fetchone()[0], 0)

    def test_fallo_al_auditar_login_o_logout_revierte_sesion(self):
        from odontologia.auth.sesiones import validar_sesion

        token = self.admin_headers['Authorization'].split(' ', 1)[1]
        identidad = validar_sesion(self.engine, token, self.secreto)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            existentes = conexion.execute('SELECT COUNT(*) FROM sesiones').fetchone()[0]
            conexion.execute('''CREATE TRIGGER falla_auditoria BEFORE INSERT ON eventos_auditoria
                BEGIN SELECT RAISE(FAIL, 'fallo inyectado'); END''')
        login = self.client.post('/sesiones', json={
            'identificador': 'admin.one', 'password': 'frase-larga-segura-2026'})
        self.assertEqual(login.status_code, 503, login.text)
        salida = self.client.delete('/sesiones/actual', headers=self.admin_headers)
        self.assertEqual(salida.status_code, 503, salida.text)
        vigente = validar_sesion(self.engine, token, self.secreto)
        self.assertEqual(vigente['sesion_id'], identidad['sesion_id'])
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute('SELECT COUNT(*) FROM sesiones').fetchone()[0], existentes)
            self.assertIsNone(conexion.execute(
                'SELECT revocada_en FROM sesiones WHERE id=?', (identidad['sesion_id'],)
            ).fetchone()[0])

    def test_fallo_auditoria_bootstrap_y_cambio_cuenta_revierten_transaccion(self):
        ruta_nueva = Path(self.temporal.name) / 'bootstrap.sqlite3'
        inicializar_agenda(ruta_nueva)
        migrar_sqlite(ruta_nueva)
        engine_nuevo = crear_engine_autenticacion('sqlite', None, ruta_nueva)
        self.addCleanup(engine_nuevo.dispose)
        with closing(sqlite3.connect(ruta_nueva)) as conexion:
            conexion.execute('''CREATE TRIGGER falla_auditoria BEFORE INSERT ON eventos_auditoria
                BEGIN SELECT RAISE(FAIL, 'fallo inyectado'); END''')
        with self.assertRaises(ErrorUsuarios) as error:
            crear_primer_administrador(
                engine_nuevo, 'otro.admin', 'otra-frase-larga-segura-2026')
        self.assertEqual(error.exception.estado, 503)
        with closing(sqlite3.connect(ruta_nueva)) as conexion:
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM usuarios WHERE identificador='otro.admin'").fetchone()[0], 0)

    def test_fallo_auditoria_cambio_cuenta_conserva_estado_y_sesion(self):
        creada = self.client.post('/usuarios', headers=self.admin_headers, json={
            'identificador': 'recepcion.a', 'password': 'otra-frase-larga-segura-2026',
            'rol': 'recepcion'})
        self.assertEqual(creada.status_code, 201, creada.text)
        token_recepcion = self._login('recepcion.a', 'otra-frase-larga-segura-2026')
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('''CREATE TRIGGER falla_auditoria BEFORE INSERT ON eventos_auditoria
                BEGIN SELECT RAISE(FAIL, 'fallo inyectado'); END''')
        respuesta = self.client.patch(
            f"/usuarios/{creada.json()['id']}", headers=self.admin_headers, json={'activo': False})
        self.assertEqual(respuesta.status_code, 503, respuesta.text)
        sesion_vigente = self.client.get('/sesiones/actual', headers=token_recepcion)
        self.assertEqual(sesion_vigente.status_code, 200, sesion_vigente.text)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            activo = conexion.execute(
                "SELECT activo FROM usuarios WHERE id=?", (creada.json()['id'],)).fetchone()[0]
            self.assertEqual(activo, 1)


if __name__ == '__main__':
    unittest.main()
