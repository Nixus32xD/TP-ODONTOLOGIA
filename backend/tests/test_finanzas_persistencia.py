import unittest

from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from odontologia.db.models import CargoFinanciero, CobroFinanciero, ReversionCobro, IdempotenciaFinanciera


class ModelosFinancierosTests(unittest.TestCase):
    def test_ledger_y_claves_tienen_restricciones_de_integridad(self):
        self.assertEqual(CargoFinanciero.__tablename__, 'cargos_financieros')
        self.assertEqual(CobroFinanciero.__tablename__, 'cobros_financieros')
        self.assertEqual(ReversionCobro.__tablename__, 'reversiones_cobros')
        self.assertEqual(IdempotenciaFinanciera.__tablename__, 'idempotencia_financiera')
        self.assertTrue(any(isinstance(c, ForeignKeyConstraint) for c in CobroFinanciero.__table__.constraints))
        self.assertTrue(any(isinstance(c, CheckConstraint) for c in CargoFinanciero.__table__.constraints))
        self.assertIn('uq_idempotencia_financiera_actor_operacion_clave', {
            constraint.name for constraint in IdempotenciaFinanciera.__table__.constraints
        })


if __name__ == '__main__':
    unittest.main()
