"""
PDF report generator using fpdf2.
Produces a weekly ward report with health score, metrics,
trend summary, and recent complaints.
"""

import io
from datetime import date
from pathlib import Path

from django.conf import settings
from django.db.models import Count
from fpdf import FPDF

from api.models import Complaint, Ward
from api.services.health_score import compute_health_score

REPORT_DIR = settings.BASE_DIR / 'media' / 'reports'
REPORT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 210  # A4
MARGIN = 12
BODY_W = WIDTH - 2 * MARGIN

BLUE = (34, 68, 136)
DARK = (30, 30, 30)
GRAY = (100, 100, 100)
LIGHT = (230, 230, 230)
GREEN = (40, 160, 60)
RED = (200, 50, 50)


class WardReport(FPDF):
    """Minimal PDF report for a single ward."""

    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*BLUE)
        self.cell(0, 10, 'MumbaiUI - Ward Report', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*BLUE)
        self.line(MARGIN, self.get_y(), WIDTH - MARGIN, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}  |  Generated {date.today().isoformat()}', align='C')

    def section_title(self, title: str):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(*DARK)
        self.set_fill_color(*LIGHT)
        self.cell(0, 9, f'  {title}', new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def metric_row(self, label: str, value: str):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*DARK)
        col_w = BODY_W * 0.4
        self.cell(col_w, 7, label)
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

    def complaint_row(self, cid: int, cat: str, status: str, created: str):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*DARK)
        self.cell(18, 6, str(cid))
        self.cell(40, 6, cat)
        self.cell(22, 6, status.upper())
        self.cell(0, 6, created[:10], new_x="LMARGIN", new_y="NEXT")


def _health_label(score: float | None) -> str:
    if score is None:
        return 'No Data'
    if score >= 70:
        return 'Good'
    if score >= 40:
        return 'Moderate'
    return 'Poor'


def generate_ward_report(ward_name: str) -> Path | None:
    """Generate a PDF report for the given ward, return file path."""
    try:
        return _generate_ward_report(ward_name)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Report generation failed for %s: %s", ward_name, exc)
        return None

def _generate_ward_report(ward_name: str) -> Path | None:
    """Generate a PDF report for the given ward, return file path."""
    ward = Ward.objects.filter(ward_name__iexact=ward_name).first()
    if not ward:
        return None

    latest_metrics = ward.metrics.order_by('-year').first()
    health = compute_health_score(latest_metrics) if latest_metrics else None

    # Recent complaints (last 30 days)
    from django.utils import timezone
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent = ward.complaints.filter(created_at__gte=thirty_days_ago).order_by('-created_at')

    # Category breakdown
    cats = ward.complaints.values('category').annotate(cnt=Count('id')).order_by('-cnt')
    cat_choices = dict(Complaint.CATEGORY_CHOICES)
    cat_lines = []
    total_cats = sum(c['cnt'] for c in cats)
    for c in cats:
        pct = round(c['cnt'] / total_cats * 100, 1) if total_cats else 0
        cat_lines.append(f"{cat_choices.get(c['category'], c['category'])}: {c['cnt']} ({pct}%)")

    pdf = WardReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Ward header ──
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 12, f'Ward {ward.ward_name} ({ward.ward_no})', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ── Health Score ──
    pdf.section_title('Health Overview')
    if health:
        score = health['score']
        label = _health_label(score)
        color = GREEN if score >= 70 else (200, 160, 0) if score >= 40 else RED
        pdf.set_font('Helvetica', 'B', 28)
        pdf.set_text_color(*color)
        pdf.cell(0, 14, f'{score:.0f} / 100  ({label})', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # Metric breakdown
        pdf.metric_row('Total Complaints', str(latest_metrics.total_complaints))
        pdf.metric_row('Closed Complaints', str(latest_metrics.closed_complaints))
        pdf.metric_row('Avg Resolution Days', str(latest_metrics.avg_resolution_days))
        pdf.metric_row('Per-capita Complaints', str(latest_metrics.per_capita_complaints))
        if latest_metrics.total_deliberations:
            pdf.metric_row('Civic Deliberations', str(latest_metrics.total_deliberations))
    else:
        pdf.set_font('Helvetica', 'I', 12)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 10, 'No metrics data available.', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # ── Category Breakdown ──
    pdf.section_title('Complaint Categories')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(*DARK)
    for line in cat_lines:
        pdf.cell(0, 6, f'  \u2022 {line}', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # ── Recent Complaints ──
    pdf.section_title(f'Recent Complaints (Last 30 Days)')
    if not recent:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 7, 'No recent complaints.', new_x="LMARGIN", new_y="NEXT")
    else:
        # Header row
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(*LIGHT)
        pdf.cell(18, 7, 'ID', fill=True)
        pdf.cell(40, 7, 'Category', fill=True)
        pdf.cell(22, 7, 'Status', fill=True)
        pdf.cell(0, 7, 'Date', fill=True, new_x="LMARGIN", new_y="NEXT")
        # Data rows
        for c in recent[:25]:
            pdf.complaint_row(c.id, c.get_category_display(), c.status, c.created_at.isoformat())
        if len(recent) > 25:
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(*GRAY)
            pdf.cell(0, 6, f'... and {len(recent) - 25} more', new_x="LMARGIN", new_y="NEXT")

    # ── Save ──
    filename = f'ward_{ward.ward_name.lower().replace(" ", "_")}_{date.today().isoformat()}.pdf'
    filepath = REPORT_DIR / filename
    pdf.output(str(filepath))
    return filepath


def generate_all_wards_reports() -> list[Path]:
    """Generate PDF reports for all wards and return list of file paths."""
    paths = []
    for ward in Ward.objects.all():
        try:
            p = generate_ward_report(ward.ward_name)
            if p:
                paths.append(p)
        except Exception:
            pass
    return paths
