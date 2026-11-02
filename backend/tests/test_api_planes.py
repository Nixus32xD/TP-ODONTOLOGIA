from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from odontologia import crear_turno, inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario
from odontologia.audit import ErrorAuditoria
from odontologia.db.models import Prestacion


class ApiPlanesTratamientoTests(unittest.TestCase):
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
        migrar_sqlite(self.ruta)
        engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.admin = crear_primer_administrador(
            engine, 'admin.planes-api', 'frase-larga-segura-2026')
        self.profesional = crear_usuario(
            engine, 'profesional.planes-api', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A', actor_id=self.admin['id'])
        self.profesional_b = crear_usuario(
            engine, 'profesional.planes-api.b', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-B', actor_id=self.admin['id'])
        self.recepcion = crear_usuario(
            engine, 'recepcion.planes-api', 'frase-larga-segura-2026', 'recepcion',
            actor_id=self.admin['id'])
        with Session(engine) as session, session.begin():
            session.add_all([
                Prestacion(id='prestacion-activa', nombre='Prestación sintética',
                           duracion_minutos=30, activo=True),
                Prestacion(id='prestacion-inactiva', nombre='Prestación no activa',
                           duracion_minutos=30, activo=False),
            ])
        engine.dispose()
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute("UPDATE turnos SET estado='atendido' WHERE id=?",
                               (self.turno_a.id,))
            connection.commit()
        with patch.dict('os.environ', {
                'JWT_SECRETO': 'secreto-local-pruebas-planes-2026',
                'ODONTOLOGIA_ENTORNO': 'desarrollo'}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.admin_headers = self.login('admin.planes-api')
        self.profesional_headers = self.login('profesional.planes-api')
        self.recepcion_headers = self.login('recepcion.planes-api')
        self.profesional_b_headers = self.login('profesional.planes-api.b')

    def login(self, identificador):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': 'frase-larga-segura-2026'})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def test_profesional_crea_consulta_y_transiciona_plan(self):
        alta = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        self.assertEqual(alta.status_code, 201, alta.text)
        self.assertEqual(alta.json()['estado'], 'propuesto')
        estado = self.client.patch(
            f"/planes/{alta.json()['id']}/estado", headers=self.profesional_headers,
            json={'estado': 'en_curso'})
        self.assertEqual(estado.status_code, 200, estado.text)
        self.assertEqual(estado.json()['estado'], 'en_curso')
        consulta = self.client.get('/pacientes/paciente-A/planes',
                                   headers=self.profesional_headers)
        self.assertEqual(consulta.status_code, 200, consulta.text)
        self.assertEqual(consulta.json()['items'][0]['estado'], 'en_curso')
        respuesta = str(consulta.json()).lower()
        for campo in ('precio', 'turno_id', 'consentimiento', 'diagnostico'):
            self.assertNotIn(campo, respuesta)

    def test_rechaza_prestacion_inactiva_y_transicion_invalida(self):
        inactiva = self.client.post('/pacientes/paciente-A/planes',
                                    headers=self.profesional_headers,
                                    json={'prestaciones_ids': ['prestacion-inactiva']})
        self.assertEqual(inactiva.status_code, 422, inactiva.text)
        plan = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        rechazada = self.client.patch(
            f"/planes/{plan.json()['id']}/estado", headers=self.profesional_headers,
            json={'estado': 'completado'})
        self.assertEqual(rechazada.status_code, 409, rechazada.text)
        consulta = self.client.get('/pacientes/paciente-A/planes',
                                   headers=self.profesional_headers)
        self.assertEqual(consulta.json()['items'][0]['estado'], 'propuesto')

    def test_admin_recepcion_y_profesional_sin_atencion_no_reciben_plan(self):
        plan = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        self.assertEqual(plan.status_code, 201, plan.text)
        for headers in (self.admin_headers, self.recepcion_headers):
            self.assertEqual(self.client.get('/pacientes/paciente-A/planes',
                                             headers=headers).status_code, 403)
            self.assertEqual(self.client.post('/pacientes/paciente-A/planes',
                                              headers=headers,
                                              json={'prestaciones_ids': ['prestacion-activa']}
                                              ).status_code, 403)
            self.assertEqual(self.client.patch(
                f"/planes/{plan.json()['id']}/estado", headers=headers,
                json={'estado': 'en_curso'}).status_code, 403)
        sin_turno = self.client.get('/pacientes/paciente-B/planes',
                                    headers=self.profesional_headers)
        self.assertEqual(sin_turno.status_code, 404)
        transicion_ajena = self.client.patch(
            f"/planes/{plan.json()['id']}/estado", headers=self.profesional_b_headers,
            json={'estado': 'en_curso'})
        self.assertEqual(transicion_ajena.status_code, 404)

    def test_openapi_expone_rutas_plan_y_rechaza_campos_extra(self):
        extra = self.client.post('/pacientes/paciente-A/planes',
                                 headers=self.profesional_headers,
                                 json={'prestaciones_ids': ['prestacion-activa'],
                                       'precio': 100})
        self.assertEqual(extra.status_code, 422)
        paths = self.client.get('/openapi.json').json()['paths']
        self.assertIn('/pacientes/{paciente_id}/planes', paths)
        self.assertIn('/planes/{plan_id}/estado', paths)

    def test_profesional_inactivo_no_consulta_crea_ni_cambia_planes(self):
        plan = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        self.assertEqual(plan.status_code, 201, plan.text)
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute(
                "UPDATE profesionales SET activo=0 WHERE id='profesional-A'")
            connection.commit()
        lectura = self.client.get('/pacientes/paciente-A/planes',
                                  headers=self.profesional_headers)
        alta = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        cambio = self.client.patch(
            f"/planes/{plan.json()['id']}/estado", headers=self.profesional_headers,
            json={'estado': 'en_curso'})
        self.assertIn(lectura.status_code, (403, 404), lectura.text)
        self.assertIn(alta.status_code, (403, 404), alta.text)
        self.assertIn(cambio.status_code, (403, 404), cambio.text)

    def test_cuenta_inactiva_no_consulta_crea_ni_cambia_planes(self):
        plan = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        self.assertEqual(plan.status_code, 201, plan.text)
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute("UPDATE usuarios SET activo=0 WHERE identificador=?",
                               ('profesional.planes-api',))
            connection.commit()
        lectura = self.client.get('/pacientes/paciente-A/planes',
                                  headers=self.profesional_headers)
        alta = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        cambio = self.client.patch(
            f"/planes/{plan.json()['id']}/estado", headers=self.profesional_headers,
            json={'estado': 'en_curso'})
        self.assertEqual(lectura.status_code, 401, lectura.text)
        self.assertEqual(alta.status_code, 401, alta.text)
        self.assertEqual(cambio.status_code, 401, cambio.text)

    def test_vinculo_actual_invalida_token_previo_para_todos_los_endpoints(self):
        plan = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        self.assertEqual(plan.status_code, 201, plan.text)
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-C', 'Profesional sintético C', 1)")
            connection.execute(
                "UPDATE usuarios SET profesional_id='profesional-C' "
                "WHERE identificador='profesional.planes-api'")
            connection.commit()
        lectura = self.client.get('/pacientes/paciente-A/planes',
                                  headers=self.profesional_headers)
        alta = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        cambio = self.client.patch(
            f"/planes/{plan.json()['id']}/estado", headers=self.profesional_headers,
            json={'estado': 'en_curso'})
        self.assertIn(lectura.status_code, (401, 403, 404), lectura.text)
        self.assertIn(alta.status_code, (401, 403, 404), alta.text)
        self.assertIn(cambio.status_code, (401, 403, 404), cambio.text)

    def test_fallo_auditoria_revierte_creacion_y_estado_y_falla_cerrado(self):
        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            alta = self.client.post('/pacientes/paciente-A/planes',
                                    headers=self.profesional_headers,
                                    json={'prestaciones_ids': ['prestacion-activa']})
        self.assertEqual(alta.status_code, 503, alta.text)
        with closing(sqlite3.connect(self.ruta)) as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM planes_tratamiento').fetchone()[0], 0)

        plan = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            cambio = self.client.patch(
                f"/planes/{plan.json()['id']}/estado", headers=self.profesional_headers,
                json={'estado': 'en_curso'})
        self.assertEqual(cambio.status_code, 503, cambio.text)
        consulta = self.client.get('/pacientes/paciente-A/planes',
                                   headers=self.profesional_headers)
        self.assertEqual(consulta.json()['items'][0]['estado'], 'propuesto')

    def test_auditoria_plan_no_guarda_etapas_nombres_ni_prestaciones(self):
        self.client.post('/pacientes/paciente-A/planes',
                         headers=self.profesional_headers,
                         json={'prestaciones_ids': ['prestacion-activa']})
        auditoria = self.client.get('/auditoria', headers=self.admin_headers)
        eventos = [evento for evento in auditoria.json()['items']
                   if evento['action'] == 'plan.creado']
        self.assertEqual(len(eventos), 1)
        self.assertEqual(set(eventos[0]), {
            'id', 'created_at', 'actor_id', 'action', 'resource_type', 'resource_id', 'result'})
        self.assertNotIn('prestacion-activa', str(auditoria.json()))

    def test_fallo_auditoria_revierte_creacion_y_estado_y_falla_cerrado(self):
        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            alta = self.client.post('/pacientes/paciente-A/planes',
                                    headers=self.profesional_headers,
                                    json={'prestaciones_ids': ['prestacion-activa']})
        self.assertEqual(alta.status_code, 503, alta.text)
        with closing(sqlite3.connect(self.ruta)) as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM planes_tratamiento').fetchone()[0], 0)

        plan = self.client.post('/pacientes/paciente-A/planes',
                                headers=self.profesional_headers,
                                json={'prestaciones_ids': ['prestacion-activa']})
        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            cambio = self.client.patch(
                f"/planes/{plan.json()['id']}/estado", headers=self.profesional_headers,
                json={'estado': 'en_curso'})
        self.assertEqual(cambio.status_code, 503, cambio.text)
        consulta = self.client.get('/pacientes/paciente-A/planes',
                                   headers=self.profesional_headers)
        self.assertEqual(consulta.json()['items'][0]['estado'], 'propuesto')

    def test_auditoria_plan_no_guarda_etapas_nombres_ni_prestaciones(self):
        self.client.post('/pacientes/paciente-A/planes',
                         headers=self.profesional_headers,
                         json={'prestaciones_ids': ['prestacion-activa']})
        auditoria = self.client.get('/auditoria', headers=self.admin_headers)
        eventos = [evento for evento in auditoria.json()['items']
                   if evento['action'] == 'plan.creado']
        self.assertEqual(len(eventos), 1)
        self.assertEqual(set(eventos[0]), {
            'id', 'created_at', 'actor_id', 'action', 'resource_type', 'resource_id', 'result'})
        self.assertNotIn('prestacion-activa', str(auditoria.json()))


if __name__ == '__main__':
    unittest.main()
