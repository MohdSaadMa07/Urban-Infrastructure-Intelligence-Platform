"""
Per-ward, per-category anomaly detection using DB complaint data.

For each ward, identifies categories that are:
  1. Overrepresented compared to city-wide distribution
  2. Showing recent growth within the ward (last 30d vs prior)

Uses the Complaint model's (ward, category, created_at) data directly.
"""

from collections import defaultdict
from datetime import timedelta
from django.db.models import Count, Q
from django.utils import timezone
from api.models import Complaint

Z_THRESHOLD = 1.5

DB_TO_DISPLAY = {
    'pothole': 'Potholes',
    'water': 'Water Supply',
    'drainage': 'Drainage',
    'garbage': 'Garbage',
    'streetlight': 'Street Lights',
    'road': 'Roads',
    'other': 'Other',
}


def detect_ward_category_anomalies(ward_name):
    """
    For a given ward, return per-category anomaly signals derived from
    the DB Complaint table.

    Returns list of dicts sorted by anomaly_score descending:
      { category, display_name, count, ward_pct, city_pct,
        concentration, recent_growth_pct, anomaly_score, is_anomaly }
    """
    # ── City-wide totals per category ────────────────────────────────────
    city_qs = Complaint.objects.values('category').annotate(
        total=Count('id')
    )
    city_total_all = sum(c['total'] for c in city_qs) or 1
    city_pcts = {c['category']: c['total'] / city_total_all for c in city_qs}

    # ── This ward's totals per category ──────────────────────────────────
    ward_qs = Complaint.objects.filter(
        ward__ward_name=ward_name
    ).values('category').annotate(
        total=Count('id')
    )
    ward_total_all = sum(c['total'] for c in ward_qs) or 1
    ward_counts = {c['category']: c['total'] for c in ward_qs}

    # ── Recent growth: last 30d vs prior 60d ────────────────────────────
    now = timezone.now()
    recent_cutoff = now - timedelta(days=30)
    prior_cutoff = now - timedelta(days=90)

    recent_qs = Complaint.objects.filter(
        ward__ward_name=ward_name,
        created_at__gte=recent_cutoff,
    ).values('category').annotate(total=Count('id'))

    prior_qs = Complaint.objects.filter(
        ward__ward_name=ward_name,
        created_at__gte=prior_cutoff,
        created_at__lt=recent_cutoff,
    ).values('category').annotate(total=Count('id'))

    recent_counts = {c['category']: c['total'] for c in recent_qs}
    prior_counts = {c['category']: c['total'] for c in prior_qs}

    results = []
    for cat_code, ward_count in ward_counts.items():
        ward_pct = ward_count / ward_total_all
        city_pct = city_pcts.get(cat_code, 0)

        concentration = round(ward_pct / city_pct, 2) if city_pct > 0 else 1.0

        recent = recent_counts.get(cat_code, 0)
        prior = prior_counts.get(cat_code, 0)
        # Rate per day to account for unequal windows (30d vs 60d)
        recent_rate = recent / 30.0
        prior_rate = prior / 60.0

        if prior_rate > 0:
            growth_pct = round((recent_rate - prior_rate) / prior_rate * 100, 1)
        elif recent_rate > 0:
            growth_pct = 100.0
        else:
            growth_pct = 0.0

        # ── Composite anomaly score ──────────────────────────────────────
        # concentration > 1.5 or growth > 30% contribute
        conc_score = max(0, (concentration - 1.0) * 2)
        growth_score = max(0, growth_pct / 50.0)
        anomaly_score = round(conc_score + growth_score, 3)

        is_anomaly = anomaly_score >= Z_THRESHOLD

        results.append({
            'category': cat_code,
            'display_name': DB_TO_DISPLAY.get(cat_code, cat_code),
            'count': ward_count,
            'ward_pct': round(ward_pct * 100, 1),
            'city_pct': round(city_pct * 100, 1),
            'concentration': concentration,
            'recent_growth_pct': growth_pct,
            'anomaly_score': anomaly_score,
            'is_anomaly': is_anomaly,
        })

    results.sort(key=lambda r: r['anomaly_score'], reverse=True)
    return results
