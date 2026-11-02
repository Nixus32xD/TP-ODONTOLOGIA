import unittest

from odontologia.finanzas import (
    centavos_a_importe_ars,
    importe_ars_a_centavos,
    importe_reversible_centavos,
    saldo_centavos,
)


class FinanzasTests(unittest.TestCase):
    def test_parsea_y_formatea_importes_ars_sin_perder_centavos(self):
        casos = {
            '0.01': (1, '0.01'),
            '1': (100, '1.00'),
            '1.2': (120, '1.20'),
            '12345.67': (1_234_567, '12345.67'),
            '999999999.99': (99_999_999_999, '999999999.99'),
        }

        for texto, (centavos, canonico) in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(importe_ars_a_centavos(texto), centavos)
                self.assertEqual(centavos_a_importe_ars(centavos), canonico)

    def test_rechaza_importes_no_positivos_malformados_y_mayores_al_limite(self):
        invalidos = (
            '0', '0.00', '-1.00', '+1.00', '1,00', '1.001', '1e2',
            ' 1.00', '1.00 ', '1,000.00', '1000000000.00',
            '00.01', '999999999.991',
            '9' * 1000, 1.25, None,
        )
        for importe in invalidos:
            with self.subTest(importe=importe):
                with self.assertRaises(ValueError):
                    importe_ars_a_centavos(importe)

    def test_calcula_saldo_exactamente_con_movimientos_acumulados(self):
        self.assertEqual(
            saldo_centavos(cargos=[10_000, 50], cobros=[7_000, 100], reversiones=[500]),
            3_450,
        )

    def test_calcula_monto_reversible_y_rechaza_reversiones_acumuladas_excesivas(self):
        self.assertEqual(importe_reversible_centavos(10_000, [2_500, 3_000]), 4_500)
        with self.assertRaises(ValueError):
            importe_reversible_centavos(10_000, [2_500, 7_501])

    def test_rechaza_saldo_negativo_y_centavos_no_enteros(self):
        with self.assertRaises(ValueError):
            saldo_centavos(cargos=[100], cobros=[101], reversiones=[])
        for centavos in (1.0, True, -1):
            with self.subTest(centavos=centavos), self.assertRaises(ValueError):
                centavos_a_importe_ars(centavos)
        with self.assertRaises(ValueError):
            saldo_centavos(cargos=[1.5], cobros=[], reversiones=[])

    def test_el_saldo_agregado_puede_superar_el_limite_de_una_operacion(self):
        saldo = saldo_centavos(cargos=[99_999_999_999, 99_999_999_999],
                               cobros=[], reversiones=[])
        self.assertEqual(centavos_a_importe_ars(saldo), '1999999999.98')

    def test_formatea_saldo_agregado_mayor_al_rango_de_entero_con_signo(self):
        self.assertEqual(
            centavos_a_importe_ars(9_223_372_036_854_775_808),
            '92233720368547758.08',
        )


if __name__ == '__main__':
    unittest.main()
