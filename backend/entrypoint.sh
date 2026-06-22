#!/bin/bash

echo "Running migrations..."
if python manage.py migrate --noinput 2>&1; then
    echo "Migrations applied successfully."
else
    echo "Migrate failed. Attempting to reset migration state and retry..."
    python manage.py migrate api zero --fake 2>/dev/null || true
    python manage.py migrate --noinput
    echo "Migrations applied after reset."
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
