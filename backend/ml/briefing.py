"""
Ward briefing generator.

Produces structured, plain-English ward summaries from:
  - Dashboard data (stats, health score)
  - Predictions (risk, forecast, recommendation)
  - Insights (major categories, failing categories)
  - Anomaly detection results

Template-based generation — no external LLM API required.
Swappable for LLM-powered generation later (just replace _generate_text).
"""

from datetime import date
from .anomaly import get_ward_anomaly_report


# ── Helpers ──────────────────────────────────────────────────────────────


def _health_label(score):
    if score is None:
        return 'unavailable'
    if score >= 70:
        return 'good'
    if score >= 45:
        return 'moderate'
    return 'poor'


def _health_emoji(score):
    if score is None:
        return '-'
    if score >= 70:
        return 'healthy'
    if score >= 45:
        return 'needs attention'
    return 'critical'


def _trend_phrase(growth):
    if growth is None:
        return 'stable'
    if growth > 10:
        return 'sharply rising'
    if growth > 5:
        return 'rising'
    if growth < -10:
        return 'sharply falling'
    if growth < -5:
        return 'falling'
    return 'stable'


def _ordinal(n):
    if n is None:
        return ''
    return f"{n}{'th' if 11 <= n <= 13 else {1:'st',2:'nd',3:'rd'}.get(n%10, 'th')}"


# ── Section builders ────────────────────────────────────────────────────


def _build_header(dashboard):
    """Ward identification + health summary."""
    if not dashboard:
        return "No dashboard data available."

    ward = dashboard.get('ward', {})
    ward_name = ward.get('ward_name', 'Unknown')
    health = dashboard.get('health_score')
    label = _health_label(health)
    emoji = _health_emoji(health)

    parts = [
        f"Ward {ward_name} — {date.today().strftime('%B %d, %Y')}",
        f"Health score: {round(health) if health else 'N/A'}/100 ({label}).",
    ]

    total = dashboard.get('total_complaints', 0)
    resolved = dashboard.get('resolved_complaints', 0)
    resolution_rate = round(resolved / total * 100, 1) if total > 0 else 0

    parts.append(
        f"{total} total complaints, {resolved} resolved "
        f"({resolution_rate}% resolution rate)."
    )

    return '\n'.join(parts)


def _build_whats_happening(dashboard, insights, anomaly_report):
    """
    Key issues: top complaint categories, anomalies, trend breaks.
    """
    parts = []

    # Top DB categories
    major = (insights or {}).get('major_categories', [])
    if major:
        top = major[0]
        parts.append(
            f"Top issue: {top['category_display']} — {top['count']} cases "
            f"({top['percentage']}% of all complaints), trend is {top.get('trend', 'stable')}."
        )
        if len(major) > 1:
            others = ', '.join(f"{c['category_display']} ({c['count']})" for c in major[1:4])
            parts.append(f"Other major categories: {others}.")

    # City-wide category anomalies from CSV
    if anomaly_report:
        cat_anomalies = anomaly_report.get('category_anomalies', [])
        for a in cat_anomalies[:3]:
            if a['direction'] == 'high':
                parts.append(
                    f"{a['issue']} is running {a['pct_above_mean']:+.1f}% above its "
                    f"historical average ({a['latest']:,} vs {a['mean']:.0f} avg) — "
                    f"{a['severity'].upper()} anomaly."
                )
            else:
                parts.append(
                    f"{a['issue']} is running {a['pct_above_mean']:+.1f}% below its "
                    f"historical average."
                )

        # Trend breaks
        trend_breaks = anomaly_report.get('trend_breaks', [])
        for t in trend_breaks[:2]:
            parts.append(
                f"{t['issue']} has seen a {t['direction']} in the last 3 years "
                f"({t['recent_mean']:.0f}/yr vs {t['early_mean']:.0f}/yr historically) — "
                f"{t['severity']} shift."
            )

        # Ward-level anomaly
        ward_anom = anomaly_report.get('ward_anomaly')
        if ward_anom and ward_anom.get('is_anomaly'):
            parts.append(
                f"Ward complaint volume ({ward_anom['latest_total']:,}) is "
                f"{'above' if ward_anom['direction'] == 'high' else 'below'} "
                f"normal range ({ward_anom['pct_above_mean']:+.1f}% vs "
                f"{ward_anom['mean']:.0f} historical mean)."
            )

    # Failing categories
    failing = (insights or {}).get('failing_categories', [])
    if failing:
        worst = failing[0]
        parts.append(
            f"Most at-risk category: {worst['issue']} — growing at "
            f"{worst.get('recent_3yr_growth_pct', 0):+.1f}%/yr, "
            f"projected {worst.get('projected_next', 0):,} complaints next year."
        )

    return '\n'.join(parts) if parts else "No significant activity to report."


def _build_forecast(dashboard, prediction):
    """Prediction summary + recommendation."""
    if not prediction:
        return "No forecast data available."

    risk = prediction.get('predicted_risk', 'unknown')
    forecast = prediction.get('predicted_complaints')
    health = prediction.get('predicted_health_score')
    current_health = dashboard.get('health_score')
    rec = prediction.get('recommendation')

    parts = [
        f"Risk classification: {risk.upper()}."
    ]

    if forecast is not None:
        parts.append(f"Forecast: {forecast:,} complaints expected next period.")

    if health is not None:
        direction = ''
        if current_health:
            diff = round(health - current_health)
            if diff > 0:
                direction = f" ({diff:+.0f} vs current)"
            elif diff < 0:
                direction = f" ({diff:+.0f} vs current)"
        parts.append(f"Predicted health score: {round(health)}/100{direction}.")

    if rec:
        parts.append(f"Recommendation: {rec}")

    return '\n'.join(parts)


def _build_action_items(dashboard, prediction, anomaly_report):
    """Concrete action items extracted from all data sources."""
    items = []
    dashboard = dashboard or {}

    # Health-based action
    health = dashboard.get('health_score')
    if health is not None and health < 45:
        items.append(f"Health score is critical ({round(health)}). Investigate root causes and allocate resources.")
    elif health is not None and health < 70:
        items.append(f"Health score is moderate ({round(health)}). Focus on improving resolution rates.")

    # Failing categories
    failing = (dashboard or {}).get('failing_categories', [])
    if failing:
        items.append(f"Address rising complaints in {failing[0].get('issue', 'top category')} — projected growth is significant.")

    # Anomaly-driven actions
    if anomaly_report:
        for a in anomaly_report.get('category_anomalies', [])[:2]:
            if a['severity'] in ('critical', 'major') and a['direction'] == 'high':
                items.append(f"Investigate spike in {a['issue']}: {a['latest']:,} complaints vs {a['mean']:.0f} average.")

        for t in anomaly_report.get('trend_breaks', [])[:1]:
            if t['severity'] in ('critical', 'major'):
                items.append(f"Sudden {t['direction']} in {t['issue']} over last 3 years — review operational changes.")

    # Prediction-driven action
    if prediction:
        risk = prediction.get('predicted_risk')
        if risk in ('high', 'medium'):
            items.append(f"{'High' if risk == 'high' else 'Medium'} risk forecast — consider preemptive measures.")

    if not items:
        items.append("No urgent actions identified. Continue monitoring.")

    return items


# ── Main briefing ───────────────────────────────────────────────────────


def generate_ward_briefing(dashboard=None, prediction=None, insights=None, ward_name=None):
    """
    Generate a complete ward briefing from all available data sources.

    Accepts the same data structures returned by the API views:
      - dashboard: dict from /api/councillor/dashboard/
      - prediction: dict from /api/predictions/?ward=XX (first item)
      - insights: dict from /api/insights/?ward=XX
      - ward_name: optional override

    Returns dict with:
      - ward: ward name
      - generated_at: ISO date
      - sections: { header, whats_happening, forecast, action_items }
      - summary: one-line summary
      - raw: { health_score, total_complaints, risk, forecast_count }
    """
    w = ward_name or (dashboard or {}).get('ward', {}).get('ward_name', 'Unknown')

    # Fetch anomaly report
    anomaly_report = get_ward_anomaly_report(w)

    # Build sections
    header = _build_header(dashboard)
    whats_happening = _build_whats_happening(dashboard, insights, anomaly_report)
    forecast = _build_forecast(dashboard, prediction)
    action_items = _build_action_items(dashboard, prediction, anomaly_report)

    # One-line summary
    health = (dashboard or {}).get('health_score')
    total = (dashboard or {}).get('total_complaints', 0)
    risk = (prediction or {}).get('predicted_risk', 'unknown')
    anomaly_count = len(anomaly_report.get('category_anomalies', [])) if anomaly_report else 0

    summary_parts = [
        f"Ward {w}: {_health_emoji(health)} health ({_health_label(health)})",
        f"{total} complaints",
        f"{risk.upper()} risk"
    ]
    if anomaly_count:
        summary_parts.append(f"{anomaly_count} anomaly/ies detected")
    summary = ' · '.join(summary_parts)

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
