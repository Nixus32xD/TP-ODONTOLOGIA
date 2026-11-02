import importlib.util
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import create_engine

from odontologia import crear_turno, inicializar_agenda
from odontologia.auth.almacenamiento import validar_esquema_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.db.postgresql import REVISION_ESQUEMA_ACTUAL
from odontologia.db.models import Base
from odontologia.disponibilidad import guardar_horario


class EsquemaDisponibilidadTests(unittest.TestCase):
    def test_modelos_definen_horarios_excepciones_bloqueos_y_restricciones(self):
        esperadas = {
            'horarios_semanales', 'excepciones_horario',
            'tramos_excepcion', 'bloqueos_agenda',
        }
        self.assertTrue(esperadas <= set(Base.metadata.tables))

        for nombre in ('horarios_semanales', 'excepciones_horario', 'bloqueos_agenda'):
            tabla = Base.metadata.tables[nombre]
            claves_foraneas = [c for c in tabla.constraints if isinstance(c, ForeignKeyConstraint)]
            self.assertTrue(claves_foraneas, nombre)
            expresiones = {
                str(c.sqltext) for c in tabla.constraints
                if getattr(c, 'sqltext', None) is not None
            }
            self.assertTrue(any('profesional_id' in e and 'box_id' in e for e in expresiones), nombre)

        horarios = Base.metadata.tables['horarios_semanales']
        restricciones = {
            str(c.sqltext) for c in horarios.constraints
            if getattr(c, 'sqltext', None) is not None
        }
        self.assertTrue(any('dia_iso' in e and 'BETWEEN 1 AND 7' in e for e in restricciones))
        self.assertTrue(any('inicio_minuto_local' in e and 'fin_minuto_local' in e
                            and '1440' in e for e in restricciones))

    def test_alembic_0006_encadena_despues_de_catalogos(self):
        ruta = Path(__file__).parents[1] / 'alembic' / 'versions' / '20261102_0006_agenda_availability.py'
        self.assertTrue(ruta.exists(), 'Debe existir la migración de disponibilidad 0006.')
        spec = importlib.util.spec_from_file_location('revision_agenda_availability', ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        self.assertEqual(modulo.revision, '20261102_0006_agenda_availability')
        self.assertEqual(modulo.down_revision, '20261102_0005_resource_catalogs')

    def test_sqlite_v5_desde_agenda_nueva_preserva_turno_y_deja_cerrado(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            turno = crear_turno(
                ruta, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio=datetime.fromisoformat('2026-10-15T09:00:00-03:00'),
                fin=datetime.fromisoformat('2026-10-15T09:30:00-03:00'))

            migrar_sqlite(ruta)

            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(
                    conexion.execute('SELECT version FROM auth_schema_version').fetchone(), (10,))
                self.assertTrue({
                    'horarios_semanales', 'excepciones_horario',
                    'tramos_excepcion', 'bloqueos_agenda',
                } <= {row[0] for row in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")})
                self.assertEqual(conexion.execute(
                    'SELECT id, paciente_id FROM turnos').fetchone(), (turno.id, 'paciente-A'))
                self.assertEqual(conexion.execute(
                    'SELECT COUNT(*) FROM horarios_semanales').fetchone(), (0,))

    def test_upgrade_sqlite_v4_a_v5_preserva_ids_y_eventos(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            with closing(sqlite3.connect(ruta)) as conexion:
                conexion.execute(
                    "INSERT INTO eventos_auditoria(created_at, action, resource_type, result) "
                    "VALUES ('2026-11-02T12:00:00+00:00', 'cuenta.bootstrap', 'cuenta', 'confirmado')")
                conexion.execute('UPDATE auth_schema_version SET version=4')
                conexion.commit()

            migrar_sqlite(ruta)

            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(
                    conexion.execute('SELECT version FROM auth_schema_version').fetchone(), (10,))
                self.assertEqual(conexion.execute(
                    "SELECT COUNT(*) FROM eventos_auditoria WHERE action='cuenta.bootstrap'"
                ).fetchone(), (1,))
                self.assertEqual(conexion.execute(
                    "SELECT id, nombre, activo FROM profesionales WHERE id='profesional-A'"
                ).fetchone(), ('profesional-A', 'Profesional de demostración profesional-A', 1))

    def test_puede_configurar_secuencialmente_turno_c01_preservado_en_migracion(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            creado = crear_turno(
                ruta, paciente_id='paciente-A', profesional_id='profesional-A',
                box_id='box-A', inicio=datetime.fromisoformat('2026-10-15T12:00:00+00:00'),
                fin=datetime.fromisoformat('2026-10-15T12:30:00+00:00'))
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                horario = {'4': [{'inicio': '09:00', 'fin': '12:00'}]}
                guardar_horario(engine, 'profesional', 'profesional-A', horario)
                guardar_horario(engine, 'box', 'box-A', horario)
                self.assertEqual(
                    {fila['inicio'] for fila in guardar_horario(
                        engine, 'profesional', 'profesional-A', horario)['dias']['4']},
                    {'09:00'})
            finally:
                engine.dispose()
            with closing(sqlite3.connect(ruta)) as conexion:
                self.assertEqual(conexion.execute('SELECT COUNT(*) FROM turnos').fetchone(), (1,))
                self.assertEqual(conexion.execute('SELECT id FROM turnos').fetchone(), (creado.id,))

    def test_sqlite_v5_impone_fk_recurso_dia_y_limites_de_tramo(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)

            with closing(sqlite3.connect(ruta)) as conexion:
                conexion.execute('PRAGMA foreign_keys=ON')
                conexion.execute(
                    'INSERT INTO horarios_semanales '
                    '(id, profesional_id, dia_iso, inicio_minuto_local, fin_minuto_local) '
                    "VALUES ('h-valido', 'profesional-A', 1, 540, 600)")
                for valores in (
                    ('h-dia', 'profesional-A', None, 8, 540, 600),
                    ('h-cruce', 'profesional-A', None, 1, 1380, 60),
                    ('h-doble', 'profesional-A', 'box-A', 1, 540, 600),
                    ('h-desconocido', 'profesional-Z', None, 1, 540, 600),
                ):
                    with self.subTest(valores=valores), self.assertRaises(sqlite3.IntegrityError):
                        conexion.execute(
                            'INSERT INTO horarios_semanales '
                            '(id, profesional_id, box_id, dia_iso, inicio_minuto_local, '
                            'fin_minuto_local) VALUES (?, ?, ?, ?, ?, ?)', valores)

    def test_guarda_de_esquema_requiere_versiones_de_disponibilidad(self):
        self.assertEqual(REVISION_ESQUEMA_ACTUAL, '20261102_0011_odontogram_treatment_plans')
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                validar_esquema_autenticacion(engine, 'sqlite', ruta)
            finally:
                engine.dispose()

    def test_validator_falla_cerrado_si_faltan_tablas_c07_con_version_v5(self):
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            with closing(sqlite3.connect(ruta)) as conexion:
                conexion.execute('DROP TABLE horarios_semanales')
                conexion.commit()
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                with self.assertRaises(RuntimeError):
                    validar_esquema_autenticacion(engine, 'sqlite', ruta)
            finally:
                engine.dispose()

    def test_dependencias_fijan_tzdata_y_cargan_zona_mendoza(self):
        raiz = Path(__file__).parents[2]
        for nombre in ('requirements.txt', 'requirements-lock.txt'):
            dependencias = (raiz / 'backend' / nombre).read_text(encoding='utf-8').splitlines()
            self.assertTrue(
                any(line.lower().startswith('tzdata==') for line in dependencias), nombre)
        self.assertEqual(ZoneInfo('America/Argentina/Mendoza').key, 'America/Argentina/Mendoza')
        manual = (raiz / 'backend' / 'README.md').read_text(encoding='utf-8')
        self.assertIn('America/Argentina/Mendoza', manual)
        self.assertIn('esquema v5', manual)
        self.assertIn('Alembic `20261102_0006_agenda_availability`', manual)
        self.assertIn('se considera cerrado hasta que', manual.lower())


if __name__ == '__main__':
    unittest.main()
