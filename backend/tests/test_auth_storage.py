from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from odontologia.auth.almacenamiento import crear_engine_autenticacion


class EngineAutenticacionTests(unittest.TestCase):
    def test_crear_engine_sqlite_no_crea_archivo_ni_conecta(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            engine = crear_engine_autenticacion('sqlite', None, ruta)
            try:
                self.assertFalse(ruta.exists())
                self.assertEqual(engine.dialect.name, 'sqlite')
                self.assertFalse(ruta.exists())
            finally:
                engine.dispose()

    def test_postgresql_exige_url_sin_abrir_conexion(self):
        engine = crear_engine_autenticacion(
            'postgresql', 'postgresql+psycopg://user:secret@127.0.0.1:55432/test_db', None)
        try:
            self.assertEqual(engine.dialect.name, 'postgresql')
        finally:
            engine.dispose()
