import contextlib
from datetime import datetime, timedelta, timezone
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, text

from odontologia import inicializar_agenda
from odontologia.auth.migraciones import migrar_sqlite


class RecordatoriosCliTests(unittest.TestCase):
    def test_falta_once_rechaza_sin_cargar_configuracion(self):
        from odontologia.workers.recordatorios_cli import main

        with patch('odontologia.core.config.cargar_configuracion') as cargar:
            with contextlib.redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as salida:
                    main([])
        self.assertEqual(salida.exception.code, 2)
        cargar.assert_not_called()

    def test_limites_fuera_de_rango_rechazan_antes_de_abrir_bd(self):
        from odontologia.workers.recordatorios_cli import main

        with patch('odontologia.core.config.cargar_configuracion') as cargar:
            for limite in ('0', '101', '-1', 'no-es-numero'):
                with self.subTest(limite=limite), contextlib.redirect_stderr(StringIO()):
                    with self.assertRaises(SystemExit) as salida:
                        main(['--once', '--limit', limite])
                    self.assertEqual(salida.exception.code, 2)
        cargar.assert_not_called()

    def test_ejecucion_valida_muestra_solo_conteos(self):
        from odontologia.workers.recordatorios_cli import main

        config = SimpleNamespace(persistencia='sqlite', database_url=None,
                                  odontologia_db='agenda-sintetica.sqlite')
        salida = StringIO()
        with (
            patch('odontologia.core.config.cargar_configuracion', return_value=config),
            patch('odontologia.auth.almacenamiento.crear_engine_autenticacion') as crear_engine,
            patch('odontologia.auth.almacenamiento.validar_ruta_sqlite_existente'),
            patch('odontologia.auth.almacenamiento.validar_esquema_autenticacion'),
            patch('odontologia.workers.recordatorios.procesar_recordatorios',
                  return_value={'procesados': 2, 'invalidados': 1, 'fallidos': 0}) as procesar,
            contextlib.redirect_stdout(salida),
        ):
            crear_engine.return_value.dispose = unittest.mock.Mock()
            self.assertEqual(main(['--once', '--limit', '7']), 0)

        procesar.assert_called_once_with(crear_engine.return_value, limite=7)
        self.assertEqual(salida.getvalue().strip(),
                         'Recordatorios simulados: procesados=2 invalidados=1 fallidos=0')

    def test_comando_real_procesa_fixture_sintetico_y_muestra_conteos(self):
        with TemporaryDirectory() as directorio:
            ruta = Path(directorio) / 'agenda-sintetica.sqlite3'
            inicializar_agenda(ruta)
            migrar_sqlite(ruta)
            engine = create_engine(f'sqlite:///{ruta.as_posix()}')
            ahora = datetime.now(timezone.utc)
            inicio = ahora + timedelta(hours=2)
            recordatorio_id = str(uuid4())
            try:
                with engine.begin() as conexion:
                    conexion.execute(text(
                        "UPDATE pacientes SET nombre='Nombre confidencial ficticio', "
                        "telefono='+54 261 5550101', acepta_recordatorios=1 "
                        "WHERE id='paciente-A'"))
                    conexion.execute(text(
                        "INSERT INTO profesionales(id, nombre, activo) "
                        "VALUES ('profesional-cli', 'Profesional ficticio', 1)"))
                    conexion.execute(text(
                        "INSERT INTO boxes(id, nombre, activo) "
                        "VALUES ('box-cli', 'Box ficticio', 1)"))
                    turno_id = conexion.execute(text(
                        "INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, "
                        "fin_minuto, estado, version) VALUES ('paciente-A', 'profesional-cli', "
                        "'box-cli', :inicio, :fin, 'confirmado', 1) RETURNING id"), {
                            'inicio': int(inicio.timestamp() // 60),
                            'fin': int((inicio + timedelta(minutes=30)).timestamp() // 60),
                        }).scalar_one()
                    vencimiento = (ahora - timedelta(minutes=1)).replace(tzinfo=None).isoformat(' ')
                    creado = ahora.replace(tzinfo=None).isoformat(' ')
                    conexion.execute(text(
                        'INSERT INTO recordatorios_outbox(id, turno_id, turno_version, tipo, '
                        'programado_para, estado, intentos, idempotency_key, created_at, updated_at) '
                        'VALUES (:id, :turno, 1, \'turno_24h\', :vencimiento, \'pendiente\', '
                        '0, :clave, :creado, :creado)'), {
                            'id': recordatorio_id, 'turno': turno_id,
                            'vencimiento': vencimiento, 'clave': f'turno:{turno_id}:version:1:turno_24h',
                            'creado': creado,
                        })
            finally:
                engine.dispose()

            entorno = os.environ.copy()
            entorno['ODONTOLOGIA_PERSISTENCIA'] = 'sqlite'
            entorno['ODONTOLOGIA_DB'] = str(ruta)
            resultado = subprocess.run(
                [sys.executable, '-m', 'odontologia.workers.recordatorios_cli',
                 '--once', '--limit', '10'],
                cwd=Path(__file__).parents[1], env=entorno, capture_output=True,
                text=True, timeout=20, check=False)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertEqual(resultado.stdout.strip(),
                             'Recordatorios simulados: procesados=1 invalidados=0 fallidos=0')
            self.assertNotIn('Nombre confidencial ficticio', resultado.stdout + resultado.stderr)
            self.assertNotIn('+54 261 5550101', resultado.stdout + resultado.stderr)


if __name__ == '__main__':
    unittest.main()
