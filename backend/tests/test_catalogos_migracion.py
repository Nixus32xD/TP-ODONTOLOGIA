from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path
import importlib.util
import sqlite3
from tempfile import TemporaryDirectory
import unittest

import odontologia.db.models as models
from odontologia import crear_turno, inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite


class MigracionCatalogosTests(unittest.TestCase):
    def test_sqlite_v4_agrega_catalogos_y_conserva_ids_y_turnos(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            crear_turno(
                ruta, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc))

            migrar_sqlite(ruta)

            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(
                    conexion.execute('SELECT version FROM auth_schema_version').fetchone(), (11,))
                self.assertEqual(conexion.execute(
                    'SELECT id, nombre, activo FROM profesionales ORDER BY id').fetchall(), [
                        ('profesional-A', 'Profesional de demostración profesional-A', 1),
                        ('profesional-B', 'Profesional de demostración profesional-B', 1),
                    ])
                self.assertEqual(conexion.execute(
                    'SELECT id, nombre, activo FROM boxes ORDER BY id').fetchall(), [
                        ('box-A', 'Box de demostración box-A', 1),
                        ('box-B', 'Box de demostración box-B', 1),
                    ])
                self.assertEqual(conexion.execute(
                    'SELECT profesional_id, box_id FROM turnos').fetchall(),
                    [('profesional-A', 'box-A')])
                self.assertEqual(conexion.execute(
                    'SELECT COUNT(*) FROM prestaciones').fetchone(), (0,))

    def test_modelo_y_alembic_agregan_prestacion_sin_tocar_turno(self):
        self.assertIn('prestaciones', models.Base.metadata.tables)
        self.assertTrue({'id', 'nombre', 'duracion_minutos', 'activo'} <= set(
            models.Prestacion.__table__.columns.keys()))
        self.assertTrue({'nombre', 'activo'} <= set(models.Profesional.__table__.columns.keys()))
        self.assertTrue({'nombre', 'activo'} <= set(models.Box.__table__.columns.keys()))
        self.assertNotIn('prestacion_id', models.Turno.__table__.columns)

        ruta = Path(__file__).parents[1] / 'alembic' / 'versions' / '20261102_0005_resource_catalogs.py'
        spec = importlib.util.spec_from_file_location('revision_resource_catalogs', ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        self.assertEqual(modulo.revision, '20261102_0005_resource_catalogs')
        self.assertEqual(modulo.down_revision, '20261102_0004_patient_management')


if __name__ == '__main__':
    unittest.main()
