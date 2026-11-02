from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zoneinfo import ZoneInfo
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from odontologia import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario
from odontologia.db.models import Box, Paciente, Profesional
from odontologia.disponibilidad import guardar_horario


class ApiPortalPacienteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        self.secreto = 'secreto-local-api-portal-sintetico-2026'
        admin = crear_primer_administrador(
            self.engine, 'admin.portal', 'frase-larga-segura-admin-2026')
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id='portal-paciente', nombre='Paciente sintético', activo=True,
                         acepta_recordatorios=False),
                Profesional(id='portal-prof', nombre='Profesional sintético', activo=True),
                Box(id='portal-box', nombre='Box sintético', activo=True),
            ])
        self.paciente = crear_usuario(
            self.engine, 'paciente.portal', 'frase-larga-segura-paciente-2026',
            'paciente', paciente_id='portal-paciente')
        self.admin_id = admin['id']
        horario = {str(dia): [{'inicio': '08:00', 'fin': '12:00'}]
                   for dia in range(1, 8)}
        guardar_horario(self.engine, 'profesional', 'portal-prof', horario)
        guardar_horario(self.engine, 'box', 'portal-box', horario)
        with patch.dict('os.environ', {
                'JWT_SECRETO': self.secreto, 'ODONTOLOGIA_ENTORNO': 'desarrollo'}, clear=True):
            self.client = TestClient(crear_app(self.ruta))
        self.addCleanup(self.client.close)
        self.admin_headers = self.login('admin.portal', 'frase-larga-segura-admin-2026')
        self.paciente_headers = self.login(
            'paciente.portal', 'frase-larga-segura-paciente-2026')
        self.ahora = datetime(2026, 11, 2, 10, 0, tzinfo=ZoneInfo('America/Argentina/Mendoza'))

    def login(self, identificador, password):
        response = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': password})
        self.assertEqual(response.status_code, 200, response.text)
        return {'Authorization': f"Bearer {response.json()['access_token']}"}

    def test_portal_muestra_disponibilidad_minima_y_reserva_solo_desde_principal(self):
        disponibilidad = self.client.get(
            '/portal/disponibilidad?fecha=2026-11-03', headers=self.paciente_headers)
        self.assertEqual(disponibilidad.status_code, 200, disponibilidad.text)
        self.assertTrue(disponibilidad.json()['items'])
        self.assertEqual(set(disponibilidad.json()['items'][0]), {'inicio', 'fin'})

        reservado = self.client.post('/mis-turnos', headers={
            **self.paciente_headers, 'Idempotency-Key': 'reserva-api-001'}, json={
                'inicio': '2026-11-03T09:00:00-03:00'})
        self.assertEqual(reservado.status_code, 201, reservado.text)
        self.assertEqual(set(reservado.json()), {
            'turno_id', 'inicio', 'fin', 'estado', 'version'})
        listado = self.client.get('/mis-turnos', headers=self.paciente_headers)
        self.assertEqual(listado.status_code, 200, listado.text)
        self.assertEqual(len(listado.json()['items']), 1)
        self.assertNotIn('paciente_id', listado.json()['items'][0])

        con_identidad_en_body = self.client.post('/mis-turnos', headers={
            **self.paciente_headers, 'Idempotency-Key': 'reserva-api-002'}, json={
                'inicio': '2026-11-03T09:30:00-03:00', 'paciente_id': 'otro-paciente'})
        self.assertEqual(con_identidad_en_body.status_code, 422)

    def test_personal_no_consulta_portal_ni_obtiene_turnos(self):
        self.assertEqual(self.client.get(
            '/mis-turnos', headers=self.admin_headers).status_code, 403)
        self.assertEqual(self.client.get(
            '/portal/disponibilidad?fecha=2026-11-03',
            headers=self.admin_headers).status_code, 403)

    def test_paciente_reprograma_y_cancela_su_turno_con_claves_idempotentes(self):
        creado = self.client.post('/mis-turnos', headers={
            **self.paciente_headers, 'Idempotency-Key': 'api-reserva-movimiento'}, json={
                'inicio': '2026-11-04T09:00:00-03:00'})
        self.assertEqual(creado.status_code, 201, creado.text)
        turno_id = creado.json()['turno_id']
        reprogramado = self.client.post(
            f'/mis-turnos/{turno_id}/reprogramacion', headers={
                **self.paciente_headers, 'Idempotency-Key': 'api-reprogramacion'}, json={
                    'version': creado.json()['version'],
                    'inicio': '2026-11-04T10:00:00-03:00'})
        self.assertEqual(reprogramado.status_code, 200, reprogramado.text)
        self.assertEqual(reprogramado.json()['version'], creado.json()['version'] + 1)
        cancelado = self.client.post(
            f'/mis-turnos/{turno_id}/cancelacion', headers={
                **self.paciente_headers, 'Idempotency-Key': 'api-cancelacion'})
        self.assertEqual(cancelado.status_code, 200, cancelado.text)
        self.assertEqual(cancelado.json()['estado'], 'cancelado')


if __name__ == '__main__':
    unittest.main()
