#!/usr/bin/env bash
set -o errexit

# Install system deps for PostGIS / GeoDjango on Render Ubuntu
apt-get update -qq
apt-get install -y -qq gdal-bin libgdal-dev binutils 2>/dev/null | tail -5

# Set GDAL paths for the build
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate
