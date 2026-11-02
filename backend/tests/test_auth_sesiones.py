from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Barrier, Event, Lock
from tempfile import TemporaryDirectory
import unittest
import jwt
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador
from odontologia.auth.usuarios import crear_usuario
from odontologia.auth.sesiones import (
    ErrorSesiones,
    autenticar,
    cerrar_sesion,
    validar_sesion,
)
from odontologia.db.models import Usuario


class ServicioSesionesTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        self.secreto = 'secreto-local-de-prueba-no-reutilizar-2026'
        self.admin = crear_primer_administrador(
            self.engine, 'admin.one', 'frase-larga-segura-2026')

    def test_login_emite_token_y_sesion_consultable(self):
        token = autenticar(
            self.engine, 'admin.one', 'frase-larga-segura-2026', self.secreto,
            ahora=1_800_000_000)
        sesion = validar_sesion(self.engine, token, self.secreto, ahora=1_800_000_001)
        self.assertEqual(sesion['usuario_id'], self.admin['id'])
        self.assertEqual(sesion['rol'], 'administrador')
        self.assertNotIn('password_hash', sesion)

    def test_credenciales_invalidas_son_genericas_y_cuenta_inexistente_no_autentica(self):
        for identificador, password in (
            ('admin.one', 'password-que-no-es-la-correcta'),
            ('no.existe', 'frase-larga-segura-2026'),
        ):
            with self.subTest(identificador=identificador), self.assertRaises(ErrorSesiones) as error:
                autenticar(self.engine, identificador, password, self.secreto, ahora=1_800_000_000)
            self.assertEqual(error.exception.estado, 401)
            self.assertEqual(error.exception.codigo, 'credenciales_invalidas')

    def test_logout_revoca_token_y_firma_o_expiracion_invalidas_se_rechazan(self):
        token = autenticar(
            self.engine, 'admin.one', 'frase-larga-segura-2026', self.secreto,
            ahora=1_800_000_000)
        cerrar_sesion(self.engine, token, self.secreto, ahora=1_800_000_001)
        with self.assertRaises(ErrorSesiones) as revocado:
            validar_sesion(self.engine, token, self.secreto, ahora=1_800_000_002)
        self.assertEqual(revocado.exception.estado, 401)

        with self.assertRaises(ErrorSesiones):
            validar_sesion(self.engine, token + 'x', self.secreto, ahora=1_800_000_002)
        with self.assertRaises(ErrorSesiones):
            validar_sesion(self.engine, token, self.secreto, ahora=1_800_000_000 + 31 * 60)

    def test_sesion_profesional_incluye_vinculo_y_falla_cerrado_si_cambia(self):
        profesional = crear_usuario(
            self.engine, 'profesional.a', 'otra-frase-segura-2026', 'profesional',
            profesional_id='profesional-A')
        token = autenticar(
            self.engine, 'profesional.a', 'otra-frase-segura-2026', self.secreto,
            ahora=1_800_000_000)
        claims = jwt.decode(token, self.secreto, algorithms=['HS256'],
                            options={'verify_exp': False, 'verify_iat': False})
        self.assertEqual(claims['profesional_id'], 'profesional-A')
        identidad = validar_sesion(
            self.engine, token, self.secreto, ahora=1_800_000_001)
        self.assertEqual(identidad['profesional_id'], 'profesional-A')
        self.assertEqual(identidad['usuario_id'], profesional['id'])

        with Session(self.engine) as session, session.begin():
            session.execute(update(Usuario).where(
                Usuario.id == profesional['id']).values(profesional_id='profesional-B'))
        with self.assertRaises(ErrorSesiones) as cambiado:
            validar_sesion(self.engine, token, self.secreto, ahora=1_800_000_002)
        self.assertEqual((cambiado.exception.codigo, cambiado.exception.estado),
                         ('token_invalido', 401))

    def test_login_profesional_sin_vinculo_se_rechaza_sin_crear_sesion(self):
        profesional = crear_usuario(
            self.engine, 'profesional.sin-vinculo', 'otra-frase-segura-2026', 'profesional',
            profesional_id='profesional-A')
        with self.engine.begin() as conexion:
            conexion.exec_driver_sql('PRAGMA ignore_check_constraints = ON')
            conexion.execute(
                Usuario.__table__.update().where(
                    Usuario.id == profesional['id']).values(profesional_id=None))
        with self.assertRaises(ErrorSesiones) as error:
            autenticar(self.engine, 'profesional.sin-vinculo', 'otra-frase-segura-2026',
                       self.secreto, ahora=1_800_000_000)
        self.assertEqual((error.exception.codigo, error.exception.estado),
                         ('credenciales_invalidas', 401))

    def test_seis_logins_concurrentes_solo_verifican_cinco_credenciales(self):
        from types import SimpleNamespace

        from odontologia.auth.limitador_login import LimitadorIntentosLogin

        class SesionFalsa:
            bind = SimpleNamespace(dialect=SimpleNamespace(name='sqlite'))

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def begin(self):
                return nullcontext()

            def scalar(self, _consulta):
                return SimpleNamespace(
                    id='usuario-ficticio', password_hash='hash-ficticio',
                    activo=True, rol='administrador', profesional_id=None)

            def add(self, _objeto):
                pass

            def flush(self):
                pass

        inicio = Barrier(6)
        verificacion = Barrier(5, timeout=0.5)
        lock = Lock()
        verificaciones = 0

        def verificar_en_barrera(_password, _password_hash):
            nonlocal verificaciones
            with lock:
                verificaciones += 1
            try:
                verificacion.wait()
            except Exception:
                # Un sexto pase detecta la siguiente generación y falla el aserto final.
                pass
            return False

        limitador = LimitadorIntentosLogin()

        def intentar_login():
            inicio.wait(timeout=3)
            try:
                autenticar(
                    object(), 'admin.one', 'clave-incorrecta-larga-2026', self.secreto,
                    limitador=limitador, origen='peer-ficticio')
            except ErrorSesiones as exc:
                return exc.codigo
            return 'autenticado'

        with patch('odontologia.auth.sesiones.Session', side_effect=lambda _engine: SesionFalsa()), \
                patch('odontologia.auth.sesiones._bloquear_sqlite'), \
                patch('odontologia.auth.sesiones.verificar_password',
                      side_effect=verificar_en_barrera), \
                patch('odontologia.audit.registrar_evento_session'):
            with ThreadPoolExecutor(max_workers=6) as ejecutor:
                resultados = list(ejecutor.map(lambda _n: intentar_login(), range(6)))

        self.assertEqual(resultados.count('credenciales_invalidas'), 5)
        self.assertEqual(resultados.count('demasiados_intentos'), 1)
        self.assertEqual(verificaciones, 5)
        self.assertEqual(len(limitador._reservas), 0)

    def test_error_de_db_libera_reserva_sin_contabilizar_fallo(self):
        from contextlib import nullcontext

        from odontologia.auth.limitador_login import LimitadorIntentosLogin

        class SesionConFallo:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def begin(self):
                return nullcontext()

            def scalar(self, _consulta):
                raise SQLAlchemyError('detalle DB de prueba')

        limitador = LimitadorIntentosLogin()
        with patch('odontologia.auth.sesiones.Session',
                   side_effect=lambda _engine: SesionConFallo()), \
                patch('odontologia.auth.sesiones._bloquear_sqlite'):
            with self.assertRaises(ErrorSesiones) as error:
                autenticar(
                    object(), 'admin.one', 'clave-incorrecta-larga-2026', self.secreto,
                    limitador=limitador, origen='peer-ficticio')
        self.assertEqual(error.exception.codigo, 'almacenamiento_error')
        self.assertIsNone(
            limitador.segundos_hasta_reintento('peer-ficticio', 'admin.one'))
        self.assertEqual(len(limitador._reservas), 0)

    def test_login_correcto_concurrente_limpia_fallos_previos(self):
        from contextlib import nullcontext
        from types import SimpleNamespace

        from odontologia.auth.limitador_login import LimitadorIntentosLogin

        class SesionFalsa:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def begin(self):
                return nullcontext()

            def scalar(self, _consulta):
                return SimpleNamespace(
                    id='usuario-ficticio', password_hash='hash-ficticio',
                    activo=True, rol='administrador', profesional_id=None)

            def add(self, _objeto):
                pass

            def flush(self):
                pass

        iniciados = Barrier(2)
        liberar_error = Event()
        liberar_exito = Event()

        def verificar(password, _password_hash):
            if password == 'clave-correcta-larga-2026':
                liberar_exito.wait(timeout=3)
                return True
            liberar_error.wait(timeout=3)
            return False

        limitador = LimitadorIntentosLogin()
        for _ in range(3):
            limitador.registrar_fallo('peer-ficticio', 'admin.one')

        def autenticar_en_paralelo(password):
            iniciados.wait(timeout=3)
            try:
                autenticar(
                    object(), 'admin.one', password, self.secreto,
                    limitador=limitador, origen='peer-ficticio')
                return 'exito'
            except ErrorSesiones as exc:
                return exc.codigo

        with patch('odontologia.auth.sesiones.Session',
                   side_effect=lambda _engine: SesionFalsa()), \
                patch('odontologia.auth.sesiones._bloquear_sqlite'), \
                patch('odontologia.auth.sesiones.verificar_password', side_effect=verificar), \
                patch('odontologia.audit.registrar_evento_session'):
            with ThreadPoolExecutor(max_workers=2) as ejecutor:
                fallido = ejecutor.submit(
                    autenticar_en_paralelo, 'clave-incorrecta-larga-2026')
                exitoso = ejecutor.submit(
                    autenticar_en_paralelo, 'clave-correcta-larga-2026')
                liberar_error.set()
                self.assertEqual(fallido.result(timeout=3), 'credenciales_invalidas')
                liberar_exito.set()
                self.assertEqual(exitoso.result(timeout=3), 'exito')

        self.assertIsNone(
            limitador.segundos_hasta_reintento('peer-ficticio', 'admin.one'))
        self.assertEqual(len(limitador._reservas), 0)


if __name__ == '__main__':
    unittest.main()
