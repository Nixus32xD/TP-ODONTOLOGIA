import subprocess
import unittest
from unittest.mock import patch

from odontologia.backup.postgresql_tools import (
    ErrorHerramientasPostgresql,
    detectar_herramientas_postgresql,
    validar_runtime_postgresql,
    validar_major_postgresql,
)


class HerramientasPostgresqlTests(unittest.TestCase):
    def test_rechaza_herramienta_ausente_sin_exponer_entorno(self):
        for ausente in ('pg_dump', 'pg_restore'):
            def buscar(nombre):
                return None if nombre == ausente else f'/pg/bin/{nombre}'

            with self.subTest(ausente=ausente), \
                    patch('odontologia.backup.postgresql_tools.shutil.which', side_effect=buscar):
                with self.assertRaises(ErrorHerramientasPostgresql) as contexto:
                    detectar_herramientas_postgresql(160002)
                self.assertEqual(contexto.exception.codigo, 'herramienta_ausente')
                self.assertNotIn('DATABASE_URL', str(contexto.exception))

    def test_rechaza_error_de_ejecucion_con_mensaje_saneado(self):
        def ejecutar(*args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0], stderr='secret=valor')

        with patch('odontologia.backup.postgresql_tools.shutil.which', return_value='C:/pg/bin/pg_dump'), \
                patch('odontologia.backup.postgresql_tools.subprocess.run', side_effect=ejecutar):
            with self.assertRaises(ErrorHerramientasPostgresql) as contexto:
                detectar_herramientas_postgresql(160002)
        self.assertEqual(contexto.exception.codigo, 'herramienta_invalida')
        self.assertNotIn('secret', str(contexto.exception))

    def test_detecta_versiones_y_rechaza_major_distinta_del_servidor(self):
        def ejecutar(command, **kwargs):
            version = 'PostgreSQL) 15.8' if 'pg_restore' in command[0] else 'PostgreSQL) 16.2'
            self.assertFalse(kwargs['shell'])
            self.assertEqual(command[1:], ['--version'])
            return subprocess.CompletedProcess(command, 0, f'{command[0]} ({version}\n', '')

        with patch('odontologia.backup.postgresql_tools.shutil.which', side_effect=['/pg/pg_dump', '/pg/pg_restore']), \
                patch('odontologia.backup.postgresql_tools.subprocess.run', side_effect=ejecutar):
            with self.assertRaises(ErrorHerramientasPostgresql) as contexto:
                detectar_herramientas_postgresql(160002)
        self.assertEqual(contexto.exception.codigo, 'version_incompatible')

    def test_rechaza_version_servidor_invalida_sin_aceptar_argumentos(self):
        for valor in ('160002;whoami', True, 0, -1):
            with self.subTest(valor=valor), self.assertRaises(ErrorHerramientasPostgresql):
                validar_major_postgresql(valor, 16, 16)

    def test_parsea_server_version_num_que_postgresql_devuelve_como_texto(self):
        self.assertEqual(validar_major_postgresql('160002', 16, 16), 16)

    def test_major_igual_del_dump_y_restore_es_compatible(self):
        self.assertEqual(validar_major_postgresql(160002, 16, 16), 16)

    def test_detecta_ambos_clientes_compatibles_sin_shell(self):
        def ejecutar(command, **kwargs):
            self.assertFalse(kwargs['shell'])
            self.assertEqual(command[1:], ['--version'])
            return subprocess.CompletedProcess(command, 0, 'pg (PostgreSQL) 16.4\n', '')

        with patch('odontologia.backup.postgresql_tools.shutil.which', side_effect=['/pg/pg_dump', '/pg/pg_restore']), \
                patch('odontologia.backup.postgresql_tools.subprocess.run', side_effect=ejecutar):
            actual = detectar_herramientas_postgresql(160002)
        self.assertEqual(actual['server_major'], 16)
        self.assertEqual(actual['pg_dump_major'], 16)
        self.assertEqual(actual['pg_restore_major'], 16)

    def test_rechaza_codigo_de_salida_no_cero(self):
        def ejecutar(command, **kwargs):
            return subprocess.CompletedProcess(command, 2, '', 'url=secreto')

        with patch('odontologia.backup.postgresql_tools.shutil.which', side_effect=['/pg/pg_dump', '/pg/pg_restore']), \
                patch('odontologia.backup.postgresql_tools.subprocess.run', side_effect=ejecutar):
            with self.assertRaises(ErrorHerramientasPostgresql) as contexto:
                detectar_herramientas_postgresql(160002)
        self.assertEqual(contexto.exception.codigo, 'herramienta_invalida')

    def test_runtime_consulta_servidor_y_falla_antes_de_procesar_destino(self):
        class Conexion:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                pass

            def execute(self, consulta):
                self.assert_query = str(consulta)
                return type('Resultado', (), {'scalar_one': lambda _self: 160002})()

        class Engine:
            def connect(self):
                return Conexion()

        with patch('odontologia.backup.postgresql_tools.detectar_herramientas_postgresql',
                   side_effect=ErrorHerramientasPostgresql('herramienta_ausente')) as detectar:
            with self.assertRaises(ErrorHerramientasPostgresql):
                validar_runtime_postgresql(Engine())
        detectar.assert_called_once_with(160002)

if __name__ == '__main__':
    unittest.main()
