from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sqlalchemy.orm import Session

from odontologia import crear_turno, inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario
from odontologia.audit import ErrorAuditoria
from odontologia.db.models import Prestacion
from odontologia.historia_clinica import ErrorHistoriaClinica
from odontologia.odontograma import (
    ErrorPlanTratamiento,
    cambiar_estado_plan_tratamiento,
    consultar_planes_tratamiento,
    crear_plan_tratamiento,
)


class PlanesTratamientoServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        self.turno = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        self.admin = crear_primer_administrador(
            self.engine, 'admin.planes', 'frase-larga-segura-2026')
        self.profesional = crear_usuario(
            self.engine, 'profesional.planes', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A', actor_id=self.admin['id'])
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Prestacion(id='prestacion-activa-A', nombre='Prestación sintética A',
                           duracion_minutos=30, activo=True),
                Prestacion(id='prestacion-activa-B', nombre='Prestación sintética B',
                           duracion_minutos=30, activo=True),
                Prestacion(id='prestacion-inactiva', nombre='Prestación sintética inactiva',
                           duracion_minutos=30, activo=False),
            ])
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute("UPDATE turnos SET estado='atendido' WHERE id=?", (self.turno.id,))
            connection.commit()

    def identidad(self):
        return {
            'usuario_id': self.profesional['id'],
            'rol': self.profesional['rol'],
            'profesional_id': self.profesional['profesional_id'],
        }

    def test_crea_etapas_en_orden_sin_precio_ni_turno_y_consulta_referencias(self):
        plan = crear_plan_tratamiento(
            self.engine, paciente_id='paciente-A',
            prestaciones_ids=['prestacion-activa-B', 'prestacion-activa-A'],
            identidad=self.identidad())
        historial = consultar_planes_tratamiento(
            self.engine, 'paciente-A', identidad=self.identidad())

        self.assertEqual(plan['estado'], 'propuesto')
        self.assertEqual([etapa['orden'] for etapa in plan['etapas']], [1, 2])
        self.assertEqual([etapa['prestacion_id'] for etapa in plan['etapas']],
                         ['prestacion-activa-B', 'prestacion-activa-A'])
        self.assertEqual(historial['items'][0]['id'], plan['id'])
        self.assertNotIn('precio', str(plan).lower())
        self.assertNotIn('turno_id', plan)

    def test_rechaza_prestacion_ausente_o_inactiva_sin_plan_parcial(self):
        for prestaciones in (
                ['prestacion-ausente'], ['prestacion-activa-A', 'prestacion-inactiva']):
            with self.subTest(prestaciones=prestaciones), self.assertRaises(ErrorPlanTratamiento):
                crear_plan_tratamiento(
                    self.engine, paciente_id='paciente-A',
                    prestaciones_ids=prestaciones, identidad=self.identidad())
        with closing(sqlite3.connect(self.ruta)) as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM planes_tratamiento').fetchone()[0], 0)

    def test_referencias_historicas_se_conservan_si_prestacion_se_desactiva(self):
        plan = crear_plan_tratamiento(
            self.engine, paciente_id='paciente-A',
            prestaciones_ids=['prestacion-activa-A'], identidad=self.identidad())
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute(
                "UPDATE prestaciones SET activo=0 WHERE id='prestacion-activa-A'")
            connection.commit()
        historial = consultar_planes_tratamiento(
            self.engine, 'paciente-A', identidad=self.identidad())
        self.assertEqual(historial['items'][0]['id'], plan['id'])
        self.assertEqual(historial['items'][0]['etapas'][0]['prestacion_id'],
                         'prestacion-activa-A')

    def test_requiere_profesional_autorizado_y_atencion_atendida(self):
        with self.assertRaises(ErrorHistoriaClinica):
            consultar_planes_tratamiento(
                self.engine, 'paciente-A', identidad={
                    'usuario_id': self.admin['id'], 'rol': 'administrador'})
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute("UPDATE turnos SET estado='confirmado' WHERE id=?",
                               (self.turno.id,))
            connection.commit()
        with self.assertRaises(ErrorHistoriaClinica):
            crear_plan_tratamiento(
                self.engine, paciente_id='paciente-A',
                prestaciones_ids=['prestacion-activa-A'], identidad=self.identidad())

    def test_vinculo_profesional_actual_no_acepta_identidad_anterior(self):
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute(
                "INSERT INTO profesionales(id, nombre, activo) "
                "VALUES ('profesional-C', 'Profesional sintético C', 1)")
            connection.execute(
                "UPDATE usuarios SET profesional_id='profesional-C' WHERE id=?",
                (self.profesional['id'],))
            connection.commit()
        with self.assertRaises(ErrorHistoriaClinica) as contexto:
            consultar_planes_tratamiento(
                self.engine, 'paciente-A', identidad=self.identidad())
        self.assertEqual(contexto.exception.estado, 403)

    def test_fallo_de_auditoria_revierte_alta_y_transicion_y_falla_cerrado_al_leer(self):
        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            with self.assertRaises(ErrorHistoriaClinica) as alta_error:
                crear_plan_tratamiento(
                    self.engine, paciente_id='paciente-A',
                    prestaciones_ids=['prestacion-activa-A'], identidad=self.identidad())
        self.assertEqual(alta_error.exception.estado, 503)
        with closing(sqlite3.connect(self.ruta)) as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM planes_tratamiento').fetchone()[0], 0)

        plan = crear_plan_tratamiento(
            self.engine, paciente_id='paciente-A',
            prestaciones_ids=['prestacion-activa-A'], identidad=self.identidad())
        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            with self.assertRaises(ErrorHistoriaClinica) as cambio_error:
                cambiar_estado_plan_tratamiento(
                    self.engine, plan_id=plan['id'], estado='en_curso',
                    identidad=self.identidad())
            with self.assertRaises(ErrorHistoriaClinica) as lectura_error:
                consultar_planes_tratamiento(
                    self.engine, 'paciente-A', identidad=self.identidad())
        self.assertEqual(cambio_error.exception.estado, 503)
        self.assertEqual(lectura_error.exception.estado, 503)
        self.assertEqual(consultar_planes_tratamiento(
            self.engine, 'paciente-A', identidad=self.identidad())['items'][0]['estado'],
            'propuesto')

    def test_transiciones_permitidas_y_cancelacion_desde_estados_no_terminales(self):
        with closing(sqlite3.connect(self.ruta)) as connection:
            turnos_antes = connection.execute('SELECT COUNT(*) FROM turnos').fetchone()[0]
        plan = crear_plan_tratamiento(
            self.engine, paciente_id='paciente-A',
            prestaciones_ids=['prestacion-activa-A'], identidad=self.identidad())
        en_curso = cambiar_estado_plan_tratamiento(
            self.engine, plan_id=plan['id'], estado='en_curso', identidad=self.identidad())
        completado = cambiar_estado_plan_tratamiento(
            self.engine, plan_id=plan['id'], estado='completado', identidad=self.identidad())
        cancelado = crear_plan_tratamiento(
            self.engine, paciente_id='paciente-A',
            prestaciones_ids=['prestacion-activa-A'], identidad=self.identidad())
        cancelado = cambiar_estado_plan_tratamiento(
            self.engine, plan_id=cancelado['id'], estado='cancelado',
            identidad=self.identidad())
        otro = crear_plan_tratamiento(
            self.engine, paciente_id='paciente-A',
            prestaciones_ids=['prestacion-activa-A'], identidad=self.identidad())
        otro_en_curso = cambiar_estado_plan_tratamiento(
            self.engine, plan_id=otro['id'], estado='en_curso', identidad=self.identidad())
        otro_cancelado = cambiar_estado_plan_tratamiento(
            self.engine, plan_id=otro['id'], estado='cancelado', identidad=self.identidad())

        self.assertEqual((en_curso['estado'], completado['estado']), ('en_curso', 'completado'))
        self.assertEqual((cancelado['estado'], otro_cancelado['estado']), ('cancelado', 'cancelado'))
        self.assertEqual(otro_en_curso['estado'], 'en_curso')
        with closing(sqlite3.connect(self.ruta)) as connection:
            self.assertEqual(
                connection.execute('SELECT COUNT(*) FROM turnos').fetchone()[0], turnos_antes)

    def test_transiciones_prohibidas_responden_409_y_conservan_estado(self):
        plan = crear_plan_tratamiento(
            self.engine, paciente_id='paciente-A',
            prestaciones_ids=['prestacion-activa-A'], identidad=self.identidad())
        for estado in ('completado', 'desconocido'):
            with self.subTest(estado=estado), self.assertRaises(ErrorPlanTratamiento) as contexto:
                cambiar_estado_plan_tratamiento(
                    self.engine, plan_id=plan['id'], estado=estado,
                    identidad=self.identidad())
            self.assertEqual(contexto.exception.estado, 409)
        self.assertEqual(consultar_planes_tratamiento(
            self.engine, 'paciente-A', identidad=self.identidad())['items'][0]['estado'],
            'propuesto')

        en_curso = cambiar_estado_plan_tratamiento(
            self.engine, plan_id=plan['id'], estado='en_curso', identidad=self.identidad())
        completado = cambiar_estado_plan_tratamiento(
            self.engine, plan_id=plan['id'], estado='completado', identidad=self.identidad())
        with self.assertRaises(ErrorPlanTratamiento) as terminal:
            cambiar_estado_plan_tratamiento(
                self.engine, plan_id=plan['id'], estado='cancelado', identidad=self.identidad())
        self.assertEqual(terminal.exception.estado, 409)
        self.assertEqual(completado['estado'], 'completado')


if __name__ == '__main__':
    unittest.main()
