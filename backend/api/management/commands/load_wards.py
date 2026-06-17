import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from api.models import Ward
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Load Mumbai ward boundaries into the database'

    def handle(self, *args, **kwargs):
        geojson_path = os.path.join(settings.BASE_DIR, 'mumbai_wards.geojson')
        
        with open(geojson_path, encoding='utf-8') as f:
            data = json.load(f)
            
        count = 0
        for feature in data['features']:
            props = feature['properties']
            geom = GEOSGeometry(json.dumps(feature['geometry']))
            
            # Ensure it's a MultiPolygon
            if isinstance(geom, Polygon):
                geom = MultiPolygon(geom)
                
            ward_name = props.get('name') or props.get('NAME') or props.get('WardName') or 'Unknown'
            # Assuming there's some kind of ID or we just assign one if missing
            ward_no = props.get('gid', count + 1)
            
            ward, created = Ward.objects.get_or_create(
                ward_name=ward_name,
                defaults={
                    'ward_no': ward_no,
                    'boundary': geom
                }
            )
            
            if not created:
                ward.boundary = geom
                ward.ward_no = ward_no
                ward.save()
                
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {count} wards'))
