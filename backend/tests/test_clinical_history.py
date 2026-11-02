from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sqlalchemy import text
from sqlalchemy.orm import Session

from odontologia.audit import ErrorAuditoria
from odontologia import crear_turno, inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario
from odontologia.db.models import EvolucionClinica
from odontologia.historia_clinica import (
    ErrorHistoriaClinica,
    consultar_historia,
    corregir_evolucion,
    crear_evolucion,
)


class HistoriaClinicaServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        self.turno_a = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T09:30:00-03:00'))
        self.turno_b = crear_turno(
            self.ruta, paciente_id='paciente-B', profesional_id='profesional-B',
            box_id='box-B', inicio=datetime.fromisoformat('2026-11-02T10:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T10:30:00-03:00'))
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        self.admin = crear_primer_administrador(
            self.engine, 'admin.clinica', 'frase-larga-segura-2026')
        self.profesional_a = crear_usuario(
            self.engine, 'profesional.a', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A', actor_id=self.admin['id'])
        self.profesional_b = crear_usuario(
            self.engine, 'profesional.b', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-B', actor_id=self.admin['id'])
        self.recepcion = crear_usuario(
            self.engine, 'recepcion.clinica', 'frase-larga-segura-2026', 'recepcion',
            actor_id=self.admin['id'])
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute("UPDATE turnos SET estado='atendido'")
            conexion.commit()

    def identidad(self, usuario):
        return {
            'usuario_id': usuario['id'],
            'rol': usuario['rol'],
            'profesional_id': usuario['profesional_id'],
        }

    def test_crear_y_consultar_evolucion_de_atencion_propia(self):
        evolucion = crear_evolucion(
            self.engine, paciente_id='paciente-A', turno_id=self.turno_a.id,
            nota='  Control ficticio sin hallazgos.  ', identidad=self.identidad(self.profesional_a))

        self.assertEqual(evolucion['nota'], 'Control ficticio sin hallazgos.')
        historia = consultar_historia(
            self.engine, 'paciente-A', identidad=self.identidad(self.profesional_a))
        self.assertEqual([item['id'] for item in historia['items']], [evolucion['id']])

    def test_profesional_no_ve_evolucion_de_otro_profesional(self):
        evolucion = crear_evolucion(
            self.engine, paciente_id='paciente-A', turno_id=self.turno_a.id,
            nota='Nota privada ficticia.', identidad=self.identidad(self.profesional_a))

        with self.assertRaises(ErrorHistoriaClinica) as contexto:
            consultar_historia(
                self.engine, 'paciente-A', identidad=self.identidad(self.profesional_b))

        self.assertEqual(contexto.exception.estado, 404)
        self.assertNotIn('Nota privada ficticia.', str(contexto.exception))
        self.assertIsNotNone(evolucion['id'])

    def test_registro_rechaza_turno_no_atendido_o_de_otro_profesional(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute("UPDATE turnos SET estado='confirmado' WHERE id=?", (self.turno_a.id,))
            conexion.commit()

        with self.assertRaises(ErrorHistoriaClinica):
            crear_evolucion(
                self.engine, paciente_id='paciente-A', turno_id=self.turno_a.id,
                nota='No debe guardarse.', identidad=self.identidad(self.profesional_a))
        with self.assertRaises(ErrorHistoriaClinica):
            crear_evolucion(
                self.engine, paciente_id='paciente-A', turno_id=self.turno_b.id,
                nota='Tampoco debe guardarse.', identidad=self.identidad(self.profesional_a))

        with Session(self.engine) as session:
            self.assertEqual(session.query(EvolucionClinica).count(), 0)

    def test_corregir_evolucion_agrega_fila_y_preserva_original(self):
        original = crear_evolucion(
            self.engine, paciente_id='paciente-A', turno_id=self.turno_a.id,
            nota='Nota original ficticia.', identidad=self.identidad(self.profesional_a))

        correccion = corregir_evolucion(
            self.engine, evolucion_id=original['id'], nota='Nota corregida ficticia.',
            identidad=self.identidad(self.profesional_a))

        self.assertEqual(correccion['corrige_a_id'], original['id'])
        with Session(self.engine) as session:
            rows = session.query(EvolucionClinica).order_by(EvolucionClinica.created_at).all()
        self.assertEqual([row.nota for row in rows],
                         ['Nota original ficticia.', 'Nota corregida ficticia.'])

    def test_acceso_admin_y_recepcion_se_deniega_y_deja_evento_sin_contenido(self):
        for usuario in (self.admin, self.recepcion):
            with self.subTest(rol=usuario['rol']):
                with self.assertRaises(ErrorHistoriaClinica) as contexto:
                    consultar_historia(
                        self.engine, 'paciente-A', identidad=self.identidad(usuario))
                self.assertEqual(contexto.exception.estado, 403)
                with self.assertRaises(ErrorHistoriaClinica):
                    crear_evolucion(
                        self.engine, paciente_id='paciente-A', turno_id=self.turno_a.id,
                        nota='Texto denegado y no persistido.', identidad=self.identidad(usuario))

        with Session(self.engine) as session:
            eventos = session.execute(text(
                "SELECT action, result FROM eventos_auditoria WHERE action='historia.denegada'"
            )).all()
            self.assertEqual(len(eventos), 4)
            self.assertTrue(all(resultado == 'rechazado' for _accion, resultado in eventos))
            self.assertEqual(session.query(EvolucionClinica).count(), 0)

    def test_nota_acepta_limite_y_rechaza_vacio_o_exceso(self):
        limite = crear_evolucion(
            self.engine, paciente_id='paciente-A', turno_id=self.turno_a.id,
            nota='x' * 5000, identidad=self.identidad(self.profesional_a))
        self.assertEqual(len(limite['nota']), 5000)
        for nota in ('   ', 'x' * 5001):
            with self.subTest(longitud=len(nota)), self.assertRaises(ErrorHistoriaClinica):
                crear_evolucion(
                    self.engine, paciente_id='paciente-A', turno_id=self.turno_a.id,
                    nota=nota, identidad=self.identidad(self.profesional_a))

    def test_profesional_desactivado_no_consulta_historia(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('UPDATE profesionales SET activo=0 WHERE id=?', ('profesional-A',))
            conexion.commit()
        with self.assertRaises(ErrorHistoriaClinica) as contexto:
            consultar_historia(
                self.engine, 'paciente-A', identidad=self.identidad(self.profesional_a))
        self.assertEqual(contexto.exception.estado, 403)

    def test_falla_cerrado_si_no_puede_auditar_lectura_o_escritura(self):
        with patch('odontologia.historia_clinica.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo de auditoría')):
            with self.assertRaises(ErrorHistoriaClinica) as escritura:
                crear_evolucion(
                    self.engine, paciente_id='paciente-A', turno_id=self.turno_a.id,
                    nota='Se debe revertir.', identidad=self.identidad(self.profesional_a))
            self.assertEqual(escritura.exception.estado, 503)
            with self.assertRaises(ErrorHistoriaClinica) as lectura:
                consultar_historia(
                    self.engine, 'paciente-A', identidad=self.identidad(self.profesional_a))
            self.assertEqual(lectura.exception.estado, 503)

        with Session(self.engine) as session:
            self.assertEqual(session.query(EvolucionClinica).count(), 0)


if __name__ == '__main__':
    unittest.main()
