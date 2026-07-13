"""
Per-ward, per-category anomaly detection using DB complaint data.

For each ward, identifies categories that are anomalous using:
  1. Weekly z-score: latest week's complaint count vs historical weekly distribution
  2. Growth signal: recent 4-week average vs overall weekly average
  3. Concentration: ward's category share vs city-wide category share

Severity tiers match ml/anomaly.py: minor >=1.5, major >=2.0, critical >=3.0.
"""

import numpy as np
from datetime import timedelta
from django.db.models import Count
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


def _severity(abs_z):
    if abs_z >= 3.0:
        return 'critical'
    if abs_z >= 2.0:
        return 'major'
    if abs_z >= 1.5:
        return 'minor'
    return 'normal'


def _explain(cat_display, ward_name, z_score, growth_pct, concentration):
    parts = []
    if abs(z_score) >= 1.5:
        direction = 'spiked' if z_score > 0 else 'dropped'
        parts.append(
            f"{cat_display} complaints in Ward {ward_name} have {direction} "
            f"({abs(z_score):.1f}σ from weekly average)"
        )
    if growth_pct > 30:
        parts.append(
            f"up {growth_pct:.0f}% in the last month"
        )
    elif growth_pct < -30:
        parts.append(
            f"down {abs(growth_pct):.0f}% in the last month"
        )
    if concentration > 1.5:
        parts.append(
            f"{concentration:.1f}x higher than city distribution"
        )
    return " · ".join(parts) if parts else "Within normal range."


def detect_ward_category_anomalies(ward_name):
    """
    For a given ward, compute per-category z-scores using weekly complaint
    counts from the DB Complaint table.

    Returns list of dicts sorted by |z_score| descending:
      { category, display_name, count, weekly_mean, weekly_std, latest_week,
        z_score, direction, severity, is_anomaly, growth_pct, concentration,
        explanation }
    """
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    # ── City-wide stats per category (for concentration) ────────────────
    city_qs = Complaint.objects.values('category').annotate(total=Count('id'))
    city_total_all = sum(c['total'] for c in city_qs) or 1
    city_pcts = {c['category']: c['total'] / city_total_all for c in city_qs}

    # ── This ward: all complaints with dates ─────────────────────────────
    ward_complaints = Complaint.objects.filter(
        ward__ward_name=ward_name
    ).values_list('category', 'created_at')

    if not ward_complaints:
        return []

    # ── Bucket by (category, ISO week) ───────────────────────────────────
    # Build a set of all weeks that exist in data
    from collections import defaultdict
    weekly = defaultdict(lambda: defaultdict(int))

    first_date = None
    for cat, created_at in ward_complaints:
        week_start = created_at.isocalendar()
        key = (week_start[0], week_start[1])  # (year, week_number)
        weekly[cat][key] += 1
        if first_date is None or created_at < first_date:
            first_date = created_at

    if first_date is None:
        return []

    # Latest complete week
    latest_isoweek = (now.isocalendar()[0], now.isocalendar()[1])

    results = []
    for cat_code, week_buckets in weekly.items():
        weeks = sorted(week_buckets.keys())
        vals = np.array([week_buckets[w] for w in weeks], dtype=float)

        if len(vals) < 3:
            continue

        mean = np.mean(vals)
        std = np.std(vals, ddof=1)

        if std == 0:
            continue

        latest_count = week_buckets.get(latest_isoweek, 0.0)
        z = (latest_count - mean) / std
        abs_z = abs(z)
        direction = 'high' if z > 0 else 'low'

        # Growth: compare last 4 weeks to all weeks
        recent_weeks = weeks[-4:] if len(weeks) >= 4 else weeks
        recent_mean = np.mean([week_buckets[w] for w in recent_weeks])
        growth_pct = round((recent_mean - mean) / mean * 100, 1) if mean > 0 else 0.0

        # Concentration
        ward_total_all = sum(len(ws) for ws in weekly.values())
        ward_pct = sum(week_buckets.values()) / ward_total_all if ward_total_all > 0 else 0
        city_pct = city_pcts.get(cat_code, 0)
        concentration = round(ward_pct / city_pct, 2) if city_pct > 0 else 1.0

        is_anomaly = abs_z >= Z_THRESHOLD or concentration > 2.0 or growth_pct > 50

        results.append({
            'category': cat_code,
            'display_name': DB_TO_DISPLAY.get(cat_code, cat_code),
            'count': int(sum(week_buckets.values())),
            'weekly_mean': round(mean, 2),
            'weekly_std': round(std, 2),
            'latest_week': int(latest_count),
            'z_score': round(z, 2),
            'direction': direction,
            'severity': _severity(abs_z),
            'is_anomaly': is_anomaly,
            'growth_pct': growth_pct,
            'concentration': concentration,
            'explanation': _explain(
                DB_TO_DISPLAY.get(cat_code, cat_code),
                ward_name, z, growth_pct, concentration,
            ),
        })

    results.sort(key=lambda r: abs(r['z_score']), reverse=True)
    return results
