"""API temporal para los E2E: sólo datos ficticios y archivo efímero."""
from pathlib import Path
import os
import signal
import sys
import tempfile

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'backend'))

from odontologia import inicializar_agenda  # noqa: E402
from odontologia.auth.almacenamiento import crear_engine_autenticacion  # noqa: E402
from odontologia.auth.migraciones import migrar_sqlite  # noqa: E402
from odontologia.auth.usuarios import crear_primer_administrador, crear_usuario  # noqa: E402
from odontologia.catalogos import crear_recurso  # noqa: E402
from odontologia.disponibilidad import guardar_horario  # noqa: E402
from odontologia.pacientes import crear_paciente  # noqa: E402
from odontologia.api import crear_app  # noqa: E402


def main() -> None:
    if not os.environ.get('JWT_SECRETO'):
        raise SystemExit('El entorno E2E debe proporcionar un JWT_SECRETO de prueba.')

    raiz_temporal = os.environ.get('ODONTOLOGIA_E2E_TEMP_ROOT')
    if raiz_temporal:
        Path(raiz_temporal).mkdir(parents=True, exist_ok=True)
    temporal = tempfile.TemporaryDirectory(prefix='tp-odontologia-e2e-', dir=raiz_temporal)

    def detener(_signum, _frame):
        temporal.cleanup()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, detener)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, detener)

    try:
        ruta_db = Path(temporal.name) / 'agenda.sqlite3'
        inicializar_agenda(ruta_db)
        migrar_sqlite(ruta_db)
        engine = crear_engine_autenticacion('sqlite', None, ruta_db)
        try:
            crear_primer_administrador(engine, 'admin.e2e', 'Clave-E2E-admin-2026!')
            crear_usuario(engine, 'recepcion.e2e', 'Clave-E2E-recepcion-2026!', 'recepcion')
            profesional = crear_recurso(engine, 'profesionales', {'nombre': 'Dra. E2E'})
            box = crear_recurso(engine, 'boxes', {'nombre': 'Box E2E'})
            crear_paciente(engine, 'Paciente Ficticio E2E', '+54 261 555-0199')
            jornadas = {str(dia): [{'inicio': '09:00', 'fin': '18:00'}] for dia in range(1, 8)}
            guardar_horario(engine, 'profesional', profesional['id'], jornadas)
            guardar_horario(engine, 'box', box['id'], jornadas)
        finally:
            engine.dispose()

        import uvicorn

        uvicorn.run(crear_app(ruta_db), host='127.0.0.1', port=8180, log_level='warning')
    finally:
        temporal.cleanup()


if __name__ == '__main__':
    main()
