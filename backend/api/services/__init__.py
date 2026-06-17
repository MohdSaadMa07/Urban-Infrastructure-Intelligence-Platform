"""
Health Score calculation service.

Computes a 0-100 infrastructure health score for a ward based on
civic metrics using a simple weighted-sum formula.

Score components:
  - Closure rate      (40%): higher is better
  - Escalation rate   (30%): lower is better
  - Resolution speed  (30%): faster is better

Qualitative labels:
  >= 70  → Good
  >= 45  → Moderate
  <  45  → Poor
"""


def compute_health_score(metrics):
    """
    Compute an infrastructure health score (0-100) for a single CivicMetrics row.

    Args:
        metrics: A CivicMetrics model instance.

    Returns:
        dict with keys: score (float), label (str), breakdown (dict)
    """
    total = metrics.total_complaints or 1
    closed = metrics.closed_complaints or 0
    escalated = metrics.escalated_complaints or 0
    avg_days = metrics.avg_resolution_days or 0

    # --- Component 1: Closure rate (higher = better) ---
    closure_rate = closed / total
    closure_score = closure_rate  # 0.0 – 1.0

    # --- Component 2: Escalation rate (lower = better) ---
    escalation_rate = escalated / total
    escalation_score = 1 - escalation_rate  # 0.0 – 1.0

    # --- Component 3: Resolution speed (faster = better) ---
    # Normalize: 1 day → ~1.0, 30 days → ~0.5, 90 days → ~0.25
    # Using a decay function: 15 / (avg_days + 15)
    resolution_score = 15.0 / (avg_days + 15.0)  # 0.0 – 1.0

    # --- Weighted sum ---
    WEIGHT_CLOSURE = 0.40
    WEIGHT_ESCALATION = 0.30
    WEIGHT_RESOLUTION = 0.30

    raw_score = (
        WEIGHT_CLOSURE * closure_score
        + WEIGHT_ESCALATION * escalation_score
        + WEIGHT_RESOLUTION * resolution_score
    ) * 100

    score = round(max(0, min(100, raw_score)), 2)

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
            'closure_rate': round(closure_rate * 100, 1),
            'escalation_rate': round(escalation_rate * 100, 1),
            'avg_resolution_days': avg_days,
            'closure_score': round(closure_score, 4),
            'escalation_score': round(escalation_score, 4),
            'resolution_score': round(resolution_score, 4),
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
