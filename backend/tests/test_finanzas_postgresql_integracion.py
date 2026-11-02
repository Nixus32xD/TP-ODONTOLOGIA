from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from odontologia.db.models import CargoFinanciero, CobroFinanciero, ReversionCobro
from odontologia.finanzas_ledger import ErrorFinanzas, crear_cargo, registrar_cobro, revertir_cobro
from odontologia.reportes import consultar_reporte_financiero
from odontologia.backup.postgresql import crear_bundle_postgresql
from odontologia.backup.restauracion_postgresql import restaurar_bundle_postgresql


class FinanzasPostgreSQLIntegracionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url_original = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not url_original:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base = make_url(url_original)
        if (base.host not in ('127.0.0.1', 'localhost', '::1') or base.port != 55432
                or not (base.database or '').lower().endswith('_test')):
            raise unittest.SkipTest('C-19 requiere localhost:55432 y una base *_test.')
        cls.schema = f'c19_finanzas_{uuid4().hex}'
        cls.root_engine = create_engine(url_original)
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {cls.schema}'))
        cls.url = str(base.update_query_dict({'options': f'-csearch_path={cls.schema}'}))
        cls.engine = create_engine(cls.url)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = cls.url
        cls.config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        cls.config.set_main_option('script_location', str(Path(__file__).parents[1] / 'alembic'))
        cls.config.config_file_name = None
        command.upgrade(cls.config, '20261102_0013_patient_self_service')
        command.upgrade(cls.config, 'head')
        with Session(cls.engine) as session, session.begin():
            session.execute(text("INSERT INTO pacientes(id, nombre, activo) VALUES "
                                 "('p-c19', 'Paciente sintético C19', true)"))
            session.execute(text("INSERT INTO usuarios(id, identificador, password_hash, rol, activo) "
                                 "VALUES ('u-c19', 'admin.c19', 'hash-sintético', 'administrador', true)"))

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, 'root_engine'):
            return
        cls.engine.dispose()
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
        cls.root_engine.dispose()
        if cls.previous_database_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = cls.previous_database_url

    def test_upgrade_constraints_append_only_y_eventos_financieros(self):
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text(
                'SELECT version_num FROM alembic_version')).scalar_one(),
                '20261102_0014_financial_ledger')
        cargo = crear_cargo(self.engine, paciente_id='p-c19', actor_id='u-c19',
                            clave='pg-cargo', monto_ars='8.01', concepto='Cargo sintético')
        pago = registrar_cobro(self.engine, cargo_id=cargo['id'], actor_id='u-c19',
                               clave='pg-pago', monto_ars='8.01')
        reversion = revertir_cobro(self.engine, cobro_id=pago['id'], actor_id='u-c19',
                                   clave='pg-reversion', monto_ars='8.01',
                                   motivo='Reversión sintética')
        self.assertEqual(reversion['saldo_ars'], '8.01')
        with self.assertRaises(Exception):
            with self.engine.begin() as connection:
                connection.execute(text("UPDATE cargos_financieros SET concepto='mutado' WHERE id=:id"),
                                   {'id': cargo['id']})
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text(
                "SELECT action FROM eventos_auditoria WHERE resource_type='finanzas' "
                "ORDER BY id DESC LIMIT 3")).scalars().all(),
                ['cobro.revertido', 'cobro.registrado', 'cargo.creado'])

    def test_concurrencia_no_permite_sobrepago(self):
        cargo = crear_cargo(self.engine, paciente_id='p-c19', actor_id='u-c19',
                            clave='pg-concurrent-cargo', monto_ars='1.00',
                            concepto='Cargo concurrency')

        def pagar(indice):
            try:
                registrar_cobro(self.engine, cargo_id=cargo['id'], actor_id='u-c19',
                                clave=f'pg-concurrent-{indice}', monto_ars='0.75')
                return 'ok'
            except ErrorFinanzas as error:
                return error.estado

        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(pagar, range(2)))
        self.assertCountEqual(resultados, ['ok', 409])

    def test_concurrencia_no_reversa_mas_que_el_cobro(self):
        cargo = crear_cargo(self.engine, paciente_id='p-c19', actor_id='u-c19',
                            clave='pg-reverse-cargo', monto_ars='1.00',
                            concepto='Cargo reverse concurrency')
        pago = registrar_cobro(self.engine, cargo_id=cargo['id'], actor_id='u-c19',
                               clave='pg-reverse-payment', monto_ars='1.00')

        def revertir(indice):
            try:
                revertir_cobro(self.engine, cobro_id=pago['id'], actor_id='u-c19',
                               clave=f'pg-reverse-{indice}', monto_ars='0.75',
                               motivo='Prueba de concurrencia')
                return 'ok'
            except ErrorFinanzas as error:
                return error.estado

        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(revertir, range(2)))
        self.assertCountEqual(resultados, ['ok', 409])

    def test_bundle_y_restore_postgresql_preservan_ledger_sin_contenido_en_manifest(self):
        sufijo = uuid4().hex[:10]
        cargo = crear_cargo(self.engine, paciente_id='p-c19', actor_id='u-c19',
                            clave=f'backup-cargo-{sufijo}', monto_ars='3.25',
                            concepto='Concepto privado sintético')
        pago = registrar_cobro(self.engine, cargo_id=cargo['id'], actor_id='u-c19',
                               clave=f'backup-pago-{sufijo}', monto_ars='1.25')
        revertir_cobro(self.engine, cobro_id=pago['id'], actor_id='u-c19',
                       clave=f'backup-reversion-{sufijo}', monto_ars='0.25',
                       motivo='Motivo privado sintético')
        destino = f'c19_finanzas_restore_{sufijo}_test'
        with TemporaryDirectory() as temporal:
            bundle = Path(temporal) / 'bundle-c19'
            try:
                manifiesto = crear_bundle_postgresql(self.engine, bundle)
                self.assertGreaterEqual(manifiesto['table_counts']['cargos_financieros'], 1)
                self.assertGreaterEqual(manifiesto['table_counts']['cobros_financieros'], 1)
                self.assertGreaterEqual(manifiesto['table_counts']['reversiones_cobros'], 1)
                texto = (bundle / 'manifest.json').read_text(encoding='utf-8')
                self.assertNotIn('Concepto privado sintético', texto)
                self.assertNotIn('Motivo privado sintético', texto)
                resultado = restaurar_bundle_postgresql(self.engine, bundle, destino)
                self.assertEqual(resultado['table_counts'], manifiesto['table_counts'])
                restored = create_engine(self.engine.url.set(database=destino))
                try:
                    with restored.connect() as connection:
                        self.assertEqual(connection.execute(text(
                            'SELECT monto_centavos FROM cargos_financieros WHERE id=:id'),
                            {'id': cargo['id']}).scalar_one(), 325)
                        self.assertEqual(connection.execute(text(
                            'SELECT motivo FROM reversiones_cobros WHERE cobro_id=:id'),
                            {'id': pago['id']}).scalar_one(), 'Motivo privado sintético')
                        self.assertEqual(connection.execute(text(
                            'SELECT count(*) FROM idempotencia_financiera WHERE clave=:clave'),
                            {'clave': f'backup-cargo-{sufijo}'}).scalar_one(), 1)
                finally:
                    restored.dispose()
            finally:
                admin = create_engine(
                    self.engine.url.set(database='postgres'), isolation_level='AUTOCOMMIT')
                try:
                    with admin.connect() as connection:
                        connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{destino}"')
                finally:
                    admin.dispose()

    def test_reporte_financiero_agrupa_por_fecha_local_y_calcula_cierre(self):
        cargo_prev = str(uuid4())
        cargo_actual = str(uuid4())
        cobro_prev = str(uuid4())
        cobro_actual = str(uuid4())
        fecha = lambda valor: datetime.fromisoformat(valor).astimezone(timezone.utc)
        with Session(self.engine) as session, session.begin():
            session.add_all([
                CargoFinanciero(id=cargo_prev, paciente_id='p-c19', monto_centavos=800,
                                concepto='Privado', created_at=fecha('2020-01-01T22:00:00+00:00')),
                CobroFinanciero(id=cobro_prev, cargo_id=cargo_prev, monto_centavos=100,
                                created_at=fecha('2020-01-01T22:10:00+00:00')),
                CargoFinanciero(id=cargo_actual, paciente_id='p-c19', monto_centavos=200,
                                concepto='No exportar', created_at=fecha('2020-01-02T13:00:00+00:00')),
                CobroFinanciero(id=cobro_actual, cargo_id=cargo_actual, monto_centavos=50,
                                created_at=fecha('2020-01-02T14:00:00+00:00')),
                ReversionCobro(id=str(uuid4()), cobro_id=cobro_actual, monto_centavos=25,
                               motivo='No exportar tampoco', created_at=fecha('2020-01-02T15:00:00+00:00')),
            ])
        reporte = consultar_reporte_financiero(self.engine, '2020-01-02', '2020-01-03')
        self.assertEqual(reporte['saldo_apertura_ars'], '7.00')
        self.assertEqual(reporte['dias'][0]['cargos']['importe_ars'], '2.00')
        self.assertEqual(reporte['dias'][0]['cobros']['importe_ars'], '0.50')
        self.assertEqual(reporte['dias'][0]['reversiones']['importe_ars'], '0.25')
        self.assertEqual(reporte['dias'][0]['saldo_cierre_ars'], '8.75')
        self.assertNotIn('Privado', str(reporte))
        self.assertNotIn('p-c19', str(reporte))


if __name__ == '__main__':
    unittest.main()
