from pathlib import Path
import csv
from datetime import date, datetime, timedelta
from io import StringIO
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from odontologia import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario
from odontologia.pacientes import crear_paciente


class ApiReportesAgendaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'agenda.sqlite3'
        inicializar_agenda(self.db)
        migrar_sqlite(self.db)
        self.engine = crear_engine_autenticacion('sqlite', None, self.db)
        self.addCleanup(self.engine.dispose)
        crear_primer_administrador(self.engine, 'admin.report', 'frase-admin-reportes-segura-2026')
        crear_usuario(self.engine, 'recepcion.report', 'frase-recepcion-reportes-2026', 'recepcion')
        crear_usuario(self.engine, 'profesional.report', 'frase-profesional-reportes-2026',
                      'profesional', profesional_id='profesional-A')
        paciente = crear_paciente(self.engine, nombre='Paciente sintético reportes')
        self.paciente_id = paciente['id']
        crear_usuario(self.engine, 'paciente.report', 'frase-paciente-reportes-2026',
                      'paciente', paciente_id=paciente['id'])
        with patch.dict(os.environ, {
                'JWT_SECRETO': 'secreto-local-reportes-test-no-reutilizar-2026',
                'ODONTOLOGIA_ENTORNO': 'desarrollo'}, clear=True):
            self.client = TestClient(crear_app(self.db))
        self.addCleanup(self.client.close)
        self.admin = self._login('admin.report', 'frase-admin-reportes-segura-2026')
        self.recepcion = self._login('recepcion.report', 'frase-recepcion-reportes-2026')
        self.profesional = self._login('profesional.report', 'frase-profesional-reportes-2026')
        self.paciente = self._login('paciente.report', 'frase-paciente-reportes-2026')

    def _login(self, identificador, password):
        respuesta = self.client.post('/sesiones', json={
            'identificador': identificador, 'password': password})
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        return {'Authorization': f"Bearer {respuesta.json()['access_token']}"}

    def test_agenda_restringe_roles_y_valida_rango(self):
        ruta = '/reportes/agenda?desde=2026-11-02&hasta=2026-11-03'
        admin = self.client.get(ruta, headers=self.admin)
        self.assertEqual(admin.status_code, 200, admin.text)
        self.assertEqual(admin.json()['zona'], 'America/Argentina/Mendoza')
        self.assertEqual(admin.json()['dias'][0]['fecha'], '2026-11-02')
        recepcion = self.client.get(ruta, headers=self.recepcion)
        self.assertEqual(recepcion.status_code, 200, recepcion.text)
        for headers in (self.profesional, self.paciente):
            with self.subTest(headers=headers):
                self.assertEqual(self.client.get(ruta, headers=headers).status_code, 403)
        self.assertEqual(self.client.get(ruta).status_code, 401)
        invalido = self.client.get(
            '/reportes/agenda?desde=2026-11-02&hasta=2026-12-04', headers=self.admin)
        self.assertEqual(invalido.status_code, 422)

    def test_openapi_documenta_consulta_de_agenda(self):
        rutas = self.client.get('/openapi.json').json()['paths']
        self.assertIn('/reportes/agenda', rutas)
        self.assertIn('/reportes/agenda.csv', rutas)
        self.assertIn('/reportes/finanzas', rutas)
        self.assertIn('/reportes/finanzas.csv', rutas)
        self.assertIn('text/csv', rutas['/reportes/agenda.csv']['get']['responses']['200']['content'])
        self.assertIn('text/csv', rutas['/reportes/finanzas.csv']['get']['responses']['200']['content'])
        parametros = {parametro['name'] for parametro in rutas['/reportes/agenda']['get']['parameters']}
        self.assertTrue({'desde', 'hasta'} <= parametros)

    def test_reporte_financiero_es_solo_admin_y_no_expone_detalle_del_ledger(self):
        cargo = self.client.post(
            f'/finanzas/pacientes/{self.paciente_id}/cargos',
            headers={**self.recepcion, 'Idempotency-Key': 'reporte-cargo'},
            json={'monto_ars': '10.00', 'concepto': 'Texto privado sintético'},
        )
        self.assertEqual(cargo.status_code, 201, cargo.text)
        cobro = self.client.post(
            f"/finanzas/cargos/{cargo.json()['id']}/cobros",
            headers={**self.recepcion, 'Idempotency-Key': 'reporte-cobro'},
            json={'monto_ars': '3.00'},
        )
        self.assertEqual(cobro.status_code, 201, cobro.text)
        reversion = self.client.post(
            f"/finanzas/cobros/{cobro.json()['id']}/reversiones",
            headers={**self.admin, 'Idempotency-Key': 'reporte-reversion'},
            json={'monto_ars': '1.00', 'motivo': 'Motivo reservado'},
        )
        self.assertEqual(reversion.status_code, 201, reversion.text)

        hoy = datetime.now(ZoneInfo('America/Argentina/Mendoza')).date()
        desde = hoy.isoformat()
        hasta = (hoy + timedelta(days=1)).isoformat()
        ruta = f'/reportes/finanzas?desde={desde}&hasta={hasta}'
        reporte = self.client.get(ruta, headers=self.admin)
        self.assertEqual(reporte.status_code, 200, reporte.text)
        self.assertEqual(reporte.json()['dias'][0]['cargos']['importe_ars'], '10.00')
        self.assertEqual(reporte.json()['dias'][0]['cobros']['importe_ars'], '3.00')
        self.assertEqual(reporte.json()['dias'][0]['reversiones']['importe_ars'], '1.00')
        self.assertEqual(reporte.json()['dias'][0]['saldo_cierre_ars'], '8.00')
        self.assertNotIn(self.paciente_id, reporte.text)
        self.assertNotIn('Texto privado', reporte.text)
        self.assertNotIn('Motivo reservado', reporte.text)
        for headers in (self.recepcion, self.profesional, self.paciente):
            with self.subTest(headers=headers):
                self.assertEqual(self.client.get(ruta, headers=headers).status_code, 403)
        self.assertEqual(self.client.get(ruta).status_code, 401)

        ruta_csv = f'/reportes/finanzas.csv?desde={desde}&hasta={hasta}'
        csv_finanzas = self.client.get(ruta_csv, headers=self.admin)
        self.assertEqual(csv_finanzas.status_code, 200, csv_finanzas.text)
        self.assertIn('text/csv', csv_finanzas.headers['content-type'])
        self.assertIn('attachment;', csv_finanzas.headers['content-disposition'])
        filas = list(csv.reader(StringIO(csv_finanzas.text, newline='')))
        self.assertEqual(filas[1][2:8], ['10.00', '1', '3.00', '1', '1.00', '2.00'])
        self.assertEqual(filas[1][-1], '8.00')
        self.assertIn('finanzas-', csv_finanzas.headers['content-disposition'])
        self.assertNotIn(self.paciente_id, csv_finanzas.text)
        self.assertNotIn('Texto privado', csv_finanzas.text)
        self.assertNotIn('Motivo reservado', csv_finanzas.text)
        self.assertEqual(self.client.get(ruta_csv, headers=self.recepcion).status_code, 403)

    def test_csv_agenda_coincide_con_json_y_respeta_restricciones(self):
        consulta = 'desde=2026-11-02&hasta=2026-11-03'
        json_agenda = self.client.get(f'/reportes/agenda?{consulta}', headers=self.recepcion)
        csv_agenda = self.client.get(f'/reportes/agenda.csv?{consulta}', headers=self.recepcion)
        self.assertEqual(csv_agenda.status_code, 200, csv_agenda.text)
        self.assertIn('text/csv', csv_agenda.headers['content-type'])
        self.assertIn('agenda-operativa-2026-11-02-2026-11-03.csv',
                      csv_agenda.headers['content-disposition'])
        filas = list(csv.reader(StringIO(csv_agenda.text, newline='')))
        self.assertEqual(filas[0][0:5], ['fecha', 'tipo_fila', 'estado', 'cantidad', 'minutos'])
        reservado = next(fila for fila in filas if fila[2:3] == ['reservado'])
        self.assertEqual(reservado[0], json_agenda.json()['dias'][0]['fecha'])
        self.assertEqual(reservado[3], str(json_agenda.json()['dias'][0]['estados']['reservado']['cantidad']))
        self.assertNotIn(self.paciente_id, csv_agenda.text)
        self.assertEqual(self.client.get(f'/reportes/agenda.csv?{consulta}',
                                         headers=self.profesional).status_code, 403)


if __name__ == '__main__':
    unittest.main()
