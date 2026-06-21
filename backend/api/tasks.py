"""
Celery tasks for UrbanIQ Phase 2.

Scheduled nightly:
  1. generate_predictions  - run predictions for all wards, save to DB
  2. retrain_models        - sync site complaints, then retrain on latest data
"""

from celery import shared_task
from datetime import date


def sync_complaints_to_portal_metrics():
    """
    Aggregate site-submitted Complaint records into PortalMetrics per ward+year.
    Separate from CivicMetrics (which holds pure Praja/CCRS historical data).
    """
    from django.db.models import Count, Q
    from django.db.models.functions import ExtractYear
    from api.models import Complaint, PortalMetrics

    agg = (
        Complaint.objects
        .values('ward_id')
        .annotate(
            year=ExtractYear('created_at'),
            total=Count('id'),
            resolved=Count('id', filter=Q(status='resolved')),
        )
    )

    created = 0
    updated = 0
    for item in agg:
        ward_id = item['ward_id']
        year = item['year']
        if not year or not ward_id:
            continue

        _, was_created = PortalMetrics.objects.update_or_create(
            ward_id=ward_id,
            year=year,
            defaults={
                'total_complaints': item['total'],
                'resolved_complaints': item['resolved'],
            }
        )
        if was_created:
            created += 1
        else:
            updated += 1

    if created or updated:
        print(f"  Synced complaints -> portal_metrics: {created} created, {updated} updated")


@shared_task
def generate_predictions():
    """Generate predictions for all wards for the next 2 years."""
    from ml.predict import generate_predictions as run_prediction
    from ml.utils import load_model, RISK_MODEL_PATH
    from api.models import WardPrediction, Ward

    if not RISK_MODEL_PATH.exists():
        return {"status": "error", "message": "Models not found. Run train_models first."}

    existing_years = set(WardPrediction.objects.values_list("prediction_date__year", flat=True))
    base_year = max(existing_years) + 1 if existing_years else date.today().year
    years_to_predict = [y for y in [base_year, base_year + 1] if y not in existing_years]

    results_prev = None
    total_created = 0
    for target_year in sorted(years_to_predict):
        try:
            results, ty = run_prediction(target_year=target_year, previous_predictions=results_prev)
        except Exception:
            results, ty = run_prediction(target_year=target_year)
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
            total_created += 1
        results_prev = results

    return {
        "status": "success",
        "predictions_generated": total_created,
        "years_predictions": years_to_predict,
    }


@shared_task
def retrain_models():
    """
    Sync site complaints into PortalMetrics, then retrain all ML models.
    CivicMetrics (Praja data) is never modified by this task.
    """
    from ml.features import build_feature_matrix
    from ml.train import train_risk_model, train_forecast_model, train_clustering

    sync_complaints_to_portal_metrics()

    X, y_risk, y_complaints, _ = build_feature_matrix(training=True)
    train_risk_model(X, y_risk)
    train_forecast_model(X, y_complaints)
    train_clustering(X)
    return {"status": "success", "rows": len(X)}
