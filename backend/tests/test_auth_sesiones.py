from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import jwt
from sqlalchemy import update
from sqlalchemy.orm import Session

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


if __name__ == '__main__':
    unittest.main()
