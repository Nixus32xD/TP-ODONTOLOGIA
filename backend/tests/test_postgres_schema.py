import unittest

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from odontologia.db.models import AgendaMutex, Base, Turno


class EsquemaPostgreSQLTests(unittest.TestCase):
    def test_esquema_representa_catalogos_turnos_y_mutex(self):
        self.assertEqual(
            set(Base.metadata.tables),
            {'pacientes', 'profesionales', 'boxes', 'turnos', 'agenda_mutex', 'usuarios', 'sesiones'},
        )
        self.assertEqual(
            set(Turno.__table__.columns.keys()),
            {'id', 'paciente_id', 'profesional_id', 'box_id', 'inicio_minuto', 'fin_minuto'},
        )
        self.assertIn('inicio_minuto < fin_minuto', {
            str(constraint.sqltext) for constraint in Turno.__table__.constraints
            if getattr(constraint, 'sqltext', None) is not None
        })
        self.assertIsNotNone(Turno.__table__.c.id.identity)
        self.assertEqual(AgendaMutex.__table__.primary_key.columns.keys(), ['id'])

    def test_lock_de_agenda_se_compila_como_bloqueo_de_fila_postgres(self):
        statement = select(AgendaMutex.id).with_for_update()

        sql = str(statement.compile(dialect=postgresql.dialect()))

        self.assertIn('FOR UPDATE', sql)
        self.assertIn('agenda_mutex', sql)


if __name__ == '__main__':
    unittest.main()
