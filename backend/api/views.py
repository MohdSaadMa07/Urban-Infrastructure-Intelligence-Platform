from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from api.models import Ward, CivicMetrics, Complaint
from api.services.health_score import compute_health_score
from api.serializers import WardSerializer
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
        ?ward=<ward_name>   -- filter to a single ward
        ?year=<year>        -- use metrics from a specific year (default: latest)
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
    """Create a complaint. Auto-detects ward from coordinates or explicit ward_name."""
    category = request.data.get('category')
    description = request.data.get('description')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    ward_name = request.data.get('ward_name')

    if not category or not description:
        return Response(
            {'error': 'category and description are required.'},
            status=400,
        )

    if not ward_name and (latitude is None or longitude is None):
        return Response(
            {'error': 'Either ward_name or both latitude and longitude are required.'},
            status=400,
        )

    valid_categories = [c[0] for c in Complaint.CATEGORY_CHOICES]
    if category not in valid_categories:
        return Response(
            {'error': f'Invalid category. Choose from: {valid_categories}'},
            status=400,
        )

    ward = None
    if ward_name:
        ward = Ward.objects.filter(ward_name=ward_name).first()
        if not ward:
            return Response({'error': f'Invalid ward_name: {ward_name}'}, status=400)
    else:
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

    image = request.FILES.get('image')
    complaint = Complaint.objects.create(
        ward=ward,
        category=category,
        description=description,
        latitude=latitude,
        longitude=longitude,
        image=image,
    )

    return Response(
        {
            'id': complaint.id,
            'category': complaint.get_category_display(),
            'description': complaint.description,
            'latitude': complaint.latitude,
            'longitude': complaint.longitude,
            'image': complaint.image.url if complaint.image else None,
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
            'image': c.image.url if c.image else None,
            'status': c.status,
            'ward_no': c.ward.ward_no,
            'ward_name': c.ward.ward_name,
            'created_at': c.created_at.isoformat(),
        }
        for c in qs
    ]

    return Response(data)


@api_view(['GET'])
def councillors(request):
    """
    Return councillor accountability data for all wards.

    Optional query params:
        ?year=<year>  -- filter to a specific year (default: latest)

    Returns per-ward: ward info, avg_councillors, total_deliberations,
    per_capita_deliberations, and a normalised engagement score (0-100).
    """
    year_filter = request.GET.get('year')

    if not year_filter:
        from django.db.models import Max
        # Default to the latest year with active deliberations/councillors (since 2024-2026 has no elected councillors)
        active_year = CivicMetrics.objects.filter(total_deliberations__gt=0).aggregate(Max('year'))['year__max']
        if active_year:
            year_filter = active_year

    wards = Ward.objects.all()
    results = []

    for ward in wards:
        metrics_qs = ward.metrics.all()
        if year_filter:
            metrics_qs = metrics_qs.filter(year=int(year_filter))
        latest = metrics_qs.order_by('-year').first()

        if latest:
            # Simple engagement score: per_capita_deliberations normalised 0-100
            # Range in data: ~21-104. Clip and scale.
            raw = latest.per_capita_deliberations
            score = round(min(100, max(0, (raw / 104) * 100)), 1)
            results.append({
                'ward_no': ward.ward_no,
                'ward_name': ward.ward_name,
                'year': latest.year,
                'avg_councillors': latest.avg_councillors,
                'total_deliberations': latest.total_deliberations,
                'per_capita_deliberations': latest.per_capita_deliberations,
                'engagement_score': score,
            })
        else:
            results.append({
                'ward_no': ward.ward_no,
                'ward_name': ward.ward_name,
                'year': None,
                'avg_councillors': None,
                'total_deliberations': None,
                'per_capita_deliberations': None,
                'engagement_score': None,
            })

    # Sort by engagement score descending, nulls last
    results.sort(key=lambda x: x['engagement_score'] if x['engagement_score'] is not None else -1, reverse=True)
    return Response(results)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def councillor_ward_dashboard(request):
    profile = request.user.profile
    if profile.role != 'councillor':
        return Response({'error': 'Only councillors can access this endpoint.'}, status=403)

    ward = profile.ward
    if not ward:
        return Response({'error': 'You are not assigned to any ward. Contact admin.'}, status=400)

    ward_info = WardSerializer(ward).data

    latest_metrics = ward.metrics.order_by('-year').first()
    health = None
    if latest_metrics:
        health = compute_health_score(latest_metrics)

    status_filter = request.GET.get('status')
    qs = ward.complaints.all().order_by('-created_at')
    if status_filter and status_filter in [c[0] for c in Complaint.STATUS_CHOICES]:
        qs = qs.filter(status=status_filter)

    complaints = [
        {
            'id': c.id,
            'category': c.get_category_display(),
            'description': c.description,
            'latitude': c.latitude,
            'longitude': c.longitude,
            'image': c.image.url if c.image else None,
            'status': c.status,
            'created_at': c.created_at.isoformat(),
        }
        for c in qs
    ]

    # Fetch the latest ML prediction for this ward
    latest_prediction = ward.predictions.order_by('-prediction_date').first()
    prediction_data = None
    if latest_prediction:
        prediction_data = {
            'prediction_date': latest_prediction.prediction_date.isoformat(),
            'predicted_risk': latest_prediction.predicted_risk,
            'predicted_complaints': latest_prediction.predicted_complaints,
            'predicted_health_score': latest_prediction.predicted_health_score,
            'recommendation': latest_prediction.recommendation,
            'model_version': latest_prediction.model_version,
        }

    # Fetch focus facility insights using ML ward_insights
    from ml.ward_insights import compute_ward_category_scores
    db_categories = set(ward.complaints.values_list('category', flat=True))
    mapping = {
        'pothole': 'Roads',
        'road': 'Roads',
        'water': 'Water Supply',
        'drainage': 'Drainage',
        'garbage': 'Solid Waste Management',
    }
    ward_category_names = {mapping.get(c, c) for c in db_categories}
    category_scores = compute_ward_category_scores(ward.ward_name, ward_category_names)
    
    focus_facility = None
    if category_scores:
        top_facility = category_scores[0]
        display_names = {
            'Roads': 'Roads & Potholes',
            'Water Supply': 'Water Supply',
            'Drainage': 'Drainage & Sewerage',
            'Solid Waste Management': 'Garbage & Solid Waste',
            'Buildings': 'Buildings & Factories',
            'Pest control': 'Pest Control',
            'Garden': 'Gardens & Open Spaces',
            'Storm Water Drainage': 'Storm Water Drainage',
        }
        focus_facility = {
            'category': top_facility['category'],
            'display_name': display_names.get(top_facility['category'], top_facility['category']),
            'score': top_facility['score'],
            'growth_rate': top_facility['growth_rate'],
            'escalation_rate': top_facility['escalation_rate'],
        }

    # 1. Compute major categories from ward's complaints
    from django.db.models import Count
    complaints_by_cat = ward.complaints.values('category').annotate(count=Count('id')).order_by('-count')
    total_db_count = sum(c['count'] for c in complaints_by_cat)
    
    major_categories = []
    category_choices_dict = dict(Complaint.CATEGORY_CHOICES)
    for c in complaints_by_cat:
        cat_code = c['category']
        cat_display = category_choices_dict.get(cat_code, cat_code)
        pct = round(c['count'] / total_db_count * 100, 1) if total_db_count > 0 else 0
        major_categories.append({
            'category_display': cat_display,
            'count': c['count'],
            'percentage': pct,
            'trend': 'stable',
        })

    # 2. Compute failing categories using city-wide growth patterns from ml.anomaly
    from ml.anomaly import detect_category_anomalies
    try:
        cat_anom = detect_category_anomalies()
    except Exception:
        cat_anom = []
        
    failing_categories = []
    for c in cat_anom:
        failing_categories.append({
            'issue': c['issue'],
            'recent_3yr_growth_pct': c['recent_3yr_growth_pct'],
            'projected_next': int(c['latest'] * (1 + c['recent_3yr_growth_pct'] / 100)) if c['recent_3yr_growth_pct'] > 0 else c['latest']
        })
    failing_categories.sort(key=lambda x: x['recent_3yr_growth_pct'], reverse=True)

    # 3. Construct input structures for the briefing generator
    dashboard_briefing_input = {
        'ward': {'ward_name': ward.ward_name},
        'health_score': health['score'] if health else None,
        'total_complaints': len(complaints),
        'resolved_complaints': sum(1 for c in qs if c.status == 'resolved'),
        'failing_categories': failing_categories,
    }
    
    prediction_briefing_input = {
        'predicted_risk': latest_prediction.predicted_risk if latest_prediction else 'unknown',
        'predicted_complaints': latest_prediction.predicted_complaints if latest_prediction else None,
        'predicted_health_score': latest_prediction.predicted_health_score if latest_prediction else None,
        'recommendation': latest_prediction.recommendation if latest_prediction else None,
    }
    
    insights_briefing_input = {
        'major_categories': major_categories,
        'failing_categories': failing_categories,
    }

    # 4. Generate the briefing
    from ml.briefing import generate_ward_briefing
    try:
        briefing_data = generate_ward_briefing(
            dashboard=dashboard_briefing_input,
            prediction=prediction_briefing_input,
            insights=insights_briefing_input,
            ward_name=ward.ward_name
        )
    except Exception as e:
        briefing_data = {
            'error': f'Could not generate briefing: {str(e)}',
            'sections': {
                'header': f'Ward {ward.ward_name}',
                'whats_happening': 'Error generating what\'s happening section.',
                'forecast': 'Error generating forecast section.',
                'action_items': []
            },
            'summary': f'Ward {ward.ward_name} · Briefing unavailable',
            'raw': {}
        }

    return Response({
        'ward': ward_info,
        'health_score': health['score'] if health else None,
        'health_label': health['label'] if health else 'No Data',
        'health_breakdown': health['breakdown'] if health else None,
        'metrics_year': latest_metrics.year if latest_metrics else None,
        'total_complaints': len(complaints),
        'open_complaints': sum(1 for c in qs if c.status == 'open'),
        'in_progress_complaints': sum(1 for c in qs if c.status == 'in_progress'),
        'resolved_complaints': sum(1 for c in qs if c.status == 'resolved'),
        'complaints': complaints,
        'predictions': prediction_data,
        'focus_facility': focus_facility,
        'briefing': briefing_data,
    })

@api_view(['GET'])
def get_complaint(request, pk):
    """Fetch a single complaint by ID."""
    complaint = Complaint.objects.filter(pk=pk).select_related('ward').first()
    if not complaint:
        return Response({'error': 'Complaint not found'}, status=404)
        
    return Response({
        'id': complaint.id,
        'category': complaint.get_category_display(),
        'description': complaint.description,
        'latitude': complaint.latitude,
        'longitude': complaint.longitude,
        'image': complaint.image.url if complaint.image else None,
        'status': complaint.status,
        'ward_no': complaint.ward.ward_no,
        'ward_name': complaint.ward.ward_name,
        'created_at': complaint.created_at.isoformat(),
    })

@api_view(['PATCH'])
def update_complaint_status(request, pk):
    """Update a complaint's status."""
    status = request.data.get('status')
    if not status or status not in [c[0] for c in Complaint.STATUS_CHOICES]:
        return Response({'error': 'Invalid or missing status.'}, status=400)
        
    complaint = Complaint.objects.filter(pk=pk).first()
    if not complaint:
        return Response({'error': 'Complaint not found'}, status=404)
        
    complaint.status = status
    complaint.save()
    
    return Response({'success': True, 'status': complaint.status})

@api_view(['GET'])
def trend_data(request):
    """
    Return 5-year historical trends.
    Optional query param: ?ward=<ward_name>
    """
    ward_name = request.GET.get('ward')
    qs = CivicMetrics.objects.select_related('ward').all().order_by('year')
    
    if ward_name:
        qs = qs.filter(ward__ward_name__iexact=ward_name)
    
    # Group by year
    years_data = {}
    for m in qs:
        y = m.year
        if y not in years_data:
            years_data[y] = {
                'year': y,
                'total_complaints': 0,
                'avg_resolution_days_sum': 0,
                'count': 0
            }
        years_data[y]['total_complaints'] += m.total_complaints
        years_data[y]['avg_resolution_days_sum'] += m.avg_resolution_days
        years_data[y]['count'] += 1
        
    results = []
    for y in sorted(years_data.keys()):
        d = years_data[y]
        results.append({
            'year': y,
            'total_complaints': d['total_complaints'],
            'avg_resolution_days': round(d['avg_resolution_days_sum'] / d['count'], 1) if d['count'] > 0 else 0
        })
        
    return Response(results)