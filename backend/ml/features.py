"""
Feature engineering for ward-level civic metrics.

Builds a feature matrix from CivicMetrics (DB) with lag/trend features.
Health score logic here mirrors api/services/health_score.py for dict-based computation.
"""

import math

import numpy as np
import pandas as pd

from api.services.health_score import _sigmoid as sigmoid


def _compute_health_score_from_row(row):
    """Compute health score from a feature row dict (mirrors api/services/health_score.py)."""
    complaints = row.get("per_capita_complaints", 0) or 0
    avg_days = row.get("avg_resolution_days", 0) or 0
    deliberations = row.get("per_capita_deliberations", 0) or 0

    complaint_score = sigmoid(complaints, midpoint=6500, steepness=0.0008)
    resolution_score = sigmoid(avg_days, midpoint=40, steepness=0.12)
    deliberation_score = sigmoid(deliberations, midpoint=55, steepness=-0.10)

    raw = (0.35 * complaint_score + 0.35 * resolution_score + 0.30 * deliberation_score) * 100
    return round(max(0.0, min(100.0, raw)), 2)


def build_feature_matrix(years=None, training=False):
    """
    Build feature matrix and target vectors from CivicMetrics.

    Features are ward-level only — no city-wide category data.
    Uses lag and rolling-window features instead of cyclical encoding.

    Args:
        years: iterable of years to include (default: all available)

    Returns:
        X: pd.DataFrame of features
        y_risk: pd.Series of risk labels (Low/Medium/High)
        y_complaints: pd.Series of total_complaints for regression
    """
    from api.models import CivicMetrics, Ward

    # --- Step 1: Load base metrics (CivicMetrics = pure Praja data only) ---
    qs = CivicMetrics.objects.select_related("ward").all()
    if years:
        qs = qs.filter(year__in=list(years))

    rows = []
    for m in qs:
        ward = m.ward
        total = m.total_complaints or 0
        closed = m.closed_complaints or 0
        escalated = m.escalated_complaints or 0

        row = {
            "ward_no": ward.ward_no,
            "ward_name": ward.ward_name,
            "year": m.year,
            "total_complaints": total,
            "closed_complaints": closed,
            "escalated_complaints": escalated,
            "pending_complaints": total - closed,
            "avg_resolution_days": m.avg_resolution_days or 0,
            "per_capita_complaints": m.per_capita_complaints or 0,
            "total_deliberations": m.total_deliberations or 0,
            "per_capita_deliberations": m.per_capita_deliberations or 0,
            "avg_councillors": m.avg_councillors or 0,
        }
        row["resolution_rate"] = round(closed / total, 4) if total > 0 else 0
        row["escalation_rate"] = round(escalated / total, 4) if total > 0 else 0
        row["health_score"] = _compute_health_score_from_row(row)
        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df, pd.Series(dtype=object), pd.Series(dtype=float)

    # --- Step 2: Lag and trend features (per ward) ---
    df = df.sort_values(["ward_name", "year"])

    df["complaints_lag1"] = df.groupby("ward_name")["total_complaints"].shift(1)
    df["complaints_lag2"] = df.groupby("ward_name")["total_complaints"].shift(2)
    df["resolution_days_lag1"] = df.groupby("ward_name")["avg_resolution_days"].shift(1)
    df["complaints_rolling_mean_3yr"] = (
        df.groupby("ward_name")["total_complaints"]
        .transform(lambda x: x.rolling(3, min_periods=1).mean())
    )
    df["complaint_growth_rate"] = df.groupby("ward_name")["total_complaints"].pct_change() * 100
    df["complaint_growth_rate"] = df["complaint_growth_rate"].fillna(0)
    df["prev_year_health_score"] = df.groupby("ward_name")["health_score"].shift(1)

    # --- Step 3: Fill NaN (first-year lags) ---
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].fillna(0)

    # --- Step 4: Target variables ---
    def risk_label(score):
        if score >= 70:
            return "Low"
        elif score >= 45:
            return "Medium"
        return "High"

    y_risk = df["health_score"].apply(risk_label)
    y_complaints = df["total_complaints"]

    # When training, shift target so T features predict T+1 complaints
    if training:
        y_complaints = df.groupby("ward_name")["total_complaints"].shift(-1)
        valid = y_complaints.notna()

    # Feature columns (exclude identifiers and targets)
    exclude = {"ward_no", "ward_name", "year", "health_score", "total_complaints"}
    feature_cols = [c for c in df.columns if c not in exclude]
    X = df[feature_cols].copy()

    meta = df[["ward_no", "ward_name", "year", "health_score", "total_complaints"]]

    if training:
        X = X.loc[valid]
        y_risk = y_risk.loc[valid]
        y_complaints = y_complaints.loc[valid]
        meta = meta.loc[valid]

    return X, y_risk, y_complaints, meta
