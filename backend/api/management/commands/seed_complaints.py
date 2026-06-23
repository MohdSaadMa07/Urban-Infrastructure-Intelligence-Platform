"""
Seed realistic complaints for all wards with proper lat/lng
so they appear on the complaint map and councillor portal.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from api.models import Ward, Complaint

WARD_BOUNDS = {
    'A':   {'lat': (18.905, 18.940), 'lng': (72.810, 72.840)},
    'B':   {'lat': (18.940, 18.975), 'lng': (72.810, 72.835)},
    'C':   {'lat': (18.965, 19.000), 'lng': (72.810, 72.840)},
    'D':   {'lat': (18.930, 18.970), 'lng': (72.790, 72.820)},
    'E':   {'lat': (18.970, 19.010), 'lng': (72.820, 72.850)},
    'F/N': {'lat': (19.020, 19.060), 'lng': (72.830, 72.870)},
    'F/S': {'lat': (19.000, 19.040), 'lng': (72.820, 72.860)},
    'G/N': {'lat': (19.040, 19.080), 'lng': (72.840, 72.880)},
    'G/S': {'lat': (19.040, 19.080), 'lng': (72.820, 72.850)},
    'H/E': {'lat': (19.100, 19.140), 'lng': (72.840, 72.880)},
    'H/W': {'lat': (19.100, 19.140), 'lng': (72.820, 72.850)},
    'K/E': {'lat': (19.070, 19.120), 'lng': (72.880, 72.930)},
    'K/W': {'lat': (19.070, 19.110), 'lng': (72.820, 72.860)},
    'L':   {'lat': (19.050, 19.100), 'lng': (72.860, 72.900)},
    'M/E': {'lat': (19.040, 19.080), 'lng': (72.880, 72.920)},
    'M/W': {'lat': (19.020, 19.060), 'lng': (72.870, 72.910)},
    'N':   {'lat': (19.080, 19.160), 'lng': (72.890, 72.960)},
    'P/N': {'lat': (19.150, 19.220), 'lng': (72.820, 72.870)},
    'P/S': {'lat': (19.140, 19.190), 'lng': (72.830, 72.860)},
    'R/C': {'lat': (19.200, 19.260), 'lng': (72.830, 72.870)},
    'R/N': {'lat': (19.140, 19.200), 'lng': (72.920, 72.970)},
    'R/S': {'lat': (19.100, 19.140), 'lng': (72.880, 72.920)},
    'S':   {'lat': (19.110, 19.160), 'lng': (72.900, 72.950)},
    'T':   {'lat': (19.160, 19.200), 'lng': (72.930, 72.980)},
}

SEED_DATA = {
    'pothole': {
        'weight': 30,
        'templates': [
            "Deep pothole on {road} near {landmark}, causing traffic congestion",
            "Large pothole on {road} approximately 2 feet deep, vehicles damaged",
            "Series of potholes along {road} stretch near {landmark}",
            "Pothole at junction of {road} and main road, dangerous for two-wheelers",
            "Road surface completely deteriorated on {road}, potholes spanning entire width",
            "Deep crater on {road} after recent rains, no warning signs placed",
            "Pothole repeatedly patched but opens again after every rain on {road}",
        ]
    },
    'garbage': {
        'weight': 25,
        'templates': [
            "Garbage not collected for over a week at {landmark}, foul smell affecting residents",
            "Overflowing garbage bin at {road} near {landmark}, stray dogs散 waste",
            "Illegal dumping site behind {landmark}, BMC not acting despite complaints",
            "Mixed waste dumped on footpath along {road}, pedestrian movement blocked",
            "Construction debris dumped on roadside near {landmark} for over a month",
            "Garbage pile attracting rodents and stray animals near {landmark}",
            "No door-to-door waste collection in {road} area for two weeks",
        ]
    },
    'water': {
        'weight': 15,
        'templates': [
            "Water pipeline burst on {road},大量 water wastage for past 3 days",
            "No water supply in {road} area for 48 hours, residents severely affected",
            "Dirty/muddy water coming from taps in {landmark} area since last week",
            "Water leakage from main pipeline at junction of {road} near {landmark}",
            "Low water pressure in {road} area, insufficient for overhead tank filling",
            "Water logging due to leaking pipe on {road} near {landmark}",
        ]
    },
    'drainage': {
        'weight': 15,
        'templates': [
            "Drainage line blocked on {road}, sewage overflowing onto street near {landmark}",
            "Storm water drain clogged with debris at {landmark}, water logging during rains",
            "Open manhole cover on {road} near {landmark}, risk to pedestrians",
            "Stagnant water in drain on {road} breeding mosquitoes since weeks",
            "Drain covers stolen on {road}, multiple open drains hazardous",
            "Sewage backflow into homes on {road} during peak hours",
        ]
    },
    'streetlight': {
        'weight': 10,
        'templates': [
            "Street lights not working on {road} for 10 days, dark stretch near {landmark}",
            "Multiple street light poles damaged on {road} after vehicle collision",
            "Flickering street lights on {road} causing voltage fluctuations",
            "No street lighting on {road} near {landmark}, safety concern at night",
            "Street light pole tilting dangerously on {road} near {landmark}",
        ]
    },
    'road': {
        'weight': 5,
        'templates': [
            "Road surface damaged on {road} near {landmark}, needs re-laying",
            "Speed breaker missing on {road} after road work near {landmark}",
            "Footpath encroached by vendors on {road} near {landmark}, pedestrians forced onto road",
        ]
    },
}

MUMBAI_ROADS = [
    'Main Road', 'Station Road', 'Market Road', 'Linking Road',
    'S V Road', 'Western Express Highway', 'Eastern Express Highway',
    'LBS Marg', 'Jogeshwari-Vikhroli Link Road', 'Andheri Kurla Road',
    'Marve Road', 'Aarey Road', 'New Link Road', 'Milan Subway Road',
    'Veera Desai Road', 'Mahakali Caves Road', 'Sahar Road',
    'Ghatkopar-Mahul Road', 'Powai Road', 'Chandivali Farm Road',
    'Kandivali Link Road', 'Borivali Link Road', 'Dahisar Link Road',
    'Mulund Check Naka Road', 'Bhandup Village Road', 'Kanjurmarg Road',
]

MUMBAI_LANDMARKS = [
    'Railway Station', 'BMC Office', 'Bus Depot', 'Market',
    'School', 'Hospital', 'Police Station', 'Post Office',
    'Temple', 'Mosque', 'Church', 'Park', 'Shopping Complex',
    'Petrol Pump', 'Flyover', 'Bridge', 'Waste Transfer Station',
    'Fire Station', 'Community Hall', 'Municipal Garden',
]

COMPLAINTS_PER_WARD = 25

STATUS_CHOICES = ['open', 'in_progress', 'resolved']
STATUS_WEIGHTS = [60, 25, 15]

def random_point(bounds):
    lat = random.uniform(*bounds['lat'])
    lng = random.uniform(*bounds['lng'])
    return round(lat, 6), round(lng, 6)

def random_date():
    days_ago = random.randint(0, 180)
    return datetime.now() - timedelta(days=days_ago)

def random_status():
    return random.choices(STATUS_CHOICES, weights=STATUS_WEIGHTS, k=1)[0]

def generate_description(category):
    data = SEED_DATA[category]
    template = random.choice(data['templates'])
    road = random.choice(MUMBAI_ROADS)
    landmark = random.choice(MUMBAI_LANDMARKS)
    desc = template.replace('{road}', road).replace('{landmark}', landmark)
    return desc

class Command(BaseCommand):
    help = 'Seed realistic complaints for all wards with proper lat/lng'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear all existing complaints first')
        parser.add_argument('--wards', type=str, default=None,
                          help='Comma-separated ward names (default: all)')

    def handle(self, *args, **options):
        if options['clear']:
            deleted = Complaint.objects.count()
            Complaint.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing complaints'))

        target_wards = options['wards'].split(',') if options['wards'] else list(WARD_BOUNDS.keys())

        total_created = 0
        for ward_name in target_wards:
            ward = Ward.objects.filter(ward_name__iexact=ward_name.strip()).first()
            if not ward:
                self.stdout.write(self.style.WARNING(f'Ward {ward_name} not found, skipping'))
                continue

            existing = ward.complaints.count()
            need = COMPLAINTS_PER_WARD - existing
            if need <= 0:
                self.stdout.write(f'Ward {ward_name}: already has {existing} complaints, skipping')
                continue

            bounds = WARD_BOUNDS.get(ward_name)
            if not bounds:
                self.stdout.write(self.style.WARNING(f'No bounds for ward {ward_name}, skipping'))
                continue

            category_pool = []
            for cat, info in SEED_DATA.items():
                category_pool.extend([cat] * info['weight'])

            created = 0
            for _ in range(need):
                category = random.choice(category_pool)
                lat, lng = random_point(bounds)
                description = generate_description(category)
                status = random_status()
                created_at = random_date()
                resolved_at = created_at + timedelta(days=random.randint(3, 30)) if status == 'resolved' else None

                Complaint.objects.create(
                    ward=ward, category=category, description=description,
                    latitude=lat, longitude=lng, status=status,
                    created_at=created_at, resolved_at=resolved_at,
                    source='portal',
                )
                created += 1

            total_created += created
            self.stdout.write(f'Ward {ward_name}: created {created} complaints (total: {ward.complaints.count()})')

        self.stdout.write(self.style.SUCCESS(f'Done — created {total_created} complaints total'))
