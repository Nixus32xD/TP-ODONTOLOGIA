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
    ErrorUsuarios, actualizar_usuario, crear_usuario, listar_usuarios,
)
from odontologia.db.models import Paciente, Profesional, Sesion


class UsuariosProfesionalTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)

    def _agregar_sesion(self, usuario_id):
        sesion_id = str(uuid4())
        sesion = Sesion(
            id=sesion_id, usuario_id=usuario_id, jti=str(uuid4()),
            expira_en=5000, revocada_en=None, creado_en=1000)
        with Session(self.engine) as session, session.begin():
            session.add(sesion)
        return sesion_id

    def test_crear_cuenta_profesional_vinculada_y_exponer_solo_datos_publicos(self):
        creada = crear_usuario(
            self.engine, 'profesional.a', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A')

        self.assertEqual(creada['rol'], 'profesional')
        self.assertEqual(creada['profesional_id'], 'profesional-A')
        self.assertEqual(listar_usuarios(self.engine), [creada])
        self.assertNotIn('password_hash', creada)
        self.assertNotIn('password', creada)

    def test_vinculo_inexistente_inactivo_o_incompatible_se_rechaza(self):
        with self.assertRaises(ErrorUsuarios) as inexistente:
            crear_usuario(
                self.engine, 'profesional.no-existe', 'frase-larga-segura-2026',
                'profesional', profesional_id='profesional-desconocido')
        self.assertEqual((inexistente.exception.codigo, inexistente.exception.estado),
                         ('profesional_desconocido', 404))

        with Session(self.engine) as session, session.begin():
            profesional = session.get(Profesional, 'profesional-B')
            profesional.activo = False
        with self.assertRaises(ErrorUsuarios) as inactivo:
            crear_usuario(
                self.engine, 'profesional.inactivo', 'frase-larga-segura-2026',
                'profesional', profesional_id='profesional-B')
        self.assertEqual((inactivo.exception.codigo, inactivo.exception.estado),
                         ('profesional_inactivo', 409))

        with self.assertRaises(ErrorUsuarios) as incompatible:
            crear_usuario(
                self.engine, 'recepcion.con-vinculo', 'frase-larga-segura-2026',
                'recepcion', profesional_id='profesional-A')
        self.assertEqual((incompatible.exception.codigo, incompatible.exception.estado),
                         ('vinculo_profesional_incompatible', 422))
        self.assertEqual(listar_usuarios(self.engine), [])

    def test_un_profesional_no_se_asigna_a_dos_cuentas(self):
        crear_usuario(
            self.engine, 'profesional.a', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A')

        with self.assertRaises(ErrorUsuarios) as error:
            crear_usuario(
                self.engine, 'profesional.b', 'otra-frase-larga-segura-2026',
                'profesional', profesional_id='profesional-A')

        self.assertEqual((error.exception.codigo, error.exception.estado),
                         ('profesional_vinculado', 409))
        self.assertEqual(len(listar_usuarios(self.engine)), 1)

    def test_cambiar_y_reasignar_vinculo_revoca_sesiones_y_retirar_rol_lo_limpia(self):
        cuenta = crear_usuario(
            self.engine, 'operador.vinculo', 'frase-larga-segura-2026', 'recepcion')
        sesion_recepcion = self._agregar_sesion(cuenta['id'])

        vinculada = actualizar_usuario(
            self.engine, cuenta['id'], rol='profesional',
            profesional_id='profesional-A', ahora=2000)

        self.assertEqual((vinculada['rol'], vinculada['profesional_id']),
                         ('profesional', 'profesional-A'))
        with Session(self.engine) as session:
            self.assertEqual(session.get(Sesion, sesion_recepcion).revocada_en, 2000)

        sesion_profesional = self._agregar_sesion(cuenta['id'])
        reasignada = actualizar_usuario(
            self.engine, cuenta['id'], profesional_id='profesional-B', ahora=3000)
        self.assertEqual(reasignada['profesional_id'], 'profesional-B')
        with Session(self.engine) as session:
            self.assertEqual(session.get(Sesion, sesion_profesional).revocada_en, 3000)

        sesion_reasignada = self._agregar_sesion(cuenta['id'])
        recepcion = actualizar_usuario(
            self.engine, cuenta['id'], rol='recepcion', ahora=4000)
        self.assertEqual((recepcion['rol'], recepcion['profesional_id']),
                         ('recepcion', None))
        with Session(self.engine) as session:
            self.assertEqual(session.get(Sesion, sesion_reasignada).revocada_en, 4000)

    def test_actualizacion_profesional_rechaza_asignacion_duplicada_sin_mutar(self):
        crear_usuario(
            self.engine, 'profesional.a', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A')
        recepcion = crear_usuario(
            self.engine, 'recepcion.b', 'otra-frase-larga-segura-2026', 'recepcion')

        with self.assertRaises(ErrorUsuarios) as duplicado:
            actualizar_usuario(
                self.engine, recepcion['id'], rol='profesional',
                profesional_id='profesional-A')

        self.assertEqual((duplicado.exception.codigo, duplicado.exception.estado),
                         ('profesional_vinculado', 409))
        actual = next(usuario for usuario in listar_usuarios(self.engine)
                      if usuario['id'] == recepcion['id'])
        self.assertEqual((actual['rol'], actual['profesional_id']), ('recepcion', None))

    def test_cambio_a_profesional_sin_vinculo_es_rechazado(self):
        recepcion = crear_usuario(
            self.engine, 'recepcion.b', 'otra-frase-larga-segura-2026', 'recepcion')

        with self.assertRaises(ErrorUsuarios) as error:
            actualizar_usuario(self.engine, recepcion['id'], rol='profesional')

        self.assertEqual((error.exception.codigo, error.exception.estado),
                         ('vinculo_profesional_invalido', 422))
        self.assertEqual(next(usuario['rol'] for usuario in listar_usuarios(self.engine)
                             if usuario['id'] == recepcion['id']), 'recepcion')

    def test_crear_cuenta_paciente_activo_unica_y_no_exponer_credenciales(self):
        with Session(self.engine) as session, session.begin():
            session.add(Paciente(
                id='paciente-vinculable', nombre='Paciente sintético', activo=True,
                acepta_recordatorios=False))

        creada = crear_usuario(
            self.engine, 'paciente.sintetico', 'frase-larga-segura-2026', 'paciente',
            paciente_id='paciente-vinculable')

        self.assertEqual((creada['rol'], creada['paciente_id']),
                         ('paciente', 'paciente-vinculable'))
        self.assertIsNone(creada['profesional_id'])
        self.assertNotIn('password_hash', creada)
        self.assertNotIn('password', creada)
        self.assertEqual(listar_usuarios(self.engine), [creada])
        with self.assertRaises(ErrorUsuarios) as duplicada:
            crear_usuario(
                self.engine, 'paciente.duplicado', 'otra-frase-larga-segura-2026', 'paciente',
                paciente_id='paciente-vinculable')
        self.assertEqual((duplicada.exception.codigo, duplicada.exception.estado),
                         ('paciente_vinculado', 409))

    def test_vinculo_paciente_inexistente_inactivo_o_incompatible_se_rechaza(self):
        with self.assertRaises(ErrorUsuarios) as inexistente:
            crear_usuario(
                self.engine, 'paciente.no-existe', 'frase-larga-segura-2026', 'paciente',
                paciente_id='paciente-desconocido')
        self.assertEqual((inexistente.exception.codigo, inexistente.exception.estado),
                         ('paciente_desconocido', 404))
        with Session(self.engine) as session, session.begin():
            session.add(Paciente(
                id='paciente-inactivo', nombre='Paciente sintético inactivo', activo=False,
                acepta_recordatorios=False))
        with self.assertRaises(ErrorUsuarios) as inactivo:
            crear_usuario(
                self.engine, 'paciente.inactivo', 'frase-larga-segura-2026', 'paciente',
                paciente_id='paciente-inactivo')
        self.assertEqual((inactivo.exception.codigo, inactivo.exception.estado),
                         ('paciente_inactivo', 409))
        with self.assertRaises(ErrorUsuarios) as incompatible:
            crear_usuario(
                self.engine, 'recepcion.con-paciente', 'frase-larga-segura-2026', 'recepcion',
                paciente_id='paciente-A')
        self.assertEqual((incompatible.exception.codigo, incompatible.exception.estado),
                         ('vinculo_paciente_incompatible', 422))


if __name__ == '__main__':
    unittest.main()
