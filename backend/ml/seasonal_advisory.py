"""
Seasonal advisory system using Praja CSV categories.

Generates proactive warnings based on known Mumbai seasonality patterns.
Pure calendar logic — no per-ward data needed.

CSV categories with seasonality:
  Drainage, Storm Water Drainage    → Monsoon (Jun-Sep)
  Roads                              → Monsoon (Jul-Oct)
  Water Supply                       → Summer (Mar-May)
  Pest control                       → Monsoon (Jun-Sep)
  Solid Waste Management             → Flat year-round
"""

from datetime import datetime

MONTH_NAMES = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

SEASONAL_PROFILES = {
    'Drainage': {
        'peak_months': [6, 7, 8, 9],
        'ramp_up_months': [5],
        'surge_factor': 3.0,
        'reason': 'Monsoon season — drainage & sewage systems are overwhelmed by heavy rainfall.',
        'advice': 'Pre-clean drains and desilt choke points before monsoon hits.',
    },
    'Storm Water Drainage': {
        'peak_months': [6, 7, 8, 9],
        'ramp_up_months': [5],
        'surge_factor': 2.5,
        'reason': 'Monsoon season — storm water drains get clogged with debris.',
        'advice': 'Clear storm water drains of debris and silt before monsoon.',
    },
    'Roads': {
        'peak_months': [7, 8, 9, 10],
        'ramp_up_months': [6],
        'surge_factor': 2.5,
        'reason': 'Monsoon rains cause potholes and road surface damage.',
        'advice': 'Conduct pre-monsoon road audits. Fill existing potholes before rains intensify.',
    },
    'Water Supply': {
        'peak_months': [3, 4, 5],
        'ramp_up_months': [2],
        'surge_factor': 2.0,
        'reason': 'Summer heat — water demand spikes and supply becomes erratic.',
        'advice': 'Schedule water tanker deployments in advance. Identify wards with chronic shortages.',
    },
    'Pest control': {
        'peak_months': [6, 7, 8, 9],
        'ramp_up_months': [5],
        'surge_factor': 2.0,
        'reason': 'Monsoon breeding season — mosquito and pest populations explode.',
        'advice': 'Step up fogging before monsoon. Clear water-logged breeding areas.',
    },
}


def _season_status(profile, month):
    if month in profile['peak_months']:
        return 'peak_season'
    if month in profile['ramp_up_months']:
        return 'pre_season'
    if profile['peak_months']:
        last_peak = max(profile['peak_months'])
        next_after = last_peak % 12 + 1
        if month == next_after:
            return 'post_season'
    return 'normal'


def _month_range(months):
    if not months:
        return ''
    if len(months) == 1:
        return MONTH_NAMES[months[0]]
    return f"{MONTH_NAMES[months[0]]}–{MONTH_NAMES[months[-1]]}"


def generate_seasonal_advisories(failing_categories=None, current_month=None):
    """
    Generate seasonal advisories based on calendar + city-wide anomaly context.

    Args:
        failing_categories: list from detect_category_anomalies() (used for context)
        current_month: int 1-12 (default: current month)

    Returns list sorted by urgency.
    """
    if current_month is None:
        current_month = datetime.now().month

    anomaly_lookup = {}
    if failing_categories:
        for c in failing_categories:
            anomaly_lookup[c['issue']] = c

    check_months = [
        (current_month, 'current'),
        (current_month % 12 + 1, 'next'),
        ((current_month + 1) % 12 + 1, 'next+1'),
    ]

    advisories = []
    for cat, profile in SEASONAL_PROFILES.items():
        status = _season_status(profile, current_month)
        upcoming_peak = any(
            _season_status(profile, m) == 'peak_season'
            for m, _ in check_months
        )

        if status == 'normal' and not upcoming_peak:
            continue

        anomaly = anomaly_lookup.get(cat, {})
        is_growing = (anomaly.get('recent_3yr_growth_pct', 0) or 0) > 10

        lines = []
        if status == 'pre_season':
            lines.append(
                f"{cat} complaints typically surge "
                f"{profile['surge_factor']}x during {_month_range(profile['peak_months'])} "
                f"({profile['reason'].split('.')[0].lower()})."
            )
            if is_growing:
                lines.append(f"⚠ Already trending +{anomaly['recent_3yr_growth_pct']:.0f}% city-wide — act now.")
            lines.append(f"Recommended: {profile['advice']}")
        elif status == 'peak_season':
            lines.append(f"{cat} is at seasonal peak (typically {profile['surge_factor']}x surge).")
            if is_growing:
                lines.append(f"⚠ Trending +{anomaly['recent_3yr_growth_pct']:.0f}% city-wide. {profile['advice']}")
            else:
                lines.append(f"Volume is within expected range for this season.")
        elif status == 'post_season':
            lines.append(f"{cat} peak season is ending. Continue monitoring — residual issues may persist.")
        elif upcoming_peak:
            for check_month, _ in check_months:
                if _season_status(profile, check_month) == 'peak_season':
                    lines.append(
                        f"{cat} will enter peak season in {MONTH_NAMES[check_month]} "
                        f"(typically {profile['surge_factor']}x surge). Recommended: {profile['advice']}"
                    )
                    break

        text = ' '.join(lines)
        if not text.strip():
            continue

        urgency = 3 if (status == 'peak_season' and is_growing) else \
                  2 if status in ('peak_season', 'pre_season') else \
                  1 if upcoming_peak else 0

        advisories.append({
            'category': cat,
            'display_name': cat,
            'season_status': status,
            'surge_factor': profile['surge_factor'],
            'advisory_text': text,
            'urgency': urgency,
        })

    advisories.sort(key=lambda a: a['urgency'], reverse=True)
    return advisories
