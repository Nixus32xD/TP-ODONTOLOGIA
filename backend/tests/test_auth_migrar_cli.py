from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.migrar_sqlite import main


class MigrarAutenticacionCliTests(unittest.TestCase):
    def test_migra_sqlite_existente_sin_argumentos(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            salida = StringIO()
            with patch.dict(os.environ, {
                    'ODONTOLOGIA_PERSISTENCIA': 'sqlite', 'ODONTOLOGIA_DB': str(ruta)}, clear=True):
                with patch('sys.argv', ['migrar_sqlite.py']):
                    with redirect_stdout(salida):
                        resultado = main()
            self.assertEqual(resultado, 0)
            self.assertIn('Migración de autenticación aplicada.', salida.getvalue())

    def test_rechaza_argumentos_y_postgresql_sin_aplicar_cambios(self):
        salida = StringIO()
        with patch('sys.argv', ['migrar_sqlite.py', '--password=secreto']):
            with redirect_stdout(salida):
                self.assertEqual(main(), 2)
        self.assertNotIn('secreto', salida.getvalue())

        with patch.dict(os.environ, {'ODONTOLOGIA_PERSISTENCIA': 'postgresql'}, clear=True):
            with patch('sys.argv', ['migrar_sqlite.py']):
                with redirect_stdout(salida):
                    self.assertEqual(main(), 1)


if __name__ == '__main__':
    unittest.main()
