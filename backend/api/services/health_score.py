"""
Health Score calculation service.

Computes a 0-100 infrastructure health score for a ward based on
civic metrics that genuinely vary across Mumbai's 24 wards.

Score components (sourced from ward_complaints.csv via CivicMetrics):
  - Per-capita complaints  (35%): lower  = better civic infrastructure
  - Avg resolution days    (35%): lower  = better responsiveness
  - Per-capita deliberations (30%): higher = better civic engagement

Each component is normalized with a sigmoid / decay function tuned to
the observed data ranges so scores spread meaningfully (≈ 20-95).

Qualitative labels:
  >= 70  → Good
  >= 45  → Moderate
  <  45  → Poor
"""

import math


def _sigmoid(x, midpoint, steepness):
    """
    Logistic sigmoid mapped to 0-1.

    Returns ~0.5 when x == midpoint.
    `steepness` controls how quickly the curve transitions.
    """
    return 1.0 / (1.0 + math.exp(steepness * (x - midpoint)))


def compute_health_score(metrics):
    """
    Compute an infrastructure health score (0-100) for a single CivicMetrics row.

    Uses three ward-level indicators that vary meaningfully across
    Mumbai's 24 wards, rather than the fixed closure / escalation rates
    produced by the data loader.

    Args:
        metrics: A CivicMetrics model instance with at least:
                 per_capita_complaints, avg_resolution_days,
                 per_capita_deliberations.

    Returns:
        dict with keys:
          score     – float, 0-100
          label     – str, one of 'Good', 'Moderate', 'Poor'
          breakdown – dict of per-component raw values and normalised scores
    """
    complaints = getattr(metrics, 'per_capita_complaints', None) or 0
    avg_days = getattr(metrics, 'avg_resolution_days', None) or 0
    deliberations = getattr(metrics, 'per_capita_deliberations', None) or 0

    # --- Component 1: Per-capita complaints (lower = better) ---
    # Data range: ~2 761 – 10 298.  Midpoint 6 500, steepness 0.0008.
    # 2 761 → ~0.95,  6 500 → 0.50,  10 298 → ~0.05
    complaint_score = _sigmoid(complaints, midpoint=6500, steepness=0.0008)

    # --- Component 2: Avg resolution days (lower = better) ---
    # Data range: ~19 – 68.  Midpoint 40, steepness 0.12.
    # 19 → ~0.93,  40 → 0.50,  68 → ~0.03
    resolution_score = _sigmoid(avg_days, midpoint=40, steepness=0.12)

    # --- Component 3: Per-capita deliberations (higher = better) ---
    # Data range: ~24 – 95.  Midpoint 55, steepness 0.10.
    # Inverted: higher deliberation → higher score.
    # 95 → ~0.98,  55 → 0.50,  24 → ~0.04
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
    """
    Recompute health scores for every ward (using latest CivicMetrics)
    and persist the result in Ward.health_score.
    Returns the number of wards updated.
    """
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
