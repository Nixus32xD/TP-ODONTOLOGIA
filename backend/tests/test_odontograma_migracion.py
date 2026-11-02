from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from odontologia import crear_turno, inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite


class MigracionOdontogramaSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        self.turno = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))
        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('PRAGMA foreign_keys=OFF')
            tablas = {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            for tabla in (
                'etapas_plan_tratamiento', 'planes_tratamiento',
                'hallazgos_odontograma', 'versiones_odontograma',
            ):
                if tabla in tablas:
                    conexion.execute(f'DROP TABLE {tabla}')
            conexion.execute('UPDATE auth_schema_version SET version=9')
            conexion.commit()
            conexion.execute('PRAGMA foreign_keys=ON')

        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('''INSERT INTO prestaciones
                (id, nombre, duracion_minutos, activo)
                VALUES ('prestacion-A', 'Prestación sintética A', 30, 1)''')
            conexion.execute("UPDATE turnos SET estado='atendido' WHERE id=?", (self.turno.id,))
            conexion.execute('''INSERT INTO eventos_auditoria
                (created_at, action, resource_type, result)
                VALUES (?, 'cuenta.bootstrap', 'cuenta', 'confirmado')''',
                ('2026-11-02T12:00:00+00:00',))
            conexion.execute('''INSERT INTO evoluciones_clinicas
                (id, paciente_id, profesional_id, turno_id, nota, created_at, corrige_a_id)
                VALUES (?, ?, ?, ?, ?, ?, NULL)''',
                ('evolucion-previa', 'paciente-A', 'profesional-A', self.turno.id,
                 'Nota sintética previa a C-16', '2026-11-02T12:01:00+00:00'))
            conexion.commit()

    def test_upgrade_v9_crea_tablas_y_preserva_datos_c15(self):
        migrar_sqlite(self.ruta)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (12,))
            tablas = {fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({
                'versiones_odontograma', 'hallazgos_odontograma',
                'planes_tratamiento', 'etapas_plan_tratamiento',
            } <= tablas)
            self.assertEqual(conexion.execute(
                "SELECT nota FROM evoluciones_clinicas WHERE id='evolucion-previa'"
            ).fetchone(), ('Nota sintética previa a C-16',))
            self.assertEqual(conexion.execute(
                'SELECT COUNT(*) FROM eventos_auditoria WHERE action=?',
                ('cuenta.bootstrap',)).fetchone(), (1,))
            self.assertEqual(conexion.execute(
                'SELECT estado FROM turnos WHERE id=?', (self.turno.id,)).fetchone(), ('atendido',))

    def test_upgrade_es_repetible_y_bloquea_edicion_borrado_de_snapshots(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('''INSERT INTO versiones_odontograma
                (id, paciente_id, profesional_id, version, created_at)
                VALUES ('odonto-v1', 'paciente-A', 'profesional-A', 1, ?)''',
                ('2026-11-02T12:02:00+00:00',))
            conexion.execute('''INSERT INTO hallazgos_odontograma
                (id, version_id, pieza_fdi, superficie_fdi, observacion)
                VALUES ('hallazgo-v1', 'odonto-v1', '11', 'I', NULL)''')
            conexion.execute('''INSERT INTO planes_tratamiento
                (id, paciente_id, profesional_id, estado, created_at)
                VALUES ('plan-v1', 'paciente-A', 'profesional-A', 'propuesto', ?)''',
                ('2026-11-02T12:02:00+00:00',))
            conexion.execute('''INSERT INTO etapas_plan_tratamiento
                (id, plan_id, prestacion_id, orden)
                VALUES ('etapa-v1', 'plan-v1', 'prestacion-A', 1)''')
            conexion.commit()

        with closing(sqlite3.connect(self.ruta)) as conexion:
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute("UPDATE versiones_odontograma SET version=2 WHERE id='odonto-v1'")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute("DELETE FROM versiones_odontograma WHERE id='odonto-v1'")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute("UPDATE hallazgos_odontograma SET observacion='Editada' WHERE id='hallazgo-v1'")
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute("DELETE FROM etapas_plan_tratamiento WHERE id='etapa-v1'")

        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                'SELECT version FROM auth_schema_version').fetchone(), (12,))
            self.assertEqual(conexion.execute(
                'SELECT version FROM versiones_odontograma WHERE id=?', ('odonto-v1',)
            ).fetchone(), (1,))
            self.assertEqual(conexion.execute(
                'SELECT observacion FROM hallazgos_odontograma WHERE id=?', ('hallazgo-v1',)
            ).fetchone(), (None,))
            self.assertEqual(conexion.execute(
                'SELECT COUNT(*) FROM etapas_plan_tratamiento WHERE id=?', ('etapa-v1',)
            ).fetchone(), (1,))

    def test_auditoria_admite_eventos_clinicos_y_rechaza_combinaciones_invalidas(self):
        migrar_sqlite(self.ruta)
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('''INSERT INTO eventos_auditoria
                (created_at, action, resource_type, result)
                VALUES ('2026-11-02T12:00:00+00:00', 'plan.creado', 'plan', 'confirmado')''')
            with self.assertRaises(sqlite3.IntegrityError):
                conexion.execute('''INSERT INTO eventos_auditoria
                    (created_at, action, resource_type, result)
                    VALUES ('2026-11-02T12:00:01+00:00', 'plan.creado',
                            'odontograma', 'confirmado')''')


if __name__ == '__main__':
    unittest.main()
