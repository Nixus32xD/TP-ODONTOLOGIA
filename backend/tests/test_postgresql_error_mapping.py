from types import SimpleNamespace
import unittest

from odontologia.db.postgresql import codigo_error_postgresql, timeout_milisegundos


class ErrorPostgreSQLTests(unittest.TestCase):
    def test_lock_timeout_se_mapea_a_agenda_ocupada(self):
        exception = SimpleNamespace(orig=SimpleNamespace(sqlstate='55P03'))

        self.assertEqual(codigo_error_postgresql(exception), 'agenda_ocupada')

    def test_errores_de_conexion_o_esquema_no_filtran_detalles(self):
        for state in ('08006', '42P01', '57014', None):
            with self.subTest(state=state):
                exception = SimpleNamespace(orig=SimpleNamespace(sqlstate=state, diag=None))
                self.assertEqual(codigo_error_postgresql(exception), 'almacenamiento_error')

    def test_timeout_positivo_se_redondea_hacia_arriba_a_milisegundos(self):
        self.assertEqual(timeout_milisegundos(5.0), 5000)
        self.assertEqual(timeout_milisegundos(0.0001), 1)


if __name__ == '__main__':
    unittest.main()
