"""
Health Score calculation service.

Computes a 0-100 infrastructure health score for a ward based on
civic metrics that genuinely vary across Mumbai's 24 wards.

Score components (sourced from ward_complaints.csv via CivicMetrics):
  - Per-capita complaints     (35%): lower  = better civic infrastructure
  - Avg resolution days       (35%): lower  = better responsiveness
  - Per-capita deliberations  (30%): higher = better civic engagement

Note: Deliberation data for 2024 uses latest available values (carried
forward from 2023 since no newer data exists).

Each component is normalized with a sigmoid function tuned to the
observed data ranges so scores spread meaningfully (~ 10-95).

Qualitative labels:
  >= 70  -> Good
  >= 45  -> Moderate
  <  45  -> Poor
"""

import math


def _sigmoid(x, midpoint, steepness):
    """
    Logistic sigmoid mapped to 0-1.
    """
    return 1.0 / (1.0 + math.exp(steepness * (x - midpoint)))


def compute_health_score(metrics):
    complaints = getattr(metrics, 'per_capita_complaints', None) or 0
    avg_days = getattr(metrics, 'avg_resolution_days', None) or 0
    deliberations = getattr(metrics, 'per_capita_deliberations', None) or 0

    # --- Component 1: Per-capita complaints (lower = better) ---
    # Data range: ~2 400 - 10 300.  Midpoint 6 500.
    complaint_score = _sigmoid(complaints, midpoint=6500, steepness=0.0008)

    # --- Component 2: Avg resolution days (lower = better) ---
    # Data range: ~16 - 74.  Midpoint 40.
    resolution_score = _sigmoid(avg_days, midpoint=40, steepness=0.12)

    # --- Component 3: Per-capita deliberations (higher = better) ---
    # Data range: ~24 - 104.  Midpoint 55.
    deliberation_score = _sigmoid(deliberations, midpoint=55, steepness=-0.10)

    # --- Weighted sum ---
    WEIGHT_COMPLAINTS = 0.35
    WEIGHT_RESOLUTION = 0.35
    WEIGHT_DELIBERATION = 0.30

    raw_score = (
        WEIGHT_COMPLAINTS * complaint_score
        + WEIGHT_RESOLUTION * resolution_score
        + WEIGHT_DELIBERATION * deliberation_score
    ) * 100

    score = round(max(0.0, min(100.0, raw_score)), 2)

    # --- Qualitative label ---
    if score >= 70:
        label = 'Good'
    elif score >= 45:
        label = 'Moderate'
    else:
        label = 'Poor'

    return {
        'score': score,
        'label': label,
        'breakdown': {
            'per_capita_complaints': complaints,
            'avg_resolution_days': avg_days,
            'per_capita_deliberations': deliberations,
            'complaint_score': round(complaint_score, 4),
            'resolution_score': round(resolution_score, 4),
            'deliberation_score': round(deliberation_score, 4),
        },
    }


def compute_and_save_all():
    from api.models import Ward
    updated = 0
    for ward in Ward.objects.all():
        latest = ward.metrics.order_by('-year').first()
        if latest:
            result = compute_health_score(latest)
            ward.health_score = result['score']
            ward.save(update_fields=['health_score'])
            updated += 1
    return updated
