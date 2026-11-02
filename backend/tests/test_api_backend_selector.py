import os
import unittest
from unittest.mock import patch

from sqlalchemy.engine import Engine

from odontologia.api import crear_app


class SelectorBackendApiTests(unittest.TestCase):
    def test_sqlite_es_default_y_la_ruta_explicita_prevalece(self):
        with patch.dict(os.environ, {
                'ODONTOLOGIA_DB': 'agenda-c01.sqlite3',
                'ODONTOLOGIA_PERSISTENCIA': 'postgresql',
                'DATABASE_URL': 'postgresql+psycopg://user:secret@localhost/testdb'}, clear=True):
            app = crear_app('test.sqlite3')

        self.assertEqual(app.state.persistencia, 'sqlite')

    def test_postgresql_seleccionado_no_conecta_al_crear_app(self):
        with patch.dict(os.environ, {
                'ODONTOLOGIA_PERSISTENCIA': 'postgresql',
                'DATABASE_URL': 'postgresql+psycopg://user:secret@localhost/testdb'}, clear=True):
            with patch.object(Engine, 'connect', side_effect=AssertionError('No debe conectar')):
                app = crear_app()

        self.assertEqual(app.state.persistencia, 'postgresql')

    def test_configuracion_invalida_falla_antes_de_crear_la_app(self):
        with patch.dict(os.environ, {
                'ODONTOLOGIA_PERSISTENCIA': 'postgresql'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'DATABASE_URL'):
                crear_app()


if __name__ == '__main__':
    unittest.main()
