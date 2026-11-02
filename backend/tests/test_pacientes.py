from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador
from odontologia.audit import ErrorAuditoria
from odontologia.pacientes import (
    ErrorPacientes, actualizar_paciente, crear_paciente, listar_pacientes,
    obtener_paciente,
)


class PacientesServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        admin = crear_primer_administrador(
            self.engine, 'admin.one', 'frase-larga-segura-2026')
        self.actor_id = admin['id']

    def test_crear_y_listar_con_datos_minimos_y_homonimos(self):
        uno = crear_paciente(
            self.engine, '  Ana   Pérez  ', '+54 (261) 555-0101', actor_id=self.actor_id)
        dos = crear_paciente(self.engine, 'Ana Pérez', None, actor_id=self.actor_id)

        self.assertEqual(uno['nombre'], 'Ana Pérez')
        self.assertEqual(uno['telefono'], '+54 (261) 555-0101')
        self.assertTrue(uno['activo'])
        self.assertNotEqual(uno['id'], dos['id'])
        self.assertEqual(len(listar_pacientes(self.engine, limit=1, offset=0)), 1)
        self.assertEqual(obtener_paciente(self.engine, uno['id']), uno)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            evento = conexion.execute(
                "SELECT action, resource_type, resource_id FROM eventos_auditoria "
                "WHERE action='paciente.creado' ORDER BY id LIMIT 1").fetchone()
        self.assertEqual(evento, ('paciente.creado', 'paciente', uno['id']))

    def test_validacion_de_nombre_telefono_y_paginacion(self):
        for nombre, telefono in (
                ('   ', None), ('x' * 121, None), ('Paciente\x00 oculto', None),
                ('Paciente', 'abc1234567'),
                ('Paciente', '12345'), ('Paciente', '+1+2345678')):
            with self.subTest(nombre=nombre, telefono=telefono):
                with self.assertRaises(ErrorPacientes) as contexto:
                    crear_paciente(self.engine, nombre, telefono, actor_id=self.actor_id)
                self.assertEqual(contexto.exception.estado, 422)

        for params in ({'limit': 101}, {'limit': 0}, {'offset': -1}):
            with self.subTest(params=params), self.assertRaises(ErrorPacientes):
                listar_pacientes(self.engine, **params)

    def test_actualizacion_baja_y_reactivacion_conservan_ficha(self):
        paciente = crear_paciente(self.engine, 'Paciente ficticio', None, actor_id=self.actor_id)
        actualizado = actualizar_paciente(
            self.engine, paciente['id'], {'nombre': 'Nombre actualizado', 'telefono': '2615550101'},
            actor_id=self.actor_id)
        inactivo = actualizar_paciente(
            self.engine, paciente['id'], {'activo': False}, actor_id=self.actor_id)
        reactivado = actualizar_paciente(
            self.engine, paciente['id'], {'activo': True}, actor_id=self.actor_id)

        self.assertEqual(actualizado['nombre'], 'Nombre actualizado')
        self.assertEqual(inactivo['telefono'], '2615550101')
        self.assertFalse(inactivo['activo'])
        self.assertTrue(reactivado['activo'])
        self.assertEqual(obtener_paciente(self.engine, paciente['id']), reactivado)

    def test_fallo_de_auditoria_revierte_alta_y_actualizacion(self):
        with patch('odontologia.pacientes.registrar_evento_session', side_effect=ErrorAuditoria):
            with self.assertRaises(ErrorPacientes):
                crear_paciente(self.engine, 'No guardar', None, actor_id=self.actor_id)

        self.assertEqual(len(listar_pacientes(self.engine)), 2)
        paciente = crear_paciente(self.engine, 'Ficha original', None, actor_id=self.actor_id)
        with patch('odontologia.pacientes.registrar_evento_session', side_effect=ErrorAuditoria):
            with self.assertRaises(ErrorPacientes):
                actualizar_paciente(
                    self.engine, paciente['id'], {'nombre': 'Cambio sin auditoría'},
                    actor_id=self.actor_id)
        self.assertEqual(obtener_paciente(self.engine, paciente['id'])['nombre'], 'Ficha original')

    def test_paciente_inexistente_devuelve_error_404(self):
        with self.assertRaises(ErrorPacientes) as contexto:
            obtener_paciente(self.engine, 'no-existe')
        self.assertEqual(contexto.exception.estado, 404)


if __name__ == '__main__':
    unittest.main()
