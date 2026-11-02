from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from sqlalchemy import create_engine

from odontologia import inicializar_agenda
from odontologia import crear_turno
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.auth.almacenamiento import crear_engine_autenticacion
from odontologia.auth.usuarios import crear_primer_administrador
from odontologia.audit import listar_eventos
from odontologia.disponibilidad import (
    crear_bloqueo,
    eliminar_bloqueo,
    eliminar_excepcion,
    ErrorDisponibilidad,
    guardar_excepcion,
    guardar_horario,
    listar_bloqueos,
    obtener_excepcion,
    obtener_horario,
)


class ServiciosDisponibilidadSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)
        migrar_sqlite(self.ruta)
        self.engine = create_engine(f'sqlite:///{self.ruta.as_posix()}')
        self.addCleanup(self.engine.dispose)
        auth_engine = crear_engine_autenticacion('sqlite', None, self.ruta)
        self.addCleanup(auth_engine.dispose)
        self.admin = crear_primer_administrador(
            auth_engine, 'admin.test', 'frase-larga-segura-prueba-2026')

    def test_horario_semanal_consulta_reemplaza_y_puede_cerrar(self):
        inicial = obtener_horario(self.engine, 'profesional', 'profesional-A')
        self.assertTrue(all(not tramos for tramos in inicial['dias'].values()))

        esperado = {'1': [
            {'inicio': '09:00', 'fin': '12:00'},
            {'inicio': '12:00', 'fin': '13:00'},
        ]}
        self.assertEqual(
            guardar_horario(self.engine, 'profesional', 'profesional-A', esperado)['dias']['1'],
            esperado['1'])
        self.assertEqual(
            obtener_horario(self.engine, 'profesional', 'profesional-A')['dias']['1'],
            esperado['1'])

        cerrado = guardar_horario(self.engine, 'profesional', 'profesional-A', {})
        self.assertTrue(all(not tramos for tramos in cerrado['dias'].values()))
        with closing(sqlite3.connect(self.ruta)) as conexion:
            self.assertEqual(conexion.execute(
                "SELECT COUNT(*) FROM horarios_semanales WHERE profesional_id='profesional-A'"
            ).fetchone(), (0,))

    def test_excepcion_vacia_crear_reemplazar_consultar_y_eliminar(self):
        self.assertIsNone(obtener_excepcion(
            self.engine, 'box', 'box-A', '2026-11-03'))
        creada = guardar_excepcion(
            self.engine, 'box', 'box-A', '2026-11-03', [
                {'inicio': '09:00', 'fin': '12:00'},
            ])
        self.assertEqual(creada['tramos'], [{'inicio': '09:00', 'fin': '12:00'}])
        self.assertEqual(obtener_excepcion(
            self.engine, 'box', 'box-A', '2026-11-03'), creada)

        actualizada = guardar_excepcion(
            self.engine, 'box', 'box-A', '2026-11-03', [])
        self.assertEqual(actualizada['id'], creada['id'])
        self.assertEqual(actualizada['tramos'], [])
        self.assertEqual(obtener_excepcion(
            self.engine, 'box', 'box-A', '2026-11-03'), actualizada)

        eliminar_excepcion(self.engine, 'box', 'box-A', '2026-11-03')
        self.assertIsNone(obtener_excepcion(
            self.engine, 'box', 'box-A', '2026-11-03'))

    def test_bloqueo_unico_recurso_utc_paginado_y_eliminable(self):
        primero = crear_bloqueo(
            self.engine, 'profesional', 'profesional-A',
            datetime.fromisoformat('2026-11-02T09:00:00-03:00'),
            datetime.fromisoformat('2026-11-02T10:00:00-03:00'))
        segundo = crear_bloqueo(
            self.engine, 'box', 'box-A',
            datetime.fromisoformat('2026-11-03T09:00:00-03:00'),
            datetime.fromisoformat('2026-11-03T10:00:00-03:00'))

        pagina = listar_bloqueos(self.engine, limit=1, offset=0)
        siguiente = listar_bloqueos(self.engine, limit=1, offset=1)
        self.assertEqual(pagina[0]['id'], primero['id'])
        self.assertEqual(siguiente[0]['id'], segundo['id'])
        self.assertEqual(pagina[0]['inicio'].tzinfo, timezone.utc)
        self.assertEqual(pagina[0]['tipo_recurso'], 'profesional')

        eliminar_bloqueo(self.engine, primero['id'])
        self.assertEqual([b['id'] for b in listar_bloqueos(self.engine)], [segundo['id']])

    def test_unknown_resource_and_invalid_pagination_are_rejected(self):
        with self.assertRaises(ErrorDisponibilidad) as error:
            obtener_horario(self.engine, 'profesional', 'profesional-desconocido')
        self.assertEqual(error.exception.codigo, 'recurso_desconocido')
        for kwargs in ({'limit': 0}, {'limit': 101}, {'offset': -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ErrorDisponibilidad):
                listar_bloqueos(self.engine, **kwargs)

    def test_readme_documenta_rutas_y_supuestos_iguales_a_salidas(self):
        manual = (Path(__file__).resolve().parents[2] / 'backend' / 'README.md').read_text(encoding='utf-8')
        self.assertIn(
            '`GET/PUT /horarios/{tipo_recurso}/{recurso_id}`', manual,
            str(Path(__file__).resolve().parents[2] / 'backend' / 'README.md'))
        self.assertIn('`GET/PUT/DELETE /horarios/{tipo_recurso}/{recurso_id}/excepciones/{fecha}`', manual)
        self.assertIn('`GET/POST /bloqueos` más `DELETE /bloqueos/{bloqueo_id}`', manual)
        self.assertIn('exactamente a un profesional o a un box', manual.lower())
        horario = obtener_horario(self.engine, 'box', 'box-A')
        self.assertEqual(set(horario), {'tipo_recurso', 'recurso_id', 'dias'})
        self.assertEqual(set(horario['dias']), {str(dia) for dia in range(1, 8)})
        excepcion = guardar_excepcion(self.engine, 'box', 'box-A', '2026-11-03', [])
        self.assertEqual(set(excepcion), {'id', 'tipo_recurso', 'recurso_id', 'fecha', 'tramos'})
        bloqueo = crear_bloqueo(
            self.engine, 'box', 'box-A', datetime.fromisoformat('2026-11-03T09:00:00-03:00'),
            datetime.fromisoformat('2026-11-03T10:00:00-03:00'))
        self.assertEqual(set(bloqueo), {'id', 'tipo_recurso', 'recurso_id', 'inicio', 'fin'})

    def _turno(self, fecha):
        inicio = datetime.fromisoformat(f'{fecha}T12:00:00+00:00')
        return crear_turno(
            self.ruta, paciente_id='paciente-A', profesional_id='profesional-A',
            box_id='box-A', inicio=inicio,
            fin=inicio.replace(minute=30), actor_id=self.admin['id'])

    def _cambiar_estado_turno(self, turno_id, estado):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('UPDATE turnos SET estado=? WHERE id=?', (estado, turno_id))
            conexion.commit()

    def test_turno_terminal_no_impide_reemplazar_horario(self):
        horario = {'1': [{'inicio': '09:00', 'fin': '12:00'}]}
        guardar_horario(self.engine, 'profesional', 'profesional-A', horario)
        guardar_horario(self.engine, 'box', 'box-A', horario)
        turno = self._turno('2026-11-02')
        self._cambiar_estado_turno(turno.id, 'cancelado')

        actualizado = guardar_horario(self.engine, 'profesional', 'profesional-A', {
            '1': [{'inicio': '10:00', 'fin': '12:00'}]})

        self.assertEqual(actualizado['dias']['1'], [{'inicio': '10:00', 'fin': '12:00'}])

    def test_turno_terminal_no_impide_cerrar_excepcion(self):
        horario = {'1': [{'inicio': '09:00', 'fin': '12:00'}]}
        guardar_horario(self.engine, 'profesional', 'profesional-A', horario)
        guardar_horario(self.engine, 'box', 'box-A', horario)
        turno = self._turno('2026-11-02')
        excepcion = guardar_excepcion(
            self.engine, 'profesional', 'profesional-A', '2026-11-02', horario['1'])
        self._cambiar_estado_turno(turno.id, 'atendido')

        actualizada = guardar_excepcion(
            self.engine, 'profesional', 'profesional-A', '2026-11-02', [])

        self.assertEqual(actualizada['id'], excepcion['id'])
        self.assertEqual(actualizada['tramos'], [])

    def test_turno_terminal_no_impide_crear_bloqueo(self):
        horario = {'1': [{'inicio': '09:00', 'fin': '12:00'}]}
        guardar_horario(self.engine, 'profesional', 'profesional-A', horario)
        guardar_horario(self.engine, 'box', 'box-A', horario)
        turno = self._turno('2026-11-02')
        self._cambiar_estado_turno(turno.id, 'ausente')

        bloqueo = crear_bloqueo(
            self.engine, 'box', 'box-A',
            datetime.fromisoformat('2026-11-02T12:15:00+00:00'),
            datetime.fromisoformat('2026-11-02T12:45:00+00:00'))

        self.assertEqual(len(listar_bloqueos(self.engine)), 1)
        self.assertEqual(bloqueo['tipo_recurso'], 'box')

    def test_cambio_horario_rechaza_turnos_pasados_y_futuros_sin_evento(self):
        horario = {'1': [{'inicio': '09:00', 'fin': '12:00'}]}
        guardar_horario(self.engine, 'profesional', 'profesional-A', horario,
                        actor_id=self.admin['id'])
        guardar_horario(self.engine, 'box', 'box-A', horario, actor_id=self.admin['id'])
        self._turno('2026-10-26')
        self._turno('2026-11-09')
        with self.assertRaises(ErrorDisponibilidad) as error:
            guardar_horario(self.engine, 'profesional', 'profesional-A', {
                '1': [{'inicio': '10:00', 'fin': '12:00'}]})
        self.assertEqual(error.exception.codigo, 'turnos_afectados')
        self.assertEqual(obtener_horario(
            self.engine, 'profesional', 'profesional-A')['dias']['1'], horario['1'])
        eventos = listar_eventos(self.engine)
        self.assertEqual(sum(e['action'] == 'horario.actualizado' for e in eventos), 2)

    def test_reemplazo_de_excepcion_vacia_no_invalida_turno_ni_audita(self):
        horario = {'1': [{'inicio': '09:00', 'fin': '12:00'}]}
        guardar_horario(self.engine, 'profesional', 'profesional-A', horario,
                        actor_id=self.admin['id'])
        guardar_horario(self.engine, 'box', 'box-A', horario, actor_id=self.admin['id'])
        self._turno('2026-11-02')
        excepcion = guardar_excepcion(
            self.engine, 'profesional', 'profesional-A', '2026-11-02', horario['1'],
            actor_id=self.admin['id'])
        eventos_antes = len(listar_eventos(self.engine))
        with self.assertRaises(ErrorDisponibilidad) as error:
            guardar_excepcion(
                self.engine, 'profesional', 'profesional-A', '2026-11-02', [],
                actor_id=self.admin['id'])
        self.assertEqual(error.exception.codigo, 'turnos_afectados')
        self.assertEqual(obtener_excepcion(
            self.engine, 'profesional', 'profesional-A', '2026-11-02'), excepcion)
        self.assertEqual(len(listar_eventos(self.engine)), eventos_antes)

    def test_eliminar_excepcion_no_cierra_dia_con_turno_pasado(self):
        guardar_horario(self.engine, 'profesional', 'profesional-A', {
            '1': [{'inicio': '09:00', 'fin': '12:00'}]}, actor_id=self.admin['id'])
        excepcion = guardar_excepcion(
            self.engine, 'box', 'box-A', '2026-10-26', [
                {'inicio': '09:00', 'fin': '12:00'}], actor_id=self.admin['id'])
        self._turno('2026-10-26')
        eventos_antes = len(listar_eventos(self.engine))
        with self.assertRaises(ErrorDisponibilidad) as error:
            eliminar_excepcion(self.engine, 'box', 'box-A', '2026-10-26')
        self.assertEqual(error.exception.codigo, 'turnos_afectados')
        self.assertEqual(obtener_excepcion(
            self.engine, 'box', 'box-A', '2026-10-26'), excepcion)
        self.assertEqual(len(listar_eventos(self.engine)), eventos_antes)

    def test_bloqueo_que_toca_turno_pasado_se_rechaza_sin_guardar(self):
        horario = {'1': [{'inicio': '09:00', 'fin': '12:00'}]}
        guardar_horario(self.engine, 'profesional', 'profesional-A', horario,
                        actor_id=self.admin['id'])
        guardar_horario(self.engine, 'box', 'box-A', horario, actor_id=self.admin['id'])
        self._turno('2026-10-26')
        eventos_antes = len(listar_eventos(self.engine))
        with self.assertRaises(ErrorDisponibilidad) as error:
            crear_bloqueo(
                self.engine, 'box', 'box-A',
                datetime.fromisoformat('2026-10-26T12:15:00+00:00'),
                datetime.fromisoformat('2026-10-26T12:45:00+00:00'))
        self.assertEqual(error.exception.codigo, 'turnos_afectados')
        self.assertEqual(listar_bloqueos(self.engine), [])
        self.assertEqual(len(listar_eventos(self.engine)), eventos_antes)


if __name__ == '__main__':
    unittest.main()
