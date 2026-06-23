"""
Seed realistic complaints for wards A, B, C, L with proper lat/lng
so they appear on the councillor portal complaint map.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from api.models import Ward, Complaint

WARD_BOUNDS = {
    'A': {'lat': (18.905, 18.940), 'lng': (72.810, 72.840)},
    'B': {'lat': (18.940, 18.975), 'lng': (72.810, 72.835)},
    'C': {'lat': (18.965, 19.000), 'lng': (72.810, 72.840)},
    'L': {'lat': (19.050, 19.100), 'lng': (72.860, 72.900)},
}

SEED_DATA = {
    'pothole': {
        'weight': 30,
        'templates': [
            "Deep pothole on {road} near {landmark}, causing traffic congestion and risk to commuters",
            "Large pothole on {road}, approximately 2 feet deep. Multiple vehicles damaged last week",
            "Series of potholes along {road} stretch near {landmark},急需 repair",
            "Pothole at junction of {road} and {cross}, tyres burst risk for two-wheelers",
            "Stretch of {road} between {landmark} and {landmark2} has multiple dangerous potholes",
            "Deep crater on {road} after recent rains, no warning signs placed by BMC",
            "Pothole repeatedly patched but opens again after every rain on {road}",
            "Road surface completely deteriorated on {road}, potholes spanning entire width",
        ]
    },
    'garbage': {
        'weight': 25,
        'templates': [
            "Garbage not collected for over a week at {landmark}, foul smell affecting residents",
            "Overflowing garbage bin at corner of {road} and {cross}, stray dogs散 waste",
            "Illegal dumping site behind {landmark}, BMC not taking action despite multiple complaints",
            "Mixed waste dumped on footpath along {road}, pedestrian movement blocked",
            "Construction debris dumped on roadside near {landmark} for over a month",
            "Garbage pile attracting rodents and stray animals near {landmark}",
            "No door-to-door waste collection in {road} area for the past two weeks",
            "Burning of garbage near {landmark} causing respiratory issues for residents",
        ]
    },
    'water': {
        'weight': 15,
        'templates': [
            "Water pipeline burst on {road},大量 water wastage for past 3 days",
            "No water supply in {road} area for 48 hours, residents severely affected",
            "Dirty/muddy water coming from taps in {landmark} area since last week",
            "Water leakage from main pipeline at junction of {road} and {cross}",
            "Low water pressure in {road} area, insufficient for overhead tank filling",
            "Broken water meter at {landmark} needs replacement",
            "Water logging due to leaking pipe on {road} near {landmark}",
            "Unauthorized water connection tapping from main line on {road}",
        ]
    },
    'drainage': {
        'weight': 15,
        'templates': [
            "Drainage line blocked on {road}, sewage overflowing onto street near {landmark}",
            "Storm water drain clogged with debris at {landmark}, water logging during rains",
            "Open manhole cover on {road} near {landmark}, risk to pedestrians and vehicles",
            "Drainage water mixing with drinking water pipeline near {landmark}",
            "Stagnant water in drain on {road} breeding mosquitoes since weeks",
            "Drain covers stolen on {road} stretch, multiple open drains hazardous",
            "Sewage backflow into homes on {road} during peak hours",
            "Illegal dumping in storm water drain at {landmark} causing blockages",
        ]
    },
    'streetlight': {
        'weight': 10,
        'templates': [
            "Street lights not working on {road} for the past 10 days, dark stretch near {landmark}",
            "Multiple street light poles damaged on {road} after vehicle collision near {landmark}",
            "Flickering street lights on {road} causing voltage fluctuations in nearby homes",
            "No street lighting on {road} between {landmark} and {landmark2}, safety concern",
            "Street light pole tilting dangerously on {road} near {landmark}",
            "LED street lights installed but not switched on yet on {road}",
        ]
    },
    'road': {
        'weight': 5,
        'templates': [
            "Road surface damaged on {road} near {landmark}, needs re-laying",
            "Speed breaker missing on {road} after road work near {landmark}",
            "Footpath encroached by vendors on {road} near {landmark}, pedestrians forced onto road",
            "Road widening work incomplete on {road} since 6 months near {landmark}",
        ]
    },
}

AREAS = {
    'A': {
        'roads': ['Shahid Bhagat Singh Road', 'Colaba Causeway', 'Sassoon Dock Road',
                  'Nathalal Parekh Marg', 'Mahakavi Bhushan Marg', 'Cuffe Parade',
                  'Madame Cama Road', 'Free Press Journal Marg', 'Dinshaw Vachha Road'],
        'landmarks': ['Colaba Market', 'Gateway of India', 'Taj Mahal Palace Hotel',
                      'CSMT Station', 'Regal Cinema', 'Badhwar Park',
                      'Cooperage Football Ground', 'Mantralaya', 'Yacht Club'],
        'crosses': ['Walton Road', 'Wodehouse Road', 'Henry Road', 'Gopalrao Deshmukh Marg']
    },
    'B': {
        'roads': ['Mohandas Karamchand Gandhi Marg', 'Veer Nariman Road', 'D N Road',
                  'Horniman Circle',                   'Ballard Estate', "P D'Mello Road",
                  'Jamshedji Tata Road', 'Sprott Road', 'Cawasji Patel Street'],
        'landmarks': ['Flora Fountain', 'Crawford Market', 'Mumbai University',
                      'Bombay High Court', 'Kala Ghoda', 'Jehangir Art Gallery',
                      'Chhatrapati Shivaji Maharaj Museum', 'St. Thomas Cathedral'],
        'crosses': ['Rustom Sidhwa Marg', 'Mahatma Gandhi Road', 'Mint Road', 'Shoorji Vallabhdas Marg']
    },
    'C': {
        'roads': ['Lamington Road', 'Grant Road', 'Maulana Shaukat Ali Road',
                  'K R Jaju Marg', 'N M Joshi Marg', 'Dr. Babasaheb Ambedkar Road',
                  'Pandit Paluskar Marg', 'Princess Street', 'Mogul Lane'],
        'landmarks': ['Bombay Hospital', 'Grant Road Station', 'Mumbai Central Station',
                      'Marine Drive', 'Babulnath Temple', 'Charni Road',
                      'Opera House', 'Mumbai Police Headquarters'],
        'crosses': ['S V P Road', 'Ravindra Natya Mandir Marg', 'Bhulabhai Desai Road', 'Walkeshwar Road']
    },
    'L': {
        'roads': ['Lal Bahadur Shastri Marg', 'Sion-Trombay Road', 'Jupiter Colony',
                  'Amrut Nagar', 'Sion Main Road', 'Kurla Andheri Road',
                  'Ghatkopar-Mahul Road', 'Chandivali Farm Road', 'Safaee Road'],
        'landmarks': ['Sion Station', 'Kurla Station', 'BARC Hospital',
                      'Phoenix Market City', 'Nehru Nagar', 'Shivaji Park Kurla',
                      'Kurla Bus Depot', 'Holy Family Hospital'],
        'crosses': ['Mohan Gokhale Marg', 'Sahar Road', 'J M Mehta Marg', 'Powai Road']
    }
}

CATEGORY_CHOICES = [c[0] for c in Complaint.CATEGORY_CHOICES]
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

def generate_description(category, ward_name):
    data = SEED_DATA[category]
    template = random.choice(data['templates'])
    area = AREAS[ward_name]
    road = random.choice(area['roads'])
    landmark = random.choice(area['landmarks'])
    landmark2 = random.choice(area['landmarks'])
    cross = random.choice(area['crosses'])

    replacements = [
        ('{road}', road), ('{landmark}', landmark),
        ('{landmark2}', landmark2), ('{cross}', cross),
    ]
    desc = template
    for pattern, value in replacements:
        if pattern in desc:
            desc = desc.replace(pattern, value, 1)
    return desc

class Command(BaseCommand):
    help = 'Seed realistic complaints for wards A, B, C, L with proper lat/lng'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing complaints first')

    def handle(self, *args, **options):
        if options['clear']:
            deleted = Complaint.objects.filter(ward__ward_name__in=['A', 'B', 'C', 'L']).count()
            Complaint.objects.filter(ward__ward_name__in=['A', 'B', 'C', 'L']).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing complaints'))

        for ward_name in ['A', 'B', 'C', 'L']:
            ward = Ward.objects.filter(ward_name=ward_name).first()
            if not ward:
                self.stdout.write(self.style.WARNING(f'Ward {ward_name} not found, skipping'))
                continue

            existing = ward.complaints.count()
            if existing >= 30:
                self.stdout.write(f'Ward {ward_name} already has {existing} complaints, skipping')
                continue

            need = 40 - existing
            if need <= 0:
                continue

            category_pool = []
            for cat, info in SEED_DATA.items():
                category_pool.extend([cat] * info['weight'])

            created = 0
            for _ in range(need):
                category = random.choice(category_pool)
                lat, lng = random_point(WARD_BOUNDS[ward_name])
                description = generate_description(category, ward_name)
                status = random_status()
                created_at = random_date()
                resolved_at = created_at + timedelta(days=random.randint(3, 30)) if status == 'resolved' else None

                Complaint.objects.create(
                    ward=ward,
                    category=category,
                    description=description,
                    latitude=lat,
                    longitude=lng,
                    status=status,
                    created_at=created_at,
                    resolved_at=resolved_at,
                    source='portal',
                )
                created += 1

            self.stdout.write(self.style.SUCCESS(
                f'Ward {ward_name}: created {created} complaints (total: {ward.complaints.count()})'
            ))
