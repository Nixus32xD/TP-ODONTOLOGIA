from pathlib import Path
import importlib.util
import unittest

from sqlalchemy import ForeignKeyConstraint

from odontologia.db.models import Base


class EsquemaAutenticacionTests(unittest.TestCase):
    def test_modelos_cuenta_y_sesion_contienen_campos_y_restricciones(self):
        self.assertIn('usuarios', Base.metadata.tables)
        self.assertIn('sesiones', Base.metadata.tables)
        usuario = Base.metadata.tables['usuarios']
        sesion = Base.metadata.tables['sesiones']

        self.assertTrue({'id', 'identificador', 'password_hash', 'rol', 'activo'} <= set(usuario.c.keys()))
        self.assertTrue(usuario.c.identificador.unique)
        self.assertTrue({'id', 'usuario_id', 'jti', 'expira_en', 'revocada_en'} <= set(sesion.c.keys()))
        self.assertTrue(any(isinstance(c, ForeignKeyConstraint) for c in sesion.constraints))

    def test_migracion_postgresql_encadena_sobre_c03(self):
        ruta = Path(__file__).parents[1] / 'alembic' / 'versions' / '20261101_0003_audit.py'
        spec = importlib.util.spec_from_file_location('revision_auth', ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        self.assertEqual(modulo.revision, '20261101_0003_audit')
        self.assertEqual(modulo.down_revision, '20261101_0002_auth')
        self.assertTrue(callable(modulo.upgrade))
        self.assertTrue(callable(modulo.downgrade))
