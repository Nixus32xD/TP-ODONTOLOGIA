import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.bootstrap_admin import main
from odontologia.auth.migraciones import migrar_sqlite


class BootstrapAdminCliTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.entorno = patch.dict(os.environ, {
            'ODONTOLOGIA_PERSISTENCIA': 'sqlite',
            'ODONTOLOGIA_DB': str(self.ruta),
            'JWT_SECRETO': 'k' * 48,
            'JWT_ALGORITMO': 'HS256',
        }, clear=True)
        self.entorno.start()
        self.addCleanup(self.entorno.stop)

    def test_crea_administrador_con_entrada_oculta_y_sin_secreto_en_salida(self):
        salida = io.StringIO()
        with patch('sys.argv', ['bootstrap_admin']), patch('builtins.input', return_value='Admin.One'), \
                patch('getpass.getpass', side_effect=['frase-larga-segura-2026'] * 2), \
                patch('sys.stdout', salida):
            codigo = main()
        self.assertEqual(codigo, 0)
        self.assertIn('Administrador creado', salida.getvalue())
        self.assertNotIn('frase-larga-segura-2026', salida.getvalue())

    def test_argumentos_son_rechazados_sin_imprimirlos(self):
        secreto = 'frase-larga-segura-2026'
        salida = io.StringIO()
        with patch('sys.argv', ['bootstrap_admin', secreto]), patch('sys.stdout', salida):
            codigo = main()
        self.assertNotEqual(codigo, 0)
        self.assertNotIn(secreto, salida.getvalue())
