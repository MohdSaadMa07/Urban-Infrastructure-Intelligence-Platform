import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
import django
django.setup()

from api.models import WardPrediction, CivicMetrics

pothole = {
    'A': 64, 'B': None, 'C': None, 'D': 116, 'E': None,
    'F/N': None, 'F/S': 557, 'G/N': 1748, 'G/S': 116, 'H/E': 312,
    'H/W': 214, 'K/E': 393, 'K/W': 712, 'L': None, 'M/E': None,
    'M/W': None, 'N': None, 'P/N': None, 'P/S': 2373, 'R/C': None,
    'R/N': None, 'R/S': None, 'S': 1499, 'T': 219,
}
garbage = {
    'A': 292, 'B': 406, 'C': None, 'D': None, 'E': None,
    'F/N': None, 'F/S': 557, 'G/N': 1748, 'G/S': 541, 'H/E': None,
    'H/W': None, 'K/E': None, 'K/W': 2717, 'L': None, 'M/E': None,
    'M/W': None, 'N': None, 'P/N': None, 'P/S': 2373, 'R/C': None,
    'R/N': None, 'R/S': None, 'S': 2057, 'T': 219,
}

pred = {p.ward.ward_name: p.predicted_complaints
        for p in WardPrediction.objects.filter(prediction_date__year=2025).select_related('ward')}
act24 = {m.ward.ward_name: m.total_complaints
         for m in CivicMetrics.objects.filter(year=2024).select_related('ward')}

rank_pred = sorted(pred, key=lambda w: pred[w], reverse=True)
rank_ph = sorted([w for w in pothole if pothole[w] and pothole[w] > 0], key=lambda w: pothole[w], reverse=True)
rank_gh = sorted([w for w in garbage if garbage[w] and garbage[w] > 0], key=lambda w: garbage[w], reverse=True)

print("Ward  2024Act  2025Pred  Chg%   Pothole Garbage  PotholeR GarbageR PredR")
print("-" * 72)
for ward in sorted(pred.keys()):
    rp = rank_pred.index(ward) + 1
    r_ph = rank_ph.index(ward) + 1 if pothole.get(ward) else 99
    r_gh = rank_gh.index(ward) + 1 if garbage.get(ward) else 99
    ph = pothole.get(ward)
    gh = garbage.get(ward)
    p = pred[ward]
    a = act24.get(ward, 0)
    pct = (p - a) / a if a > 0 else 0
    ph_s = f'{ph:>6,}' if ph else '   N/A'
    gh_s = f'{gh:>6,}' if gh else '   N/A'
    r_ph_s = f'#{r_ph:>2}' if r_ph < 99 else '  -'
    r_gh_s = f'#{r_gh:>2}' if r_gh < 99 else '  -'
    print(f'{ward:>5} {a:>8,} {p:>8,} {pct:>+5.1%}  {ph_s} {gh_s}  {r_ph_s:>5}   {r_gh_s:>5}   #{rp:>2}')

print()
print("Top 6 by pothole  |  Top 6 by garbage  |  Top 6 predicted 2025")
print("Ward  Count   PredR | Ward  Count   PredR | Ward  Predicted")
for i in range(6):
    w_ph = rank_ph[i] if i < len(rank_ph) else ''
    w_gh = rank_gh[i] if i < len(rank_gh) else ''
    w_pr = rank_pred[i] if i < len(rank_pred) else ''
    ph_c = f'{pothole[w_ph]:>5,}' if w_ph else ''
    gh_c = f'{garbage[w_gh]:>5,}' if w_gh else ''
    pr_c = f'{pred[w_pr]:>8,}' if w_pr else ''
    r_ph = f'#{rank_pred.index(w_ph)+1}' if w_ph else ''
    r_gh = f'#{rank_pred.index(w_gh)+1}' if w_gh else ''
    print(f'{w_ph:>5} {ph_c:>6} {r_ph:>5}  | {w_gh:>5} {gh_c:>6} {r_gh:>5}  | {w_pr:>5} {pr_c:>8}')
