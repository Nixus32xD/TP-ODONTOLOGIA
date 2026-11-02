from contextlib import closing
from pathlib import Path
import os
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi.testclient import TestClient

from odontologia import inicializar_agenda
from odontologia.api import crear_app
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario
from odontologia.pacientes import crear_paciente


class ApiFinanzasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'agenda.sqlite3'
        inicializar_agenda(self.db)
        migrar_sqlite(self.db)
        self.engine = crear_engine_autenticacion('sqlite', None, self.db)
        self.addCleanup(self.engine.dispose)
        crear_primer_administrador(self.engine, 'admin.one', 'frase-admin-test-segura-2026')
        crear_usuario(self.engine, 'recepcion.one', 'frase-recepcion-test-segura-2026', 'recepcion')
        crear_usuario(self.engine, 'profesional.one', 'frase-profesional-test-2026',
                      'profesional', profesional_id='profesional-A')
        crear_paciente(self.engine, nombre='Paciente sintético financiero')
        self.secreto = 'secreto-local-finanzas-test-no-reutilizar-2026'
        with patch.dict(os.environ, {
                'JWT_SECRETO': self.secreto, 'ODONTOLOGIA_ENTORNO': 'desarrollo'}, clear=True):
            self.client = TestClient(crear_app(self.db))
        self.addCleanup(self.client.close)
        self.admin = self._login('admin.one', 'frase-admin-test-segura-2026')
        self.recepcion = self._login('recepcion.one', 'frase-recepcion-test-segura-2026')
        self.profesional = self._login('profesional.one', 'frase-profesional-test-2026')

    def _login(self, usuario, clave):
        response = self.client.post('/sesiones', json={'identificador': usuario, 'password': clave})
        self.assertEqual(response.status_code, 200, response.text)
        return {'Authorization': f"Bearer {response.json()['access_token']}"}

    def test_cargo_cobro_reversion_y_saldo_exactos_con_permisos(self):
        pacientes = self.client.get('/pacientes', headers=self.recepcion).json()['items']
        paciente_id = pacientes[0]['id']
        base = f'/finanzas/pacientes/{paciente_id}'
        self.assertEqual(self.client.post(f'{base}/cargos', headers=self.profesional,
                                          json={'monto_ars': '10.01', 'concepto': 'Control'}).status_code, 403)
        cargo = self.client.post(f'{base}/cargos', headers={**self.recepcion, 'Idempotency-Key': 'cargo-1'},
                                 json={'monto_ars': '10.01', 'concepto': 'Control'})
        self.assertEqual(cargo.status_code, 201, cargo.text)
        self.assertEqual(cargo.json()['saldo_ars'], '10.01')
        cobro = self.client.post(f"/finanzas/cargos/{cargo.json()['id']}/cobros",
                                 headers={**self.recepcion, 'Idempotency-Key': 'cobro-1'},
                                 json={'monto_ars': '3.33'})
        self.assertEqual(cobro.status_code, 201, cobro.text)
        self.assertEqual(cobro.json()['saldo_ars'], '6.68')
        reversion = self.client.post(f"/finanzas/cobros/{cobro.json()['id']}/reversiones",
                                     headers={**self.admin, 'Idempotency-Key': 'rev-1'},
                                     json={'monto_ars': '1.11', 'motivo': 'Corrección sintética'})
        self.assertEqual(reversion.status_code, 201, reversion.text)
        self.assertEqual(reversion.json()['saldo_ars'], '7.79')
        ledger = self.client.get(base, headers=self.recepcion)
        self.assertEqual(ledger.status_code, 200, ledger.text)
        self.assertEqual(ledger.json()['saldo_ars'], '7.79')
        eventos = self.client.get('/auditoria', headers=self.admin).json()['items']
        financieros = [evento for evento in eventos if evento['resource_type'] == 'finanzas']
        self.assertEqual([evento['action'] for evento in financieros[:4]], [
            'finanzas.consultadas', 'cobro.revertido', 'cobro.registrado', 'cargo.creado'])
        self.assertNotIn('Control', str(financieros))
        self.assertNotIn('Corrección sintética', str(financieros))

    def test_sobrepago_recepcion_reversion_y_idempotencia_se_rechazan_o_reproducen(self):
        paciente_id = self.client.get('/pacientes', headers=self.recepcion).json()['items'][0]['id']
        cargo = self.client.post(f'/finanzas/pacientes/{paciente_id}/cargos',
            headers={**self.admin, 'Idempotency-Key': 'cargo-x'},
            json={'monto_ars': '2.00', 'concepto': 'Servicio sintético'})
        self.assertEqual(cargo.status_code, 201, cargo.text)
        replay_headers = {**self.recepcion, 'Idempotency-Key': 'pay-x'}
        pago = self.client.post(f"/finanzas/cargos/{cargo.json()['id']}/cobros",
                                headers=replay_headers, json={'monto_ars': '2.00'})
        self.assertEqual(pago.status_code, 201, pago.text)
        self.assertEqual(self.client.post(f"/finanzas/cargos/{cargo.json()['id']}/cobros",
                                          headers=replay_headers,
                                          json={'monto_ars': '2.00'}).json(), pago.json())
        with closing(sqlite3.connect(self.db)) as conexion:
            self.assertEqual(conexion.execute(
                "SELECT count(*) FROM eventos_auditoria WHERE action='cobro.registrado'"
            ).fetchone()[0], 1)
        self.assertEqual(self.client.post(f"/finanzas/cargos/{cargo.json()['id']}/cobros",
            headers={**self.recepcion, 'Idempotency-Key': 'over-x'},
            json={'monto_ars': '0.01'}).status_code, 409)
        self.assertEqual(self.client.post(f"/finanzas/cobros/{pago.json()['id']}/reversiones",
            headers={**self.recepcion, 'Idempotency-Key': 'forbidden-x'},
            json={'monto_ars': '0.01', 'motivo': 'no'}).status_code, 403)
        self.assertEqual(self.client.post(f"/finanzas/cargos/{cargo.json()['id']}/cobros",
            headers=replay_headers, json={'monto_ars': '1.99'}).status_code, 409)
        self.assertEqual(self.client.post(f"/finanzas/cargos/{cargo.json()['id']}/cobros",
            headers={**self.recepcion, 'Idempotency-Key': 'malformed-x'},
            json={'monto_ars': 1.25}).status_code, 422)

    def test_cobros_concurrentes_no_sobrepagan_y_fallo_de_auditoria_hace_rollback(self):
        paciente_id = self.client.get('/pacientes', headers=self.recepcion).json()['items'][0]['id']
        cargo = self.client.post(f'/finanzas/pacientes/{paciente_id}/cargos',
            headers={**self.admin, 'Idempotency-Key': 'concurrent-cargo'},
            json={'monto_ars': '1.00', 'concepto': 'Control sintético'}).json()

        def cobrar(indice):
            return self.client.post(f"/finanzas/cargos/{cargo['id']}/cobros",
                headers={**self.recepcion, 'Idempotency-Key': f'concurrent-{indice}'},
                json={'monto_ars': '0.75'}).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(cobrar, range(2)))
        self.assertCountEqual(resultados, [201, 409])
        self.assertEqual(self.client.get(f'/finanzas/pacientes/{paciente_id}',
                                         headers=self.recepcion).json()['saldo_ars'], '0.25')

        with patch('odontologia.finanzas_ledger.registrar_evento_session',
                   side_effect=RuntimeError('auditoría no disponible')):
            respuesta = self.client.post(f'/finanzas/pacientes/{paciente_id}/cargos',
                headers={**self.admin, 'Idempotency-Key': 'audit-fails'},
                json={'monto_ars': '2.00', 'concepto': 'Rollback sintético'})
        self.assertEqual(respuesta.status_code, 503)
        with self.engine.connect() as conexion:
            self.assertEqual(conexion.exec_driver_sql(
                "SELECT count(*) FROM cargos_financieros WHERE concepto='Rollback sintético'"
            ).scalar_one(), 0)
            self.assertEqual(conexion.exec_driver_sql(
                "SELECT count(*) FROM idempotencia_financiera WHERE clave='audit-fails'"
            ).scalar_one(), 0)

    def test_openapi_documenta_rutas_financieras_y_no_publica_integraciones_externas(self):
        esquema = self.client.get('/openapi.json').json()
        rutas = esquema['paths']
        self.assertIn('/finanzas/pacientes/{paciente_id}', rutas)
        self.assertIn('/finanzas/pacientes/{paciente_id}/cargos', rutas)
        self.assertIn('/finanzas/cargos/{cargo_id}/cobros', rutas)
        self.assertIn('/finanzas/cobros/{cobro_id}/reversiones', rutas)
        operaciones = str({ruta: rutas[ruta] for ruta in rutas if ruta.startswith('/finanzas/')})
        self.assertNotIn('provider', operaciones.casefold())
        self.assertNotIn('arca', operaciones.casefold())


if __name__ == '__main__':
    unittest.main()
