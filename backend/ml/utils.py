"""
Shared utilities for the ML module.
"""

import os
import joblib
import pandas as pd
from pathlib import Path

# Paths
ML_DIR = Path(__file__).resolve().parent
MODELS_DIR = ML_DIR / "models"
CATEGORY_CSV = ML_DIR.parent / "data" / "Table_1_Issue_Wise_Overall_Complaints.csv"

RISK_MODEL_PATH = MODELS_DIR / "risk_model.pkl"
FORECAST_MODEL_PATH = MODELS_DIR / "forecast_model.pkl"
FORECAST_LOWER_PATH = MODELS_DIR / "forecast_lower.pkl"
FORECAST_UPPER_PATH = MODELS_DIR / "forecast_upper.pkl"
FORECAST_N2_MODEL_PATH = MODELS_DIR / "forecast_n2_model.pkl"
FORECAST_N2_LOWER_PATH = MODELS_DIR / "forecast_n2_lower.pkl"
FORECAST_N2_UPPER_PATH = MODELS_DIR / "forecast_n2_upper.pkl"
CLUSTER_MODEL_PATH = MODELS_DIR / "cluster_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
FEATURES_PATH = MODELS_DIR / "feature_columns.pkl"


def ensure_models_dir():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


def save_model(model, path):
    ensure_models_dir()
    joblib.dump(model, str(path))


def load_model(path):
    if not path.exists():
        return None
    return joblib.load(str(path))


def load_category_data():
    """Load issue-wise complaint data if available. Returns DataFrame or None."""
    if not CATEGORY_CSV.exists():
        return None
    df = pd.read_csv(str(CATEGORY_CSV))
    # Melt year columns into rows
    year_cols = [c for c in df.columns if c.isdigit()]
    melted = df.melt(id_vars=["Issue"], value_vars=year_cols,
                     var_name="Year", value_name="count")
    melted["Year"] = melted["Year"].astype(int)
    # Pivot: each Issue becomes a column
    pivoted = melted.pivot_table(index="Year", columns="Issue",
                                 values="count", aggfunc="sum").fillna(0)
    # Convert to percentages per year
    pivoted = pivoted.div(pivoted.sum(axis=1), axis=0) * 100
    pivoted.columns = [f"cat_{col}" for col in pivoted.columns]
    pivoted = pivoted.reset_index()
    return pivoted
