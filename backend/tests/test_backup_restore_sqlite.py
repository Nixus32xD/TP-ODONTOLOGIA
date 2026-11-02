from contextlib import closing
from datetime import datetime
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4
from unittest.mock import patch

from odontologia import crear_turno, inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.backup.bundle import crear_bundle_sqlite
from odontologia.backup.errors import ErrorBackup
from odontologia.backup.restauracion_sqlite import restaurar_bundle_sqlite
from odontologia.backup.manifest import leer_manifiesto


class RestauracionSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.root = Path(self.temporal.name)
        self.origen = self.root / 'origen.sqlite3'
        self.bundle = self.root / 'bundle'
        inicializar_agenda(self.origen)
        self.turno = crear_turno(
            self.origen, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))
        migrar_sqlite(self.origen)
        self.paciente_id = str(uuid4())
        with closing(sqlite3.connect(self.origen)) as conexion:
            conexion.execute(
                "INSERT INTO pacientes(id, nombre, telefono, activo) VALUES (?, ?, NULL, 1)",
                (self.paciente_id, 'Paciente ficticio'),
            )
            conexion.execute("UPDATE turnos SET estado='atendido' WHERE id=?", (self.turno.id,))
            conexion.execute('''INSERT INTO evoluciones_clinicas
                (id, paciente_id, profesional_id, turno_id, nota, created_at, corrige_a_id)
                VALUES (?, ?, ?, ?, ?, ?, NULL)''',
                ('evolucion-demo', 'paciente-A', 'profesional-A', self.turno.id,
                 'Nota clínica ficticia de respaldo.', '2026-11-02T12:00:00+00:00'))
            conexion.execute('''INSERT INTO eventos_auditoria
                (created_at, actor_id, action, resource_type, resource_id, result)
                VALUES (?, NULL, 'evolucion.creada', 'evolucion', ?, 'confirmado')''',
                ('2026-11-02T12:00:00+00:00', 'evolucion-demo'))
            conexion.execute('''INSERT INTO versiones_odontograma
                (id, paciente_id, profesional_id, version, created_at)
                VALUES ('version-demo', 'paciente-A', 'profesional-A', 1,
                        '2026-11-02T12:00:00+00:00')''')
            conexion.execute('''INSERT INTO hallazgos_odontograma
                (id, version_id, pieza_fdi, superficie_fdi, observacion)
                VALUES ('hallazgo-demo', 'version-demo', '16', 'O',
                        'Hallazgo odontológico sintético.')''')
            conexion.execute('''INSERT INTO prestaciones
                (id, nombre, duracion_minutos, activo)
                VALUES ('prestacion-demo', 'Prestación sintética', 30, 1)''')
            conexion.execute('''INSERT INTO planes_tratamiento
                (id, paciente_id, profesional_id, estado, created_at)
                VALUES ('plan-demo', 'paciente-A', 'profesional-A', 'propuesto',
                        '2026-11-02T12:00:00+00:00')''')
            conexion.execute('''INSERT INTO etapas_plan_tratamiento
                (id, plan_id, prestacion_id, orden)
                VALUES ('etapa-demo', 'plan-demo', 'prestacion-demo', 1)''')
            conexion.commit()
        crear_bundle_sqlite(self.origen, self.bundle)

    def tearDown(self):
        self.temporal.cleanup()

    def test_rechaza_destino_existente_y_preserva_bytes(self):
        destino = self.root / 'existente.sqlite3'
        destino.write_bytes(b'no reemplazar')
        with self.assertRaises(ErrorBackup) as contexto:
            restaurar_bundle_sqlite(self.bundle, destino)
        self.assertEqual(contexto.exception.codigo, 'destino_existente')
        self.assertEqual(destino.read_bytes(), b'no reemplazar')

    def test_rechaza_alias_normalizado_de_agenda_activa_sin_mutarla(self):
        antes = self.origen.read_bytes()
        alias = self.origen.parent / '..' / self.origen.parent.name / self.origen.name
        with self.assertRaises(ErrorBackup) as contexto:
            restaurar_bundle_sqlite(self.bundle, alias, origen_activo=self.origen)
        self.assertEqual(contexto.exception.codigo, 'agenda_activa')
        self.assertEqual(self.origen.read_bytes(), antes)

    def test_rechaza_ruta_invalida_y_bundle_incompatible_sin_crear_destino(self):
        ruta_invalida = self.root / 'padre-ausente' / 'restore.sqlite3'
        with self.assertRaises(ErrorBackup):
            restaurar_bundle_sqlite(self.bundle, ruta_invalida)
        self.assertFalse(ruta_invalida.parent.exists())

        payload = self.bundle / 'agenda.sqlite3'
        with closing(sqlite3.connect(payload)) as conexion:
            conexion.execute('UPDATE auth_schema_version SET version=7')
            conexion.commit()
        destino = self.root / 'incompatible.sqlite3'
        with self.assertRaises(ErrorBackup):
            restaurar_bundle_sqlite(self.bundle, destino)
        self.assertFalse(destino.exists())

    def test_rechaza_symlink_a_la_agenda_activa_sin_seguirlo(self):
        destino = self.root / 'enlace.sqlite3'
        try:
            os.symlink(self.origen, destino)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f'El host no permite crear symlinks de prueba: {exc}')
        antes = self.origen.read_bytes()
        with self.assertRaises(ErrorBackup):
            restaurar_bundle_sqlite(self.bundle, destino, origen_activo=self.origen)
        self.assertTrue(destino.is_symlink())
        self.assertEqual(self.origen.read_bytes(), antes)

    def test_fallo_de_snapshot_limpia_solo_staging_y_no_publica(self):
        destino = self.root / 'restore-fallida.sqlite3'
        bundle_antes = (self.bundle / 'agenda.sqlite3').read_bytes()
        with patch('odontologia.backup.restauracion_sqlite.crear_snapshot_sqlite',
                   side_effect=ErrorBackup('operacion_fallida')):
            with self.assertRaises(ErrorBackup):
                restaurar_bundle_sqlite(self.bundle, destino)
        self.assertFalse(destino.exists())
        self.assertEqual((self.bundle / 'agenda.sqlite3').read_bytes(), bundle_antes)
        self.assertFalse(list(self.root.glob('.tmp-restore-*')))

    def test_error_tras_link_atomico_quita_solo_el_destino_propio(self):
        destino = self.root / 'restore-validacion-fallida.sqlite3'
        with patch('odontologia.backup.restauracion_sqlite._validar_sqlite',
                   side_effect=[None, ErrorBackup('integridad_invalida')]):
            with self.assertRaises(ErrorBackup):
                restaurar_bundle_sqlite(self.bundle, destino)
        self.assertFalse(destino.exists())
        self.assertFalse(list(self.root.glob('.tmp-restore-*')))

    def test_restaura_bundle_ficticio_y_permite_escritura_en_nueva_conexion(self):
        destino = self.root / 'restore-valid.sqlite3'
        origen_antes = self.origen.read_bytes()
        bundle_antes = (self.bundle / 'agenda.sqlite3').read_bytes()
        resultado = restaurar_bundle_sqlite(
            self.bundle, destino, origen_activo=self.origen)
        self.assertTrue(resultado['restored'])
        self.assertEqual(resultado['schema_version'], '10')
        manifiesto = leer_manifiesto(self.bundle / 'manifest.json')
        self.assertEqual(manifiesto['table_counts']['evoluciones_clinicas'], 1)
        self.assertEqual({tabla: manifiesto['table_counts'][tabla] for tabla in (
            'versiones_odontograma', 'hallazgos_odontograma',
            'planes_tratamiento', 'etapas_plan_tratamiento')}, {
                'versiones_odontograma': 1, 'hallazgos_odontograma': 1,
                'planes_tratamiento': 1, 'etapas_plan_tratamiento': 1})
        self.assertNotIn('Nota clínica ficticia de respaldo.', str(manifiesto))
        self.assertNotIn('Hallazgo odontológico sintético.', str(manifiesto))

        with closing(sqlite3.connect(destino)) as conexion:
            self.assertEqual(
                conexion.execute('SELECT nombre FROM pacientes WHERE id=?',
                                 (self.paciente_id,)).fetchone(),
                ('Paciente ficticio',),
            )
            self.assertEqual(conexion.execute(
                'SELECT paciente_id, profesional_id, turno_id, nota, corrige_a_id '
                'FROM evoluciones_clinicas WHERE id=?', ('evolucion-demo',)).fetchone(),
                ('paciente-A', 'profesional-A', self.turno.id,
                 'Nota clínica ficticia de respaldo.', None))
            self.assertEqual(conexion.execute(
                'SELECT paciente_id, profesional_id, version FROM versiones_odontograma '
                "WHERE id='version-demo'").fetchone(), ('paciente-A', 'profesional-A', 1))
            self.assertEqual(conexion.execute(
                "SELECT pieza_fdi, superficie_fdi, observacion FROM hallazgos_odontograma "
                "WHERE id='hallazgo-demo'").fetchone(),
                ('16', 'O', 'Hallazgo odontológico sintético.'))
            self.assertEqual(conexion.execute(
                "SELECT estado FROM planes_tratamiento WHERE id='plan-demo'"
            ).fetchone(), ('propuesto',))
            self.assertEqual(conexion.execute(
                "SELECT prestacion_id, orden FROM etapas_plan_tratamiento WHERE id='etapa-demo'"
            ).fetchone(), ('prestacion-demo', 1))
            conexion.execute(
                "INSERT INTO pacientes(id, nombre, telefono, activo) VALUES (?, ?, NULL, 1)",
                ('paciente-alta-despues-de-restaurar', 'Alta ficticia posterior'),
            )
            conexion.commit()
        with closing(sqlite3.connect(destino)) as conexion:
            self.assertEqual(conexion.execute(
                "SELECT count(*) FROM pacientes WHERE id='paciente-alta-despues-de-restaurar'"
            ).fetchone(), (1,))
        self.assertEqual(self.origen.read_bytes(), origen_antes)
        self.assertEqual((self.bundle / 'agenda.sqlite3').read_bytes(), bundle_antes)


if __name__ == '__main__':
    unittest.main()
