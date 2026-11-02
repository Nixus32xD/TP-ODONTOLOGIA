import unittest

from odontologia.odontograma import ErrorOdontograma, validar_hallazgos


class ValidacionOdontogramaTests(unittest.TestCase):
    def test_acepta_denticion_permanente_y_primaria_con_codigos_exactos(self):
        resultado = validar_hallazgos([
            {'pieza_fdi': '11', 'superficies': ['M', 'V'], 'observacion': 'control sintético'},
            {'pieza_fdi': '54', 'superficies': ['O'], 'observacion': None},
        ])

        self.assertEqual(resultado, [
            {'pieza_fdi': '11', 'superficie_fdi': 'M', 'observacion': 'control sintético'},
            {'pieza_fdi': '11', 'superficie_fdi': 'V', 'observacion': 'control sintético'},
            {'pieza_fdi': '54', 'superficie_fdi': 'O', 'observacion': None},
        ])

    def test_acepta_todas_las_superficies_individuales_admitidas(self):
        resultado = validar_hallazgos([
            {'pieza_fdi': '16', 'superficies': ['M', 'D', 'O', 'B', 'L'], 'observacion': None},
            {'pieza_fdi': '21', 'superficies': ['M', 'D', 'I', 'V', 'L'], 'observacion': None},
        ])
        self.assertEqual(len(resultado), 10)

    def test_acepta_snapshot_vacio_como_version_completa_sin_hallazgos(self):
        self.assertEqual(validar_hallazgos([]), [])

    def test_rechaza_piezas_fuera_de_denticiones_fdi(self):
        for pieza in ('00', '19', '49', '56', 'A1', '1', '111', ' 11'):
            with self.subTest(pieza=pieza), self.assertRaises(ErrorOdontograma):
                validar_hallazgos([{
                    'pieza_fdi': pieza, 'superficies': ['M'], 'observacion': None}])

    def test_rechaza_superficies_desconocidas_repetidas_o_incompatibles(self):
        for pieza, superficies in (
                ('11', ['Z']), ('11', ['M', 'M']), ('11', ['O']), ('16', ['I']),
                ('54', ['I']), ('54', ['B', 'B'])):
            with self.subTest(pieza=pieza, superficies=superficies), \
                    self.assertRaises(ErrorOdontograma):
                validar_hallazgos([{
                    'pieza_fdi': pieza, 'superficies': superficies, 'observacion': None}])

    def test_rechaza_observacion_larga_o_con_caracteres_de_control(self):
        for observacion in ('x' * 501, 'dato\x00sintético', 12):
            with self.subTest(observacion=type(observacion).__name__), \
                    self.assertRaises(ErrorOdontograma):
                validar_hallazgos([{
                    'pieza_fdi': '11', 'superficies': ['M'],
                    'observacion': observacion}])

    def test_rechaza_duplicados_y_estructuras_incompletas(self):
        duplicado = [
            {'pieza_fdi': '11', 'superficies': ['M'], 'observacion': None},
            {'pieza_fdi': '11', 'superficies': ['M'], 'observacion': 'otra'},
        ]
        for dato in (None, {}, duplicado, [
                {'pieza_fdi': '11', 'superficies': [], 'observacion': None}]) :
            with self.subTest(dato=type(dato).__name__), self.assertRaises(ErrorOdontograma):
                validar_hallazgos(dato)


if __name__ == '__main__':
    unittest.main()
