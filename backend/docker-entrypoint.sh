#!/bin/sh
# Prepara una agenda ficticia de C-01 sólo si no existe y levanta la API.
set -e
if [ ! -f "$ODONTOLOGIA_DB" ]; then
  python -c "import os; from odontologia import inicializar_agenda; inicializar_agenda(os.environ['ODONTOLOGIA_DB'])"
fi
exec uvicorn odontologia.api:crear_app --factory --host 0.0.0.0 --port 8000
