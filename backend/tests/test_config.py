from unittest import TestCase
from unittest.mock import patch

from odontologia.core.config import cargar_configuracion


class ConfiguracionTests(TestCase):
    def test_sqlite_sigue_como_default_y_conserva_ruta(self):
        with patch.dict('os.environ', {}, clear=True):
            config = cargar_configuracion()

        self.assertEqual(config.persistencia, 'sqlite')
        self.assertEqual(config.odontologia_db, 'agenda.sqlite3')
        self.assertIsNone(config.database_url)

    def test_postgresql_exige_seleccion_y_url(self):
        with patch.dict('os.environ', {
                'ODONTOLOGIA_PERSISTENCIA': 'postgresql',
                'DATABASE_URL': 'postgresql+psycopg://usuario:clave@localhost/agenda'}, clear=True):
            config = cargar_configuracion()

        self.assertEqual(config.persistencia, 'postgresql')
        self.assertEqual(config.database_url, 'postgresql+psycopg://usuario:clave@localhost/agenda')

    def test_postgresql_sin_url_falla_cerrado(self):
        with patch.dict('os.environ', {'ODONTOLOGIA_PERSISTENCIA': 'postgresql'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'DATABASE_URL'):
                cargar_configuracion()

    def test_backend_desconocido_se_rechaza(self):
        with patch.dict('os.environ', {'ODONTOLOGIA_PERSISTENCIA': 'mysql'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'ODONTOLOGIA_PERSISTENCIA'):
                cargar_configuracion()


if __name__ == '__main__':
    import unittest
    unittest.main()
