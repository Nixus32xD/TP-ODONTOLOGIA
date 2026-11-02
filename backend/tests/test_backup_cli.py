from pathlib import Path
import subprocess
import sys
from io import StringIO
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from odontologia.backup.cli import main
from odontologia.backup.errors import ErrorBackup
from odontologia.backup.manifest import (
    TABLAS_ESQUEMA_ACTUAL,
    crear_manifiesto,
    guardar_manifiesto,
)
from odontologia.backup.verificacion import verificar_bundle


class SuperficieBackupCliTests(unittest.TestCase):
    def test_manifiesto_no_expone_datos_del_payload_ni_configuracion(self):
        with TemporaryDirectory() as temporal:
            payload = Path(temporal) / 'agenda.sqlite3'
            payload.write_text(
                'paciente ficticio: Ana Prueba; telefono: 555-0100; password secreto; '
                'jwt secreto; postgresql://usuario:clave@localhost/db',
                encoding='utf-8',
            )
            manifiesto = crear_manifiesto(
                payload, backend='sqlite', schema_version='8',
                table_counts={tabla: 0 for tabla in TABLAS_ESQUEMA_ACTUAL['sqlite']})
            ruta_manifest = Path(temporal) / 'manifest.json'
            guardar_manifiesto(manifiesto, ruta_manifest)
            texto = ruta_manifest.read_text(encoding='utf-8')

        for dato_sensible in (
            'Ana Prueba', '555-0100', 'password secreto', 'jwt secreto',
            'postgresql://', 'usuario:clave', str(temporal),
        ):
            with self.subTest(dato_sensible=dato_sensible):
                self.assertNotIn(dato_sensible, texto)
        self.assertEqual(
            set(manifiesto),
            {
                'format_version', 'created_at_utc', 'backend', 'application_version',
                'schema_version', 'payload_name', 'payload_size_bytes', 'payload_sha256',
                'table_counts',
            },
        )

    def test_ayuda_cli_ofrece_acciones_sin_argumentos_de_credenciales(self):
        proceso = subprocess.run(
            [sys.executable, '-m', 'odontologia.backup', '--help'],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proceso.returncode, 0, proceso.stderr)
        ayuda = proceso.stdout.lower()
        for accion in ('crear', 'verificar', 'restaurar'):
            self.assertIn(accion, ayuda)
        for argumento in ('--database-url', '--password', '--jwt-secreto', '--token'):
            self.assertNotIn(argumento, ayuda)

    def test_crear_sqlite_delega_en_bundle_y_muestra_resultado(self):
        salida = StringIO()
        with patch('odontologia.backup.cli.cargar_configuracion') as cargar, \
                patch('odontologia.backup.cli.crear_bundle_sqlite', return_value={'backend': 'sqlite'}) as crear, \
                patch('sys.stdout', salida):
            cargar.return_value.persistencia = 'sqlite'
            cargar.return_value.odontologia_db = 'agenda-ficticia.sqlite3'
            codigo = main(['crear', 'bundle-nuevo'])
        self.assertEqual(codigo, 0)
        crear.assert_called_once_with('agenda-ficticia.sqlite3', 'bundle-nuevo')
        self.assertIn('sqlite', salida.getvalue())
        self.assertIn('datos sensibles', salida.getvalue().lower())
        self.assertIn('fuera del repositorio', salida.getvalue().lower())

    def test_crear_postgresql_prepara_engine_dispose_y_mensaje_sin_url(self):
        salida = StringIO()
        engine = type('Engine', (), {'dispose': lambda _self: setattr(_self, 'disposed', True)})()
        with patch('odontologia.backup.cli.cargar_configuracion') as cargar, \
                patch('odontologia.db.postgresql.crear_engine', return_value=engine) as crear_engine, \
                patch('odontologia.backup.cli.crear_bundle_postgresql', return_value={'backend': 'postgresql'}), \
                patch('sys.stdout', salida):
            cargar.return_value.persistencia = 'postgresql'
            cargar.return_value.database_url = 'postgresql+psycopg://user:password@db/agenda'
            codigo = main(['crear', 'bundle-nuevo'])
        self.assertEqual(codigo, 0)
        self.assertTrue(engine.disposed)
        self.assertNotIn('password', salida.getvalue())
        self.assertIn('datos sensibles', salida.getvalue().lower())
        self.assertIn('fuera del repositorio', salida.getvalue().lower())

    def test_fallo_de_backup_da_codigo_y_no_muestra_secreto(self):
        salida_error = StringIO()
        with patch('odontologia.backup.cli.cargar_configuracion') as cargar, \
                patch('odontologia.backup.cli.crear_bundle_sqlite',
                      side_effect=ErrorBackup('operacion_fallida')), \
                patch('sys.stderr', salida_error):
            cargar.return_value.persistencia = 'sqlite'
            cargar.return_value.odontologia_db = 'agenda-ficticia.sqlite3'
            codigo = main(['crear', 'bundle-nuevo'])
        self.assertEqual(codigo, 2)
        self.assertIn('operacion_fallida', salida_error.getvalue())
        self.assertNotIn('password', salida_error.getvalue())

    def test_value_error_de_operacion_no_imprime_detalle_privado(self):
        salida_error = StringIO()
        detalle = r'C:\private\ruta-centinela postgresql://usuario:secreto@db/agenda'
        with patch('odontologia.backup.cli.cargar_configuracion') as cargar, \
                patch('odontologia.backup.cli.crear_bundle_sqlite',
                      side_effect=ValueError(detalle)), \
                patch('sys.stderr', salida_error):
            cargar.return_value.persistencia = 'sqlite'
            cargar.return_value.odontologia_db = 'agenda-ficticia.sqlite3'
            codigo = main(['crear', 'bundle-nuevo'])
        self.assertEqual(codigo, 2)
        self.assertIn('operacion_fallida', salida_error.getvalue())
        self.assertNotIn(detalle, salida_error.getvalue())
        self.assertNotIn('secreto', salida_error.getvalue())

    def test_verificar_cli_delega_sin_consultar_configuracion_activa(self):
        salida = StringIO()
        with patch('odontologia.backup.cli.verificar_bundle',
                   return_value={'verified': True, 'backend': 'sqlite', 'schema_version': '8'}) as verificar, \
                patch('odontologia.backup.cli.cargar_configuracion',
                      side_effect=AssertionError('verificar no debe abrir la agenda activa')), \
                patch('sys.stdout', salida):
            codigo = main(['verificar', 'bundle-elegido'])
        self.assertEqual(codigo, 0)
        verificar.assert_called_once_with('bundle-elegido')
        self.assertIn('verificado', salida.getvalue().lower())

    def test_restaurar_sqlite_pasa_agenda_activa_para_protegerla(self):
        salida = StringIO()
        with patch('odontologia.backup.cli.cargar_configuracion') as cargar, \
                patch('odontologia.backup.cli.verificar_bundle',
                      return_value={'backend': 'sqlite'}), \
                patch('odontologia.backup.cli.restaurar_bundle_sqlite',
                      return_value={'restored': True, 'backend': 'sqlite'}) as restaurar, \
                patch('sys.stdout', salida):
            cargar.return_value.persistencia = 'sqlite'
            cargar.return_value.odontologia_db = 'agenda-activa.sqlite3'
            codigo = main(['restaurar', 'bundle', 'restaurada.sqlite3'])
        self.assertEqual(codigo, 0)
        restaurar.assert_called_once_with(
            'bundle', 'restaurada.sqlite3', origen_activo='agenda-activa.sqlite3')
        self.assertIn('sqlite', salida.getvalue())

    def test_restaurar_postgresql_usa_engine_seleccionado_y_lo_cierra(self):
        salida = StringIO()
        engine = type('Engine', (), {'dispose': lambda _self: setattr(_self, 'disposed', True)})()
        with patch('odontologia.backup.cli.cargar_configuracion') as cargar, \
                patch('odontologia.backup.cli.verificar_bundle',
                      return_value={'backend': 'postgresql'}), \
                patch('odontologia.db.postgresql.crear_engine', return_value=engine) as crear_engine, \
                patch('odontologia.backup.cli.restaurar_bundle_postgresql',
                      return_value={'restored': True, 'backend': 'postgresql'}) as restaurar, \
                patch('sys.stdout', salida):
            cargar.return_value.persistencia = 'postgresql'
            cargar.return_value.database_url = 'postgresql+psycopg://user:secret@127.0.0.1/agenda'
            codigo = main(['restaurar', 'bundle-pg', 'agenda_nueva'])
        self.assertEqual(codigo, 0)
        crear_engine.assert_called_once_with(cargar.return_value.database_url)
        restaurar.assert_called_once_with(engine, 'bundle-pg', 'agenda_nueva')
        self.assertTrue(engine.disposed)
        self.assertNotIn('secret', salida.getvalue())


if __name__ == '__main__':
    unittest.main()
