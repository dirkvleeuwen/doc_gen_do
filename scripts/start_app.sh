#!/usr/bin/env bash
set -euo pipefail

cd /home/ubuntu/instrument_generator

# Activeer de wérkelijke venv
source /home/ubuntu/instrument_generator/venv/bin/activate

# Stop evt. bestaande processen
pkill -f 'gunicorn .*instrument_generator.wsgi' || true

# Start gunicorn bindend op 0.0.0.0:8000
gunicorn instrument_generator.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile - \
  --daemon
