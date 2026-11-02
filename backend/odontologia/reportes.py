"""Consultas agregadas de agenda y ledger para la demostración local."""

from collections import defaultdict
import csv
from datetime import date, datetime, time, timedelta, timezone
from io import StringIO
from zoneinfo import ZoneInfo

from sqlalchemy import literal, select, union_all
from sqlalchemy.orm import Session

from odontologia.db.models import (
    BloqueoAgenda,
    Box,
    CargoFinanciero,
    CobroFinanciero,
    ExcepcionHorario,
    HorarioSemanal,
    Profesional,
    ReversionCobro,
    TramoExcepcion,
    Turno,
)
from odontologia.finanzas import centavos_a_importe_ars


ZONA_REPORTES = ZoneInfo('America/Argentina/Mendoza')
ESTADOS_TURNO = ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')
_RECURSOS = (
    ('profesional', Profesional, 'profesional_id', 'profesionales'),
    ('box', Box, 'box_id', 'boxes'),
)


def normalizar_rango_local(desde: object, hasta: object) -> tuple[date, date]:
    """Valida el rango local semiabierto y limita la consulta a 31 fechas."""
    inicio = _fecha_local(desde)
    fin = _fecha_local(hasta)
    dias = (fin - inicio).days
    if not 1 <= dias <= 31:
        raise ValueError('El rango debe ser semiabierto y abarcar entre 1 y 31 días.')
    return inicio, fin


def calcular_minutos_disponibles(
        tramos: list[tuple[int, int]], bloqueos: list[tuple[int, int]]) -> int:
    """Mide la unión de tramos locales después de quitar las intersecciones bloqueadas."""
    return _duracion_union(_restar_intervalos(_unir(tramos), _unir(bloqueos)))


def consultar_reporte_agenda(engine, desde: object, hasta: object) -> dict[str, object]:
    inicio, fin = normalizar_rango_local(desde, hasta)
    fechas = [inicio + timedelta(days=offset) for offset in range((fin - inicio).days)]
    dias = {
        fecha.isoformat(): {
            'fecha': fecha.isoformat(),
            'estados': {estado: {'cantidad': 0, 'minutos': 0} for estado in ESTADOS_TURNO},
            'recursos': {'profesionales': [], 'boxes': []},
        }
        for fecha in fechas
    }

    with Session(engine) as session:
        recursos_agenda = {}
        ventanas_por_recurso = {}
        recursos_por_tipo = {}
        bloques_por_recurso = defaultdict(list)

        for tipo, modelo, columna, clave in _RECURSOS:
            recursos = session.scalars(select(modelo).where(
                modelo.activo.is_(True)).order_by(modelo.id)).all()
            recursos_por_tipo[tipo] = recursos
            for recurso in recursos:
                recursos_agenda[(tipo, recurso.id)] = (columna, clave)
                for fecha in fechas:
                    tramos = _tramos_del_dia(session, recurso.id, columna, fecha)
                    ventanas = _unir([
                        (_minuto_utc(fecha, desde), _minuto_utc(fecha, hasta))
                        for desde, hasta in tramos
                    ])
                    ventanas_por_recurso[(tipo, recurso.id, fecha)] = ventanas
                    dias[fecha.isoformat()]['recursos'][clave].append({
                        'recurso_id': recurso.id,
                        'minutos_disponibles': 0,
                        'minutos_ocupados': 0,
                        'ocupacion_porcentaje': None,
                    })

        todos_los_intervalos = [
            ventana for ventanas in ventanas_por_recurso.values() for ventana in ventanas
        ]
        if todos_los_intervalos:
            limite_inicio = min(inicio for inicio, _fin in todos_los_intervalos)
            limite_fin = max(fin for _inicio, fin in todos_los_intervalos)
            bloqueos = session.scalars(select(BloqueoAgenda).where(
                BloqueoAgenda.inicio_minuto < limite_fin,
                BloqueoAgenda.fin_minuto > limite_inicio,
            )).all()
            for bloqueo in bloqueos:
                tipo = 'profesional' if bloqueo.profesional_id else 'box'
                recurso_id = bloqueo.profesional_id or bloqueo.box_id
                if (tipo, recurso_id) in recursos_agenda:
                    bloques_por_recurso[(tipo, recurso_id)].append(
                        (bloqueo.inicio_minuto, bloqueo.fin_minuto))

        inicio_utc = _minuto_utc(inicio, 0)
        fin_utc = _minuto_utc(fin, 0)
        turnos = session.scalars(select(Turno).where(
            Turno.inicio_minuto >= inicio_utc,
            Turno.inicio_minuto < fin_utc,
        ).order_by(Turno.inicio_minuto, Turno.id)).all()
        turnos_por_recurso_fecha = defaultdict(list)
        for turno in turnos:
            fecha = _fecha_turno_local(turno.inicio_minuto)
            fila = dias.get(fecha.isoformat())
            if fila is None or turno.estado not in ESTADOS_TURNO:
                continue
            minutos = max(0, turno.fin_minuto - turno.inicio_minuto)
            estado = fila['estados'][turno.estado]
            estado['cantidad'] += 1
            estado['minutos'] += minutos
            if turno.estado in {'reservado', 'confirmado'}:
                intervalo = (turno.inicio_minuto, turno.fin_minuto)
                turnos_por_recurso_fecha[('profesional', turno.profesional_id, fecha)].append(intervalo)
                turnos_por_recurso_fecha[('box', turno.box_id, fecha)].append(intervalo)

        for tipo, _modelo, _columna, clave in _RECURSOS:
            for recurso in recursos_por_tipo[tipo]:
                bloqueos = bloques_por_recurso[(tipo, recurso.id)]
                for fecha in fechas:
                    ventanas = ventanas_por_recurso[(tipo, recurso.id, fecha)]
                    ventanas_libres = _restar_intervalos(ventanas, bloqueos)
                    disponibles = _duracion_union(ventanas_libres)
                    ocupados = _duracion_interseccion(
                        ventanas_libres,
                        turnos_por_recurso_fecha[(tipo, recurso.id, fecha)],
                    )
                    fila = next(item for item in dias[fecha.isoformat()]['recursos'][clave]
                                if item['recurso_id'] == recurso.id)
                    fila['minutos_disponibles'] = disponibles
                    fila['minutos_ocupados'] = ocupados
                    fila['ocupacion_porcentaje'] = (
                        round(ocupados * 100 / disponibles, 2) if disponibles else None)

    return {
        'zona': 'America/Argentina/Mendoza',
        'desde': inicio.isoformat(),
        'hasta': fin.isoformat(),
        'dias': [dias[fecha.isoformat()] for fecha in fechas],
    }


def consultar_reporte_financiero(engine, desde: object, hasta: object) -> dict[str, object]:
    inicio, fin = normalizar_rango_local(desde, hasta)
    inicio_utc = _limite_utc(inicio)
    fin_utc = _limite_utc(fin)
    fechas = [inicio + timedelta(days=offset) for offset in range((fin - inicio).days)]
    acumulados = {
        fecha.isoformat(): {
            'cargos': {'cantidad': 0, 'centavos': 0},
            'cobros': {'cantidad': 0, 'centavos': 0},
            'reversiones': {'cantidad': 0, 'centavos': 0},
        }
        for fecha in fechas
    }
    apertura = 0
    modelos = (
        (CargoFinanciero, 'cargos', 1),
        (CobroFinanciero, 'cobros', -1),
        (ReversionCobro, 'reversiones', 1),
    )
    with Session(engine) as session:
        movimientos = union_all(*(
            select(
                literal(clave).label('tipo'),
                literal(signo).label('signo'),
                modelo.monto_centavos.label('monto_centavos'),
                modelo.created_at.label('created_at'),
            ).where(modelo.created_at < fin_utc)
            for modelo, clave, signo in modelos
        )).subquery()
        filas = session.execute(select(
            movimientos.c.tipo,
            movimientos.c.signo,
            movimientos.c.monto_centavos,
            movimientos.c.created_at,
        )).all()
        for clave, signo, monto, creado in filas:
            instante = _como_utc(creado)
            centavos = int(monto)
            fecha_local = instante.astimezone(ZONA_REPORTES).date()
            if instante < inicio_utc:
                apertura += int(signo) * centavos
                continue
            resumen = acumulados.get(fecha_local.isoformat())
            if resumen is not None:
                resumen[clave]['cantidad'] += 1
                resumen[clave]['centavos'] += centavos

    dias = []
    saldo = apertura
    for fecha in fechas:
        resumen = acumulados[fecha.isoformat()]
        cargos = resumen['cargos']['centavos']
        cobros = resumen['cobros']['centavos']
        reversiones = resumen['reversiones']['centavos']
        neto = cobros - reversiones
        saldo += cargos - cobros + reversiones
        dias.append({
            'fecha': fecha.isoformat(),
            'cargos': _resumen_monetario(resumen['cargos']),
            'cobros': _resumen_monetario(resumen['cobros']),
            'reversiones': _resumen_monetario(resumen['reversiones']),
            'neto_ars': _formatear_centavos(neto),
            'saldo_cierre_ars': centavos_a_importe_ars(saldo),
        })
    return {
        'zona': 'America/Argentina/Mendoza',
        'desde': inicio.isoformat(),
        'hasta': fin.isoformat(),
        'saldo_apertura_ars': centavos_a_importe_ars(apertura),
        'dias': dias,
    }


def _fecha_local(valor: object) -> date:
    if not isinstance(valor, str):
        raise ValueError('La fecha debe usar YYYY-MM-DD.')
    try:
        fecha = date.fromisoformat(valor)
    except ValueError as exc:
        raise ValueError('La fecha debe usar YYYY-MM-DD.') from exc
    if fecha.isoformat() != valor:
        raise ValueError('La fecha debe usar YYYY-MM-DD.')
    return fecha


def _tramos_del_dia(session: Session, recurso_id: str, columna: str,
                     fecha: date) -> list[tuple[int, int]]:
    excepcion = session.scalar(select(ExcepcionHorario).where(
        getattr(ExcepcionHorario, columna) == recurso_id,
        ExcepcionHorario.fecha_local == fecha,
    ))
    if excepcion is not None:
        filas = session.execute(select(
            # An empty exception intentionally means the resource is closed.
            TramoExcepcion.inicio_minuto_local,
            TramoExcepcion.fin_minuto_local,
        ).where(
            TramoExcepcion.excepcion_id == excepcion.id,
        ).order_by(TramoExcepcion.inicio_minuto_local)).all()
    else:
        filas = session.execute(select(
            HorarioSemanal.inicio_minuto_local,
            HorarioSemanal.fin_minuto_local,
        ).where(
            getattr(HorarioSemanal, columna) == recurso_id,
            HorarioSemanal.dia_iso == fecha.isoweekday(),
        ).order_by(HorarioSemanal.inicio_minuto_local)).all()
    return [(int(inicio), int(fin)) for inicio, fin in filas]


def _minuto_utc(fecha: date, minuto_local: int) -> int:
    fecha_local = fecha + timedelta(days=minuto_local // 1440)
    minuto_del_dia = minuto_local % 1440
    instante = datetime.combine(
        fecha_local,
        time(hour=minuto_del_dia // 60, minute=minuto_del_dia % 60),
        tzinfo=ZONA_REPORTES,
    )
    return int(instante.astimezone(timezone.utc).timestamp() // 60)


def _limite_utc(fecha: date) -> datetime:
    return datetime.combine(fecha, time.min, tzinfo=ZONA_REPORTES).astimezone(timezone.utc)


def _como_utc(instante: datetime) -> datetime:
    if instante.tzinfo is None:
        return instante.replace(tzinfo=timezone.utc)
    return instante.astimezone(timezone.utc)


def _resumen_monetario(resumen: dict[str, int]) -> dict[str, object]:
    return {
        'cantidad': resumen['cantidad'],
        'importe_ars': centavos_a_importe_ars(resumen['centavos']),
    }


def _formatear_centavos(centavos: int) -> str:
    signo = '-' if centavos < 0 else ''
    return signo + centavos_a_importe_ars(abs(centavos))


def serializar_reporte_agenda_csv(reporte: dict[str, object]) -> str:
    salida = StringIO(newline='')
    writer = csv.writer(salida, lineterminator='\r\n')
    writer.writerow([
        'fecha', 'tipo_fila', 'estado', 'cantidad', 'minutos', 'tipo_recurso',
        'recurso_id', 'minutos_disponibles', 'minutos_ocupados', 'ocupacion_porcentaje',
    ])
    for dia in reporte['dias']:
        for estado, totales in dia['estados'].items():
            writer.writerow([
                dia['fecha'], 'estado', estado, totales['cantidad'], totales['minutos'],
                '', '', '', '', '',
            ])
        for tipo, clave in (('profesional', 'profesionales'), ('box', 'boxes')):
            for recurso in dia['recursos'][clave]:
                porcentaje = recurso['ocupacion_porcentaje']
                writer.writerow([
                    dia['fecha'], 'recurso', '', '', '', tipo,
                    _neutralizar_formula(str(recurso['recurso_id'])),
                    recurso['minutos_disponibles'], recurso['minutos_ocupados'],
                    '' if porcentaje is None else f"{porcentaje:.2f}",
                ])
    return salida.getvalue()


def serializar_reporte_financiero_csv(reporte: dict[str, object]) -> str:
    salida = StringIO(newline='')
    writer = csv.writer(salida, lineterminator='\r\n')
    writer.writerow([
        'fecha', 'cargos_cantidad', 'cargos_ars', 'cobros_cantidad', 'cobros_ars',
        'reversiones_cantidad', 'reversiones_ars', 'neto_ars',
        'saldo_apertura_ars', 'saldo_cierre_ars',
    ])
    for dia in reporte['dias']:
        writer.writerow([
            dia['fecha'], dia['cargos']['cantidad'], dia['cargos']['importe_ars'],
            dia['cobros']['cantidad'], dia['cobros']['importe_ars'],
            dia['reversiones']['cantidad'], dia['reversiones']['importe_ars'],
            dia['neto_ars'], reporte['saldo_apertura_ars'], dia['saldo_cierre_ars'],
        ])
    return salida.getvalue()


def _neutralizar_formula(valor: str) -> str:
    if valor.lstrip(' \t\r\n').startswith(('=', '+', '-', '@')):
        return "'" + valor
    return valor


def _fecha_turno_local(inicio_minuto: int) -> date:
    return datetime.fromtimestamp(inicio_minuto * 60, timezone.utc).astimezone(ZONA_REPORTES).date()


def _unir(intervalos: list[tuple[int, int]]) -> list[tuple[int, int]]:
    resultado = []
    for inicio, fin in sorted((a, b) for a, b in intervalos if a < b):
        if resultado and inicio <= resultado[-1][1]:
            resultado[-1] = (resultado[-1][0], max(resultado[-1][1], fin))
        else:
            resultado.append((inicio, fin))
    return resultado


def _restar_intervalos(
        ventanas: list[tuple[int, int]], bloqueos: list[tuple[int, int]]) -> list[tuple[int, int]]:
    libres = []
    bloqueos_unidos = _unir(bloqueos)
    for inicio, fin in ventanas:
        cursor = inicio
        for bloqueo_inicio, bloqueo_fin in bloqueos_unidos:
            if bloqueo_fin <= cursor:
                continue
            if bloqueo_inicio >= fin:
                break
            if bloqueo_inicio > cursor:
                libres.append((cursor, min(fin, bloqueo_inicio)))
            cursor = max(cursor, min(fin, bloqueo_fin))
            if cursor >= fin:
                break
        if cursor < fin:
            libres.append((cursor, fin))
    return libres


def _duracion_union(intervalos: list[tuple[int, int]]) -> int:
    return sum(fin - inicio for inicio, fin in _unir(intervalos))


def _duracion_interseccion(
        ventanas: list[tuple[int, int]], intervalos: list[tuple[int, int]]) -> int:
    intersecciones = []
    for inicio, fin in _unir(intervalos):
        for ventana_inicio, ventana_fin in ventanas:
            inicio_comun = max(inicio, ventana_inicio)
            fin_comun = min(fin, ventana_fin)
            if inicio_comun < fin_comun:
                intersecciones.append((inicio_comun, fin_comun))
    return _duracion_union(intersecciones)
