import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from odontologia.backup.manifest import (
    ESQUEMAS_SOPORTADOS,
    ErrorManifiesto,
    TABLAS_ESQUEMA_ACTUAL,
    crear_manifiesto,
    guardar_manifiesto,
    leer_manifiesto,
)


class ManifiestoBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.directorio = Path(self.temporal.name)
        self.payload = self.directorio / 'agenda.sqlite3'
        self.payload.write_bytes(b'base ficticia para respaldo')

    def tearDown(self):
        self.temporal.cleanup()

    def _crear(self):
        return crear_manifiesto(
            self.payload, backend='sqlite', schema_version=ESQUEMAS_SOPORTADOS['sqlite'],
            table_counts={tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['sqlite']},
            created_at=datetime(2026, 11, 2, 12, 30, tzinfo=timezone.utc),
        )

    def test_schema_vigente_conserva_tabla_clinica_c15(self):
        self.assertIn('evoluciones_clinicas', TABLAS_ESQUEMA_ACTUAL['sqlite'])
        self.assertIn('evoluciones_clinicas', TABLAS_ESQUEMA_ACTUAL['postgresql'])

    def test_schema_c16_conserva_tablas_clinicas_en_schema_vigente(self):
        tablas_c16 = {
            'versiones_odontograma', 'hallazgos_odontograma',
            'planes_tratamiento', 'etapas_plan_tratamiento',
        }
        self.assertTrue(tablas_c16 <= TABLAS_ESQUEMA_ACTUAL['sqlite'])
        self.assertTrue(tablas_c16 <= TABLAS_ESQUEMA_ACTUAL['postgresql'])

    def test_schema_c17_incluye_outbox_en_schema_actual(self):
        self.assertEqual(ESQUEMAS_SOPORTADOS['sqlite'], '13')
        self.assertEqual(
            ESQUEMAS_SOPORTADOS['postgresql'],
            '20261102_0014_financial_ledger')
        self.assertIn('recordatorios_outbox', TABLAS_ESQUEMA_ACTUAL['sqlite'])
        self.assertIn('recordatorios_outbox', TABLAS_ESQUEMA_ACTUAL['postgresql'])

    def test_schema_c18_incluye_idempotencia_portal_y_nueva_revision(self):
        self.assertEqual(ESQUEMAS_SOPORTADOS['sqlite'], '13')
        self.assertEqual(
            ESQUEMAS_SOPORTADOS['postgresql'],
            '20261102_0014_financial_ledger')
        self.assertIn('idempotencia_portal_paciente', TABLAS_ESQUEMA_ACTUAL['sqlite'])
        self.assertIn('idempotencia_portal_paciente', TABLAS_ESQUEMA_ACTUAL['postgresql'])

    def test_manifiesto_registra_utc_versiones_y_hash_del_payload(self):
        manifiesto = self._crear()
        self.assertEqual(manifiesto['format_version'], 1)
        self.assertEqual(manifiesto['created_at_utc'], '2026-11-02T12:30:00+00:00')
        self.assertEqual(manifiesto['backend'], 'sqlite')
        self.assertEqual(manifiesto['application_version'], '0.1.0')
        self.assertEqual(manifiesto['schema_version'], ESQUEMAS_SOPORTADOS['sqlite'])
        self.assertEqual(manifiesto['table_counts'], {
            tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['sqlite']})
        self.assertEqual(manifiesto['payload_name'], 'agenda.sqlite3')
        self.assertEqual(manifiesto['payload_size_bytes'], self.payload.stat().st_size)
        self.assertEqual(len(manifiesto['payload_sha256']), 64)
        ruta = self.directorio / 'manifest.json'
        guardar_manifiesto(manifiesto, ruta)
        self.assertEqual(leer_manifiesto(ruta, self.payload), manifiesto)

    def test_rechaza_campos_ausentes_extra_y_version_o_esquema_no_admitidos(self):
        manifiesto = self._crear()
        with self.assertRaises(ErrorManifiesto):
            crear_manifiesto(self.payload, backend='sqlite', schema_version='7')
        for alterado in (
            {k: v for k, v in manifiesto.items() if k != 'schema_version'},
            {**manifiesto, 'dato_extra': 'no permitido'},
            {**manifiesto, 'format_version': 9},
        ):
            with self.subTest(alterado=alterado):
                ruta = self._guardar(alterado)
                with self.assertRaises(ErrorManifiesto):
                    leer_manifiesto(ruta, self.payload)

    def test_rechaza_fecha_sin_zona_y_hash_o_tamano_alterados(self):
        manifiesto = self._crear()
        alteraciones = (
            {**manifiesto, 'created_at_utc': '2026-11-02T12:30:00'},
            {**manifiesto, 'payload_sha256': '0' * 64},
            {**manifiesto, 'payload_size_bytes': manifiesto['payload_size_bytes'] + 1},
        )
        for alterado in alteraciones:
            with self.subTest(alterado=alterado):
                ruta = self._guardar(alterado)
                with self.assertRaises(ErrorManifiesto):
                    leer_manifiesto(ruta, self.payload)

    def test_rechaza_recuentos_ausentes_invalidos_o_tablas_ajenas(self):
        manifiesto = self._crear()
        for recuentos in (
                None,
                {**manifiesto['table_counts'], 'pacientes': True},
                {**manifiesto['table_counts'], 'pacientes': -1},
                {**manifiesto['table_counts'], 'tabla_ajena': 0},
        ):
            with self.subTest(recuentos=recuentos):
                alterado = {**manifiesto, 'table_counts': recuentos}
                with self.assertRaises(ErrorManifiesto):
                    leer_manifiesto(self._guardar(alterado), self.payload)
        del manifiesto['table_counts']
        ruta = self._guardar(manifiesto)
        with self.assertRaises(ErrorManifiesto):
            leer_manifiesto(ruta, self.payload)

    def test_normaliza_fecha_con_offset_y_no_sobrescribe_manifiesto(self):
        manifiesto = crear_manifiesto(
            self.payload, backend='sqlite', schema_version=ESQUEMAS_SOPORTADOS['sqlite'],
            table_counts={tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['sqlite']},
            created_at=datetime.fromisoformat('2026-11-02T09:30:00-03:00'),
        )
        self.assertEqual(manifiesto['created_at_utc'], '2026-11-02T12:30:00+00:00')
        ruta = self.directorio / 'manifest.json'
        guardar_manifiesto(manifiesto, ruta)
        original = ruta.read_bytes()
        with self.assertRaises(ErrorManifiesto):
            guardar_manifiesto(manifiesto, ruta)
        self.assertEqual(ruta.read_bytes(), original)

    def _guardar(self, manifiesto):
        ruta = self.directorio / 'manifest.json'
        ruta.write_text(json.dumps(manifiesto), encoding='utf-8')
        return ruta


if __name__ == '__main__':
    unittest.main()
