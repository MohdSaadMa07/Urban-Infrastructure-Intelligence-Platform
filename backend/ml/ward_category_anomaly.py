"""
Per-ward, per-category anomaly detection using DB complaint data.

For each ward, identifies categories that are overrepresented compared to
the city-wide distribution. Works with any amount of data (even 1 day).

Method:
  - concentration = ward_proportion / city_proportion for each category
  - concentration > 1.5 → anomalous (category is overrepresented in this ward)

Severity tiers: minor >=1.5x, major >=2.5x, critical >=4.0x.
"""

from django.db.models import Count
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


def _severity(concentration):
    if concentration >= 4.0:
        return 'critical'
    if concentration >= 2.5:
        return 'major'
    if concentration >= 1.5:
        return 'minor'
    return 'normal'


def _explain(cat_display, ward_name, concentration, count, expected):
    if concentration > 1.5:
        direction = 'higher' if concentration > 1 else 'lower'
        return (
            f"{cat_display} complaints in Ward {ward_name} are "
            f"{concentration:.1f}x {direction} than city distribution "
            f"({count} actual vs {expected:.0f} expected)"
        )
    return "Within normal range."


def detect_ward_category_anomalies(ward_name):
    """
    For a given ward, find categories that are disproportionately high
    compared to city-wide averages.

    Returns list of dicts sorted by concentration descending:
      { category, display_name, count, expected_count,
        concentration, severity, is_anomaly, explanation }
    """
    # ── City-wide totals per category ────────────────────────────────────
    city_qs = Complaint.objects.values('category').annotate(total=Count('id'))
    city_total_all = sum(c['total'] for c in city_qs) or 1
    city_pcts = {c['category']: c['total'] / city_total_all for c in city_qs}

    # ── This ward's totals per category ──────────────────────────────────
    ward_qs = Complaint.objects.filter(
        ward__ward_name=ward_name
    ).values('category').annotate(total=Count('id'))
    ward_total_all = sum(c['total'] for c in ward_qs) or 1

    if ward_total_all == 0:
        return []

    results = []
    for c in ward_qs:
        cat_code = c['category']
        count = c['total']
        ward_pct = count / ward_total_all
        city_pct = city_pcts.get(cat_code, 0)

        concentration = round(ward_pct / city_pct, 2) if city_pct > 0 else 1.0
        expected = round(ward_total_all * city_pct, 1)
        is_anomaly = concentration >= 1.5

        results.append({
            'category': cat_code,
            'display_name': DB_TO_DISPLAY.get(cat_code, cat_code),
            'count': count,
            'expected_count': expected,
            'concentration': concentration,
            'severity': _severity(concentration),
            'is_anomaly': is_anomaly,
            'explanation': _explain(
                DB_TO_DISPLAY.get(cat_code, cat_code),
                ward_name, concentration, count, expected,
            ),
        })

    results.sort(key=lambda r: r['concentration'], reverse=True)
    return results
