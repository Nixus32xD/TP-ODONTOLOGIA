from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from odontologia import crear_turno, inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.db.models import Base, EvolucionClinica


class EsquemaHistoriaClinicaTests(unittest.TestCase):
    def test_evolucion_es_separada_y_restringe_longitud_y_referencias(self):
        tabla = Base.metadata.tables['evoluciones_clinicas']

        self.assertEqual(
            set(tabla.columns.keys()),
            {'id', 'paciente_id', 'profesional_id', 'turno_id', 'nota', 'created_at', 'corrige_a_id'},
        )
        self.assertEqual(EvolucionClinica.__tablename__, 'evoluciones_clinicas')
        self.assertEqual(
            {str(clave.column) for clave in tabla.foreign_keys},
            {'pacientes.id', 'profesionales.id', 'turnos.id', 'evoluciones_clinicas.id'},
        )
        checks = {str(restriccion.sqltext) for restriccion in tabla.constraints
                  if getattr(restriccion, 'sqltext', None) is not None}
        self.assertTrue(any('5000' in condicion and 'nota' in condicion for condicion in checks))

    def test_nota_es_texto_requerido_y_los_vinculos_no_se_borran_en_cascada(self):
        tabla = EvolucionClinica.__table__

        self.assertEqual(tabla.c.nota.type.__class__.__name__, 'Text')
        self.assertFalse(tabla.c.nota.nullable)
        self.assertFalse(tabla.c.created_at.nullable)
        self.assertTrue(tabla.c.corrige_a_id.nullable)
        self.assertTrue(all(clave.ondelete == 'RESTRICT' for clave in tabla.foreign_keys))


class MigracionHistoriaClinicaSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        self.turno = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))

    def test_esquema_vigente_v9_crea_evoluciones_inmutables(self):
        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (9,))
            tablas = {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn('evoluciones_clinicas', tablas)
            conexion.execute(
                "UPDATE turnos SET estado='atendido' WHERE id=?", (self.turno.id,))
            conexion.execute('''INSERT INTO evoluciones_clinicas
                (id, paciente_id, profesional_id, turno_id, nota, created_at, corrige_a_id)
                VALUES (?, ?, ?, ?, ?, ?, NULL)''',
                ('evolucion-A', 'paciente-A', 'profesional-A', self.turno.id,
                 'Nota ficticia', '2026-11-02T12:00:00+00:00'))
            conexion.commit()
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute(
                    "UPDATE evoluciones_clinicas SET nota='Otra nota' WHERE id='evolucion-A'")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute("DELETE FROM evoluciones_clinicas WHERE id='evolucion-A'")

    def test_upgrade_desde_v8_conserva_turnos_y_eventos_previos(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute(
                "INSERT INTO eventos_auditoria(created_at, action, resource_type, result) "
                "VALUES ('2026-11-02T12:00:00+00:00', 'cuenta.bootstrap', 'cuenta', 'confirmado')")
            conexion.execute('DROP TABLE evoluciones_clinicas')
            conexion.execute('UPDATE auth_schema_version SET version=8')
            conexion.commit()

        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (9,))
            self.assertEqual(conexion.execute(
                'SELECT COUNT(*) FROM turnos WHERE id=?', (self.turno.id,)).fetchone(), (1,))
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM eventos_auditoria WHERE action='cuenta.bootstrap'"
            ).fetchone(), (1,))
            self.assertIsNotNone(conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='evoluciones_clinicas'").fetchone())


if __name__ == '__main__':
    unittest.main()
