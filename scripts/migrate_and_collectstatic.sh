#!/usr/bin/env bash
set -euo pipefail

# Ga naar project-dir
cd /home/ubuntu/instrument_generator

# Exporteer alle vars uit .env
set -o allexport
source .env
set +o allexport

# Activeer virtuele omgeving
source venv/bin/activate

# Migrate & collectstatic
python manage.py migrate --noinput
python manage.py collectstatic --noinput