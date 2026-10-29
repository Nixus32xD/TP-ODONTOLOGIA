import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DemoTests(unittest.TestCase):
    def ejecutar(self, temporal):
        entorno = os.environ.copy()
        entorno.update(TMP=temporal, TEMP=temporal, TMPDIR=temporal)
        resultado = subprocess.run([sys.executable, '-m', 'odontologia.demo'],
                                   capture_output=True, text=True, timeout=20, env=entorno)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stderr, '')
        self.assertEqual(list(Path(temporal).iterdir()), [])
        return json.loads(resultado.stdout)

    def test_demo_ejercita_altas_conflictos_y_adyacencia(self):
        with tempfile.TemporaryDirectory() as temporal:
            salida = self.ejecutar(temporal)
        self.assertEqual([caso['resultado'] for caso in salida['casos']],
                         ['ok', 'conflicto_profesional', 'conflicto_box', 'ok'])
        self.assertEqual(salida['turnos_persistidos'], 2)
        self.assertTrue(salida['agenda_temporal_eliminada'])

    def test_demo_repetible_sin_reutilizar_datos(self):
        with tempfile.TemporaryDirectory(prefix='demo con espacios-') as temporal:
            primera = self.ejecutar(temporal)
            segunda = self.ejecutar(temporal)
        self.assertEqual(primera, segunda)
        self.assertEqual([caso['id'] for caso in segunda['casos'] if caso['resultado'] == 'ok'], [1, 2])


if __name__ == '__main__':
    unittest.main()
