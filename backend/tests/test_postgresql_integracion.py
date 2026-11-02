from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from ipaddress import ip_address
import multiprocessing
import os
import sqlite3
import tempfile
import unittest
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, event, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from odontologia import ErrorAgenda, crear_turno, inicializar_agenda
from odontologia.api import crear_app
from odontologia.db.migracion import ErrorMigracion, migrar_agenda_sqlite
from odontologia.db.models import AgendaMutex, Base, Box, Paciente, Profesional, Turno
from odontologia.db.postgresql import crear_turno_postgresql


def _url_test_database_permitida(url):
    """Permitir tests sólo contra una DB identificable como aislada y loopback."""
    nombre = (url.database or '').lower()
    if not (nombre == 'test' or nombre.endswith('_test')):
        return False

    host = (url.host or '').lower()
    try:
        es_loopback = ip_address(host).is_loopback
    except ValueError:
        es_loopback = host == 'localhost'

    puerto = url.port if url.port is not None else 5432
    return es_loopback and puerto != 5432


def _solicitar_turno_postgres(url, preparados, salida, inicio, profesional, box):
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect():
            preparados.put(True)
        if not inicio.wait(10):
            raise RuntimeError('No se recibió la señal de inicio.')
        try:
            turno = crear_turno_postgresql(
                engine, paciente_id='paciente-A', profesional_id=profesional, box_id=box,
                inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc),
            )
            salida.put(('ok', turno.id))
        except ErrorAgenda as exc:
            salida.put(('error', exc.codigo))
    finally:
        engine.dispose()


class IntegracionPostgreSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        if not _url_test_database_permitida(base_url):
            raise unittest.SkipTest(
                'Se exige una base test o *_test en loopback y puerto distinto de 5432.')

        cls.schema = f'tp_odontologia_test_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as conexion:
            conexion.execute(text(f'CREATE SCHEMA {cls.schema}'))

        cls.database_url = str(base_url.update_query_dict(
            {'options': f'-csearch_path={cls.schema}'}))
        cls.engine = create_engine(cls.database_url, pool_pre_ping=True)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        cls.previous_persistence = os.environ.get('ODONTOLOGIA_PERSISTENCIA')
        os.environ['DATABASE_URL'] = cls.database_url
        os.environ['ODONTOLOGIA_PERSISTENCIA'] = 'postgresql'
        config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        command.upgrade(config, 'head')

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, 'root_engine'):
            return
        cls.engine.dispose()
        with cls.root_engine.begin() as conexion:
            conexion.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
        cls.root_engine.dispose()
        if cls.previous_database_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = cls.previous_database_url
        if cls.previous_persistence is None:
            os.environ.pop('ODONTOLOGIA_PERSISTENCIA', None)
        else:
            os.environ['ODONTOLOGIA_PERSISTENCIA'] = cls.previous_persistence

    def setUp(self):
        with Session(self.engine) as session, session.begin():
            session.execute(delete(Turno))
            session.execute(delete(Paciente))
            session.execute(delete(Profesional))
            session.execute(delete(Box))

    def _sqlite_con_datos(self, ruta):
        inicializar_agenda(ruta)
        primero = crear_turno(
            ruta, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
            inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
            fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc),
        )
        segundo = crear_turno(
            ruta, paciente_id='paciente-B', profesional_id='profesional-B', box_id='box-B',
            inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
            fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc),
        )
        return primero, segundo

    def _seed_catalogos(self):
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Paciente(id='paciente-A'), Paciente(id='paciente-B'),
                Profesional(id='profesional-A'), Profesional(id='profesional-B'),
                Box(id='box-A'), Box(id='box-B'),
            ])

    def test_migracion_preserva_agenda_ids_y_secuencia_y_rechaza_repeticion(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            ids_esperados = self._sqlite_con_datos(ruta)
            fuente_original = ruta.read_bytes()

            resumen = migrar_agenda_sqlite(self.engine, ruta)
            with Session(self.engine) as session:
                turnos = session.scalars(select(Turno).order_by(Turno.id)).all()

            self.assertEqual((resumen.pacientes, resumen.profesionales, resumen.boxes, resumen.turnos),
                             (2, 2, 2, 2))
            self.assertEqual([turno.id for turno in turnos], [turno.id for turno in ids_esperados])
            self.assertEqual(ruta.read_bytes(), fuente_original)
            siguiente = crear_turno_postgresql(
                self.engine, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc),
                fin=datetime(2026, 10, 15, 13, tzinfo=timezone.utc),
            )
            self.assertEqual(siguiente.id, 3)

            with self.assertRaises(ErrorMigracion) as contexto:
                migrar_agenda_sqlite(self.engine, ruta)
            self.assertEqual(contexto.exception.codigo, 'destino_no_vacio')
            with Session(self.engine) as session:
                self.assertEqual(session.scalar(select(func.count()).select_from(Turno)), 3)

    def test_fallo_a_mitad_de_importacion_revierte_filas_de_catalogo(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / 'agenda.sqlite3'
            self._sqlite_con_datos(ruta)

            def fallar_antes_de_insertar_turno(_conn, _cursor, statement, _parameters, _context, _many):
                if statement.lstrip().lower().startswith('insert into turnos'):
                    raise SQLAlchemyError('fallo inyectado')

            event.listen(self.engine, 'before_cursor_execute', fallar_antes_de_insertar_turno)
            try:
                with self.assertRaises(ErrorMigracion) as contexto:
                    migrar_agenda_sqlite(self.engine, ruta)
            finally:
                event.remove(self.engine, 'before_cursor_execute', fallar_antes_de_insertar_turno)

            self.assertEqual(contexto.exception.codigo, 'destino_error')
            with Session(self.engine) as session:
                for modelo in (Paciente, Profesional, Box, Turno):
                    self.assertEqual(session.scalar(select(func.count()).select_from(modelo)), 0)

    def test_dos_procesos_no_confirman_solapamientos_por_profesional(self):
        self._seed_catalogos()
        contexto = multiprocessing.get_context('spawn')
        preparados, salida = contexto.Queue(), contexto.Queue()
        inicio = contexto.Event()
        procesos = [
            contexto.Process(target=_solicitar_turno_postgres,
                             args=(self.database_url, preparados, salida, inicio,
                                   'profesional-A', 'box-A')),
            contexto.Process(target=_solicitar_turno_postgres,
                             args=(self.database_url, preparados, salida, inicio,
                                   'profesional-A', 'box-B')),
        ]
        try:
            for proceso in procesos:
                proceso.start()
            for _ in procesos:
                preparados.get(timeout=10)
            inicio.set()
            resultados = [salida.get(timeout=10) for _ in procesos]
            for proceso in procesos:
                proceso.join(timeout=10)
            self.assertTrue(all(proceso.exitcode == 0 for proceso in procesos))
        finally:
            inicio.set()
            for proceso in procesos:
                if proceso.is_alive():
                    proceso.terminate()
                    proceso.join(timeout=5)

        self.assertEqual(sum(resultado[0] == 'ok' for resultado in resultados), 1)
        self.assertIn(('error', 'conflicto_profesional'), resultados)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Turno)), 1)

    def test_dos_procesos_no_confirman_solapamientos_por_box(self):
        self._seed_catalogos()
        contexto = multiprocessing.get_context('spawn')
        preparados, salida = contexto.Queue(), contexto.Queue()
        inicio = contexto.Event()
        procesos = [
            contexto.Process(target=_solicitar_turno_postgres,
                             args=(self.database_url, preparados, salida, inicio,
                                   'profesional-A', 'box-A')),
            contexto.Process(target=_solicitar_turno_postgres,
                             args=(self.database_url, preparados, salida, inicio,
                                   'profesional-B', 'box-A')),
        ]
        try:
            for proceso in procesos:
                proceso.start()
            for _ in procesos:
                preparados.get(timeout=10)
            inicio.set()
            resultados = [salida.get(timeout=10) for _ in procesos]
            for proceso in procesos:
                proceso.join(timeout=10)
            self.assertTrue(all(proceso.exitcode == 0 for proceso in procesos))
        finally:
            inicio.set()
            for proceso in procesos:
                if proceso.is_alive():
                    proceso.terminate()
                    proceso.join(timeout=5)

        self.assertEqual(sum(resultado[0] == 'ok' for resultado in resultados), 1)
        self.assertIn(('error', 'conflicto_box'), resultados)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Turno)), 1)

    def test_api_postgresql_conserva_respuesta_c01(self):
        self._seed_catalogos()
        with TestClient(crear_app()) as cliente:
            cuerpo = {
                'paciente_id': 'paciente-A',
                'profesional_id': 'profesional-A',
                'box_id': 'box-A',
                'inicio': '2026-10-15T12:00:00+00:00',
                'fin': '2026-10-15T12:30:00+00:00',
            }
            respuesta = cliente.post('/turnos', json=cuerpo)
            adyacente = dict(cuerpo, inicio='2026-10-15T12:30:00+00:00',
                             fin='2026-10-15T13:00:00+00:00')
            respuesta_adyacente = cliente.post('/turnos', json=adyacente)
            desconocido = dict(cuerpo, paciente_id='paciente-inexistente',
                               inicio='2026-10-15T13:00:00+00:00',
                               fin='2026-10-15T13:30:00+00:00')
            respuesta_desconocido = cliente.post('/turnos', json=desconocido)

        self.assertEqual(respuesta.status_code, 201)
        self.assertGreater(respuesta.json()['id'], 0)
        self.assertEqual(respuesta.json()['inicio'], '2026-10-15T12:00:00Z')
        self.assertEqual(respuesta_adyacente.status_code, 201)
        self.assertEqual(respuesta_desconocido.status_code, 404)

    def test_revision_esquema_desconocida_falla_cerrado(self):
        self._seed_catalogos()
        with self.engine.begin() as conexion:
            conexion.execute(text("UPDATE alembic_version SET version_num = 'revision-desconocida'"))
        try:
            with self.assertRaises(ErrorAgenda) as contexto:
                crear_turno_postgresql(
                    self.engine, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                    inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                    fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc),
                )
        finally:
            with self.engine.begin() as conexion:
                conexion.execute(text(
                    "UPDATE alembic_version SET version_num = '20261101_0001'"))

        self.assertEqual(contexto.exception.codigo, 'almacenamiento_error')
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Turno)), 0)

    def test_timeout_de_mutex_devuelve_agenda_ocupada_y_se_recupera(self):
        self._seed_catalogos()
        with Session(self.engine) as session, session.begin():
            session.scalar(select(AgendaMutex.id).where(AgendaMutex.id == 1).with_for_update())
            with self.assertRaises(ErrorAgenda) as contexto:
                crear_turno_postgresql(
                    self.engine, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                    inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                    fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc), timeout_segundos=0.05,
                )
            self.assertEqual(contexto.exception.codigo, 'agenda_ocupada')

        turno = crear_turno_postgresql(
            self.engine, paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
            inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
            fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc),
        )
        self.assertGreater(turno.id, 0)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Turno)), 1)

    def test_upgrade_head_repetido_conserva_esquema_y_agenda(self):
        self._seed_catalogos()
        with Session(self.engine) as session, session.begin():
            session.add(Turno(
                paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio_minuto=29700000, fin_minuto=29700030,
            ))
        config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        command.upgrade(config, 'head')

        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Turno)), 1)


if __name__ == '__main__':
    unittest.main()
