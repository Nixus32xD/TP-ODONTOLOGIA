import unittest

from sqlalchemy.engine import make_url

from tests.test_postgresql_integracion import _url_test_database_permitida


class GuardBasePostgreSQLTests(unittest.TestCase):
    def test_acepta_solo_test_exacta_o_sufijo_test_en_loopback_y_otro_puerto(self):
        for nombre in ('test', 'odontologia_test'):
            with self.subTest(nombre=nombre):
                url = make_url(f'postgresql+psycopg://user:pass@127.0.0.1:55432/{nombre}')
                self.assertTrue(_url_test_database_permitida(url))

    def test_rechaza_nombres_parecidos_productivos_host_remoto_o_puerto_real(self):
        urls_no_seguras = (
            'postgresql+psycopg://user:pass@127.0.0.1:55432/contest',
            'postgresql+psycopg://user:pass@127.0.0.1:55432/odontologia_test_backup',
            'postgresql+psycopg://user:pass@127.0.0.1:5432/odontologia_test',
            'postgresql+psycopg://user:pass@127.0.0.1/odontologia_test',
            'postgresql+psycopg://user:pass@db.example.com:55432/odontologia_test',
        )
        for raw_url in urls_no_seguras:
            with self.subTest(raw_url=raw_url):
                self.assertFalse(_url_test_database_permitida(make_url(raw_url)))


if __name__ == '__main__':
    unittest.main()
