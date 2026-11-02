from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sqlalchemy.orm import Session

from odontologia import inicializar_agenda
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.db.models import Turno
from odontologia.consulta_turnos import ErrorConsultaTurnos, listar_turnos


class ConsultaTurnosTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(self.engine.dispose)
        inicio = int(datetime(2026, 10, 15, 12, tzinfo=timezone.utc).timestamp() // 60)
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Turno(id=10, paciente_id='paciente-A', profesional_id='profesional-A',
                      box_id='box-A', inicio_minuto=inicio, fin_minuto=inicio + 30,
                      estado='reservado'),
                Turno(id=11, paciente_id='paciente-B', profesional_id='profesional-A',
                      box_id='box-B', inicio_minuto=inicio, fin_minuto=inicio + 35,
                      estado='confirmado'),
                Turno(id=12, paciente_id='paciente-A', profesional_id='profesional-B',
                      box_id='box-A', inicio_minuto=inicio + 60, fin_minuto=inicio + 90,
                      estado='reservado'),
            ])

    def test_rango_semiaabierto_filtros_y_orden_estable_con_paginacion(self):
        resultado = listar_turnos(
            self.engine, desde=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
            hasta=datetime(2026, 10, 15, 13, tzinfo=timezone.utc),
            profesional_id='profesional-A', estado='confirmado', limit=1, offset=0)
        self.assertEqual((resultado['limit'], resultado['offset']), (1, 0))
        self.assertEqual([turno['id'] for turno in resultado['items']], [11])
        self.assertEqual(resultado['items'][0]['paciente_nombre'],
                         'Paciente de demostración paciente-B')
        self.assertEqual(resultado['items'][0]['version'], 1)
        self.assertNotIn('telefono', resultado['items'][0])

        pagina_dos = listar_turnos(
            self.engine, desde=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
            hasta=datetime(2026, 10, 15, 13, tzinfo=timezone.utc),
            profesional_id='profesional-A', limit=1, offset=1)
        self.assertEqual([turno['id'] for turno in pagina_dos['items']], [11])

    def test_profesional_solo_ve_su_agenda_y_no_puede_delegar_filtro(self):
        resultado = listar_turnos(
            self.engine, desde=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
            hasta=datetime(2026, 10, 15, 13, tzinfo=timezone.utc),
            profesional_vinculado_id='profesional-A')
        self.assertEqual(len(resultado['items']), 2)
        self.assertEqual(set(resultado['items'][0]), {'inicio', 'fin', 'paciente_nombre'})
        self.assertNotIn('version', resultado['items'][0])
        with self.assertRaises(ErrorConsultaTurnos) as otro:
            listar_turnos(
                self.engine, desde=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                hasta=datetime(2026, 10, 15, 13, tzinfo=timezone.utc),
                profesional_id='profesional-B',
                profesional_vinculado_id='profesional-A')
        self.assertEqual((otro.exception.codigo, otro.exception.estado),
                         ('permiso_denegado', 403))

        with self.assertRaises(ErrorConsultaTurnos) as desconocido:
            listar_turnos(
                self.engine, desde=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                hasta=datetime(2026, 10, 15, 13, tzinfo=timezone.utc),
                box_id='box-inexistente')
        self.assertEqual((desconocido.exception.codigo, desconocido.exception.estado),
                         ('recurso_desconocido', 404))

    def test_rechaza_rango_paginacion_estado_y_filtros_invalidos(self):
        desde = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)
        hasta = datetime(2026, 10, 15, 13, tzinfo=timezone.utc)
        invalidos = [
            {'desde': datetime(2026, 10, 15, 12)},
            {'hasta': desde},
            {'hasta': datetime(2026, 11, 20, 13, tzinfo=timezone.utc)},
            {'limit': 101}, {'offset': -1}, {'estado': 'pendiente'},
            {'profesional_id': ' desconocido '},
        ]
        for cambio in invalidos:
            parametros = {'desde': desde, 'hasta': hasta}
            parametros.update(cambio)
            with self.subTest(cambio=cambio), self.assertRaises(ErrorConsultaTurnos):
                listar_turnos(self.engine, **parametros)


if __name__ == '__main__':
    unittest.main()
