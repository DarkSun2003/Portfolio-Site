#!/bin/bash

# 1. Collect Static Files (CSS, JS) for WhiteNoise
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 2. Run Migrations (Create tables in PostgreSQL)
echo "Running database migrations..."
python manage.py migrate --noinput

# 3. Start the Gunicorn Server
# Note: We use 'myproject.wsgi' because your settings are in the 'myproject' folder
echo "Starting Gunicorn..."
gunicorn myproject.wsgi:application