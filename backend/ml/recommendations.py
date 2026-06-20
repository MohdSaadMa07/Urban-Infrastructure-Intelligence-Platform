"""
Rule-based recommendation engine for UrbanIQ.

Generates actionable recommendations based on prediction outputs and
ward-specific patterns from Table_3 (top-3 ward rankings).
"""

import csv
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TOP3_CSV = DATA_DIR / "Table_3_Top_3_Wards.csv"


def _load_top3_wards():
    """Load Table_3 and build a set of persistently flagged wards."""
    if not TOP3_CSV.exists():
        return {}
    flagged = {}
    with open(str(TOP3_CSV), newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for rank in ["Rank1", "Rank2", "Rank3"]:
                ward = row.get(f"{rank}_Ward", "").strip()
                issue = row.get("MainIssue", "").strip()
                sub = row.get("SubIssue", "").strip()
                if ward:
                    flagged.setdefault(ward, set()).add(f"{issue}: {sub}")
    return flagged


# Load once at import time
_FLAGGED_WARDS = _load_top3_wards()


def generate_recommendation(predicted_risk, predicted_complaints, health_score, ward_name):
    """
    Generate a recommendation string for a ward based on its predictions.

    Args:
        predicted_risk: str, one of 'Low', 'Medium', 'High'
        predicted_complaints: int
        health_score: float or None
        ward_name: str (e.g. 'A', 'B', 'F/N')

    Returns:
        str recommendation
    """
    parts = []

    # --- Risk-based ---
    risk_map = {
        "High": "Immediate intervention required. Prioritize resource allocation for this ward.",
        "Medium": "Monitor closely. Deploy preventive maintenance to avoid escalation.",
        "Low": "Maintain current service levels. Routine monitoring sufficient.",
    }
    parts.append(risk_map.get(predicted_risk, "Continue standard monitoring."))

    # --- Volume-based ---
    if predicted_complaints > 50000:
        parts.append("High complaint volume expected. Consider temporary resource augmentation.")
    elif predicted_complaints > 35000:
        parts.append("Moderate complaint volume. Ensure adequate staffing.")

    # --- Health-based ---
    if health_score is not None:
        if health_score < 45:
            parts.append("Schedule comprehensive infrastructure audit for this ward.")
        elif health_score < 70:
            parts.append("Targeted improvements recommended to raise health score above 70.")

    # --- Persistent issue flags from Table_3 ---
    ward_issues = _FLAGGED_WARDS.get(ward_name, set())
    if ward_issues:
        top_issues = sorted(ward_issues)[:3]
        parts.append(f"Persistent issues: {'; '.join(top_issues)}.")

    return " ".join(parts)
