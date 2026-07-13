import csv
import json
import logging
import time
from pathlib import Path

from django.db.models import Count, Max, Q
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.gis.geos import Point

from api.models import Ward, CivicMetrics, Complaint, PortalMetrics, WardPrediction
from api.services.health_score import compute_health_score
from api.serializers import WardSerializer
from ml.anomaly import detect_category_anomalies
from ml.briefing import generate_ward_briefing
from ml.ward_insights import compute_ward_category_scores
from ml.ward_category_anomaly import detect_ward_category_anomalies
from ml.seasonal_advisory import generate_seasonal_advisories
from .twilio_views import send_status_update

logger = logging.getLogger(__name__)

_escalation_cache = None
_escalation_cache_ttl = 0

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
    ward_filter = request.GET.get('ward')
    year_filter = request.GET.get('year')

    wards = Ward.objects.all().prefetch_related('metrics')
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
    ward_name = request.GET.get('ward')
    qs = Complaint.objects.select_related('ward').all().order_by('-created_at')

    if ward_name:
        qs = qs.filter(ward__ward_name__iexact=ward_name.strip())

    paginator = PageNumberPagination()
    paginator.page_size = 50
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 500
    page = paginator.paginate_queryset(qs, request)

    def serialize(c):
        return {
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

    if page is not None:
        return paginator.get_paginated_response([serialize(c) for c in page])

    return Response([serialize(c) for c in qs])


@api_view(['GET'])
def councillors(request):
    year_filter = request.GET.get('year')

    if not year_filter:
        active_year = CivicMetrics.objects.filter(total_deliberations__gt=0).aggregate(Max('year'))['year__max']
        if active_year:
            year_filter = active_year

    wards = Ward.objects.all().prefetch_related('metrics')
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
        logger.exception("Dashboard error for user %s", request.user.username)
        return Response({
            'error': 'Dashboard error occurred. Please try again later.',
        }, status=500)

def _councillor_ward_dashboard(request):
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

    max_pred_year = ward.predictions.aggregate(m=Max('prediction_date__year'))['m']
    latest_prediction = ward.predictions.filter(prediction_date__year=max_pred_year).first() if max_pred_year else None
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

    complaints_by_cat = ward.complaints.values('category').annotate(count=Count('id')).order_by('-count')
    total_db_count = sum(c['count'] for c in complaints_by_cat)

    conc_lookup = {a['category']: a['concentration'] for a in ward_cat_anom}

    major_categories = []
    category_choices_dict = dict(Complaint.CATEGORY_CHOICES)
    for c in complaints_by_cat:
        cat_code = c['category']
        cat_display = category_choices_dict.get(cat_code, cat_code)
        pct = round(c['count'] / total_db_count * 100, 1) if total_db_count > 0 else 0
        conc = conc_lookup.get(cat_code, 1.0)
        trend = 'rising' if conc >= 1.3 else ('falling' if conc <= 0.7 else 'stable')
        major_categories.append({
            'category_display': cat_display,
            'count': c['count'],
            'percentage': pct,
            'trend': trend,
        })

    try:
        cat_anom = detect_category_anomalies()
    except Exception:
        logger.exception("Category anomaly detection failed")
        cat_anom = []

    failing_categories = []
    for c in cat_anom:
        failing_categories.append({
            'issue': c['issue'],
            'recent_3yr_growth_pct': c['recent_3yr_growth_pct'],
            'projected_next': int(c['latest'] * (1 + c['recent_3yr_growth_pct'] / 100)) if c['recent_3yr_growth_pct'] > 0 else c['latest']
        })
    failing_categories.sort(key=lambda x: x['recent_3yr_growth_pct'], reverse=True)

    try:
        seasonal_advisories = generate_seasonal_advisories(ward_cat_anom, ward.ward_name)
    except Exception:
        logger.exception("Seasonal advisory generation failed for ward %s", ward.ward_name)
        seasonal_advisories = []

    max_metric_year = ward.metrics.aggregate(m=Max('year'))['m'] or 9999
    ward_metrics_qs = ward.metrics.filter(year__lte=max_metric_year).order_by('year')
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

    all_wards_list = Ward.objects.all().prefetch_related('metrics')
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

    predicted_data = {}
    for pred in ward.predictions.all():
        pred_year = pred.prediction_date.year
        predicted_data[str(pred_year)] = {
            'predicted_risk': pred.predicted_risk,
            'predicted_complaints': pred.predicted_complaints,
            'predicted_complaints_lower': pred.predicted_complaints_lower,
            'predicted_complaints_upper': pred.predicted_complaints_upper,
            'predicted_health_score': pred.predicted_health_score,
            'recommendation': pred.recommendation,
        }

    civic_total = latest_metrics.total_complaints if latest_metrics else 0
    civic_year = latest_metrics.year if latest_metrics else None

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

    try:
        briefing_data = generate_ward_briefing(
            dashboard=dashboard_briefing_input,
            prediction=prediction_briefing_input,
            insights=insights_briefing_input,
            ward_name=ward.ward_name
        )
    except Exception as e:
        logger.exception("Briefing generation failed for ward %s", ward.ward_name)
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
        'ward_metrics_history': ward_metrics_history,
        'ward_rankings': ward_rankings,
        'city_averages': city_averages,
        'yoy_change': yoy_change,
        'predicted_data': predicted_data,
        'major_categories': major_categories,
        'failing_categories': failing_categories,
        'ward_category_anomalies': ward_cat_anom,
        'seasonal_advisories': seasonal_advisories,
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

    if complaint.sender_phone:
        try:
            send_status_update(complaint.id, new_status, complaint.sender_phone)
        except Exception:
            logger.warning("Twilio status update failed for complaint #%s", complaint.id)

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
    global _escalation_cache, _escalation_cache_ttl
    now = time.time()
    if _escalation_cache is not None and now < _escalation_cache_ttl:
        return _escalation_cache

    path = Path(__file__).resolve().parent.parent / 'data' / 'escalation_data.csv'
    if not path.exists():
        _escalation_cache = []
        _escalation_cache_ttl = now + 60
        return _escalation_cache
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
    _escalation_cache = result
    _escalation_cache_ttl = now + 300
    return result


_hotspots_cache = {}
_hotspots_cache_ttl = 0

@api_view(['GET'])
def complaint_hotspots(request):
    global _hotspot_cache, _hotspot_cache_ttl
    ward_name = request.GET.get('ward')
    cache_key = ward_name or '__all__'

    now = time.time()
    if cache_key in _hotspot_cache and now < _hotspot_cache_ttl:
        return Response(_hotspot_cache[cache_key])

    from sklearn.cluster import DBSCAN
    import numpy as np

    qs = Complaint.objects.filter(
        latitude__isnull=False, longitude__isnull=False
    ).order_by('-created_at')[:2000]
    if ward_name:
        qs = qs.filter(ward__ward_name__iexact=ward_name)

    coords_list = [(c.latitude, c.longitude) for c in qs]
    if len(coords_list) < 3:
        _hotspot_cache[cache_key] = []
        _hotspot_cache_ttl = now + 300
        return Response([])

    coords = np.array(coords_list)
    clustering = DBSCAN(eps=0.005, min_samples=2).fit(coords)
    labels = clustering.labels_

    cluster_map = {}
    for i, (lat, lng) in enumerate(coords_list):
        label = int(labels[i])
        if label == -1:
            continue
        if label not in cluster_map:
            cluster_map[label] = {'lats': [], 'lngs': [], 'count': 0}
        cluster_map[label]['lats'].append(lat)
        cluster_map[label]['lngs'].append(lng)
        cluster_map[label]['count'] += 1

    result = []
    for label, data in cluster_map.items():
        if data['count'] < 2:
            continue
        result.append({
            'cluster_id': label,
            'center_lat': round(np.mean(data['lats']), 6),
            'center_lng': round(np.mean(data['lngs']), 6),
            'count': data['count'],
        })

    _hotspot_cache[cache_key] = result
    _hotspot_cache_ttl = now + 300
    return Response(result)


# ── Public Dashboard (no auth) ───────────────────────────────────────────


@api_view(['GET'])
@permission_classes([AllowAny])
def public_wards(request):
    year = request.GET.get('year')
    wards = Ward.objects.all().order_by('ward_name').prefetch_related('metrics')

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
    all_wards = Ward.objects.all().prefetch_related('metrics')
    health_scores = []
    total_complaints = 0
    for w in all_wards:
        m = w.metrics.order_by('-year').first()
        if m:
            h = compute_health_score(m)
            health_scores.append({'ward': w.ward_name, 'score': h['score'], 'label': h['label']})
            total_complaints += m.total_complaints or 0

    if health_scores:
        avg_health = round(sum(s['score'] for s in health_scores) / len(health_scores), 1)
        best = max(health_scores, key=lambda x: x['score'])
        worst = min(health_scores, key=lambda x: x['score'])
    else:
        avg_health = None
        best = None
        worst = None

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
    from django.conf import settings as dj_settings
    raw = dj_settings.TWILIO_WHATSAPP_NUMBER or ''
    number = raw.replace('whatsapp:', '').strip()
    twilio_configured = bool(dj_settings.TWILIO_ACCOUNT_SID and number and 'your_account' not in dj_settings.TWILIO_ACCOUNT_SID)
    return Response({
        'whatsapp_number': number or None,
        'whatsapp_link': f'https://wa.me/{number.replace("+", "")}?text=Hello' if number else None,
        'twilio_configured': twilio_configured,
    })


# ── PDF Report Download ─────────────────────────────────────────────────


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_ward_report(request):
    from api.services.report_generator import generate_ward_report
    profile = request.user.profile
    if profile.role != 'councillor':
        return Response({'error': 'Councillor access required.'}, status=403)

    ward_name = request.GET.get('ward') or (profile.ward.ward_name if profile.ward else None)
    if not ward_name:
        return Response({'error': 'No ward specified.'}, status=400)

    filepath = generate_ward_report(ward_name)
    if not filepath or not filepath.exists():
        return Response({'error': 'Report could not be generated.'}, status=500)

    return FileResponse(filepath.open('rb'), as_attachment=True, filename=filepath.name)


import os
from datetime import date
from django.conf import settings

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def cron_retrain(request):
    """
    Cron endpoint for daily model retraining and prediction regeneration.
    Protected by CRON_API_KEY env var (passed as X-API-Key header or ?key= param).
    """
    expected_key = os.environ.get('CRON_API_KEY', '')
    if expected_key:
        provided = request.headers.get('X-API-Key', '') or request.GET.get('key', '')
        if provided != expected_key:
            return Response({'status': 'error', 'message': 'Invalid API key.'}, status=403)

    from api.tasks import sync_complaints_to_portal_metrics
    from ml.features import build_feature_matrix
    from ml.train import train_risk_model, train_forecast_model, train_clustering
    from ml.predict import generate_predictions as run_prediction
    from ml.utils import load_model, RISK_MODEL_PATH
    from api.models import WardPrediction, Ward

    sync_complaints_to_portal_metrics()

    X, y_risk, y_complaints, _ = build_feature_matrix(training=True)
    train_risk_model(X, y_risk)
    train_forecast_model(X, y_complaints, horizon=1)

    X_n2, _, y_complaints_n2, _ = build_feature_matrix(training=True, horizon=2)
    train_forecast_model(X_n2, y_complaints_n2, horizon=2)

    train_clustering(X)

    if not RISK_MODEL_PATH.exists():
        return Response({'status': 'error', 'message': 'Models not found after training.'}, status=500)

    latest_metric_year = None
    from api.models import CivicMetrics
    latest_metric_year = CivicMetrics.objects.order_by("-year").values_list("year", flat=True).first()
    if not latest_metric_year:
        latest_metric_year = date.today().year

    total_predictions = 0
    for horizon in [1, 2]:
        target_year = latest_metric_year + horizon
        try:
            results, ty = run_prediction(target_year=target_year, horizon=horizon)
        except Exception:
            continue
        if not results:
            continue
        for r in results:
            ward = Ward.objects.filter(ward_name=r["ward_name"]).first()
            if not ward:
                continue
            WardPrediction.objects.update_or_create(
                ward=ward,
                prediction_date=date(target_year, 1, 1),
                defaults={
                    "predicted_risk": r["predicted_risk"].lower(),
                    "predicted_complaints": r["predicted_complaints"],
                    "predicted_complaints_lower": r.get("predicted_complaints_lower"),
                    "predicted_complaints_upper": r.get("predicted_complaints_upper"),
                    "predicted_health_score": r["predicted_health_score"],
                    "recommendation": r["recommendation"],
                    "top_features": r.get("top_features"),
                    "model_version": f"xgboost-v1-{target_year}",
                }
            )
            total_predictions += 1

    return Response({
        'status': 'success',
        'rows_trained': len(X),
        'predictions_generated': total_predictions,
    })