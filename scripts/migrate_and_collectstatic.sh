#!/bin/bash
cd /home/ubuntu/instrument_generator
source venv/bin/activate
python manage.py migrate --noinput
python manage.py collectstatic --noinput
