"""
Ward briefing generator — plain, simple English for non-technical users.
Template-based, no external LLM API required.
"""

from datetime import date
from .anomaly import get_ward_anomaly_report


def _health_label(score):
    if score is None: return 'unavailable'
    if score >= 70: return 'good'
    if score >= 45: return 'moderate'
    return 'poor'


def _health_emoji(score):
    if score is None: return '-'
    if score >= 70: return 'healthy'
    if score >= 45: return 'needs attention'
    return 'critical'


def _trend_phrase(growth):
    if growth is None: return 'stable'
    if growth > 10: return 'rapidly rising'
    if growth > 5: return 'rising'
    if growth < -10: return 'rapidly falling'
    if growth < -5: return 'falling'
    return 'stable'


def _build_header(dashboard):
    """Simple ward identification + health summary."""
    if not dashboard:
        return "No data available for this ward."

    ward = dashboard.get('ward', {})
    ward_name = ward.get('ward_name', 'Unknown')
    health = dashboard.get('health_score')
    label = _health_label(health)
    emoji = _health_emoji(health)

    total = dashboard.get('total_complaints', 0)
    resolved = dashboard.get('resolved_complaints', 0)
    resolution_rate = round(resolved / total * 100, 1) if total > 0 else 0

    lines = [
        f"Ward {ward_name} has a health score of {round(health) if health else 'N/A'} out of 100 — this means it is {emoji}.",
        f"There are {total} complaints in total. Of these, {resolved} complaints have been resolved ({resolution_rate}% resolution rate).",
    ]
    return '\n'.join(lines)


def _build_whats_happening(dashboard, insights, anomaly_report):
    """Key issues in simple language."""
    parts = []

    major = (insights or {}).get('major_categories', [])
    if major:
        top = major[0]
        trend = top.get('trend', 'stable')
        parts.append(
            f"Most complaints are about '{top['category_display']}' — {top['count']} cases "
            f"({top['percentage']}% of all complaints). This is {trend}."
        )
        if len(major) > 1:
            others = ', '.join(f"{c['category_display']} ({c['count']})" for c in major[1:4])
            parts.append(f"Other major categories: {others}.")

    if anomaly_report:
        cat_anomalies = anomaly_report.get('category_anomalies', [])
        for a in cat_anomalies[:3]:
            direction = 'increased' if a['direction'] == 'high' else 'decreased'
            severity = 'very high' if a['severity'] == 'critical' else 'moderately high' if a['severity'] == 'major' else 'slight'
            parts.append(
                f"'{a['issue']}' complaints have {direction} by {a['pct_above_mean']:+.1f}% compared to last year "
                f"({a['latest']:,} now vs {a['mean']:.0f} average). This is a {severity} change."
            )

        trend_breaks = anomaly_report.get('trend_breaks', [])
        for t in trend_breaks[:2]:
            direction = 'upsurge' if 'upsurge' in t.get('direction', '') else 'downfall'
            severity = 'major' if t.get('severity') == 'critical' else 'minor'
            parts.append(
                f"Over the last 3 years, '{t['issue']}' has seen a {severity} {direction} "
                f"({t['recent_mean']:.0f}/year now vs {t['early_mean']:.0f}/year before)."
            )

        ward_anom = anomaly_report.get('ward_anomaly')
        if ward_anom and ward_anom.get('is_anomaly'):
            parts.append(
                f"Complaint volume in your ward ({ward_anom['latest_total']:,}) is "
                f"{'above normal' if ward_anom['direction'] == 'high' else 'below normal'} "
                f"({ward_anom['pct_above_mean']:+.1f}% vs the historical average)."
            )

    failing = (insights or {}).get('failing_categories', [])
    if failing:
        worst = failing[0]
        trend = _trend_phrase(worst.get('recent_3yr_growth_pct'))
        parts.append(
            f"Most at-risk category: '{worst['issue']}' — this is {trend} "
            f"({worst.get('recent_3yr_growth_pct', 0):+.1f}% each year). "
            f"Next year it may reach {worst.get('projected_next', 0):,} complaints."
        )

    if not parts:
        parts.append("No significant activity to report. Everything is normal.")

    return '\n'.join(parts)


def _build_forecast(dashboard, prediction):
    """Prediction summary in simple language."""
    if not prediction:
        return "Next year's forecast is not available yet."

    risk = prediction.get('predicted_risk', 'unknown')
    forecast_count = prediction.get('predicted_complaints')
    health = prediction.get('predicted_health_score')
    current_health = dashboard.get('health_score')
    rec = prediction.get('recommendation')

    risk_labels = {'high': 'High Risk — needs attention', 'medium': 'Medium Risk — keep watch', 'low': 'Low Risk — good shape'}
    parts = [f"Next year's risk level: {risk_labels.get(risk, 'Unknown')}."]

    if forecast_count is not None:
        parts.append(f"We expect about {forecast_count:,} complaints next year.")

    if health is not None:
        diff_text = ''
        if current_health:
            diff = round(health - current_health)
            if diff > 0:
                diff_text = f" ({diff} points better than today)"
            elif diff < 0:
                diff_text = f" ({abs(diff)} points worse than today)"
        parts.append(f"Predicted health score: {round(health)}/100{diff_text}.")

    if rec:
        parts.append(f"Suggestion: {rec}")

    return '\n'.join(parts)


def _build_action_items(dashboard, prediction, anomaly_report):
    """Concrete action items in simple English."""
    items = []
    dashboard = dashboard or {}

    health = dashboard.get('health_score')
    if health is not None and health < 45:
        items.append(f"Health score is very low ({round(health)}). Investigate causes and arrange resources immediately.")
    elif health is not None and health < 70:
        items.append(f"Health score needs improvement ({round(health)}). Focus on resolving complaints faster.")

    failing = (dashboard or {}).get('failing_categories', [])
    if failing:
        items.append(f"Complaints are rising fast in '{failing[0].get('issue', 'top category')}'. Pay attention to this area.")

    if anomaly_report:
        for a in anomaly_report.get('category_anomalies', [])[:2]:
            if a['severity'] in ('critical', 'major') and a['direction'] == 'high':
                items.append(f"Spike in '{a['issue']}' complaints — {a['latest']:,} complaints vs {a['mean']:.0f} average. Take immediate action.")

        for t in anomaly_report.get('trend_breaks', [])[:1]:
            if t['severity'] in ('critical', 'major'):
                direction = 'upsurge' if 'upsurge' in t.get('direction', '') else 'downfall'
                items.append(f"Major shift in '{t['issue']}' over the last 3 years ({direction}). Review what has changed.")

    if prediction:
        risk = prediction.get('predicted_risk')
        if risk == 'high':
            items.append("High risk forecast for next year. Start preparing now.")
        elif risk == 'medium':
            items.append("Medium risk forecast for next year. Keep monitoring closely.")

    if not items:
        items.append("Everything looks normal. No urgent action needed.")

    return items


def generate_ward_briefing(dashboard=None, prediction=None, insights=None, ward_name=None):
    """Generate a complete ward briefing in simple English."""
    w = ward_name or (dashboard or {}).get('ward', {}).get('ward_name', 'Unknown')

    anomaly_report = get_ward_anomaly_report(w)

    header = _build_header(dashboard)
    whats_happening = _build_whats_happening(dashboard, insights, anomaly_report)
    forecast = _build_forecast(dashboard, prediction)
    action_items = _build_action_items(dashboard, prediction, anomaly_report)

    health = (dashboard or {}).get('health_score')
    total = (dashboard or {}).get('total_complaints', 0)
    risk = (prediction or {}).get('predicted_risk', 'unknown')
    anomaly_count = len(anomaly_report.get('category_anomalies', [])) if anomaly_report else 0

    health_text = _health_emoji(health)
    risk_labels = {'high': 'High Risk', 'medium': 'Medium Risk', 'low': 'Low Risk'}
    summary = f"Ward {w}: Health is {health_text} · {total} complaints · {risk_labels.get(risk, 'Unknown Risk')}"
    if anomaly_count:
        summary += f" · {anomaly_count} unusual pattern(s) detected"

    return {
        'ward': w,
        'generated_at': date.today().isoformat(),
        'sections': {
            'header': header,
            'whats_happening': whats_happening,
            'forecast': forecast,
            'action_items': action_items,
        },
        'summary': summary,
        'raw': {
            'health_score': round(health) if health else None,
            'health_label': _health_label(health),
            'total_complaints': total,
            'resolution_rate': round(
                (dashboard or {}).get('resolved_complaints', 0) / total * 100, 1
            ) if total > 0 else 0,
            'predicted_risk': risk,
            'predicted_complaints': (prediction or {}).get('predicted_complaints'),
            'anomaly_count': anomaly_count,
        },
    }
