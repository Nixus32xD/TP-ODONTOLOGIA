import unittest

from odontologia.auth.limitador_login import LimitadorIntentosLogin


class RelojFalso:
    def __init__(self, valor=100.0):
        self.valor = valor

    def __call__(self):
        return self.valor


class LimitadorIntentosLoginTests(unittest.TestCase):
    def setUp(self):
        self.reloj = RelojFalso()
        self.limitador = LimitadorIntentosLogin(reloj=self.reloj)

    def test_quinto_fallo_limita_el_siguiente_y_retry_after_es_positivo(self):
        for _ in range(5):
            self.limitador.registrar_fallo('192.0.2.1', 'admin.one')
        restante = self.limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one')
        self.assertGreater(restante, 0)
        self.assertIsNone(self.limitador.segundos_hasta_reintento('192.0.2.1', 'otro.admin'))

    def test_ventana_movil_expira_el_fallo_mas_antiguo_y_no_bloquea_permanentemente(self):
        for _ in range(5):
            self.limitador.registrar_fallo('192.0.2.1', 'admin.one')
        self.reloj.valor += 300
        self.assertIsNone(self.limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one'))

    def test_login_correcto_limpia_contador(self):
        for _ in range(5):
            self.limitador.registrar_fallo('192.0.2.1', 'admin.one')
        self.limitador.limpiar('192.0.2.1', 'admin.one')
        self.assertIsNone(self.limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one'))
        self.limitador.registrar_fallo('192.0.2.1', 'admin.one')
        self.assertIsNone(self.limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one'))

    def test_separa_por_origen_y_cuenta_normalizada(self):
        for _ in range(5):
            self.limitador.registrar_fallo('192.0.2.1', 'admin.one')
        self.assertIsNone(self.limitador.segundos_hasta_reintento('192.0.2.2', 'admin.one'))
        self.assertIsNone(self.limitador.segundos_hasta_reintento('192.0.2.1', 'recepcion.a'))

    def test_buckets_expirados_se_eliminan_y_capacidad_es_limitada(self):
        limitador = LimitadorIntentosLogin(reloj=self.reloj, max_claves=2)
        limitador.registrar_fallo('192.0.2.1', 'admin.one')
        limitador.registrar_fallo('192.0.2.2', 'admin.one')
        limitador.registrar_fallo('192.0.2.3', 'admin.one')
        self.assertLessEqual(len(limitador._intentos), 2)
        self.assertIsNone(limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one'))

    def test_reserva_de_base_error_se_libera_y_login_exitoso_limpia_fallos(self):
        token, retry_after = self.limitador.reservar_intento('192.0.2.1', 'admin.one')
        self.assertIsNotNone(token)
        self.assertIsNone(retry_after)
        self.limitador.finalizar_intento(
            '192.0.2.1', 'admin.one', token, credenciales_validas=None)
        self.assertEqual(len(self.limitador._reservas), 0)
        self.assertIsNone(
            self.limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one'))

        for _ in range(4):
            self.limitador.registrar_fallo('192.0.2.1', 'admin.one')
        token, retry_after = self.limitador.reservar_intento('192.0.2.1', 'admin.one')
        self.assertIsNotNone(token)
        self.assertIsNone(retry_after)
        self.limitador.finalizar_intento(
            '192.0.2.1', 'admin.one', token, credenciales_validas=True)
        self.assertEqual(len(self.limitador._reservas), 0)
        self.assertIsNone(
            self.limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one'))

    def test_reservas_concurrentes_se_limitan_atomico_a_cinco(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        barrera = Barrier(6)

        def reservar(_indice):
            barrera.wait(timeout=3)
            return self.limitador.reservar_intento('192.0.2.1', 'admin.one')

        with ThreadPoolExecutor(max_workers=6) as ejecutor:
            resultados = list(ejecutor.map(reservar, range(6)))
        admitidos = [token for token, retry_after in resultados if token is not None]
        rechazados = [retry_after for token, retry_after in resultados if token is None]
        self.assertEqual(len(admitidos), 5)
        self.assertEqual(len(rechazados), 1)
        self.assertGreater(rechazados[0], 0)
        for token in admitidos:
            self.limitador.finalizar_intento(
                '192.0.2.1', 'admin.one', token, credenciales_validas=None)
        self.assertEqual(len(self.limitador._reservas), 0)

    def test_exito_limpia_fallos_previos_y_conserva_otro_intento_en_curso(self):
        for _ in range(3):
            self.limitador.registrar_fallo('192.0.2.1', 'admin.one')
        exito, _ = self.limitador.reservar_intento('192.0.2.1', 'admin.one')
        pendiente, _ = self.limitador.reservar_intento('192.0.2.1', 'admin.one')

        self.limitador.finalizar_intento(
            '192.0.2.1', 'admin.one', exito, credenciales_validas=True)
        self.assertIsNone(
            self.limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one'))
        self.limitador.finalizar_intento(
            '192.0.2.1', 'admin.one', pendiente, credenciales_validas=False)
        for _ in range(4):
            self.limitador.registrar_fallo('192.0.2.1', 'admin.one')
        self.assertGreater(
            self.limitador.segundos_hasta_reintento('192.0.2.1', 'admin.one'), 0)
        self.assertEqual(len(self.limitador._reservas), 0)


if __name__ == '__main__':
    unittest.main()
