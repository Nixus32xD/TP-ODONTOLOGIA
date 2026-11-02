from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest
from unittest.mock import patch

from odontologia.backup.errors import ErrorBackup
from odontologia.backup.restauracion_postgresql import restaurar_bundle_postgresql


class _URL:
    database = 'agenda_activa'
    host = '127.0.0.1'
    port = 55432
    username = 'tester'
    password = 'ficticio'
    query = {}

    def set(self, **kwargs):
        nuevo = type('_URL', (), dict(vars(type(self))))()
        for key, value in vars(self).items():
            setattr(nuevo, key, value)
        for key, value in kwargs.items():
            setattr(nuevo, key, value)
        return nuevo


class _Engine:
    url = _URL()

    def connect(self):
        raise AssertionError('las conexiones se sustituyen en las pruebas de orquestación')


class RestauracionPostgreSQLTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.root = Path(self.temporal.name)
        self.bundle = self.root / 'bundle'
        self.bundle.mkdir()
        (self.bundle / 'agenda.dump').write_bytes(b'archive custom ficticio')
        (self.bundle / 'manifest.json').write_text('{}', encoding='utf-8')

    def tearDown(self):
        self.temporal.cleanup()

    def test_rechaza_destino_activo_o_existente_sin_crear_staging(self):
        with patch('odontologia.backup.restauracion_postgresql.verificar_bundle',
                   return_value={'backend': 'postgresql', 'payload_name': 'agenda.dump'}):
            with self.assertRaises(ErrorBackup) as contexto:
                restaurar_bundle_postgresql(_Engine(), self.bundle, 'agenda_activa')
        self.assertEqual(contexto.exception.codigo, 'agenda_activa')
        with self.assertRaises(ErrorBackup) as contexto:
            restaurar_bundle_postgresql(_Engine(), self.bundle, 'nombre-invalido;DROP')
        self.assertEqual(contexto.exception.codigo, 'ruta_invalida')

    def test_rechaza_bundle_invalido_antes_de_crear_base(self):
        with patch('odontologia.backup.restauracion_postgresql.verificar_bundle',
                   side_effect=ErrorBackup('bundle_invalido')), \
                patch('odontologia.backup.restauracion_postgresql._crear_engine_mantenimiento') as crear_admin:
            with self.assertRaises(ErrorBackup):
                restaurar_bundle_postgresql(_Engine(), self.bundle, 'nueva_agenda')
        crear_admin.assert_not_called()

    def test_no_crea_staging_sin_createdb_y_no_publica_destino(self):
        with patch('odontologia.backup.restauracion_postgresql.verificar_bundle',
                   return_value={'backend': 'postgresql', 'payload_name': 'agenda.dump'}), \
                patch('odontologia.backup.restauracion_postgresql.validar_runtime_postgresql',
                      return_value={'pg_restore': 'pg_restore'}), \
                patch('odontologia.backup.restauracion_postgresql._crear_engine_mantenimiento'), \
                patch('odontologia.backup.restauracion_postgresql._validar_cluster_destino',
                      side_effect=ErrorBackup('permiso_insuficiente')) as validar:
            with self.assertRaises(ErrorBackup) as contexto:
                restaurar_bundle_postgresql(_Engine(), self.bundle, 'nueva_agenda')
        self.assertEqual(contexto.exception.codigo, 'permiso_insuficiente')
        validar.assert_called_once()

    def test_rechaza_base_objetivo_ya_existente_antes_de_crear_staging(self):
        with patch('odontologia.backup.restauracion_postgresql.verificar_bundle',
                   return_value={'backend': 'postgresql', 'payload_name': 'agenda.dump'}), \
                patch('odontologia.backup.restauracion_postgresql.validar_runtime_postgresql',
                      return_value={'pg_restore': 'pg_restore'}), \
                patch('odontologia.backup.restauracion_postgresql._crear_engine_mantenimiento'), \
                patch('odontologia.backup.restauracion_postgresql._validar_cluster_destino',
                      side_effect=ErrorBackup('destino_existente')), \
                patch('odontologia.backup.restauracion_postgresql._crear_base_staging') as crear:
            with self.assertRaises(ErrorBackup) as contexto:
                restaurar_bundle_postgresql(_Engine(), self.bundle, 'destino_preexistente')
        self.assertEqual(contexto.exception.codigo, 'destino_existente')
        crear.assert_not_called()

    def test_archive_corrupto_falla_antes_de_abrir_conexion_de_admin(self):
        with patch('odontologia.backup.restauracion_postgresql.verificar_bundle',
                   side_effect=ErrorBackup('bundle_invalido')), \
                patch('odontologia.backup.restauracion_postgresql._crear_engine_mantenimiento') as crear_admin:
            with self.assertRaises(ErrorBackup):
                restaurar_bundle_postgresql(_Engine(), self.bundle, 'destino_nuevo')
        crear_admin.assert_not_called()

    def test_fallo_parcial_pg_restore_elimina_solo_staging(self):
        with patch('odontologia.backup.restauracion_postgresql.verificar_bundle',
                   return_value={'backend': 'postgresql', 'payload_name': 'agenda.dump'}), \
                patch('odontologia.backup.restauracion_postgresql.validar_runtime_postgresql',
                      return_value={'pg_restore': 'pg_restore'}), \
                patch('odontologia.backup.restauracion_postgresql._crear_engine_mantenimiento'), \
                patch('odontologia.backup.restauracion_postgresql._validar_cluster_destino'), \
                patch('odontologia.backup.restauracion_postgresql._crear_base_staging') as crear, \
                patch('odontologia.backup.restauracion_postgresql._ejecutar_restore',
                      side_effect=ErrorBackup('operacion_fallida')), \
                patch('odontologia.backup.restauracion_postgresql._eliminar_base_staging') as eliminar:
            crear.return_value = 'c12_restore_123abc'
            with self.assertRaises(ErrorBackup):
                restaurar_bundle_postgresql(_Engine(), self.bundle, 'nueva_agenda')
        crear.assert_called_once()
        eliminar.assert_called_once_with(unittest.mock.ANY, 'c12_restore_123abc')


if __name__ == '__main__':
    unittest.main()
