"""Límite temporal local para fallos de autenticación."""
from collections import OrderedDict, deque
from dataclasses import dataclass
from hashlib import sha256
from math import ceil
from threading import Lock
from time import monotonic
from uuid import uuid4


@dataclass
class _Intento:
    iniciado: float
    reserva: str | None
    fallo: bool


class LimitadorIntentosLogin:
    """Contador acotado por peer y hash de cuenta, coordinado en este proceso."""

    def __init__(self, *, reloj=monotonic, ventana_segundos: int = 300,
                 max_fallos: int = 5, max_claves: int = 10_000):
        self._reloj = reloj
        self._ventana = ventana_segundos
        self._max_fallos = max_fallos
        self._max_claves = max_claves
        self._intentos: OrderedDict[tuple[str, str], deque[_Intento]] = OrderedDict()
        self._reservas: dict[str, tuple[str, str]] = {}
        self._lock = Lock()

    def _clave(self, origen: str, cuenta_normalizada: str) -> tuple[str, str]:
        hash_cuenta = sha256(cuenta_normalizada.encode('utf-8')).hexdigest()
        return origen, hash_cuenta

    def _purgar_clave(self, clave: tuple[str, str], ahora: float) -> deque[_Intento] | None:
        marcas = self._intentos.get(clave)
        if marcas is None:
            return None
        limite = ahora - self._ventana
        while marcas and marcas[0].iniciado <= limite:
            vencido = marcas.popleft()
            if vencido.reserva is not None:
                self._reservas.pop(vencido.reserva, None)
        if not marcas:
            del self._intentos[clave]
            return None
        self._intentos.move_to_end(clave)
        return marcas

    def _eliminar_clave(self, clave: tuple[str, str]) -> None:
        marcas = self._intentos.pop(clave, ())
        for intento in marcas:
            if intento.reserva is not None:
                self._reservas.pop(intento.reserva, None)

    def _descartar_menos_reciente(self) -> None:
        if not self._intentos:
            return
        _, marcas = self._intentos.popitem(last=False)
        for intento in marcas:
            if intento.reserva is not None:
                self._reservas.pop(intento.reserva, None)

    def _restante(self, marcas: deque[_Intento], ahora: float) -> int:
        primer_intento = marcas[0]
        # Una reserva aún en curso puede liberarse en cualquier momento.
        if primer_intento.reserva is not None:
            return 1
        return max(1, ceil(primer_intento.iniciado + self._ventana - ahora))

    def segundos_hasta_reintento(self, origen: str,
                                 cuenta_normalizada: str) -> int | None:
        clave = self._clave(origen, cuenta_normalizada)
        with self._lock:
            ahora = self._reloj()
            marcas = self._purgar_clave(clave, ahora)
            if marcas is None or len(marcas) < self._max_fallos:
                return None
            return self._restante(marcas, ahora)

    def reservar_intento(self, origen: str,
                         cuenta_normalizada: str) -> tuple[str | None, int | None]:
        """Admitir atómicamente un intento antes del trabajo costoso de credenciales."""
        clave = self._clave(origen, cuenta_normalizada)
        with self._lock:
            ahora = self._reloj()
            marcas = self._purgar_clave(clave, ahora)
            if marcas is not None and len(marcas) >= self._max_fallos:
                return None, self._restante(marcas, ahora)
            if marcas is None:
                if len(self._intentos) >= self._max_claves:
                    self._descartar_menos_reciente()
                marcas = deque()
                self._intentos[clave] = marcas
            token = str(uuid4())
            marcas.append(_Intento(ahora, token, False))
            self._reservas[token] = clave
            self._intentos.move_to_end(clave)
            return token, None

    def finalizar_intento(self, origen: str, cuenta_normalizada: str, reserva: str,
                          *, credenciales_validas: bool | None) -> None:
        """Confirmar fallo, limpiar en éxito o liberar si el intento no fue evaluable."""
        clave_esperada = self._clave(origen, cuenta_normalizada)
        with self._lock:
            ahora = self._reloj()
            clave = self._reservas.pop(reserva, None)
            if clave is None or clave != clave_esperada:
                return
            marcas = self._purgar_clave(clave, ahora)
            if marcas is None:
                return
            intento = next((marca for marca in marcas if marca.reserva == reserva), None)
            if intento is None:
                return
            if credenciales_validas is True:
                # El éxito limpia fallos confirmados, pero deja vivas otras peticiones en curso.
                self._intentos[clave] = deque(
                    marca for marca in marcas
                    if marca.reserva is not None and marca.reserva != reserva)
                if not self._intentos[clave]:
                    del self._intentos[clave]
                return
            if credenciales_validas is False:
                intento.reserva = None
                intento.fallo = True
            else:
                marcas.remove(intento)
                if not marcas:
                    del self._intentos[clave]

    def registrar_fallo(self, origen: str, cuenta_normalizada: str) -> None:
        """Registrar un fallo ya evaluado (también usado por pruebas/consumidores internos)."""
        clave = self._clave(origen, cuenta_normalizada)
        with self._lock:
            ahora = self._reloj()
            marcas = self._purgar_clave(clave, ahora)
            if marcas is None:
                if len(self._intentos) >= self._max_claves:
                    self._descartar_menos_reciente()
                marcas = deque()
                self._intentos[clave] = marcas
            marcas.append(_Intento(ahora, None, True))
            self._intentos.move_to_end(clave)

    def limpiar(self, origen: str, cuenta_normalizada: str) -> None:
        clave = self._clave(origen, cuenta_normalizada)
        with self._lock:
            self._eliminar_clave(clave)
