from pathlib import Path
from contextlib import closing
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador
from odontologia.audit import ErrorAuditoria
from odontologia.catalogos import (
    ErrorCatalogos, actualizar_recurso, crear_recurso, listar_recursos,
    obtener_recurso,
)


class CatalogosServiceTests(unittest.TestCase):
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

    def test_crud_paginado_para_los_tres_catalogos(self):
        casos = (
            ('profesionales', {'nombre': 'Dra. Ficticia'}),
            ('boxes', {'nombre': 'Box norte'}),
            ('prestaciones', {'nombre': 'Limpieza ficticia', 'duracion_minutos': 30}),
        )
        for tipo, datos in casos:
            with self.subTest(tipo=tipo):
                creado = crear_recurso(
                    self.engine, tipo, datos, actor_id=self.actor_id)
                self.assertTrue(creado['activo'])
                self.assertTrue(creado['id'])
                self.assertEqual(obtener_recurso(self.engine, tipo, creado['id']), creado)
                self.assertIn(creado, listar_recursos(self.engine, tipo, limit=100, offset=0))
                actualizado = actualizar_recurso(
                    self.engine, tipo, creado['id'], {'nombre': 'Nombre editado'},
                    actor_id=self.actor_id)
                self.assertEqual(actualizado['nombre'], 'Nombre editado')
                self.assertEqual(actualizado['id'], creado['id'])
                if tipo == 'prestaciones':
                    self.assertEqual(actualizado['duracion_minutos'], 30)

    def test_listado_aplica_limites_orden_y_incluye_seeds(self):
        profesionales = listar_recursos(self.engine, 'profesionales', limit=1, offset=0)
        self.assertEqual(len(profesionales), 1)
        self.assertEqual(profesionales[0]['id'], 'profesional-A')
        self.assertEqual(profesionales[0]['nombre'], 'Profesional de demostración profesional-A')
        self.assertTrue(profesionales[0]['activo'])
        for parametros in ({'limit': 0}, {'limit': 101}, {'offset': -1}):
            with self.subTest(parametros=parametros), self.assertRaises(ErrorCatalogos):
                listar_recursos(self.engine, 'boxes', **parametros)

    def test_nombres_y_duracion_rechazan_entradas_invalidas(self):
        for nombre in ('', '   ', 'x' * 121, None):
            for tipo, extra in (('profesionales', {}), ('boxes', {}),
                                ('prestaciones', {'duracion_minutos': 30})):
                with self.subTest(nombre=nombre, tipo=tipo), self.assertRaises(ErrorCatalogos):
                    crear_recurso(self.engine, tipo, {'nombre': nombre, **extra})

        for duracion in (None, 0, -1, 1.5, True, '30', 2_147_483_648):
            with self.subTest(duracion=duracion), self.assertRaises(ErrorCatalogos):
                crear_recurso(self.engine, 'prestaciones', {
                    'nombre': 'Prestación ficticia', 'duracion_minutos': duracion})
        limite = crear_recurso(self.engine, 'prestaciones', {
            'nombre': 'Duración límite', 'duracion_minutos': 2_147_483_647})
        self.assertEqual(limite['duracion_minutos'], 2_147_483_647)

    def test_estado_logico_es_idempotente_y_errores_de_referencia_claros(self):
        box = crear_recurso(self.engine, 'boxes', {'nombre': 'Box de prueba'})
        inactivo = actualizar_recurso(
            self.engine, 'boxes', box['id'], {'activo': False}, actor_id=self.actor_id)
        repetido = actualizar_recurso(
            self.engine, 'boxes', box['id'], {'activo': False}, actor_id=self.actor_id)
        self.assertFalse(inactivo['activo'])
        self.assertEqual(repetido, inactivo)
        with self.assertRaises(ErrorCatalogos) as contexto:
            obtener_recurso(self.engine, 'boxes', 'no-existe')
        self.assertEqual(contexto.exception.estado, 404)

    def test_mutaciones_auditadas_solo_con_metadatos_permitidos(self):
        casos = (
            ('profesionales', {'nombre': 'Nombre profesional confidencial'},
             ('profesional.creado', 'profesional.actualizado',
              'profesional.desactivado', 'profesional.reactivado'), 'profesional'),
            ('boxes', {'nombre': 'Box con nombre confidencial'},
             ('box.creado', 'box.actualizado', 'box.desactivado', 'box.reactivado'), 'box'),
            ('prestaciones', {
                'nombre': 'Prestación confidencial', 'duracion_minutos': 37},
             ('prestacion.creada', 'prestacion.actualizada',
              'prestacion.desactivada', 'prestacion.reactivada'), 'prestacion'),
        )
        ids = []
        for tipo, datos, acciones, resource_type in casos:
            creado = crear_recurso(self.engine, tipo, datos, actor_id=self.actor_id)
            ids.append(creado['id'])
            actualizar_recurso(
                self.engine, tipo, creado['id'], {'nombre': 'Nuevo nombre privado'},
                actor_id=self.actor_id)
            actualizar_recurso(
                self.engine, tipo, creado['id'], {'activo': False}, actor_id=self.actor_id)
            actualizar_recurso(
                self.engine, tipo, creado['id'], {'activo': True}, actor_id=self.actor_id)
            with closing(sqlite3.connect(self.ruta)) as conexion:
                eventos = conexion.execute(
                    'SELECT actor_id, action, resource_type, resource_id, result '
                    'FROM eventos_auditoria WHERE resource_id=? ORDER BY id',
                    (creado['id'],)).fetchall()
                contenido = conexion.execute(
                    'SELECT * FROM eventos_auditoria WHERE resource_id=?', (creado['id'],)
                ).fetchall()
                columnas_auditoria = {columna[1] for columna in conexion.execute(
                    'PRAGMA table_info(eventos_auditoria)')}
            self.assertEqual([evento[1] for evento in eventos], list(acciones))
            self.assertTrue(all(
                evento[0] == self.actor_id and evento[2] == resource_type
                and evento[3] == creado['id'] and evento[4] == 'confirmado'
                for evento in eventos))
            self.assertNotIn(datos['nombre'], str(contenido))
            self.assertNotIn('Nuevo nombre privado', str(contenido))
            if tipo == 'prestaciones':
                self.assertEqual(columnas_auditoria, {
                    'id', 'created_at', 'actor_id', 'action', 'resource_type',
                    'resource_id', 'result'})

        self.assertEqual(len(set(ids)), 3)

    def test_fallo_de_auditoria_revierte_alta_y_actualizacion(self):
        with patch('odontologia.catalogos.registrar_evento_session', side_effect=ErrorAuditoria):
            with self.assertRaises(ErrorCatalogos):
                crear_recurso(
                    self.engine, 'profesionales', {'nombre': 'No guardar'},
                    actor_id=self.actor_id)
        self.assertEqual(len(listar_recursos(self.engine, 'profesionales')), 2)

        creado = crear_recurso(
            self.engine, 'boxes', {'nombre': 'Nombre original'}, actor_id=self.actor_id)
        with patch('odontologia.catalogos.registrar_evento_session', side_effect=ErrorAuditoria):
            with self.assertRaises(ErrorCatalogos):
                actualizar_recurso(
                    self.engine, 'boxes', creado['id'], {'nombre': 'No guardar'},
                    actor_id=self.actor_id)
        self.assertEqual(
            obtener_recurso(self.engine, 'boxes', creado['id'])['nombre'], 'Nombre original')


if __name__ == '__main__':
    unittest.main()
