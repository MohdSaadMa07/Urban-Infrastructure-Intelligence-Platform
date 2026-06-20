"""
Ward-specific category insight computation.

Combines THREE data sources for per-ward failing category rankings:
  1. City-wide complaint growth trends  (Table_1 CSV — 2012-2024)
  2. Escalation rates per category/ward  (escalation_data.csv — Table 55)
  3. Ward-level total-complaint metrics  (ward_metrics_multiyear.csv)

Categories that are BOTH growing fast AND rarely resolved (high escalation)
rank highest.  Wards with high escalation volume see an additional boost.
"""

import pandas as pd
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR.parent / "data"

CATEGORY_CSV = DATA_DIR / "Table_1_Issue_Wise_Overall_Complaints.csv"
ESCALATION_CSV = DATA_DIR / "escalation_data.csv"
WARD_METRICS_CSV = DATA_DIR / "ward_metrics_multiyear.csv"

# ── Load helpers ──────────────────────────────────────────────────────────


def _load_csv(path):
    if not path.exists():
        return None
    return pd.read_csv(str(path))


def load_ward_metrics():
    return _load_csv(WARD_METRICS_CSV)


def load_escalation():
    return _load_csv(ESCALATION_CSV)

# ── Ward profile (volume + growth trajectory) ─────────────────────────────


def get_ward_profile(ward_name):
    df = load_ward_metrics()
    if df is None:
        return None
    ward_df = df[df['Ward'] == ward_name]
    if ward_df.empty:
        return None

    recent = ward_df[ward_df['Year'] >= 2022].sort_values('Year')
    if len(recent) < 2:
        return None

    latest = recent.iloc[-1]
    first = recent.iloc[0]
    fv, lv = first['Total_Complaints'], latest['Total_Complaints']
    ward_growth = ((lv - fv) / fv * 100) if fv > 0 else 0

    all_latest = df[df['Year'] == latest['Year']]
    max_total = all_latest['Total_Complaints'].max()
    volume_ratio = latest['Total_Complaints'] / max_total if max_total > 0 else 0.5

    return {
        'ward': ward_name,
        'latest_total': int(latest['Total_Complaints']),
        'growth_rate': round(ward_growth, 1),
        'volume_ratio': round(volume_ratio, 3),
        'trend': 'increasing' if ward_growth > 5 else (
            'decreasing' if ward_growth < -5 else 'stable'),
    }


def get_ward_trend_description(ward_profile):
    if ward_profile is None:
        return ""
    w = ward_profile['ward']
    total = ward_profile['latest_total']
    rate = ward_profile['growth_rate']
    t = ward_profile['trend']
    if t == 'increasing':
        return f"Ward {w} has {total:,} total complaints (+{rate}% recent growth) — higher than average volume magnifies impact."
    elif t == 'decreasing':
        return f"Ward {w} has {total:,} total complaints ({rate}% recent decline) — lower volume dampens impact."
    else:
        return f"Ward {w} has {total:,} total complaints (stable trend) — moderate impact."

# ── City-wide category growth rates ───────────────────────────────────────


def load_category_growth_rates():
    """
    Returns dict:  {category_name: recent_3yr_growth_pct}
    Uses the last 3 available years from the updated CSV.
    """
    df = _load_csv(CATEGORY_CSV)
    if df is None:
        return {}

    year_cols = [c for c in df.columns if c.isdigit()]
    if len(year_cols) < 3:
        return {}

    rates = {}
    for _, row in df.iterrows():
        vals = row[year_cols].values.astype(float)
        if len(vals) < 3:
            continue
        recent = vals[-3:]
        start, end = recent[0], recent[-1]
        growth = ((end - start) / start * 100) if start > 0 else 0
        rates[row['Issue']] = round(growth, 1)

    return rates

# ── Escalation data ───────────────────────────────────────────────────────


def get_category_escalation_rate(category_name, esc_df):
    """Return escalation ratio (Level I / total) for a category, 0 if unknown."""
    if esc_df is None:
        return 0.0
    row = esc_df[(esc_df['entity_type'] == 'category')
                 & (esc_df['entity'] == category_name)]
    if row.empty:
        return 0.0
    total = row.iloc[0]['total_complaints']
    l1 = row.iloc[0]['escalated_level1']
    return l1 / total if total > 0 else 0.0


def get_ward_escalation_rate(ward_name, esc_df):
    """Return escalation ratio (Level I / total) for a ward, 0 if unknown."""
    if esc_df is None:
        return 0.0
    row = esc_df[(esc_df['entity_type'] == 'ward')
                 & (esc_df['entity'] == ward_name)]
    if row.empty:
        return 0.0
    total = row.iloc[0]['total_complaints']
    l1 = row.iloc[0]['escalated_level1']
    return l1 / total if total > 0 else 0.0


def get_all_category_escalation_rates(esc_df):
    """Return dict {category_name: escalation_rate} for all categories."""
    if esc_df is None:
        return {}
    cat_df = esc_df[esc_df['entity_type'] == 'category']
    result = {}
    for _, row in cat_df.iterrows():
        t = row['total_complaints']
        result[row['entity']] = round(row['escalated_level1'] / t, 4) if t > 0 else 0
    return result

# ── Combined scoring ──────────────────────────────────────────────────────


# Category–ward affinity: which wards are most affected by which category.
# Derived from Table_3 (Top 3 Wards per sub-issue, aggregated to main categories).
CATEGORY_WARD_AFFINITY = {
    'Drainage':               ['B', 'H/W', 'K/W'],
    'Roads':                  ['A', 'B', 'D'],
    'Solid Waste Management': ['C', 'D', 'H/W', 'R/C'],
    'Water Supply':           ['B', 'C', 'K/E', 'M/E', 'M/W', 'N'],
}


def compute_ward_category_scores(ward_name=None, ward_category_names=None):
    """
    Compute a severity score for each city-wide category, optionally
    adjusted for a specific ward.

    Scoring factors:
      - growth_norm:  city-wide recent growth rate (0-1 normalised)
      - esc_norm:     category escalation rate (0-1 normalised)
      - db_boost:     +0.25 if category appears in ward's own DB complaint data
      - aff_boost:    +0.30 if ward is a known high-affinity ward for this
                      category (from Table_3 Top-3 Wards data)
      - esc_boost:    +0.15 × ward_escalation_rate (wards with high escalation
                      see all categories as more severe)

    Returns list of dicts sorted by descending score.
    """
    growth_rates = load_category_growth_rates()
    if not growth_rates:
        return []

    esc_df = load_escalation()
    cat_esc_rates = get_all_category_escalation_rates(esc_df)

    ward_esc_rate = 0.0
    if ward_name:
        ward_esc_rate = get_ward_escalation_rate(ward_name, esc_df)

    max_growth = max(abs(v) for v in growth_rates.values()) or 1
    max_esc = max(cat_esc_rates.values()) or 1

    scored = []
    for cat, growth in growth_rates.items():
        growth_norm = abs(growth) / max_growth
        esc_rate = cat_esc_rates.get(cat, 0)
        esc_norm = esc_rate / max_esc

        db_boost = 0.25 if (ward_category_names and cat in ward_category_names) else 0.0
        aff_boost = 0.30 if (ward_name and ward_name in CATEGORY_WARD_AFFINITY.get(cat, [])) else 0.0
        esc_boost = 0.15 * ward_esc_rate

        score = (0.35 * growth_norm) + (0.35 * esc_norm) + db_boost + aff_boost + esc_boost

        if score > 0:
            scored.append({
                'category': cat,
                'growth_rate': growth,
                'escalation_rate': round(esc_rate * 100, 1),
                'growth_norm': round(growth_norm, 3),
                'esc_norm': round(esc_norm, 3),
                'score': round(score, 3),
            })

    scored.sort(key=lambda s: s['score'], reverse=True)
    return scored
