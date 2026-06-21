"""
Model training for UrbanIQ Phase 2.

Trains:
  - XGBClassifier -> risk classification (Low/Medium/High)
  - XGBRegressor  -> complaint count forecasting
  - DBSCAN        -> ward clustering for anomaly/pattern detection
"""

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier, XGBRegressor

from ml.utils import save_model, RISK_MODEL_PATH, FORECAST_MODEL_PATH, FORECAST_LOWER_PATH, FORECAST_UPPER_PATH, CLUSTER_MODEL_PATH, SCALER_PATH, FEATURES_PATH


def _label_encode(y_risk):
    mapping = {"Low": 0, "Medium": 1, "High": 2}
    return y_risk.map(mapping)


def train_risk_model(X, y_risk):
    """Train XGBClassifier for risk prediction. Returns (model, accuracy)."""
    y_enc = _label_encode(y_risk)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    save_model(scaler, SCALER_PATH)
    save_model(list(X.columns), FEATURES_PATH)

    model = XGBClassifier(
        n_estimators=150, max_depth=5, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, eval_metric="mlogloss",
    )
    model.fit(X_train_s, y_train)
    acc = model.score(X_test_s, y_test)
    print(f"  Risk model accuracy: {acc:.3f}")

    save_model(model, RISK_MODEL_PATH)
    print(f"  Saved: {RISK_MODEL_PATH.name}")
    return model, acc


def _train_quantile_model(X_train_s, y_train, alpha, path, label):
    """Train a single quantile XGBRegressor and save it."""
    model = XGBRegressor(
        n_estimators=150, max_depth=5, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        objective='reg:quantileerror',
        quantile_alpha=alpha,
    )
    model.fit(X_train_s, y_train)
    save_model(model, path)
    print(f"  Saved {label}: {path.name}")
    return model


def train_forecast_model(X, y_complaints):
    """Train XGBRegressor quantile models (0.1, 0.5, 0.9). Returns (model, R^2)."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_complaints.values, test_size=0.2, random_state=42
    )

    from ml.utils import load_model
    scaler = load_model(SCALER_PATH)
    if scaler is None:
        raise RuntimeError("Train risk model first (scaler needed).")
    expected_cols = load_model(FEATURES_PATH)

    X_train_s = scaler.transform(X_train[expected_cols])
    X_test_s = scaler.transform(X_test[expected_cols])

    # Median (0.5) for point predictions
    model = _train_quantile_model(X_train_s, y_train, 0.5, FORECAST_MODEL_PATH, "forecast (median)")

    # Lower bound (0.1) and upper bound (0.9) for intervals
    _train_quantile_model(X_train_s, y_train, 0.1, FORECAST_LOWER_PATH, "forecast (lower)")
    _train_quantile_model(X_train_s, y_train, 0.9, FORECAST_UPPER_PATH, "forecast (upper)")

    r2 = model.score(X_test_s, y_test)
    print(f"  Forecast model R^2: {r2:.3f}")
    return model, r2


def train_clustering(X):
    """Run DBSCAN clustering. Saves cluster metadata."""
    from ml.utils import load_model
    scaler = load_model(SCALER_PATH)
    expected_cols = load_model(FEATURES_PATH)
    X_s = scaler.transform(X[expected_cols])

    model = DBSCAN(eps=1.5, min_samples=3)
    labels = model.fit_predict(X_s)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    print(f"  DBSCAN: {n_clusters} clusters, {n_noise} noise points")

    save_model({
        "eps": 1.5, "min_samples": 3,
        "labels": labels.tolist(),
        "n_clusters": n_clusters, "n_noise": n_noise,
    }, CLUSTER_MODEL_PATH)
    print(f"  Saved: {CLUSTER_MODEL_PATH.name}")
    return model, labels


def expanding_window_validation(target_years=None):
    """
    Expanding-window time-series cross-validation.

    For each test year, trains on ALL prior years and predicts that year.
    Reports out-of-sample R² (regression) and accuracy (classification).

    Args:
        target_years: years to use as test folds (default: 2020..2024)
    """
    from ml.features import build_feature_matrix
    from ml.utils import load_model, save_model, SCALER_PATH, FEATURES_PATH
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBClassifier, XGBRegressor
    from sklearn.metrics import r2_score, accuracy_score
    import warnings

    if target_years is None:
        target_years = [2020, 2021, 2022, 2023, 2024]

    all_years = sorted(target_years)
    min_year = all_years[0]

    r2_scores = []
    acc_scores = []

    print("\n" + "=" * 60)
    print("EXPANDING-WINDOW TIME-SERIES VALIDATION")
    print("=" * 60)

    for test_year in all_years:
        train_years = list(range(2019, test_year))
        print(f"\n  Fold: train {train_years} -> predict {test_year}")

        X_train, y_risk_train, y_complaints_train, _ = build_feature_matrix(
            years=train_years, training=True
        )
        if X_train.empty:
            print(f"  SKIP — no training data for years {train_years}")
            continue

        # Also get full feature set (with lag features computed correctly)
        X_full, _, _, meta_full = build_feature_matrix(
            years=train_years + [test_year]
        )
        test_mask = meta_full["year"] == test_year
        if not test_mask.any():
            print(f"  SKIP — no test data for {test_year}")
            continue

        X_test_raw = X_full[test_mask]
        y_test_complaints = meta_full.loc[test_mask, "total_complaints"]

        # Fit scaler on training columns
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test_raw[X_train.columns])

        # --- Risk model ---
        y_risk_enc = y_risk_train.map({"Low": 0, "Medium": 1, "High": 2})
        clf = XGBClassifier(
            n_estimators=150, max_depth=5, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, eval_metric="mlogloss",
        )
        clf.fit(X_train_s, y_risk_enc)
        y_pred_risk = clf.predict(X_test_s)
        y_true_risk = meta_full.loc[test_mask, "health_score"].apply(
            lambda s: 0 if s >= 70 else 1 if s >= 45 else 2
        )
        acc = accuracy_score(y_true_risk, y_pred_risk)

        # --- Forecast model ---
        reg = XGBRegressor(
            n_estimators=150, max_depth=5, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, random_state=42,
        )
        reg.fit(X_train_s, y_complaints_train)
        y_pred_comp = reg.predict(X_test_s)
        r2 = r2_score(y_test_complaints, y_pred_comp)

        r2_scores.append(r2)
        acc_scores.append(acc)

        print(f"    Risk accuracy:    {acc:.3f}")
        print(f"    Forecast R²:      {r2:.3f}")

    print("\n  " + "-" * 50)
    if r2_scores:
        print(f"  Mean OOS R²:        {np.mean(r2_scores):.3f} "
              f"(range: {min(r2_scores):.3f} – {max(r2_scores):.3f})")
    if acc_scores:
        print(f"  Mean OOS accuracy:  {np.mean(acc_scores):.3f} "
              f"(range: {min(acc_scores):.3f} – {max(acc_scores):.3f})")
    print("=" * 60)

    return r2_scores, acc_scores
