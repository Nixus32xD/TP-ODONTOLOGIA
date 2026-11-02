import os
import unittest
from unittest.mock import patch

from odontologia.core.config import cargar_configuracion
from odontologia.auth.tokens import validar_secreto_jwt


class ConfiguracionJWTTests(unittest.TestCase):
    def test_configuracion_expone_secreto_sin_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(cargar_configuracion().jwt_secreto)
        with patch.dict(os.environ, {'JWT_SECRETO': 's' * 48}, clear=True):
            self.assertEqual(cargar_configuracion().jwt_secreto, 's' * 48)

    def test_secreto_requiere_longitud_y_no_acepta_marcador(self):
        validar_secreto_jwt('x' * 48)
        for secreto in (None, '', 'x' * 31, 'CAMBIAR_POR_UN_VALOR_LOCAL_LARGO_123456'):
            with self.subTest(secreto=secreto), self.assertRaises(ValueError):
                validar_secreto_jwt(secreto)

    def test_algoritmo_se_limita_a_hs256(self):
        validar_secreto_jwt('k' * 48, 'HS256')
        with self.assertRaises(ValueError):
            validar_secreto_jwt('k' * 48, 'none')
