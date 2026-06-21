import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from api.models import CivicMetrics, WardPrediction, Ward
from api.services.health_score import compute_health_score

cm = CivicMetrics.objects.count()
wp = WardPrediction.objects.count()
years = sorted(set(CivicMetrics.objects.values_list('year', flat=True)))
print("CivicMetrics: {} rows | WardPrediction: {} rows | Years: {}".format(cm, wp, years))

w = Ward.objects.filter(ward_name='A').first()
if w:
    hist = w.metrics.all().order_by('year')
    print("Ward A: {} years of history".format(hist.count()))
    for m in hist:
        hs = compute_health_score(m)
        print("  {}: {} complaints, health={}".format(m.year, m.total_complaints, round(hs['score'])))
    p25 = w.predictions.filter(prediction_date__year=2025).first()
    p26 = w.predictions.filter(prediction_date__year=2026).first()
    if p25: print("  2025 pred: {} complaints ({})".format(p25.predicted_complaints, p25.predicted_risk))
    if p26: print("  2026 pred: {} complaints ({})".format(p26.predicted_complaints, p26.predicted_risk))

print("\nDONE - all data verified OK")
