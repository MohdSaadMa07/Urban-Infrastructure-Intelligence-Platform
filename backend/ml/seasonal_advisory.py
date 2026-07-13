"""
Seasonal advisory system for ward-level complaint categories.

Uses known Mumbai seasonality patterns to generate proactive warnings
before complaint surges occur. No ML — pure rule-based calendar logic.

Monsoon:  Jun-Sep    → Drainage, Roads/Potholes, Pest Control surge
Summer:   Mar-May    → Water Supply peaks
Winter:   Nov-Feb    → Streetlights slightly up (shorter days)
Garbage:  Flat year-round
"""

from datetime import datetime

MONTH_NAMES = [
    '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

SEASONAL_PROFILES = {
    'drainage': {
        'peak_months': [6, 7, 8, 9],
        'ramp_up_months': [5],
        'surge_factor': 3.0,
        'reason': 'Monsoon season — drainage & sewage systems are overwhelmed by heavy rainfall.',
        'advice': 'Pre-clean drains and desilt choke points before monsoon hits. Deploy mobile pumping units to vulnerable low-lying areas.',
    },
    'road': {
        'peak_months': [7, 8, 9, 10],
        'ramp_up_months': [6],
        'surge_factor': 2.5,
        'reason': 'Monsoon rains cause potholes and road surface damage.',
        'advice': 'Conduct pre-monsoon road audits. Prioritize filling existing potholes before rains intensify to prevent them from widening.',
    },
    'pothole': {
        'peak_months': [7, 8, 9, 10],
        'ramp_up_months': [6],
        'surge_factor': 2.5,
        'reason': 'Monsoon rains cause potholes and road surface damage.',
        'advice': 'Conduct pre-monsoon road audits. Prioritize filling existing potholes before rains intensify to prevent them from widening.',
    },
    'water': {
        'peak_months': [3, 4, 5],
        'ramp_up_months': [2],
        'surge_factor': 2.0,
        'reason': 'Summer heat — water demand spikes and supply becomes erratic.',
        'advice': 'Schedule water tanker deployments in advance. Identify wards with chronic shortages and pre-position reserves.',
    },
    'pest control': {
        'peak_months': [6, 7, 8, 9],
        'ramp_up_months': [5],
        'surge_factor': 2.0,
        'reason': 'Monsoon breeding season — mosquito and pest populations explode in stagnant water.',
        'advice': 'Step up fogging and larvicide spraying before monsoon. Clear water-logged areas that serve as breeding grounds.',
    },
    'streetlight': {
        'peak_months': [11, 12, 1],
        'ramp_up_months': [10],
        'surge_factor': 1.3,
        'reason': 'Winter — shorter daylight hours mean lights are on longer and faults are noticed more.',
        'advice': 'Conduct pre-winter streetlight audit. Replace aging bulbs and repair damaged poles before the darker months.',
    },
    'garbage': {
        'peak_months': [],
        'ramp_up_months': [],
        'surge_factor': 1.0,
        'reason': 'Year-round issue with no strong seasonal pattern.',
        'advice': 'Maintain regular collection schedules. Focus on high-density commercial zones.',
    },
    'other': {
        'peak_months': [],
        'ramp_up_months': [],
        'surge_factor': 1.0,
        'reason': 'Miscellaneous category — no seasonal pattern.',
        'advice': '',
    },
}


def _season_status(profile, month):
    if month in profile['peak_months']:
        return 'peak_season'
    if month in profile['ramp_up_months']:
        return 'pre_season'
    # Post-peak: 1 month after last peak month
    if profile['peak_months']:
        last_peak = max(profile['peak_months'])
        next_after = last_peak % 12 + 1
        if month == next_after:
            return 'post_season'
    return 'normal'


def generate_seasonal_advisories(anomaly_results, ward_name, current_month=None):
    """
    Generate proactive seasonal advisories for a ward.

    Args:
        anomaly_results: list from detect_ward_category_anomalies()
        ward_name: str
        current_month: int 1-12 (default: current month)

    Returns:
        list of advisory dicts sorted by urgency:
          { category, display_name, season_status, surge_factor,
            current_count, baseline_count, is_elevated,
            advisory_text }
    """
    if current_month is None:
        current_month = datetime.now().month

    # Build lookup from anomaly results
    cat_lookup = {}
    for r in anomaly_results:
        cat_lookup[r['category']] = r

    # Check next 2 months for upcoming peaks
    check_months = [
        (current_month, 'current'),
        (current_month % 12 + 1, 'next'),
        ((current_month + 1) % 12 + 1, 'next+1'),
    ]

    advisories = []
    for cat, profile in SEASONAL_PROFILES.items():
        if cat not in cat_lookup and cat not in ('pest control',):
            continue

        info = cat_lookup.get(cat, {})
        display_name = info.get('display_name', cat.replace('_', ' ').title())
        baseline = info.get('weekly_mean', 0)
        latest = info.get('latest_week', 0)
        growth = info.get('growth_pct', 0)
        severity = info.get('severity', 'normal')

        status = _season_status(profile, current_month)
        next_status = _season_status(profile, check_months[1][1])
        upcoming_peak = any(
            _season_status(profile, m) == 'peak_season'
            for m, _ in check_months
        )

        if status == 'normal' and not upcoming_peak:
            continue

        is_elevated = latest > baseline * 1.2

        lines = []
        if status == 'pre_season':
            lines.append(
                f"{display_name} complaints typically surge "
                f"{profile['surge_factor']}x during {_month_range(profile['peak_months'])} "
                f"({profile['reason'].split('.')[0].lower()})."
            )
            lines.append(f"Current weekly count: {latest:.0f} (baseline: {baseline:.1f}).")
            if is_elevated:
                lines.append(
                    f"⚠ Already {growth:.0f}% above baseline — pre-season levels are elevated. "
                    f"Act now: {profile['advice']}"
                )
            else:
                lines.append(f"Preparedness recommended: {profile['advice']}")
        elif status == 'peak_season':
            lines.append(
                f"{display_name} is at seasonal peak. "
                f"Current weekly count: {latest:.0f} vs baseline {baseline:.1f}."
            )
            if is_elevated and severity != 'normal':
                lines.append(
                    f"⚠ Volume is significantly above normal even for peak season. "
                    f"{profile['advice']}"
                )
            else:
                lines.append(
                    f"Volume is within expected range for this season."
                )
        elif status == 'post_season':
            lines.append(
                f"{display_name} peak season is ending. "
                f"Current weekly count: {latest:.0f} vs baseline {baseline:.1f}. "
                f"Continue monitoring — residual issues may persist."
            )
        elif upcoming_peak and status == 'normal':
            for check_month, label in check_months:
                if _season_status(profile, check_month) == 'peak_season':
                    lines.append(
                        f"{display_name} complaints will enter peak season "
                        f"in {MONTH_NAMES[check_month]} (typically {profile['surge_factor']}x surge). "
                        f"Current weekly count: {latest:.0f}."
                    )
                    if is_elevated:
                        lines.append(f"⚠ Already elevated — start preparations now.")
                    lines.append(f"Recommended: {profile['advice']}")
                    break

        advisory_text = ' '.join(lines)
        if not advisory_text.strip():
            continue

        urgency = 0
        if status == 'pre_season' and is_elevated:
            urgency = 3
        elif status == 'peak_season' and severity in ('critical', 'major'):
            urgency = 3
        elif status == 'pre_season':
            urgency = 2
        elif status == 'peak_season':
            urgency = 2
        elif upcoming_peak:
            urgency = 1
        else:
            urgency = 0

        advisories.append({
            'category': cat,
            'display_name': display_name,
            'season_status': status,
            'surge_factor': profile['surge_factor'],
            'peak_months': profile['peak_months'],
            'reason': profile['reason'],
            'current_weekly_count': int(latest),
            'baseline_weekly_count': round(baseline, 1),
            'is_elevated': is_elevated,
            'advisory_text': advisory_text,
            'urgency': urgency,
        })

    advisories.sort(key=lambda a: a['urgency'], reverse=True)
    return advisories


def _month_range(months):
    if not months:
        return ''
    if len(months) == 1:
        return MONTH_NAMES[months[0]]
    start = MONTH_NAMES[months[0]]
    end = MONTH_NAMES[months[-1]]
    return f"{start}–{end}"
