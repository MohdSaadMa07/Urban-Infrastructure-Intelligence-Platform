"""
Generate synthetic 2025 ward metrics informed by real 2025 data signals.

Real data sources incorporated:
  - Pothole complaints (Jun-Aug 2025): 7,621 total, ward-wise (Indian Express)
  - BMC WhatsApp garbage helpline (Jun 2023-Oct 2025): 27,634, ward-wise (TOI)
  - Road concretisation progress: 63% Phase I by May 2025 vs 26% in May 2024
  - Praja May 2025 report: resolution time 32->41 days trend, SWM +380% decade
  - BMC budget 2025-26: Rs 74,367 cr (+24% YoY)
  - No elected councillors since March 2022 (deliberations frozen)

Output: ward_metrics_multiyear_2025.csv
"""

import csv
import os
import math
import random

random.seed(42)

CSV_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(CSV_DIR, 'ward_metrics_multiyear_extended.csv')
OUTPUT_CSV = os.path.join(CSV_DIR, 'ward_metrics_multiyear_2025.csv')

FIELD_NAMES = [
    'Ward', 'Year', 'Avg_No_of_Councillors',
    'Total_Complaints', 'Per_Capita_Complaints',
    'Avg_No_of_Days', 'Total_Deliberation', 'Per_Capita_Deliberation'
]

# Real 2025 partial data
POTHOLE_2025 = {
    'A': 64, 'B': None, 'C': None, 'D': 116, 'E': None,
    'F/N': None, 'F/S': 557, 'G/N': 1748, 'G/S': 116, 'H/E': 312,
    'H/W': 214, 'K/E': 393, 'K/W': 712, 'L': None, 'M/E': None,
    'M/W': None, 'N': None, 'P/N': None, 'P/S': 2373, 'R/C': None,
    'R/N': None, 'R/S': None, 'S': 1499, 'T': 219,
}

GARBAGE_HELPLINE_CUMULATIVE = {
    'A': 292, 'B': 406, 'C': None, 'D': None, 'E': None,
    'F/N': None, 'F/S': 557, 'G/N': 1748, 'G/S': 541, 'H/E': None,
    'H/W': None, 'K/E': None, 'K/W': 2717, 'L': None, 'M/E': None,
    'M/W': None, 'N': None, 'P/N': None, 'P/S': 2373, 'R/C': None,
    'R/N': None, 'R/S': None, 'S': 2057, 'T': 219,
}

VIP_WARDS = {'A', 'D', 'G/S', 'H/W'}


def read_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'Ward': row['Ward'].strip(),
                'Year': int(row['Year']),
                'Avg_No_of_Councillors': int(row['Avg_No_of_Councillors']),
                'Total_Complaints': int(row['Total_Complaints']),
                'Per_Capita_Complaints': int(row['Per_Capita_Complaints']),
                'Avg_No_of_Days': float(row['Avg_No_of_Days']),
                'Total_Deliberation': int(row['Total_Deliberation']),
                'Per_Capita_Deliberation': int(row['Per_Capita_Deliberation']),
            })
    return rows


def compute_cagr(start_val, end_val, num_years):
    if start_val <= 0 or end_val <= 0:
        return 0.0
    return (end_val / start_val) ** (1 / num_years) - 1.0


def estimate_ward_growth_factor(ward, ward_rows_2019_2024):
    """
    Estimate 2024->2025 complaint growth factor using real 2025 signals.
    Returns a multiplier (1.0 = flat, 1.05 = +5%, etc.)
    """
    sorted_rows = sorted(ward_rows_2019_2024, key=lambda r: r['Year'])
    latest = sorted_rows[-1]

    cagr = compute_cagr(sorted_rows[0]['Total_Complaints'],
                         latest['Total_Complaints'],
                         latest['Year'] - sorted_rows[0]['Year'])
    base_growth = 1.0 + cagr

    pothole = POTHOLE_2025.get(ward, None)
    garbage = GARBAGE_HELPLINE_CUMULATIVE.get(ward, None)

    pothole_bonus = 0.0
    if pothole is not None and latest['Total_Complaints'] > 0:
        pothole_ratio = pothole / (latest['Total_Complaints'] * 2 / 12)
        if pothole_ratio > 0.03:
            pothole_bonus = min(pothole_ratio * 0.5, 0.06)

    garbage_bonus = 0.0
    if garbage is not None and latest['Total_Complaints'] > 0:
        garbage_monthly = garbage / 29
        garbage_ratio = garbage_monthly / (latest['Total_Complaints'] / 12)
        if garbage_ratio > 0.03:
            garbage_bonus = min(garbage_ratio * 0.4, 0.05)

    vip_penalty = -0.02 if ward in VIP_WARDS else 0.0

    noise = random.gauss(0, 0.015)

    growth_factor = 1.0 + (base_growth - 1.0) * 0.6 + pothole_bonus + garbage_bonus + vip_penalty + noise
    growth_factor = max(0.85, min(1.15, growth_factor))

    return growth_factor


def generate_2025_row(ward, ward_rows_2019_2024):
    sorted_rows = sorted(ward_rows_2019_2024, key=lambda r: r['Year'])
    latest = sorted_rows[-1]

    growth_factor = estimate_ward_growth_factor(ward, ward_rows_2019_2024)
    projected_total = round(latest['Total_Complaints'] * growth_factor)
    projected_total = max(projected_total, 500)

    ratio = latest['Total_Complaints'] / max(latest['Per_Capita_Complaints'], 1)
    per_capita = round(projected_total / ratio) if ratio > 0 else 0

    latest_days = latest['Avg_No_of_Days']
    prev_days = sorted_rows[-2]['Avg_No_of_Days'] if len(sorted_rows) >= 2 else latest_days
    days_delta = latest_days - prev_days

    avg_days = max(1, round(latest_days + days_delta * random.uniform(0.6, 1.4), 1))

    total_delib = latest['Total_Deliberation']
    delib_ratio = latest['Total_Deliberation'] / max(latest['Per_Capita_Deliberation'], 1)
    per_capita_delib = round(total_delib / delib_ratio) if delib_ratio > 0 else 0

    return {
        'Ward': ward,
        'Year': 2025,
        'Avg_No_of_Councillors': latest['Avg_No_of_Councillors'],
        'Total_Complaints': projected_total,
        'Per_Capita_Complaints': per_capita,
        'Avg_No_of_Days': avg_days,
        'Total_Deliberation': total_delib,
        'Per_Capita_Deliberation': per_capita_delib,
    }


def main():
    rows = read_csv(INPUT_CSV)
    print(f"Read {len(rows)} rows (2019-2024)")

    wards_data = {}
    for r in rows:
        wards_data.setdefault(r['Ward'], []).append(r)

    new_rows = []
    total_2024 = sum(r['Total_Complaints'] for r in rows if r['Year'] == 2024)
    total_2025 = 0

    print(f"\n{'Ward':>5} {'2024':>8} {'2025':>8} {'Δ%':>7}  {'Days 24':>7} {'Days 25':>7}  Signals")
    print("-" * 70)

    for ward in sorted(wards_data.keys()):
        r25 = generate_2025_row(ward, wards_data[ward])
        new_rows.append(r25)
        r24 = next(r for r in wards_data[ward] if r['Year'] == 2024)
        pct = (r25['Total_Complaints'] - r24['Total_Complaints']) / r24['Total_Complaints']

        total_2025 += r25['Total_Complaints']

        signals = []
        p = POTHOLE_2025.get(ward)
        g = GARBAGE_HELPLINE_CUMULATIVE.get(ward)
        if p and p > 200:
            signals.append(f"pothole={p}")
        if g and g > 500:
            signals.append(f"garbage={g}")
        if ward in VIP_WARDS:
            signals.append("VIP")
        if not signals:
            signals.append("trend")

        print(f"  {ward:>4} {r24['Total_Complaints']:>8,} {r25['Total_Complaints']:>8,} {pct:>+6.1%}  "
              f"{r24['Avg_No_of_Days']:>7.0f} {r25['Avg_No_of_Days']:>7.0f}  {', '.join(signals)}")

    all_rows = rows + new_rows
    all_rows.sort(key=lambda r: (r['Ward'], r['Year']))

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELD_NAMES)
        w.writeheader()
        w.writerows(all_rows)

    print(f"\nWritten {len(all_rows)} rows to: {OUTPUT_CSV}")
    print(f"\nGrand Total_Complaints:")
    print(f"  2024: {total_2024:>10,}")
    print(f"  2025: {total_2025:>10,}")
    print(f"  Growth: {total_2025/total_2024 - 1:+.1%}")


if __name__ == '__main__':
    main()
