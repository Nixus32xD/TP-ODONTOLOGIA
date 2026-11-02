from pathlib import Path
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class RecordatoriosPostgreSQLIntegracionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw_url = os.environ.get('ODONTOLOGIA_TEST_DATABASE_URL')
        if not raw_url:
            raise unittest.SkipTest('Definir ODONTOLOGIA_TEST_DATABASE_URL para PostgreSQL aislado.')
        base_url = make_url(raw_url)
        if (base_url.host not in ('127.0.0.1', 'localhost', '::1')
                or base_url.port != 55432
                or not (base_url.database or '').lower().endswith('_test')):
            raise unittest.SkipTest('C-17 exige localhost:55432 y una base *_test.')

        cls.schema = f'c17_recordatorios_{uuid4().hex}'
        cls.root_engine = create_engine(raw_url)
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {cls.schema}'))
        cls.url = str(base_url.update_query_dict({'options': f'-csearch_path={cls.schema}'}))
        cls.engine = create_engine(cls.url)
        cls.previous_database_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = cls.url
        cls.config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))
        cls.config.set_main_option('script_location', str(Path(__file__).parents[1] / 'alembic'))
        cls.config.config_file_name = None
        try:
            command.upgrade(cls.config, '20261102_0011_odontogram_treatment_plans')
        except Exception:
            cls.engine.dispose()
            with cls.root_engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
            cls.root_engine.dispose()
            raise

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, 'root_engine'):
            return
        cls.engine.dispose()
        with cls.root_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
        cls.root_engine.dispose()
        if cls.previous_database_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = cls.previous_database_url

    def test_upgrade_0011_a_0012_agrega_consentimiento_outbox_y_constraints(self):
        command.upgrade(self.config, 'head')

        with self.engine.begin() as connection:
            self.assertEqual(connection.execute(text(
                'SELECT version_num FROM alembic_version')).scalar_one(),
                '20261102_0013_patient_self_service')
            connection.execute(text(
                "INSERT INTO pacientes(id, nombre, activo) "
                "VALUES ('paciente-c17', 'Paciente ficticio C17', true)"))
            consentimiento = connection.execute(text(
                "SELECT acepta_recordatorios FROM pacientes WHERE id='paciente-c17'"
            )).scalar_one()
            self.assertFalse(consentimiento)
            columnas = {fila[0] for fila in connection.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema=current_schema() AND table_name='recordatorios_outbox'"))}
            self.assertTrue({
                'id', 'turno_id', 'turno_version', 'generation', 'tipo',
                'programado_para', 'estado',
                'intentos', 'idempotency_key', 'created_at', 'updated_at',
            } <= columnas)
            estado_largo = connection.execute(text(
                "SELECT character_maximum_length FROM information_schema.columns "
                "WHERE table_schema=current_schema() AND table_name='recordatorios_outbox' "
                "AND column_name='estado'")).scalar_one()
            self.assertEqual(estado_largo, 32)
            connection.execute(text(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-c17', 'Profesional ficticio C17', true)"))
            connection.execute(text(
                "INSERT INTO boxes(id, nombre, activo) "
                "VALUES ('box-c17', 'Box ficticio C17', true)"))
            turno_id = connection.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES ('paciente-c17', 'profesional-c17', "
                "'box-c17', 100, 130, 'confirmado', 1) RETURNING id")).scalar_one()
            connection.execute(text(
                "INSERT INTO recordatorios_outbox(id, turno_id, turno_version, tipo, "
                "programado_para, estado, intentos, idempotency_key, created_at, updated_at) "
                "VALUES ('recordatorio-c17', :turno_id, 1, 'turno_24h', "
                "now() + interval '2 days', 'invalidado', "
                "0, 'c17:turno:1:turno_24h', now(), now())"), {'turno_id': turno_id})
            generation = connection.execute(text(
                "SELECT generation FROM recordatorios_outbox "
                "WHERE id='recordatorio-c17'")).scalar_one()
            self.assertEqual(generation, 1)
            connection.execute(text(
                "INSERT INTO eventos_auditoria(created_at, action, resource_type, resource_id, result) "
                "VALUES (now(), 'recordatorio.programado', 'recordatorio', "
                "'recordatorio-c17', 'confirmado')"))
            auditoria = connection.execute(text(
                "SELECT action, resource_type, resource_id, result FROM eventos_auditoria "
                "WHERE resource_id='recordatorio-c17'")).one()
            self.assertEqual(tuple(auditoria), (
                'recordatorio.programado', 'recordatorio', 'recordatorio-c17', 'confirmado'))

        valores = {
            'id': 'recordatorio-duplicado', 'turno_id': turno_id, 'turno_version': 1,
            'tipo': 'turno_24h', 'estado': 'pendiente',
            'intentos': 0, 'idempotency_key': 'otra-clave',
        }
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO recordatorios_outbox(id, turno_id, turno_version, tipo, "
                    "programado_para, estado, intentos, idempotency_key, created_at, updated_at) "
                    "VALUES (:id, :turno_id, :turno_version, :tipo, now(), :estado, :intentos, "
                    ":idempotency_key, now(), now())"), valores)
        with self.engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO recordatorios_outbox(id, turno_id, turno_version, generation, "
                "tipo, programado_para, estado, intentos, idempotency_key, created_at, updated_at) "
                "VALUES ('recordatorio-reconsentido', :turno_id, 1, 2, 'turno_24h', now(), "
                "'pendiente', 0, 'c17:turno:1:generation:2', now(), now())"),
                {'turno_id': turno_id})
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO recordatorios_outbox(id, turno_id, turno_version, generation, "
                    "tipo, programado_para, estado, intentos, idempotency_key, created_at, updated_at) "
                    "VALUES ('recordatorio-generation-invalida', :turno_id, 1, 0, "
                    "'turno_24h', now(), 'pendiente', 0, 'c17:generation:0', now(), now())"),
                    {'turno_id': turno_id})
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO recordatorios_outbox(id, turno_id, turno_version, tipo, "
                    "programado_para, estado, intentos, idempotency_key, created_at, updated_at) "
                    "VALUES ('recordatorio-huerfano', 999999, 1, 'turno_24h', now(), "
                    "'pendiente', 0, 'c17:huerfano', now(), now())"))
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO recordatorios_outbox(id, turno_id, turno_version, tipo, "
                    "programado_para, estado, intentos, idempotency_key, created_at, updated_at) "
                    "VALUES ('recordatorio-tipo-invalido', :turno_id, 1, 'email', now(), "
                    "'pendiente', 0, 'c17:tipo-invalido', now(), now())"),
                    {'turno_id': turno_id})

    def test_consentimiento_concurrente_programa_una_vez_y_retirada_invalida(self):
        from odontologia.pacientes import actualizar_paciente

        command.upgrade(self.config, 'head')
        paciente_id = f'paciente-{uuid4().hex}'
        profesional_id = f'profesional-{uuid4().hex}'
        box_id = f'box-{uuid4().hex}'
        inicio = datetime(2026, 11, 5, 18, tzinfo=timezone.utc)
        ahora = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        with self.engine.begin() as connection:
            connection.execute(text(
                'INSERT INTO pacientes(id, nombre, activo) '
                'VALUES (:id, :nombre, true)'), {'id': paciente_id, 'nombre': 'Paciente C17'})
            connection.execute(text(
                'INSERT INTO profesionales(id, nombre, activo) '
                'VALUES (:id, :nombre, true)'), {'id': profesional_id, 'nombre': 'Profesional C17'})
            connection.execute(text(
                'INSERT INTO boxes(id, nombre, activo) VALUES (:id, :nombre, true)'),
                {'id': box_id, 'nombre': 'Box C17'})
            turno_id = connection.execute(text(
                'INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, '
                'fin_minuto, estado, version) VALUES (:paciente, :profesional, :box, '
                ':inicio, :fin, \'confirmado\', 1) RETURNING id'), {
                    'paciente': paciente_id, 'profesional': profesional_id, 'box': box_id,
                    'inicio': int(inicio.timestamp() // 60),
                    'fin': int((inicio + timedelta(minutes=30)).timestamp() // 60),
                }).scalar_one()

        def habilitar():
            return actualizar_paciente(
                self.engine, paciente_id, {'acepta_recordatorios': True},
                actor_id=None, ahora=ahora)

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(lambda _: habilitar(), range(2)))
        self.assertTrue(all(resultado['acepta_recordatorios'] for resultado in resultados))
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text(
                'SELECT COUNT(*) FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).scalar_one(), 1)
            estado = connection.execute(text(
                'SELECT estado FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).scalar_one()
        self.assertEqual(estado, 'pendiente')

        actualizar_paciente(
            self.engine, paciente_id, {'acepta_recordatorios': False},
            actor_id=None, ahora=ahora + timedelta(hours=1))
        with self.engine.connect() as connection:
            estado = connection.execute(text(
                'SELECT estado FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).scalar_one()
            acciones = connection.execute(text(
                "SELECT action FROM eventos_auditoria WHERE resource_type='recordatorio' "
                'ORDER BY id')).scalars().all()
        self.assertEqual(estado, 'invalidado')
        self.assertIn('recordatorio.invalidado', acciones)

        def reconsentir():
            return actualizar_paciente(
                self.engine, paciente_id, {'acepta_recordatorios': True},
                actor_id=None, ahora=ahora + timedelta(hours=2))

        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(lambda _: reconsentir(), range(2)))
        with self.engine.connect() as connection:
            filas = connection.execute(text(
                'SELECT generation, estado FROM recordatorios_outbox WHERE turno_id=:id '
                'ORDER BY generation'), {'id': turno_id}).all()
        self.assertEqual([tuple(fila) for fila in filas], [
            (1, 'invalidado'), (2, 'pendiente')])

    def test_worker_postgresql_revalida_y_simula_sin_exponer_datos(self):
        from odontologia.auth.almacenamiento import validar_esquema_autenticacion
        from odontologia.db.models import Turno
        from odontologia.recordatorios import programar_recordatorio_confirmacion
        from odontologia.workers.recordatorios import procesar_recordatorios

        command.upgrade(self.config, 'head')
        validar_esquema_autenticacion(self.engine, 'postgresql')
        paciente_id = f'paciente-{uuid4().hex}'
        profesional_id = f'profesional-{uuid4().hex}'
        box_id = f'box-{uuid4().hex}'
        programado_ahora = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        procesamiento = datetime(2026, 11, 3, 19, tzinfo=timezone.utc)
        inicio = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)
        with self.engine.begin() as connection:
            connection.execute(text('DELETE FROM recordatorios_outbox'))
            connection.execute(text(
                'INSERT INTO pacientes(id, nombre, activo, acepta_recordatorios, telefono) '
                'VALUES (:id, :nombre, true, true, :telefono)'), {
                    'id': paciente_id, 'nombre': 'Nombre sintético confidencial',
                    'telefono': '+54 261 5550101',
                })
            connection.execute(text(
                'INSERT INTO profesionales(id, nombre, activo) '
                'VALUES (:id, :nombre, true)'), {'id': profesional_id, 'nombre': 'Profesional C17'})
            connection.execute(text(
                'INSERT INTO boxes(id, nombre, activo) VALUES (:id, :nombre, true)'),
                {'id': box_id, 'nombre': 'Box C17'})
            turno_id = connection.execute(text(
                "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                "fin_minuto, estado, version) VALUES (:paciente, :profesional, :box, "
                ":inicio, :fin, 'confirmado', 1) RETURNING id"), {
                    'paciente': paciente_id, 'profesional': profesional_id, 'box': box_id,
                    'inicio': int(inicio.timestamp() // 60),
                    'fin': int((inicio + timedelta(minutes=30)).timestamp() // 60),
                }).scalar_one()
        with Session(self.engine) as session, session.begin():
            turno = session.get(Turno, turno_id)
            programar_recordatorio_confirmacion(
                session, turno, actor_id=None, ahora=programado_ahora)
        resultado = procesar_recordatorios(
            self.engine, limite=1, ahora=procesamiento)
        with self.engine.connect() as connection:
            estado = connection.execute(text(
                'SELECT estado FROM recordatorios_outbox WHERE turno_id=:id'),
                {'id': turno_id}).scalar_one()
            eventos = connection.execute(text(
                "SELECT action, resource_type, result FROM eventos_auditoria "
                "WHERE resource_type='recordatorio'")).all()
            texto_auditoria = connection.execute(text(
                'SELECT COALESCE(actor_id, \'\') || action || resource_type || '
                "COALESCE(resource_id, '') || result FROM eventos_auditoria "
                "WHERE resource_type='recordatorio'")).scalars().all()
        self.assertEqual(resultado, {'procesados': 1, 'invalidados': 0, 'fallidos': 0})
        self.assertEqual(estado, 'procesado_simulado')
        self.assertIn(('recordatorio.procesado', 'recordatorio', 'confirmado'), eventos)
        self.assertNotIn('Nombre sintético confidencial', ''.join(texto_auditoria))
        self.assertNotIn('+54 261 5550101', ''.join(texto_auditoria))
