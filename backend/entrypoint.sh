#!/bin/bash

export DJANGO_SETTINGS_MODULE=config.settings

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

# If api_ward table is still missing (e.g., stale/faked migration state),
# reset and re-apply migrations to create the tables.
if ! python -c "
import django; django.setup()
from django.db import connection
with connection.cursor() as c:
    c.execute(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'api_ward')\")
    exit(0 if c.fetchone()[0] else 1)
" 2>/dev/null; then
    echo "api_ward table missing. Resetting migration state and re-applying..."
    python manage.py migrate api zero --fake 2>/dev/null || true
    python manage.py migrate --noinput
fi

echo "Loading seed data..."
python manage.py load_wards
python manage.py load_metrics --csv data/ward_metrics_multiyear_2025.csv
python manage.py update_health_scores

# Create/reset default councillor accounts (one per ward)
echo "Creating/resetting default councillor accounts..."
python -c "
import django; django.setup()
from django.contrib.auth.models import User
from api.models import Ward, UserProfile

for ward in Ward.objects.all():
    name = ward.ward_name.lower().replace('/', '_')
    username = f'{name}ward'
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{name}ward@urbaniq.local',
        }
    )
    user.set_password('123456')
    user.email = f'{name}ward@urbaniq.local'
    user.save()

    profile = user.profile
    profile.role = 'councillor'
    profile.ward = ward
    profile.save()

    if created:
        print(f'  Created councillor: {username} (Ward {ward.ward_name})')
    else:
        print(f'  Reset password for: {username} (Ward {ward.ward_name})')
"
# Train ML models (ensures fresh models on every deploy)
echo "Training ML models..."
python manage.py train_models

# Seed realistic complaints with lat/lng for map visibility
echo "Seeding complaints for map..."
python manage.py seed_complaints
echo "Seed data loaded."

exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level debug --error-logfile -
