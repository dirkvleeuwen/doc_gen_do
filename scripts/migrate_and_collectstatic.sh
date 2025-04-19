#!/usr/bin/env bash
set -euo pipefail

# Ga naar project-dir
cd /home/ubuntu/instrument_generator

# Controle: toon even de bucket (debug)
echo ">> Bucket from .env is: ${AWS_STORAGE_BUCKET_NAME:-<unset>}"

# Exporteer alle vars uit .env
set -o allexport
source .env
set +o allexport

# na source .env
echo ">> Bucket from .env is now: $AWS_STORAGE_BUCKET_NAME"

# Activeer virtuele omgeving
source venv/bin/activate

# Migrate & collectstatic
python manage.py migrate --noinput
python manage.py collectstatic --noinput