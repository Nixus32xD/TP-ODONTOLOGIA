"""Aritmética monetaria exacta para el ledger sintético del consultorio."""

import re
from collections.abc import Iterable


MAXIMO_CENTAVOS = 99_999_999_999
_IMPORTE_ARS = re.compile(r"(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,2})?\Z")


def importe_ars_a_centavos(importe: str) -> int:
    """Convierte texto decimal positivo a centavos sin pasar por punto flotante."""
    if not isinstance(importe, str) or not _IMPORTE_ARS.fullmatch(importe):
        raise ValueError('El importe debe ser texto decimal ARS con hasta dos decimales.')
    entero, _separador, fraccion = importe.partition('.')
    centavos = int(entero) * 100 + int((fraccion + '00')[:2])
    if centavos <= 0 or centavos > MAXIMO_CENTAVOS:
        raise ValueError('El importe debe ser positivo y no superar ARS 999999999.99.')
    return centavos


def centavos_a_importe_ars(centavos: int) -> str:
    if isinstance(centavos, bool) or not isinstance(centavos, int):
        raise ValueError('El importe interno debe expresarse en centavos enteros.')
    if centavos < 0:
        raise ValueError('Los centavos no pueden ser negativos.')
    return f'{centavos // 100}.{centavos % 100:02d}'


def saldo_centavos(*, cargos: Iterable[int], cobros: Iterable[int],
                   reversiones: Iterable[int]) -> int:
    cargos = tuple(cargos)
    cobros = tuple(cobros)
    reversiones = tuple(reversiones)
    if any(type(valor) is not int or valor <= 0
           for valor in (*cargos, *cobros, *reversiones)):
        raise ValueError('Los movimientos deben ser importes positivos en centavos enteros.')
    saldo = sum(cargos) - sum(cobros) + sum(reversiones)
    if saldo < 0:
        raise ValueError('Los movimientos producen un saldo negativo inválido.')
    return saldo


def importe_reversible_centavos(importe_cobro: int,
                                reversiones: Iterable[int]) -> int:
    reversiones = tuple(reversiones)
    if type(importe_cobro) is not int or importe_cobro <= 0 or any(
            type(valor) is not int or valor <= 0 for valor in reversiones):
        raise ValueError('El cobro y las reversiones deben ser centavos positivos.')
    restante = importe_cobro - sum(reversiones)
    if restante < 0:
        raise ValueError('Las reversiones exceden el cobro original.')
    return restante
