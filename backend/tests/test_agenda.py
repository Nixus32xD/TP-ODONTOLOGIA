from contextlib import closing
from datetime import datetime, timezone, timedelta, tzinfo
from pathlib import Path
import sqlite3
import tempfile
import unittest

from odontologia import ErrorAgenda, inicializar_agenda


class OffsetInvalido(tzinfo):
    def utcoffset(self, dt):
        return 'no es un offset'


class AgendaCaso(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(self.ruta)

    def filas(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            return conexion.execute('SELECT * FROM turnos ORDER BY id').fetchall()

    def alta(self, **cambios):
        from odontologia import crear_turno
        datos = dict(paciente_id='paciente-A', profesional_id='profesional-A',
                     box_id='box-A', inicio=datetime.fromisoformat('2026-10-15T09:00-03:00'),
                     fin=datetime.fromisoformat('2026-10-15T09:30-03:00'))
        datos.update(cambios)
        return crear_turno(self.ruta, **datos)

    def error(self, codigo, campo=None, **cambios):
        anteriores = self.filas()
        with self.assertRaises(ErrorAgenda) as contexto:
            self.alta(**cambios)
        self.assertEqual((contexto.exception.codigo, contexto.exception.campo), (codigo, campo))
        self.assertEqual(self.filas(), anteriores)


class BootstrapTests(AgendaCaso):
    def test_agenda_nueva_tiene_seis_recursos_sin_turnos(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            for tabla, prefijo in [('pacientes', 'paciente'), ('profesionales', 'profesional'), ('boxes', 'box')]:
                self.assertEqual(conexion.execute(f'SELECT id FROM {tabla} ORDER BY id').fetchall(),
                                 [(prefijo+'-A',), (prefijo+'-B',)])
        self.assertEqual(self.filas(), [])

    def test_preparacion_repetida_conserva_turno(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('INSERT INTO turnos VALUES (1, ?, ?, ?, ?, ?)',
                             ('paciente-A', 'profesional-A', 'box-A', 100, 130))
            conexion.commit()
        anteriores = self.filas()
        with self.assertRaises(ErrorAgenda) as contexto:
            inicializar_agenda(self.ruta)
        self.assertEqual(contexto.exception.codigo, 'agenda_existente')
        self.assertEqual(self.filas(), anteriores)

    def test_no_sobrescribe_archivo_ajeno(self):
        ruta = Path(self.temporal.name) / 'ajeno.txt'
        ruta.write_text('conservar', encoding='utf-8')
        with self.assertRaises(ErrorAgenda) as contexto:
            inicializar_agenda(ruta)
        self.assertEqual(contexto.exception.codigo, 'agenda_existente')
        self.assertEqual(ruta.read_text(encoding='utf-8'), 'conservar')


class AperturaTests(AgendaCaso):
    def test_alta_sin_agenda_no_crea_archivo(self):
        self.ruta = Path(self.temporal.name) / 'ausente.sqlite3'
        with self.assertRaises(ErrorAgenda) as contexto:
            self.alta()
        self.assertEqual(contexto.exception.codigo, 'almacenamiento_error')
        self.assertFalse(self.ruta.exists())

    def test_ruta_invalida_no_crea_directorios(self):
        self.ruta = Path(self.temporal.name) / 'ausente' / 'agenda.sqlite3'
        with self.assertRaises(ErrorAgenda) as contexto:
            self.alta()
        self.assertEqual(contexto.exception.codigo, 'almacenamiento_error')
        self.assertFalse(self.ruta.parent.exists())


class AltaValidaTests(AgendaCaso):
    def test_alta_retorna_datos_y_persiste_al_reabrir(self):
        turno = self.alta()
        self.assertGreater(turno.id, 0)
        self.assertEqual((turno.paciente_id, turno.profesional_id, turno.box_id),
                         ('paciente-A', 'profesional-A', 'box-A'))
        self.assertEqual(turno.inicio, datetime(2026, 10, 15, 12, tzinfo=timezone.utc))
        self.assertEqual(turno.fin, datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc))
        self.assertIs(turno.inicio.tzinfo, timezone.utc)
        filas = self.filas()
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0][:4], (turno.id, 'paciente-A', 'profesional-A', 'box-A'))
        self.assertEqual(filas[0][5] - filas[0][4], 30)

    def test_dos_altas_distintas_se_conservan(self):
        primero = self.alta()
        segundo = self.alta(paciente_id='paciente-B', profesional_id='profesional-B', box_id='box-B',
                            inicio=datetime(2026, 10, 16, 14, tzinfo=timezone.utc),
                            fin=datetime(2026, 10, 16, 14, 45, tzinfo=timezone.utc))
        self.assertNotEqual(primero.id, segundo.id)
        self.assertEqual([f[0] for f in self.filas()], [primero.id, segundo.id])
        self.assertEqual(segundo.fin - segundo.inicio, timedelta(minutes=45))


class IdentificadoresTests(AgendaCaso):
    def test_forma_invalida_en_cada_campo(self):
        for campo, argumento in [('paciente', 'paciente_id'), ('profesional', 'profesional_id'), ('box', 'box_id')]:
            for valor in ['', ' paciente-A', 'paciente-A ', 'x'*65, 17, None, True]:
                with self.subTest(campo=campo, valor=valor):
                    self.error('entrada_invalida', campo, **{argumento: valor})

    def test_referencias_desconocidas_y_longitud_limite(self):
        for campo, argumento in [('paciente', 'paciente_id'), ('profesional', 'profesional_id'), ('box', 'box_id')]:
            for valor in ['desconocido', 'x'*64]:
                with self.subTest(campo=campo, valor=valor):
                    self.error('recurso_desconocido', campo, **{argumento: valor})

    def test_prioridad_y_sin_cambio_de_mayusculas(self):
        self.error('entrada_invalida', 'paciente', paciente_id='', profesional_id='')
        self.error('recurso_desconocido', 'paciente', paciente_id='PACIENTE-A', profesional_id='inexistente')
        self.error('recurso_desconocido', 'profesional', profesional_id='inexistente', box_id='inexistente')


class FechasTests(AgendaCaso):
    def test_fecha_sin_offset_rechazada(self):
        self.error('entrada_invalida', 'inicio', inicio=datetime(2026, 10, 15, 9))

    def test_tipos_y_precision_rechazados_en_ambos_limites(self):
        for campo in ['inicio', 'fin']:
            for valor in ['2026-10-15T12:00Z', None, 15,
                          datetime(2026, 10, 15, 12, 0, 1, tzinfo=timezone.utc),
                          datetime(2026, 10, 15, 12, 0, 0, 1, tzinfo=timezone.utc),
                          datetime(2026, 10, 15, 12)]:
                with self.subTest(campo=campo, valor=valor):
                    self.error('entrada_invalida', campo, **{campo: valor})

    def test_intervalo_vacio_e_invertido(self):
        for fin in [datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                    datetime(2026, 10, 15, 11, 59, tzinfo=timezone.utc)]:
            with self.subTest(fin=fin):
                self.error('entrada_invalida', 'intervalo', fin=fin)

    def test_offset_equivalente_se_persiste_exactamente(self):
        a = self.alta()
        b = self.alta(profesional_id='profesional-B', box_id='box-B',
                      inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                      fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc))
        self.assertEqual((a.inicio, a.fin), (b.inicio, b.fin))
        self.assertEqual(self.filas()[0][4:], self.filas()[1][4:])

    def test_orden_de_errores_ids_antes_fechas(self):
        self.error('entrada_invalida', 'paciente', paciente_id='', inicio=None)
        self.error('entrada_invalida', 'inicio', inicio=None, fin=None)

    def test_minutos_anteriores_epoch_sin_redondeo(self):
        turno = self.alta(inicio=datetime(1969, 12, 31, 23, 59, tzinfo=timezone.utc),
                          fin=datetime(1970, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(self.filas()[0][4:], (-1, 0))
        self.assertEqual(turno.fin - turno.inicio, timedelta(minutes=1))

    def test_offset_con_segundos_no_se_redondea_a_utc(self):
        zona = timezone(timedelta(seconds=1))
        self.error('entrada_invalida', 'inicio',
                   inicio=datetime(2026, 10, 15, 12, tzinfo=zona))

    def test_limites_no_representables_en_utc_se_rechazan(self):
        valores = [datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=1))),
                   datetime(9999, 12, 31, 23, 59, tzinfo=timezone(timedelta(hours=-1)))]
        for campo in ['inicio', 'fin']:
            for valor in valores:
                with self.subTest(campo=campo, valor=valor):
                    self.error('entrada_invalida', campo, **{campo: valor})

    def test_zona_invalida_no_filtra_excepcion_interna(self):
        for campo in ['inicio', 'fin']:
            with self.subTest(campo=campo):
                self.error('entrada_invalida', campo,
                           **{campo: datetime(2026, 10, 15, 12, tzinfo=OffsetInvalido())})


class TimeoutTests(AgendaCaso):
    def test_timeout_cero_rechazado_antes_de_abrir(self):
        self.ruta = Path(self.temporal.name) / 'ausente.sqlite3'
        with self.assertRaises(ErrorAgenda) as contexto:
            self.alta(timeout_segundos=0)
        self.assertEqual((contexto.exception.codigo, contexto.exception.campo), ('entrada_invalida', 'timeout'))
        self.assertFalse(self.ruta.exists())

    def test_timeout_invalido_no_accede_a_agenda(self):
        self.ruta = Path(self.temporal.name) / 'ausente.sqlite3'
        for valor in [-1, float('inf'), float('-inf'), float('nan'), True, False, '5', None]:
            with self.subTest(valor=valor), self.assertRaises(ErrorAgenda) as contexto:
                self.alta(timeout_segundos=valor)
            self.assertEqual((contexto.exception.codigo, contexto.exception.campo), ('entrada_invalida', 'timeout'))
        self.assertFalse(self.ruta.exists())

    def test_timeout_positivo(self):
        for indice, valor in enumerate([0.1, 5.0, 1]):
            with self.subTest(valor=valor):
                self.alta(inicio=datetime(2026, 10, 15, 14+indice, tzinfo=timezone.utc),
                          fin=datetime(2026, 10, 15, 14+indice, 30, tzinfo=timezone.utc),
                          timeout_segundos=valor)
        self.assertEqual(len(self.filas()), 3)


class ProfesionalTests(AgendaCaso):
    def test_solapamiento_parcial_profesional_otro_box(self):
        self.alta()
        self.error('conflicto_profesional', 'profesional', box_id='box-B',
                   inicio=datetime(2026, 10, 15, 12, 15, tzinfo=timezone.utc),
                   fin=datetime(2026, 10, 15, 12, 45, tzinfo=timezone.utc))

    def test_igualdad_y_contencion_profesional(self):
        self.alta(fin=datetime(2026, 10, 15, 13, tzinfo=timezone.utc))
        for inicio, fin in [(12, 13), (12.25, 12.5), (11.5, 13.5)]:
            with self.subTest(inicio=inicio, fin=fin):
                inicio_dt = datetime(2026, 10, 15, int(inicio), int((inicio % 1)*60), tzinfo=timezone.utc)
                fin_dt = datetime(2026, 10, 15, int(fin), int((fin % 1)*60), tzinfo=timezone.utc)
                self.error('conflicto_profesional', 'profesional', box_id='box-B', inicio=inicio_dt, fin=fin_dt)

    def test_offset_equivalente_conflicta(self):
        self.alta()
        self.error('conflicto_profesional', 'profesional', box_id='box-B',
                   inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                   fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc))


class BoxTests(AgendaCaso):
    def test_solapamiento_box_otro_profesional(self):
        self.alta()
        self.error('conflicto_box', 'box', profesional_id='profesional-B',
                   inicio=datetime(2026, 10, 15, 12, 15, tzinfo=timezone.utc),
                   fin=datetime(2026, 10, 15, 12, 45, tzinfo=timezone.utc))

    def test_igualdad_y_contenciones_box(self):
        self.alta(fin=datetime(2026, 10, 15, 13, tzinfo=timezone.utc))
        for horas in [(12, 0, 13, 0), (12, 15, 12, 30), (11, 30, 13, 30)]:
            with self.subTest(horas=horas):
                self.error('conflicto_box', 'box', profesional_id='profesional-B',
                           inicio=datetime(2026, 10, 15, horas[0], horas[1], tzinfo=timezone.utc),
                           fin=datetime(2026, 10, 15, horas[2], horas[3], tzinfo=timezone.utc))

    def test_prioridad_profesional_con_conflictos_independientes(self):
        self.alta()
        self.alta(profesional_id='profesional-B', box_id='box-B')
        self.error('conflicto_profesional', 'profesional', box_id='box-B')
        self.error('conflicto_profesional', 'profesional', profesional_id='profesional-B', box_id='box-A')


class BordesTests(AgendaCaso):
    def test_adyacencia_anterior_y_posterior(self):
        self.alta()
        anterior = self.alta(inicio=datetime(2026, 10, 15, 11, 30, tzinfo=timezone.utc),
                             fin=datetime(2026, 10, 15, 12, tzinfo=timezone.utc))
        posterior = self.alta(inicio=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc),
                              fin=datetime(2026, 10, 15, 13, tzinfo=timezone.utc))
        self.assertEqual(len(self.filas()), 3)
        self.assertNotEqual(anterior.id, posterior.id)

    def test_recursos_distintos_y_paciente_simultaneo_permitido(self):
        primero = self.alta()
        segundo = self.alta(profesional_id='profesional-B', box_id='box-B')
        self.assertEqual(primero.paciente_id, segundo.paciente_id)
        self.assertEqual((primero.inicio, primero.fin), (segundo.inicio, segundo.fin))
        self.assertEqual(len(self.filas()), 2)

    def test_cruce_de_dia_y_duracion_libre(self):
        for indice, minutos in enumerate([1, 30, 75]):
            inicio = datetime(2026, 10, 16+indice, 23, 45, tzinfo=timezone.utc)
            turno = self.alta(inicio=inicio, fin=inicio+timedelta(minutes=minutos))
            self.assertEqual(turno.fin - turno.inicio, timedelta(minutes=minutos))
        self.assertEqual(len(self.filas()), 3)


class RollbackTests(AgendaCaso):
    def test_fallo_despues_de_insertar_revierte_y_libera_agenda(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.executescript("""
                CREATE TRIGGER fallo_controlado AFTER INSERT ON turnos
                BEGIN SELECT RAISE(FAIL, 'fallo controlado'); END;
            """)
        self.error('almacenamiento_error')
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.execute('DROP TRIGGER fallo_controlado')
        turno = self.alta()
        self.assertEqual(len(self.filas()), 1)
        self.assertEqual(self.filas()[0][0], turno.id)

    def test_claves_foraneas_activas_en_cada_alta(self):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            conexion.executescript("""
                CREATE TRIGGER forzar_fk AFTER INSERT ON turnos
                BEGIN
                    INSERT INTO turnos(paciente_id, profesional_id, box_id, inicio_minuto, fin_minuto)
                    VALUES ('desconocido', 'profesional-A', 'box-A', 10, 20);
                END;
            """)
        self.error('almacenamiento_error')
        self.assertEqual(self.filas(), [])


class ContencionTests(AgendaCaso):
    def test_timeout_de_escritor_y_recuperacion(self):
        with closing(sqlite3.connect(self.ruta, autocommit=True)) as escritor:
            escritor.execute('BEGIN IMMEDIATE')
            self.error('agenda_ocupada', timeout_segundos=0.03)
            escritor.execute('ROLLBACK')
        self.assertGreater(self.alta().id, 0)
        self.assertEqual(len(self.filas()), 1)

    def test_contencion_no_altera_turnos_previos(self):
        self.alta()
        with closing(sqlite3.connect(self.ruta, autocommit=True)) as escritor:
            escritor.execute('BEGIN IMMEDIATE')
            self.error('agenda_ocupada', timeout_segundos=0.02,
                       profesional_id='profesional-B', box_id='box-B')
            escritor.execute('ROLLBACK')
        self.assertEqual(len(self.filas()), 1)


class ReintentosYErroresTests(AgendaCaso):
    def test_ruta_con_nul_produce_error_publico(self):
        original = self.ruta
        self.ruta = Path(self.temporal.name) / 'invalida\x00.sqlite3'
        with self.assertRaises(ErrorAgenda) as contexto:
            self.alta()
        self.assertEqual(contexto.exception.codigo, 'almacenamiento_error')
        with self.assertRaises(ErrorAgenda) as contexto:
            inicializar_agenda(self.ruta)
        self.assertEqual(contexto.exception.codigo, 'almacenamiento_error')
        self.ruta = original
        self.assertEqual(self.filas(), [])

    def test_repeticion_no_es_idempotente(self):
        turno = self.alta()
        self.error('conflicto_profesional', 'profesional')
        self.error('conflicto_profesional', 'profesional',
                   inicio=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
                   fin=datetime(2026, 10, 15, 12, 30, tzinfo=timezone.utc))
        self.assertEqual(self.filas()[0][0], turno.id)

    def test_archivo_inaccesible_y_no_sqlite_no_se_reemplazan(self):
        original = self.ruta
        for nombre in ['ausente.sqlite3', 'no-sqlite.txt']:
            with self.subTest(nombre=nombre):
                self.ruta = Path(self.temporal.name) / nombre
                if nombre.endswith('.txt'):
                    self.ruta.write_bytes(b'contenido ajeno que no es una base SQLite')
                with self.assertRaises(ErrorAgenda) as contexto:
                    self.alta()
                self.assertEqual(contexto.exception.codigo, 'almacenamiento_error')
                self.assertNotIn(str(self.ruta), str(contexto.exception))
                if nombre.endswith('.txt'):
                    self.assertEqual(self.ruta.read_bytes(), b'contenido ajeno que no es una base SQLite')
                else:
                    self.assertFalse(self.ruta.exists())
        self.ruta = original
        self.assertEqual(self.filas(), [])


if __name__ == '__main__':
    unittest.main()
