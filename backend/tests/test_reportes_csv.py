import csv
from io import StringIO
import unittest

from odontologia.reportes import (
    serializar_reporte_agenda_csv,
    serializar_reporte_financiero_csv,
)


class ReportesCSVTests(unittest.TestCase):
    def test_agenda_csv_tiene_orden_estable_utf8_y_protege_celda_formula(self):
        reporte = {
            'zona': 'America/Argentina/Mendoza', 'desde': '2026-11-02', 'hasta': '2026-11-03',
            'dias': [{
                'fecha': '2026-11-02',
                'estados': {
                    'reservado': {'cantidad': 1, 'minutos': 30},
                    'confirmado': {'cantidad': 0, 'minutos': 0},
                    'atendido': {'cantidad': 0, 'minutos': 0},
                    'ausente': {'cantidad': 0, 'minutos': 0},
                    'cancelado': {'cantidad': 0, 'minutos': 0},
                },
                'recursos': {
                    'profesionales': [{
                        'recurso_id': '=HYPERLINK("x", "ñ")', 'minutos_disponibles': 60,
                        'minutos_ocupados': 30, 'ocupacion_porcentaje': 50.0,
                    }],
                    'boxes': [],
                },
            }],
        }
        contenido = serializar_reporte_agenda_csv(reporte)
        self.assertIn('ñ', contenido)
        self.assertTrue(contenido.endswith('\r\n'))
        filas = list(csv.reader(StringIO(contenido, newline='')))
        self.assertEqual(filas[0], [
            'fecha', 'tipo_fila', 'estado', 'cantidad', 'minutos', 'tipo_recurso',
            'recurso_id', 'minutos_disponibles', 'minutos_ocupados', 'ocupacion_porcentaje',
        ])
        self.assertEqual(filas[1][2:5], ['reservado', '1', '30'])
        self.assertEqual(filas[-1][6], "'=HYPERLINK(\"x\", \"ñ\")")

    def test_agenda_csv_protege_los_cuatro_prefijos_de_formula(self):
        reporte = {
            'dias': [{
                'fecha': '2026-11-02', 'estados': {},
                'recursos': {'profesionales': [
                    {'recurso_id': prefijo + 'recurso', 'minutos_disponibles': 1,
                     'minutos_ocupados': 0, 'ocupacion_porcentaje': 0}
                    for prefijo in ('=', '+', '-', '@')
                ], 'boxes': []},
            }],
        }
        filas = list(csv.reader(StringIO(serializar_reporte_agenda_csv(reporte), newline='')))
        self.assertEqual([fila[6] for fila in filas[1:]], [
            "'=recurso", "'+recurso", "'-recurso", "'@recurso",
        ])

    def test_finanzas_csv_preserva_importes_negativos_y_saldos_de_apertura_cierre(self):
        reporte = {
            'zona': 'America/Argentina/Mendoza', 'desde': '2026-11-02', 'hasta': '2026-11-03',
            'saldo_apertura_ars': '80.00',
            'dias': [{
                'fecha': '2026-11-02',
                'cargos': {'cantidad': 1, 'importe_ars': '50.00'},
                'cobros': {'cantidad': 1, 'importe_ars': '30.00'},
                'reversiones': {'cantidad': 2, 'importe_ars': '35.00'},
                'neto_ars': '-5.00', 'saldo_cierre_ars': '95.00',
            }],
        }
        contenido = serializar_reporte_financiero_csv(reporte)
        filas = list(csv.reader(StringIO(contenido, newline='')))
        self.assertEqual(filas[0], [
            'fecha', 'cargos_cantidad', 'cargos_ars', 'cobros_cantidad', 'cobros_ars',
            'reversiones_cantidad', 'reversiones_ars', 'neto_ars',
            'saldo_apertura_ars', 'saldo_cierre_ars',
        ])
        self.assertEqual(filas[1], [
            '2026-11-02', '1', '50.00', '1', '30.00', '2', '35.00',
            '-5.00', '80.00', '95.00',
        ])


if __name__ == '__main__':
    unittest.main()
