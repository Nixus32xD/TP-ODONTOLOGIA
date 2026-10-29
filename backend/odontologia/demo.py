"""Demostración reproducible sin red y con una agenda temporal propia."""

from contextlib import closing
from datetime import datetime
from pathlib import Path
import json
import sqlite3
import tempfile

from .agenda import ErrorAgenda, crear_turno, inicializar_agenda


def ejecutar_demo() -> dict:
    casos = []
    with tempfile.TemporaryDirectory(prefix='odontologia-demo-') as temporal:
        ruta = Path(temporal) / 'agenda.sqlite3'
        inicializar_agenda(ruta)
        base = dict(paciente_id='paciente-A', profesional_id='profesional-A', box_id='box-A',
                    inicio=datetime.fromisoformat('2026-10-15T09:00-03:00'),
                    fin=datetime.fromisoformat('2026-10-15T09:30-03:00'))
        solicitudes = [
            ('alta', {}),
            ('profesional', {'box_id': 'box-B'}),
            ('box', {'profesional_id': 'profesional-B'}),
            ('adyacencia', {'inicio': datetime.fromisoformat('2026-10-15T09:30-03:00'),
                            'fin': datetime.fromisoformat('2026-10-15T10:00-03:00')}),
        ]
        for nombre, cambios in solicitudes:
            try:
                turno = crear_turno(ruta, **(base | cambios))
                casos.append(dict(caso=nombre, resultado='ok', id=turno.id,
                                  inicio=turno.inicio.isoformat(), fin=turno.fin.isoformat()))
            except ErrorAgenda as exc:
                casos.append(dict(caso=nombre, resultado=exc.codigo, mensaje=str(exc)))
        with closing(sqlite3.connect(ruta)) as conexion:
            cantidad = conexion.execute('SELECT COUNT(*) FROM turnos').fetchone()[0]
    return dict(casos=casos, turnos_persistidos=cantidad,
                agenda_temporal_eliminada=not ruta.parent.exists())


if __name__ == '__main__':
    print(json.dumps(ejecutar_demo(), indent=2, ensure_ascii=True))
