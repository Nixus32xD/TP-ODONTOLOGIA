from datetime import datetime, timezone
import unittest

from odontologia.agenda import ErrorAgenda, validar_solicitud_turno


class ValidacionSolicitudTests(unittest.TestCase):
    def test_normaliza_instantes_a_utc_y_minutos_enteros(self):
        solicitud = validar_solicitud_turno(
            paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
            inicio=datetime(2026, 1, 1, 9, tzinfo=timezone.utc),
            fin=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc), timeout_segundos=0.5,
        )

        self.assertEqual(solicitud.inicio_minuto + 30, solicitud.fin_minuto)
        self.assertEqual(solicitud.inicio.tzinfo, timezone.utc)
        self.assertEqual(solicitud.timeout_segundos, 0.5)

    def test_identificador_precede_error_de_fecha(self):
        with self.assertRaises(ErrorAgenda) as contexto:
            validar_solicitud_turno(
                paciente_id=' paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio='no-fecha', fin='no-fecha', timeout_segundos=True,
            )

        self.assertEqual(contexto.exception.codigo, 'entrada_invalida')
        self.assertEqual(contexto.exception.campo, 'paciente')

    def test_timeout_invalido_se_rechaza_antes_de_abrir_storage(self):
        with self.assertRaises(ErrorAgenda) as contexto:
            validar_solicitud_turno(
                paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                inicio=datetime(2026, 1, 1, 9, tzinfo=timezone.utc),
                fin=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc), timeout_segundos=True,
            )

        self.assertEqual(contexto.exception.codigo, 'entrada_invalida')
        self.assertEqual(contexto.exception.campo, 'timeout')


if __name__ == '__main__':
    unittest.main()
