#!/bin/bash

export DJANGO_SETTINGS_MODULE=config.settings

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
python manage.py load_metrics
python manage.py update_health_scores

# Create default councillor accounts (one per ward) if they don't exist
echo "Creating default councillor accounts..."
python -c "
import django; django.setup()
from django.contrib.auth.models import User
from api.models import Ward, UserProfile

for ward in Ward.objects.all():
    name = ward.ward_name.lower().replace('/', '_')
    username = f'{name}ward'
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username,
            password='123456',
            email=f'{name}ward@urbaniq.local',
        )
        user.profile.role = 'councillor'
        user.profile.ward = ward
        user.profile.save()
        print(f'  Created councillor: {username} (Ward {ward.ward_name})')
    else:
        print(f'  Skipped (exists): {username}')
"
echo "Seed data loaded."

exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
