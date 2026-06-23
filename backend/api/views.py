from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
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
    try:
        return _councillor_ward_dashboard(request)
    except Exception as e:
        import traceback
        return Response({
            'error': f'Dashboard error: {str(e)}',
            'detail': traceback.format_exc(),
        }, status=500)

def _councillor_ward_dashboard(request):
    profile = request.user.profile
    if profile.role != 'councillor':
        return Response({'error': 'Only councillors can access this endpoint.'}, status=403)

    ward = profile.ward
    if not ward:
        return Response({'error': 'You are not assigned to any ward. Contact admin.'}, status=400)

    ward_info = WardSerializer(ward).data

    # Latest CivicMetrics (pure Praja historical data)
    latest_metrics = ward.metrics.order_by('-year').first()
    health = None
    if latest_metrics:
        health = compute_health_score(latest_metrics)

    # Portal-submitted complaint stats
    from api.models import PortalMetrics
    portal_stats = PortalMetrics.objects.filter(ward=ward).order_by('-year').first()
    portal_total = portal_stats.total_complaints if portal_stats else 0
    portal_resolved = portal_stats.resolved_complaints if portal_stats else 0

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
            'resolved_at': c.resolved_at.isoformat() if c.resolved_at else None,
        }
        for c in qs
    ]

    # Fetch the latest ML prediction for this ward (within predicted_data range)
    latest_prediction = ward.predictions.filter(prediction_date__year__lte=2026).order_by('-prediction_date').first()
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

    # ── Ward Metrics History (2019-2025) for trend charts ──────────
    ward_metrics_qs = ward.metrics.filter(year__lte=2025).order_by('year')
    ward_metrics_history = []
    for m in ward_metrics_qs:
        hs = compute_health_score(m)
        ward_metrics_history.append({
            'year': m.year,
            'total_complaints': m.total_complaints,
            'per_capita_complaints': m.per_capita_complaints,
            'avg_resolution_days': m.avg_resolution_days,
            'per_capita_deliberations': m.per_capita_deliberations,
            'total_deliberations': m.total_deliberations,
            'health_score': hs['score'],
            'health_label': hs['label'],
        })

    # ── City-wide rankings and averages ────────────────────────────────
    all_wards_list = Ward.objects.all()
    rankings_data = []
    city_totals = {'health_score': 0, 'complaints': 0, 'days': 0, 'deliberations': 0}
    city_count = 0
    for w in all_wards_list:
        lm = w.metrics.order_by('-year').first()
        if lm:
            hs = compute_health_score(lm)
            city_totals['health_score'] += hs['score']
            city_totals['complaints'] += lm.per_capita_complaints
            city_totals['days'] += lm.avg_resolution_days
            city_totals['deliberations'] += lm.per_capita_deliberations
            city_count += 1
            rankings_data.append({
                'ward_name': w.ward_name,
                'health_score': hs['score'],
                'total_complaints': lm.total_complaints,
                'per_capita_complaints': lm.per_capita_complaints,
                'avg_resolution_days': lm.avg_resolution_days,
                'per_capita_deliberations': lm.per_capita_deliberations,
            })

    city_averages = {}
    if city_count > 0:
        city_averages = {
            'health_score': round(city_totals['health_score'] / city_count, 1),
            'per_capita_complaints': round(city_totals['complaints'] / city_count, 1),
            'avg_resolution_days': round(city_totals['days'] / city_count, 1),
            'per_capita_deliberations': round(city_totals['deliberations'] / city_count, 1),
        }

    # Compute ward's rank
    ward_rankings = {}
    if rankings_data:
        hs_sorted = sorted(rankings_data, key=lambda x: x['health_score'], reverse=True)
        comp_sorted = sorted(rankings_data, key=lambda x: x['total_complaints'])
        days_sorted = sorted(rankings_data, key=lambda x: x['avg_resolution_days'])
        delib_sorted = sorted(rankings_data, key=lambda x: x['per_capita_deliberations'], reverse=True)
        ward_rankings = {
            'health_score_rank': next(i+1 for i, w in enumerate(hs_sorted) if w['ward_name'] == ward.ward_name),
            'complaints_rank': next(i+1 for i, w in enumerate(comp_sorted) if w['ward_name'] == ward.ward_name),
            'resolution_rank': next(i+1 for i, w in enumerate(days_sorted) if w['ward_name'] == ward.ward_name),
            'deliberation_rank': next(i+1 for i, w in enumerate(delib_sorted) if w['ward_name'] == ward.ward_name),
            'total_wards': city_count,
        }

    # ── Year-over-year change ──────────────────────────────────────────
    yoy_change = {}
    if len(ward_metrics_history) >= 2:
        latest_yr = ward_metrics_history[-1]
        prev_yr = ward_metrics_history[-2]
        yoy_change = {
            'complaints_change_pct': round(
                (latest_yr['total_complaints'] - prev_yr['total_complaints'])
                / max(prev_yr['total_complaints'], 1) * 100, 1
            ),
            'resolution_days_change_pct': round(
                (latest_yr['avg_resolution_days'] - prev_yr['avg_resolution_days'])
                / max(prev_yr['avg_resolution_days'], 1) * 100, 1
            ),
            'health_score_change': round(latest_yr['health_score'] - prev_yr['health_score'], 1),
        }

    # ── 2025 + 2026 ML Predictions ─────────────────────────────────────
    predicted_data = {}
    for pred_year in [2025, 2026]:
        pred = ward.predictions.filter(
            prediction_date__year=pred_year
        ).first()
        if pred:
            predicted_data[str(pred_year)] = {
                'predicted_risk': pred.predicted_risk,
                'predicted_complaints': pred.predicted_complaints,
                'predicted_complaints_lower': pred.predicted_complaints_lower,
                'predicted_complaints_upper': pred.predicted_complaints_upper,
                'predicted_health_score': pred.predicted_health_score,
                'recommendation': pred.recommendation,
            }

    # CivicMetrics = pure Praja historical data; PortalMetrics = citizen-submitted
    civic_total = latest_metrics.total_complaints if latest_metrics else 0
    civic_year = latest_metrics.year if latest_metrics else None

    # 3. Construct input structures for the briefing generator
    dashboard_briefing_input = {
        'ward': {'ward_name': ward.ward_name},
        'health_score': health['score'] if health else None,
        'total_complaints': civic_total,
        'resolved_complaints': round(civic_total * 0.86) if latest_metrics else 0,
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
        'metrics_year': civic_year,
        'total_complaints': civic_total,
        'open_complaints': sum(1 for c in qs if c.status == 'open'),
        'in_progress_complaints': sum(1 for c in qs if c.status == 'in_progress'),
        'resolved_complaints': sum(1 for c in qs if c.status == 'resolved'),
        'portal_total': portal_total,
        'portal_resolved': portal_resolved,
        'complaints': complaints,
        'predictions': prediction_data,
        'focus_facility': focus_facility,
        'briefing': briefing_data,
        # New insight data
        'ward_metrics_history': ward_metrics_history,
        'ward_rankings': ward_rankings,
        'city_averages': city_averages,
        'yoy_change': yoy_change,
        'predicted_data': predicted_data,
        # Category breakdowns
        'major_categories': major_categories,
        'failing_categories': failing_categories,
        # Escalation triage data per category
        'escalation_data': _load_escalation_data(),
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
    """Update a complaint's status. Sets resolved_at when status becomes resolved."""
    from django.utils import timezone
    new_status = request.data.get('status')
    if not new_status or new_status not in [c[0] for c in Complaint.STATUS_CHOICES]:
        return Response({'error': 'Invalid or missing status.'}, status=400)

    complaint = Complaint.objects.filter(pk=pk).first()
    if not complaint:
        return Response({'error': 'Complaint not found'}, status=404)

    complaint.status = new_status
    if new_status == 'resolved':
        complaint.resolved_at = timezone.now()
    elif complaint.resolved_at and new_status != 'resolved':
        complaint.resolved_at = None
    complaint.save()

    return Response({'success': True, 'status': complaint.status, 'resolved_at': complaint.resolved_at})

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


def _load_escalation_data():
    """Load escalation rates per category from escalation_data.csv."""
    import csv
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / 'data' / 'escalation_data.csv'
    if not path.exists():
        return []
    result = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['entity_type'] != 'category':
                continue
            total = int(row['total_complaints'])
            escalated = int(row['escalated_level1'])
            result.append({
                'category': row['entity'],
                'total': total,
                'escalated': escalated,
                'escalation_rate': round(escalated / total, 3) if total > 0 else 0,
            })
    return result


@api_view(['GET'])
def complaint_hotspots(request):
    """
    Run DBSCAN clustering on complaint coordinates for a ward.
    Returns cluster centers and member count.
    """
    from sklearn.cluster import DBSCAN
    import numpy as np

    ward_name = request.GET.get('ward')
    qs = Complaint.objects.select_related('ward').filter(
        latitude__isnull=False, longitude__isnull=False
    )
    if ward_name:
        qs = qs.filter(ward__ward_name__iexact=ward_name)

    coords = np.array([[c.latitude, c.longitude] for c in qs])
    if len(coords) < 3:
        return Response([])

    clustering = DBSCAN(eps=0.005, min_samples=2).fit(coords)
    labels = clustering.labels_

    clusters = {}
    for i, (lat, lng) in enumerate(coords):
        label = int(labels[i])
        if label == -1:
            continue
        if label not in clusters:
            clusters[label] = {'lats': [], 'lngs': [], 'count': 0}
        clusters[label]['lats'].append(lat)
        clusters[label]['lngs'].append(lng)
        clusters[label]['count'] += 1

    result = []
    for label, data in clusters.items():
        if data['count'] < 2:
            continue
        result.append({
            'cluster_id': label,
            'center_lat': round(np.mean(data['lats']), 6),
            'center_lng': round(np.mean(data['lngs']), 6),
            'count': data['count'],
        })

    return Response(result)


# ── Public Dashboard (no auth) ───────────────────────────────────────────


@api_view(['GET'])
@permission_classes([AllowAny])
def public_wards(request):
    """
    Simplified ward overview for the public dashboard.
    Returns health label, complaint counts, and a couple headline metrics.
    No auth required.
    """
    year = request.GET.get('year')
    wards = Ward.objects.all().order_by('ward_name')

    results = []
    for ward in wards:
        qs = ward.metrics.all()
        if year:
            qs = qs.filter(year=int(year))
        m = qs.order_by('-year').first()

        health = compute_health_score(m) if m else None

        complaint_count = ward.complaints.filter(source='portal').count()
        results.append({
            'ward_no': ward.ward_no,
            'ward_name': ward.ward_name,
            'year': m.year if m else None,
            'health_score': health['score'] if health else None,
            'health_label': health['label'] if health else 'No Data',
            'total_complaints': m.total_complaints if m else 0,
            'avg_resolution_days': m.avg_resolution_days if m else None,
            'recent_complaints': complaint_count,
        })

    return Response(results)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_health_summary(request):
    """
    Return a city-wide summary for the public landing:
    - total complaints (all wards)
    - average health score
    - best / worst ward names
    """
    from django.db.models import Avg
    all_wards = Ward.objects.all()
    health_scores = []
    best = worst = None
    for w in all_wards:
        m = w.metrics.order_by('-year').first()
        if m:
            h = compute_health_score(m)
            health_scores.append({'ward': w.ward_name, 'score': h['score'], 'label': h['label']})

    total_complaints = sum(
        (w.metrics.order_by('-year').first().total_complaints if w.metrics.order_by('-year').first() else 0)
        for w in all_wards
    )

    if health_scores:
        avg_health = round(sum(s['score'] for s in health_scores) / len(health_scores), 1)
        best = max(health_scores, key=lambda x: x['score'])
        worst = min(health_scores, key=lambda x: x['score'])
    else:
        avg_health = None

    return Response({
        'total_complaints': total_complaints,
        'average_health_score': avg_health,
        'best_ward': best,
        'worst_ward': worst,
        'wards_count': len(all_wards),
    })


# ── Public Config ───────────────────────────────────────────────────────


@api_view(['GET'])
@permission_classes([AllowAny])
def public_config(request):
    from django.conf import settings
    number = settings.TWILIO_WHATSAPP_NUMBER.replace('whatsapp:', '').strip()
    return Response({
        'whatsapp_number': number,
        'whatsapp_link': f'https://wa.me/{number.replace("+", "")}?text=Hello',
    })


# ── PDF Report Download ─────────────────────────────────────────────────


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_ward_report(request):
    """Generate and return a PDF report for the councillor's ward."""
    from api.services.report_generator import generate_ward_report
    from django.http import FileResponse
    profile = request.user.profile
    if profile.role != 'councillor':
        return Response({'error': 'Councillor access required.'}, status=403)

    ward_name = request.GET.get('ward') or (profile.ward.ward_name if profile.ward else None)
    if not ward_name:
        return Response({'error': 'No ward specified.'}, status=400)

    filepath = generate_ward_report(ward_name)
    if not filepath or not filepath.exists():
        return Response({'error': 'Report could not be generated.'}, status=500)

    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=filepath.name)