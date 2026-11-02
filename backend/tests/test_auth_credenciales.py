import unittest

from odontologia.auth.credenciales import (
    derivar_password,
    normalizar_identificador,
    validar_password,
    verificar_password,
)


class CredencialesTests(unittest.TestCase):
    def test_hash_usa_sales_unicas_y_verifica_sin_guardar_texto(self):
        password = 'frase-larga-segura-2026'
        hash_uno = derivar_password(password)
        hash_dos = derivar_password(password)

        self.assertNotEqual(hash_uno, hash_dos)
        self.assertNotIn(password, hash_uno)
        self.assertTrue(verificar_password(password, hash_uno))
        self.assertFalse(verificar_password('otra-frase', hash_uno))

    def test_identificador_se_normaliza_y_rechaza_formas_invalidas(self):
        self.assertEqual(normalizar_identificador('  Recepcion.A  '), 'recepcion.a')
        for invalido in ('ab', 'usuario con espacios', 'nombre@correo.test', 'a' * 65, ''):
            with self.subTest(invalido=invalido), self.assertRaises(ValueError):
                normalizar_identificador(invalido)

    def test_password_tiene_limites_y_hash_heredado_falla_cerrado(self):
        self.assertTrue(validar_password('frase-larga-segura'))
        for invalida in ('corta123', 'x' * 129, ''):
            with self.subTest(invalida=invalida), self.assertRaises(ValueError):
                validar_password(invalida)
        self.assertFalse(verificar_password('frase-larga-segura', 'sha256$sin-sal'))
