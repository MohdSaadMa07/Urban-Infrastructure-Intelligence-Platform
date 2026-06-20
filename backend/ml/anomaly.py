"""
Anomaly detection for ward and category data.

Uses statistical baselines computed from historical CSV data:
  - Table_1_Issue_Wise_Overall_Complaints.csv: 18 categories, 13 years (2012-2024)
  - ward_metrics_multiyear.csv: 24 wards, 8 years (2019-2026)

Method: z-score against rolling mean + std.  |z| > 2.0 → anomaly.
"""

import pandas as pd
import numpy as np
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR.parent / "data"

CATEGORY_CSV = DATA_DIR / "Table_1_Issue_Wise_Overall_Complaints.csv"
WARD_METRICS_CSV = DATA_DIR / "ward_metrics_multiyear.csv"
ESCALATION_CSV = DATA_DIR / "escalation_data.csv"

Z_THRESHOLD = 1.5


def _load_csv(path):
    if not path.exists():
        return None
    return pd.read_csv(str(path))


# ── Category-level anomalies ─────────────────────────────────────────────


def detect_category_anomalies(z_threshold=Z_THRESHOLD):
    """
    For each of the 18 categories, compute z-score of the latest year (2024)
    against the full 2012-2024 distribution.

    Returns list of dicts sorted by |z_score| descending:
      { issue, latest, mean, std, z_score, direction, severity }
    """
    df = _load_csv(CATEGORY_CSV)
    if df is None:
        return []

    year_cols = [c for c in df.columns if c.isdigit()]
    if len(year_cols) < 5:
        return []

    results = []
    for _, row in df.iterrows():
        vals = row[year_cols].values.astype(float)
        if len(vals) < 3:
            continue

        mean = np.mean(vals)
        std = np.std(vals, ddof=1)
        latest = vals[-1]

        if std == 0:
            continue

        z = (latest - mean) / std
        direction = 'high' if z > 0 else 'low'

        # Severity labels
        abs_z = abs(z)
        if abs_z >= 3:
            severity = 'critical'
        elif abs_z >= 2:
            severity = 'major'
        elif abs_z >= 1.5:
            severity = 'minor'
        else:
            severity = 'normal'

        growth_3yr = ((vals[-1] - vals[-4]) / vals[-4] * 100) if len(vals) >= 4 and vals[-4] > 0 else 0

        results.append({
            'issue': row['Issue'],
            'latest': int(round(latest)),
            'mean': round(mean, 1),
            'std': round(std, 1),
            'z_score': round(z, 2),
            'direction': direction,
            'severity': severity,
            'is_anomaly': abs_z >= z_threshold,
            'pct_above_mean': round((latest - mean) / mean * 100, 1) if mean > 0 else 0,
            'recent_3yr_growth_pct': round(growth_3yr, 1),
        })

    results.sort(key=lambda r: abs(r['z_score']), reverse=True)
    return results


# ── Ward-level anomalies ────────────────────────────────────────────────


def detect_ward_anomalies(ward_name=None, z_threshold=Z_THRESHOLD):
    """
    Detect wards with unusual complaint volumes using ward_metrics CSV.

    For each ward, computes mean/std of Total_Complaints over all available
    years and flags the latest year if it's an outlier.

    If ward_name provided, returns only that ward's result.
    Returns list of dicts sorted by |z_score| descending.
    """
    df = _load_csv(WARD_METRICS_CSV)
    if df is None:
        return []

    results = []
    wards = [ward_name] if ward_name else df['Ward'].unique()

    for w in wards:
        ward_df = df[df['Ward'] == w].sort_values('Year')
        if len(ward_df) < 3:
            continue

        totals = ward_df['Total_Complaints'].values.astype(float)
        years = ward_df['Year'].values

        mean = np.mean(totals)
        std = np.std(totals, ddof=1)
        latest_total = totals[-1]
        latest_year = int(years[-1])

        if std == 0:
            continue

        z = (latest_total - mean) / std
        direction = 'high' if z > 0 else 'low'

        abs_z = abs(z)
        if abs_z >= 3:
            severity = 'critical'
        elif abs_z >= 2:
            severity = 'major'
        elif abs_z >= 1.5:
            severity = 'minor'
        else:
            severity = 'normal'

        # Year-over-year change
        yoy_change = None
        if len(totals) >= 2:
            yoy_change = round((totals[-1] - totals[-2]) / totals[-2] * 100, 1) if totals[-2] > 0 else 0

        results.append({
            'ward': w,
            'latest_year': latest_year,
            'latest_total': int(round(latest_total)),
            'mean': round(mean, 1),
            'std': round(std, 1),
            'z_score': round(z, 2),
            'direction': direction,
            'severity': severity,
            'is_anomaly': abs_z >= z_threshold,
            'pct_above_mean': round((latest_total - mean) / mean * 100, 1) if mean > 0 else 0,
            'yoy_change_pct': yoy_change,
        })

    results.sort(key=lambda r: abs(r['z_score']), reverse=True)
    return results


# ── Trend-break anomalies (direction change) ────────────────────────────


def detect_trend_breaks(z_threshold=Z_THRESHOLD):
    """
    Find categories where the 3-year trend direction has reversed compared
    to the long-term baseline. E.g. a category that was stable for a decade
    but suddenly spiked in the last 3 years.

    Uses split-window: early years (all but last 3) vs recent 3 years.
    """
    df = _load_csv(CATEGORY_CSV)
    if df is None:
        return []

    year_cols = [c for c in df.columns if c.isdigit()]
    if len(year_cols) < 6:
        return []

    results = []
    for _, row in df.iterrows():
        vals = row[year_cols].values.astype(float)
        if len(vals) < 6:
            continue

        early = vals[:-3]
        recent = vals[-3:]

        early_mean = np.mean(early)
        recent_mean = np.mean(recent)
        early_std = np.std(early, ddof=1)

        if early_std == 0:
            continue

        z = (recent_mean - early_mean) / early_std
        direction = 'surge' if z > 0 else 'drop'

        abs_z = abs(z)
        if abs_z >= 3:
            severity = 'critical'
        elif abs_z >= 2:
            severity = 'major'
        else:
            severity = 'minor'

        if abs_z >= z_threshold:
            results.append({
                'issue': row['Issue'],
                'early_mean': round(early_mean, 1),
                'recent_mean': round(recent_mean, 1),
                'z_score': round(z, 2),
                'direction': direction,
                'severity': severity,
                'early_years': f"{year_cols[0]}-{year_cols[-4]}",
                'recent_years': f"{year_cols[-3]}-{year_cols[-1]}",
                'pct_change': round((recent_mean - early_mean) / early_mean * 100, 1) if early_mean > 0 else 0,
            })

    results.sort(key=lambda r: abs(r['z_score']), reverse=True)
    return results


# ── Combined anomaly report ─────────────────────────────────────────────


def get_ward_anomaly_report(ward_name=None):
    """
    Returns a combined anomaly snapshot for a ward (or all wards):
      - category_anomalies: city-wide category anomalies affecting this ward
      - ward_anomaly: this ward's own volume anomaly (if any)
      - trend_breaks: categories with recent trend reversals
      - summary: plain-english summary sentence
    """
    cat_anomalies = detect_category_anomalies()
    ward_results = detect_ward_anomalies(ward_name)
    trend_breaks = detect_trend_breaks()

    ward_anomaly = ward_results[0] if ward_results else None

    # Filter category anomalies to the most relevant
    sig_cats = [c for c in cat_anomalies if c['is_anomaly']]

    # Summary
    summary_parts = []
    if sig_cats:
        high_count = sum(1 for c in sig_cats if c['direction'] == 'high')
        low_count = sum(1 for c in sig_cats if c['direction'] == 'low')
        if high_count:
            summary_parts.append(f"{high_count} category/categories running unusually high")
        if low_count:
            summary_parts.append(f"{low_count} category/categories running unusually low")

    if ward_anomaly and ward_anomaly['is_anomaly']:
        summary_parts.append(
            f"Ward {ward_anomaly['ward']} complaints are "
            f"{'above' if ward_anomaly['direction'] == 'high' else 'below'} "
            f"historical norm ({ward_anomaly['pct_above_mean']:+.1f}%)"
        )

    if trend_breaks:
        surge_count = sum(1 for t in trend_breaks if t['direction'] == 'surge')
        if surge_count:
            summary_parts.append(f"{surge_count} category/categories show sudden recent surge")

    return {
        'ward': ward_name,
        'category_anomalies': sig_cats[:10],
        'ward_anomaly': ward_anomaly,
        'trend_breaks': trend_breaks[:5],
        'summary': '. '.join(summary_parts) if summary_parts else 'No significant anomalies detected.',
    }
