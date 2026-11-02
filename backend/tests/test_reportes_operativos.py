from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite
from odontologia.db.models import (
    BloqueoAgenda,
    CargoFinanciero,
    CobroFinanciero,
    ExcepcionHorario,
    HorarioSemanal,
    ReversionCobro,
    TramoExcepcion,
    Turno,
)
from odontologia.reportes import (
    _minuto_utc,
    calcular_minutos_disponibles,
    consultar_reporte_agenda,
    consultar_reporte_financiero,
    normalizar_rango_local,
)
from odontologia.pacientes import crear_paciente


class ReportesAgendaTests(unittest.TestCase):
    def test_rango_local_semiabierto_admite_31_dias_y_rechaza_formato_o_limite(self):
        self.assertEqual(
            normalizar_rango_local('2026-11-02', '2026-12-03'),
            (date(2026, 11, 2), date(2026, 12, 3)),
        )
        for desde, hasta in (
            ('2026-11-02', '2026-12-04'),
            ('2026-11-03', '2026-11-02'),
            ('2026-11-02', '2026-11-02'),
            ('2026-2-02', '2026-11-03'),
        ):
            with self.subTest(desde=desde, hasta=hasta), self.assertRaises(ValueError):
                normalizar_rango_local(desde, hasta)

    def test_horario_local_respeta_el_cambio_historico_de_zona(self):
        instante = datetime.fromtimestamp(
            _minuto_utc(date(1992, 10, 18), 540) * 60, timezone.utc)
        self.assertEqual(instante.isoformat(), '1992-10-18T11:00:00+00:00')

    def test_disponibilidad_resta_intersecciones_de_bloqueos(self):
        self.assertEqual(
            calcular_minutos_disponibles(
                [(540, 720), (780, 900)], [(600, 630), (840, 960)]),
            210,
        )
        self.assertEqual(calcular_minutos_disponibles([(540, 600)], [(500, 700)]), 0)

    def test_excepcion_vacia_cierra_dia_y_capacidad_cero_no_divide(self):
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                with Session(engine) as session, session.begin():
                    session.add(HorarioSemanal(
                        id='horario-box', profesional_id=None, box_id='box-A', dia_iso=1,
                        inicio_minuto_local=540, fin_minuto_local=600))
                    session.add(ExcepcionHorario(
                        id='excepcion-box-vacia', profesional_id=None, box_id='box-A',
                        fecha_local=date(2026, 11, 2)))
                reporte = consultar_reporte_agenda(engine, '2026-11-02', '2026-11-03')
                boxes = reporte['dias'][0]['recursos']['boxes']
                self.assertEqual(boxes[0]['minutos_disponibles'], 0)
                self.assertIsNone(boxes[0]['ocupacion_porcentaje'])
            finally:
                engine.dispose()

    def test_reporte_separa_estados_y_calcula_capacidad_con_excepcion_y_bloqueos(self):
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                with Session(engine) as session, session.begin():
                    session.add(HorarioSemanal(
                        id='horario-prof', profesional_id='profesional-A', box_id=None,
                        dia_iso=1, inicio_minuto_local=540, fin_minuto_local=720))
                    excepcion = ExcepcionHorario(
                        id='excepcion-box', profesional_id=None, box_id='box-A',
                        fecha_local=date(2026, 11, 2))
                    session.add(excepcion)
                    session.add(TramoExcepcion(
                        id='tramo-box', excepcion_id=excepcion.id,
                        inicio_minuto_local=600, fin_minuto_local=720))
                    session.add_all([
                        BloqueoAgenda(
                            id='bloqueo-prof', profesional_id='profesional-A', box_id=None,
                            inicio_minuto=_utc_minute('2026-11-02T13:00:00+00:00'),
                            fin_minuto=_utc_minute('2026-11-02T13:30:00+00:00')),
                        BloqueoAgenda(
                            id='bloqueo-box', profesional_id=None, box_id='box-A',
                            inicio_minuto=_utc_minute('2026-11-02T14:00:00+00:00'),
                            fin_minuto=_utc_minute('2026-11-02T14:30:00+00:00')),
                    ])
                    session.add_all([
                        _turno(1, '2026-11-02T12:30:00+00:00', '2026-11-02T13:00:00+00:00', 'reservado'),
                        _turno(2, '2026-11-02T13:30:00+00:00', '2026-11-02T14:00:00+00:00', 'confirmado'),
                        _turno(3, '2026-11-02T14:00:00+00:00', '2026-11-02T14:30:00+00:00', 'atendido'),
                        _turno(4, '2026-11-02T14:30:00+00:00', '2026-11-02T15:00:00+00:00', 'cancelado'),
                    ])

                reporte = consultar_reporte_agenda(engine, '2026-11-02', '2026-11-03')
                dia = reporte['dias'][0]
                self.assertEqual(dia['fecha'], '2026-11-02')
                self.assertEqual(dia['estados'], {
                    'reservado': {'cantidad': 1, 'minutos': 30},
                    'confirmado': {'cantidad': 1, 'minutos': 30},
                    'atendido': {'cantidad': 1, 'minutos': 30},
                    'ausente': {'cantidad': 0, 'minutos': 0},
                    'cancelado': {'cantidad': 1, 'minutos': 30},
                })
                profesional = dia['recursos']['profesionales'][0]
                self.assertEqual(profesional['minutos_disponibles'], 150)
                self.assertEqual(profesional['minutos_ocupados'], 60)
                box = dia['recursos']['boxes'][0]
                self.assertEqual(box['minutos_disponibles'], 90)
                self.assertEqual(box['minutos_ocupados'], 30)
                self.assertNotIn('paciente_id', str(reporte))
            finally:
                engine.dispose()

    def test_reporte_financiero_agrupa_fecha_local_y_conserva_saldos_exactos(self):
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            try:
                paciente = crear_paciente(engine, nombre='Paciente financiero sintético')
                with Session(engine) as session, session.begin():
                    session.add_all([
                        CargoFinanciero(
                            id='cargo-anterior', paciente_id=paciente['id'], monto_centavos=10000,
                            concepto='No se exporta', created_at=_fecha_hora('2026-11-01T23:00:00+00:00')),
                        CargoFinanciero(
                            id='cargo-dentro', paciente_id=paciente['id'], monto_centavos=5000,
                            concepto='Tampoco se exporta', created_at=_fecha_hora('2026-11-02T13:00:00+00:00')),
                        CargoFinanciero(
                            id='cargo-fuera', paciente_id=paciente['id'], monto_centavos=700,
                            concepto='Fuera del rango', created_at=_fecha_hora('2026-11-05T04:00:00+00:00')),
                        CobroFinanciero(
                            id='cobro-anterior', cargo_id='cargo-anterior', monto_centavos=2000,
                            created_at=_fecha_hora('2026-11-01T23:10:00+00:00')),
                        CobroFinanciero(
                            id='cobro-dentro', cargo_id='cargo-dentro', monto_centavos=3000,
                            created_at=_fecha_hora('2026-11-02T14:00:00+00:00')),
                        ReversionCobro(
                            id='reversion-1', cobro_id='cobro-dentro', monto_centavos=500,
                            motivo='Privado', created_at=_fecha_hora('2026-11-02T15:00:00+00:00')),
                        ReversionCobro(
                            id='reversion-2', cobro_id='cobro-dentro', monto_centavos=400,
                            motivo='Privado también', created_at=_fecha_hora('2026-11-03T14:00:00+00:00')),
                    ])

                reporte = consultar_reporte_financiero(engine, '2026-11-02', '2026-11-04')
                self.assertEqual(reporte['saldo_apertura_ars'], '80.00')
                primero, segundo = reporte['dias']
                self.assertEqual(primero['fecha'], '2026-11-02')
                self.assertEqual(primero['cargos'], {'cantidad': 1, 'importe_ars': '50.00'})
                self.assertEqual(primero['cobros'], {'cantidad': 1, 'importe_ars': '30.00'})
                self.assertEqual(primero['reversiones'], {'cantidad': 1, 'importe_ars': '5.00'})
                self.assertEqual(primero['neto_ars'], '25.00')
                self.assertEqual(primero['saldo_cierre_ars'], '105.00')
                self.assertEqual(segundo['neto_ars'], '-4.00')
                self.assertEqual(segundo['saldo_cierre_ars'], '109.00')
                self.assertNotIn('paciente', str(reporte).casefold())
                self.assertNotIn('privado', str(reporte).casefold())

                vacio = consultar_reporte_financiero(engine, '2026-11-04', '2026-11-05')
                self.assertEqual(vacio['saldo_apertura_ars'], '109.00')
                self.assertEqual(vacio['dias'][0]['saldo_cierre_ars'], '109.00')
                self.assertEqual(vacio['dias'][0]['cargos'], {'cantidad': 0, 'importe_ars': '0.00'})
            finally:
                engine.dispose()

    def test_movimientos_financieros_se_leen_en_un_solo_snapshot_sql(self):
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'agenda.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            consultas_movimientos = []

            def registrar_consulta(_conexion, _cursor, statement, _parametros,
                                   _contexto, _executemany):
                consulta = statement.casefold()
                if any(tabla in consulta for tabla in (
                        'cargos_financieros', 'cobros_financieros', 'reversiones_cobros')):
                    consultas_movimientos.append(consulta)

            event.listen(engine, 'before_cursor_execute', registrar_consulta)
            try:
                consultar_reporte_financiero(engine, '2026-11-02', '2026-11-03')
                self.assertEqual(len(consultas_movimientos), 1)
                self.assertIn('union all', consultas_movimientos[0])
            finally:
                event.remove(engine, 'before_cursor_execute', registrar_consulta)
                engine.dispose()


def _utc_minute(value: str) -> int:
    return int(datetime.fromisoformat(value).astimezone(timezone.utc).timestamp() // 60)


def _fecha_hora(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _turno(turno_id: int, inicio: str, fin: str, estado: str) -> Turno:
    return Turno(
        id=turno_id, paciente_id='paciente-A', profesional_id='profesional-A',
        box_id='box-A', inicio_minuto=_utc_minute(inicio),
        fin_minuto=_utc_minute(fin), estado=estado, version=1,
    )


if __name__ == '__main__':
    unittest.main()
