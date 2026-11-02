from contextlib import redirect_stderr
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.engine import Engine

from odontologia.db.migrar_sqlite import main


class MigrarSQLiteCliTests(unittest.TestCase):
    def test_exige_backend_postgresql_y_url_sin_conectar(self):
        error = io.StringIO()
        with patch.dict(os.environ, {'ODONTOLOGIA_PERSISTENCIA': 'sqlite'}, clear=True):
            with redirect_stderr(error), patch.object(
                    Engine, 'connect', side_effect=AssertionError('No debe conectar')):
                resultado = main()

        self.assertEqual(resultado, 2)
        self.assertIn('Error de migración', error.getvalue())

    def test_fuente_ausente_falla_antes_de_abrir_postgresql(self):
        with tempfile.TemporaryDirectory() as temporal:
            error = io.StringIO()
            entorno = {
                'ODONTOLOGIA_PERSISTENCIA': 'postgresql',
                'DATABASE_URL': 'postgresql+psycopg://user:secret@127.0.0.1:55432/odontologia_test',
                'ODONTOLOGIA_DB': str(Path(temporal) / 'no-existe.sqlite3'),
            }
            with patch.dict(os.environ, entorno, clear=True):
                with redirect_stderr(error), patch.object(
                        Engine, 'connect', side_effect=AssertionError('No debe conectar')):
                    resultado = main()

        self.assertEqual(resultado, 2)
        self.assertIn('Error de migración', error.getvalue())


if __name__ == '__main__':
    unittest.main()
