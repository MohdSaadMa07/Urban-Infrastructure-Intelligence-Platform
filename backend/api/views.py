from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from api.models import Ward, CivicMetrics, Complaint
from api.services.health_score import compute_health_score
import json

def home(request):
    return JsonResponse({
        "message": "API is working "
    })

@api_view(['GET'])
def identify_ward(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    
    if not lat or not lng:
        return Response({'error': 'Please provide lat and lng'}, status=400)
        
    try:
        # PostGIS uses (longitude, latitude) for Point
        point = Point(float(lng), float(lat), srid=4326)
        
        # Native spatial query
        ward = Ward.objects.filter(boundary__contains=point).first()
        
        if ward:
            return Response({
                'ward_name': ward.ward_name,
                'ward_no': ward.ward_no
            })
        else:
            return Response({'message': 'No ward found for this location'}, status=404)
            
    except ValueError:
        return Response({'error': 'Invalid coordinates'}, status=400)

@api_view(['GET'])
def wards_geojson(request):
    # Retrieve all wards
    wards = Ward.objects.all()
    
    features = []
    for ward in wards:
        feature = {
            "type": "Feature",
            "properties": {
                "ward_no": ward.ward_no,
                "ward_name": ward.ward_name
            },
            "geometry": json.loads(ward.boundary.geojson)
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return Response(geojson)


@api_view(['GET'])
def health_scores(request):
    """
    Return health scores for all wards, including underlying metrics
    and a qualitative label (Good / Moderate / Poor).

    Optional query params:
        ?ward=<ward_name>   — filter to a single ward
        ?year=<year>        — use metrics from a specific year (default: latest)
    """
    ward_filter = request.GET.get('ward')
    year_filter = request.GET.get('year')

    wards = Ward.objects.all()
    if ward_filter:
        wards = wards.filter(ward_name__iexact=ward_filter.strip())

    results = []
    for ward in wards:
        metrics_qs = ward.metrics.all()
        if year_filter:
            metrics_qs = metrics_qs.filter(year=int(year_filter))
        latest = metrics_qs.order_by('-year').first()

        if latest:
            result = compute_health_score(latest)
            results.append({
                'ward_no': ward.ward_no,
                'ward_name': ward.ward_name,
                'year': latest.year,
                'health_score': result['score'],
                'label': result['label'],
                'metrics': {
                    'total_complaints': latest.total_complaints,
                    'closed_complaints': latest.closed_complaints,
                    'escalated_complaints': latest.escalated_complaints,
                    'avg_resolution_days': latest.avg_resolution_days,
                    'per_capita_complaints': latest.per_capita_complaints,
                    'total_deliberations': latest.total_deliberations,
                },
                'breakdown': result['breakdown'],
            })
        else:
            results.append({
                'ward_no': ward.ward_no,
                'ward_name': ward.ward_name,
                'year': None,
                'health_score': None,
                'label': 'No Data',
                'metrics': None,
                'breakdown': None,
            })

    return Response(results)


@api_view(['POST'])
def submit_complaint(request):
    """Create a complaint. Auto-detects ward from coordinates."""
    category = request.data.get('category')
    description = request.data.get('description')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if not all([category, description, latitude, longitude]):
        return Response(
            {'error': 'category, description, latitude, and longitude are required.'},
            status=400,
        )

    valid_categories = [c[0] for c in Complaint.CATEGORY_CHOICES]
    if category not in valid_categories:
        return Response(
            {'error': f'Invalid category. Choose from: {valid_categories}'},
            status=400,
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return Response({'error': 'Invalid coordinates'}, status=400)

    point = Point(longitude, latitude, srid=4326)
    ward = Ward.objects.filter(boundary__contains=point).first()

    if not ward:
        return Response(
            {'error': 'Location does not fall within any known ward.'},
            status=404,
        )

    complaint = Complaint.objects.create(
        ward=ward,
        category=category,
        description=description,
        latitude=latitude,
        longitude=longitude,
    )

    return Response(
        {
            'id': complaint.id,
            'category': complaint.get_category_display(),
            'description': complaint.description,
            'latitude': complaint.latitude,
            'longitude': complaint.longitude,
            'status': complaint.status,
            'ward_no': ward.ward_no,
            'ward_name': ward.ward_name,
            'created_at': complaint.created_at.isoformat(),
        },
        status=201,
    )


@api_view(['GET'])
def list_complaints(request):
    """List complaints, optionally filtered by ward name."""
    ward_name = request.GET.get('ward')
    qs = Complaint.objects.select_related('ward').all()

    if ward_name:
        qs = qs.filter(ward__ward_name__iexact=ward_name.strip())

    data = [
        {
            'id': c.id,
            'category': c.get_category_display(),
            'description': c.description,
            'latitude': c.latitude,
            'longitude': c.longitude,
            'status': c.status,
            'ward_no': c.ward.ward_no,
            'ward_name': c.ward.ward_name,
            'created_at': c.created_at.isoformat(),
        }
        for c in qs
    ]

    return Response(data)