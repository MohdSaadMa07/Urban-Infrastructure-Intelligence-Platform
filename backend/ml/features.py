"""
Feature engineering for ward-level civic metrics.

Builds a feature matrix from CivicMetrics (DB) and optional category-wide data.
"""

import numpy as np
import pandas as pd
from django.db.models import Avg

from ml.utils import load_category_data


def _compute_health_score_from_row(row):
    """Replicate the health score logic for a feature row dict."""
    complaints = row.get("per_capita_complaints", 0) or 0
    avg_days = row.get("avg_resolution_days", 0) or 0
    deliberations = row.get("per_capita_deliberations", 0) or 0

    import math

    def sigmoid(x, midpoint, steepness):
        return 1.0 / (1.0 + math.exp(steepness * (x - midpoint)))

    complaint_score = sigmoid(complaints, midpoint=6500, steepness=0.0008)
    resolution_score = sigmoid(avg_days, midpoint=40, steepness=0.12)
    deliberation_score = sigmoid(deliberations, midpoint=55, steepness=-0.10)

    raw = (0.35 * complaint_score + 0.35 * resolution_score + 0.30 * deliberation_score) * 100
    return round(max(0.0, min(100.0, raw)), 2)


def build_feature_matrix(years=None):
    """
    Build feature matrix and target vectors from CivicMetrics and optional category data.

    Args:
        years: iterable of years to include (default: all available)

    Returns:
        X: pd.DataFrame of features
        y_risk: pd.Series of risk labels (Low/Medium/High)
        y_complaints: pd.Series of total_complaints for regression
    """
    from api.models import CivicMetrics, Ward

    # --- Step 1: Load base metrics ---
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
        # Derived rates
        row["resolution_rate"] = round(closed / total, 4) if total > 0 else 0
        row["escalation_rate"] = round(escalated / total, 4) if total > 0 else 0
        # Health score
        row["health_score"] = _compute_health_score_from_row(row)
        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df, pd.Series(dtype=object), pd.Series(dtype=float)

    # --- Step 2: Lagged features ---
    df = df.sort_values(["ward_name", "year"])
    df["prev_year_health_score"] = df.groupby("ward_name")["health_score"].shift(1)
    df["complaint_growth_rate"] = df.groupby("ward_name")["total_complaints"].pct_change() * 100
    df["complaint_growth_rate"] = df["complaint_growth_rate"].fillna(0)

    # --- Step 3: Cyclical year encoding ---
    df["year_sin"] = np.sin(2 * np.pi * (df["year"] - 2019) / 10)
    df["year_cos"] = np.cos(2 * np.pi * (df["year"] - 2019) / 10)

    # --- Step 4: Category distribution features ---
    cat_df = load_category_data()
    if cat_df is not None:
        cat_df = cat_df.rename(columns={"Year": "year"})
        # Merge year-aligned category percentages
        df = df.merge(cat_df, on="year", how="left")
        # For years beyond cat data, use the latest available distribution
        max_cat_year = cat_df["year"].max()
        for col in [c for c in cat_df.columns if c != "year"]:
            df[col] = df[col].fillna(
                df[df["year"] == max_cat_year][col].iloc[0] if max_cat_year in df["year"].values else 0
            )

    # --- Step 5: Fill NaN (first-year lagged features) ---
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].fillna(0)

    # --- Step 6: Target variables ---
    def risk_label(score):
        if score >= 70:
            return "Low"
        elif score >= 45:
            return "Medium"
        return "High"

    y_risk = df["health_score"].apply(risk_label)
    y_complaints = df["total_complaints"]

    # Feature columns (exclude identifiers and targets)
    exclude = {"ward_no", "ward_name", "year", "health_score", "total_complaints"}
    feature_cols = [c for c in df.columns if c not in exclude]
    X = df[feature_cols].copy()

    return X, y_risk, y_complaints, df[["ward_no", "ward_name", "year", "health_score", "total_complaints"]]
