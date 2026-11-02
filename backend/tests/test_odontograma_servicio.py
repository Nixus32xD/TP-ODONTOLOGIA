from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia import crear_turno, inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario
from odontologia.audit import ErrorAuditoria
from odontologia.historia_clinica import ErrorHistoriaClinica
from odontologia.odontograma import (
    consultar_odontograma, crear_odontograma, listar_atenciones_atendidas,
)


class OdontogramaServiceTests(unittest.TestCase):
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
        self.turno_c = crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-B',
            box_id='box-B', inicio=datetime.fromisoformat('2026-11-02T11:00:00-03:00'),
            fin=datetime.fromisoformat('2026-11-02T11:30:00-03:00'))
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        self.admin = crear_primer_administrador(
            self.engine, 'admin.odonto', 'frase-larga-segura-2026')
        self.profesional_a = crear_usuario(
            self.engine, 'profesional.odonto.a', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-A', actor_id=self.admin['id'])
        self.profesional_b = crear_usuario(
            self.engine, 'profesional.odonto.b', 'frase-larga-segura-2026', 'profesional',
            profesional_id='profesional-B', actor_id=self.admin['id'])
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute("UPDATE turnos SET estado='atendido'")
            connection.commit()

    def identidad(self, usuario):
        return {
            'usuario_id': usuario['id'],
            'rol': usuario['rol'],
            'profesional_id': usuario['profesional_id'],
        }

    def test_crea_snapshots_completos_y_consulta_historial_versionado(self):
        primero = crear_odontograma(
            self.engine, paciente_id='paciente-A',
            hallazgos=[{'pieza_fdi': '11', 'superficies': ['M'], 'observacion': 'sintético'}],
            identidad=self.identidad(self.profesional_a))
        segundo = crear_odontograma(
            self.engine, paciente_id='paciente-A',
            hallazgos=[{'pieza_fdi': '11', 'superficies': ['V'], 'observacion': None}],
            identidad=self.identidad(self.profesional_a))
        historial = consultar_odontograma(
            self.engine, 'paciente-A', identidad=self.identidad(self.profesional_a))

        self.assertEqual((primero['version'], segundo['version']), (1, 2))
        self.assertEqual(historial['version_vigente'], 2)
        self.assertEqual([item['id'] for item in historial['items']], [primero['id'], segundo['id']])
        self.assertEqual(historial['items'][0]['hallazgos'][0]['superficie_fdi'], 'M')
        self.assertEqual(historial['items'][1]['hallazgos'][0]['superficie_fdi'], 'V')

    def test_versionado_separado_por_profesional_vinculado(self):
        propia_a = crear_odontograma(
            self.engine, paciente_id='paciente-A', hallazgos=[],
            identidad=self.identidad(self.profesional_a))
        propia_b = crear_odontograma(
            self.engine, paciente_id='paciente-A', hallazgos=[],
            identidad=self.identidad(self.profesional_b))
        consultada_b = consultar_odontograma(
            self.engine, 'paciente-A', identidad=self.identidad(self.profesional_b))

        self.assertEqual(propia_a['version'], 1)
        self.assertEqual(propia_b['version'], 1)
        self.assertEqual([item['id'] for item in consultada_b['items']], [propia_b['id']])

    def test_profesional_solo_accede_a_su_atencion_y_admin_no_ve_contenido(self):
        crear_odontograma(
            self.engine, paciente_id='paciente-A', hallazgos=[],
            identidad=self.identidad(self.profesional_a))
        with self.assertRaises(ErrorHistoriaClinica) as otro_profesional:
            consultar_odontograma(
                self.engine, 'paciente-B',
                identidad=self.identidad(self.profesional_a))
        with self.assertRaises(ErrorHistoriaClinica) as administrador:
            consultar_odontograma(
                self.engine, 'paciente-A', identidad=self.identidad(self.admin))
        self.assertEqual(otro_profesional.exception.estado, 404)
        self.assertEqual(administrador.exception.estado, 403)
        self.assertNotIn('hallazgos', str(administrador.exception))

    def test_rechaza_escritura_si_el_turno_no_esta_atendido(self):
        with closing(sqlite3.connect(self.ruta)) as connection:
            connection.execute("UPDATE turnos SET estado='confirmado' WHERE id=?",
                               (self.turno_a.id,))
            connection.commit()
        with self.assertRaises(ErrorHistoriaClinica) as contexto:
            crear_odontograma(
                self.engine, paciente_id='paciente-A', hallazgos=[],
                identidad=self.identidad(self.profesional_a))
        self.assertEqual(contexto.exception.estado, 404)
        with closing(sqlite3.connect(self.ruta)) as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM versiones_odontograma').fetchone()[0], 0)

    def test_fallo_de_auditoria_reversa_snapshot_y_consulta_falla_cerrada(self):
        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            with self.assertRaises(ErrorHistoriaClinica) as crear_error:
                crear_odontograma(
                    self.engine, paciente_id='paciente-A', hallazgos=[],
                    identidad=self.identidad(self.profesional_a))
            with self.assertRaises(ErrorHistoriaClinica) as consultar_error:
                consultar_odontograma(
                    self.engine, 'paciente-A', identidad=self.identidad(self.profesional_a))
        self.assertEqual(crear_error.exception.estado, 503)
        self.assertEqual(consultar_error.exception.estado, 503)

    def test_lista_paginada_solo_atenciones_atendidas_propias_con_campos_minimos(self):
        primera = listar_atenciones_atendidas(
            self.engine, identidad=self.identidad(self.profesional_a), limit=1, offset=0)
        segunda = listar_atenciones_atendidas(
            self.engine, identidad=self.identidad(self.profesional_a), limit=1, offset=1)
        otra = listar_atenciones_atendidas(
            self.engine, identidad=self.identidad(self.profesional_b))

        self.assertEqual((primera['limit'], primera['offset']), (1, 0))
        self.assertEqual(len(primera['items']), 1)
        self.assertEqual(len(segunda['items']), 0)
        self.assertEqual(len(otra['items']), 2)
        self.assertEqual(set(primera['items'][0]), {
            'turno_id', 'paciente_id', 'paciente_nombre', 'inicio', 'fin',
        })
        self.assertEqual(primera['items'][0]['paciente_id'], 'paciente-A')

    def test_lista_atenciones_deniega_roles_operativos_y_falla_cerrada_sin_auditoria(self):
        with self.assertRaises(ErrorHistoriaClinica) as admin:
            listar_atenciones_atendidas(self.engine, identidad=self.identidad(self.admin))
        self.assertEqual(admin.exception.estado, 403)

        with patch('odontologia.odontograma.registrar_evento_session',
                   side_effect=ErrorAuditoria('fallo sintético')):
            with self.assertRaises(ErrorHistoriaClinica) as error:
                listar_atenciones_atendidas(
                    self.engine, identidad=self.identidad(self.profesional_a))
        self.assertEqual(error.exception.estado, 503)
        with closing(sqlite3.connect(self.ruta)) as connection:
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM versiones_odontograma').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
