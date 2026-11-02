from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from odontologia import inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import (
    ErrorUsuarios,
    actualizar_usuario,
    crear_primer_administrador,
    crear_usuario,
    listar_usuarios,
)
from odontologia.db.models import Sesion


class UsuariosAutenticacionTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        self.password = 'frase-larga-segura-2026'

    def test_bootstrap_crea_un_solo_administrador_y_no_expone_hash(self):
        admin = crear_primer_administrador(self.engine, 'Admin.One', self.password)
        self.assertEqual(admin['identificador'], 'admin.one')
        self.assertEqual(admin['rol'], 'administrador')
        self.assertTrue(admin['activo'])
        self.assertNotIn('password_hash', admin)
        with self.assertRaises(ErrorUsuarios):
            crear_primer_administrador(self.engine, 'otro.admin', self.password)
        self.assertEqual(len(listar_usuarios(self.engine)), 1)

    def test_cuenta_duplicada_normalizada_y_rol_profesional_se_rechazan(self):
        admin = crear_primer_administrador(self.engine, 'admin.one', self.password)
        recepcion = crear_usuario(self.engine, ' Recepcion.A ', self.password, 'recepcion')
        self.assertEqual(recepcion['identificador'], 'recepcion.a')
        with self.assertRaises(ErrorUsuarios):
            crear_usuario(self.engine, 'RECEPCION.A', self.password, 'recepcion')
        with self.assertRaises(ErrorUsuarios):
            crear_usuario(self.engine, 'profesional.a', self.password, 'profesional')
        self.assertEqual({u['rol'] for u in listar_usuarios(self.engine)}, {'administrador', 'recepcion'})

    def test_cambio_de_rol_revoca_sesiones_y_no_devuelve_hash(self):
        admin = crear_primer_administrador(self.engine, 'admin.one', self.password)
        recepcion = crear_usuario(self.engine, 'recepcion.a', self.password, 'recepcion')
        ahora = 1_800_000_000
        with Session(self.engine) as session, session.begin():
            session.add(Sesion(
                id=str(uuid4()), usuario_id=recepcion['id'], jti=str(uuid4()),
                expira_en=ahora + 600, creado_en=ahora,
            ))
        actualizada = actualizar_usuario(
            self.engine, recepcion['id'], rol='administrador', ahora=ahora)
        self.assertEqual(actualizada['rol'], 'administrador')
        self.assertNotIn('password_hash', actualizada)
        with Session(self.engine) as session:
            sesion = session.scalar(select(Sesion).where(Sesion.usuario_id == recepcion['id']))
            self.assertEqual(sesion.revocada_en, ahora)

    def test_no_se_puede_desactivar_o_degradar_al_ultimo_administrador_activo(self):
        admin = crear_primer_administrador(self.engine, 'admin.one', self.password)
        for cambios in ({'activo': False}, {'rol': 'recepcion'}):
            with self.subTest(cambios=cambios):
                with self.assertRaises(ErrorUsuarios) as error:
                    actualizar_usuario(self.engine, admin['id'], **cambios)
                self.assertEqual(error.exception.estado, 409)
        self.assertEqual(listar_usuarios(self.engine)[0]['rol'], 'administrador')
        self.assertTrue(listar_usuarios(self.engine)[0]['activo'])
