"""
Extend ward_metrics_multiyear.csv with 2024 data using Praja Foundation report estimates.

Methodology:
- 2024 Total_Complaints: Compute 2023→2024 growth rate from Praja report
  (Table 53: Ward-wise Total Complaints 2015-2024), apply to existing CSV 2023 values.
- 2024 Avg_No_of_Days: Apply absolute change (Praja 2024 days - Praja 2023 days)
  to existing CSV 2023 days.
- Per_Capita_Complaints: Compute using per-ward Total/PerCapita ratio from 2023.
- Deliberation 2024+: set to 0 (no elected councillors since March 2022).
- Avg_No_of_Councillors 2024+: same as 2023.
- 2025-2026: NOT generated here — use XGBoost ML predictions instead (see ml/predict.py)

Context: Existing CSV values differ from Praja report absolute figures (~7-10x larger).
This suggests a different data source/aggregation. Using Praja-derived growth rates 
preserves existing data scale while incorporating the latest ward-level trends.

Data sources:
- Praja 2025 Report (published May 2025, covers data through Dec 2024):
  https://data.opencity.in/dataset/report-on-the-status-of-civic-issues-in-mumbai-may-2025
  - Table 53: Ward-wise Total Complaints from 2015 to 2024
  - Table 45: Ward-wise Comparison of Total Complaints and Complaints Closed in 2023 and 2024
"""
import csv
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), 'ward_metrics_multiyear.csv')
OUT_PATH = os.path.join(os.path.dirname(__file__), 'ward_metrics_multiyear_extended.csv')

FIELD_NAMES = [
    'Ward', 'Year', 'Avg_No_of_Councillors',
    'Total_Complaints', 'Per_Capita_Complaints',
    'Avg_No_of_Days', 'Total_Deliberation', 'Per_Capita_Deliberation'
]

# ============================================================
# Praja 2025 Report: Table 53 (Ward-wise Total Complaints 2015-2024)
# ============================================================
PRAJA_TOTAL_COMPLAINTS = {
    'A':   {2015: 1418, 2016: 1972, 2017: 1840, 2018: 2474, 2019: 2896, 2020: 1763, 2021: 1764, 2022: 2061, 2023: 2468, 2024: 3207},
    'B':   {2015: 1326, 2016: 1916, 2017: 2341, 2018: 3972, 2019: 3959, 2020: 2461, 2021: 2901, 2022: 3047, 2023: 3324, 2024: 3019},
    'C':   {2015: 1525, 2016: 1899, 2017: 2895, 2018: 3696, 2019: 3596, 2020: 2888, 2021: 2632, 2022: 2826, 2023: 3306, 2024: 3864},
    'D':   {2015: 3282, 2016: 4081, 2017: 4053, 2018: 4815, 2019: 5159, 2020: 3730, 2021: 3191, 2022: 3566, 2023: 4022, 2024: 3748},
    'E':   {2015: 2414, 2016: 2992, 2017: 3183, 2018: 4337, 2019: 4642, 2020: 3660, 2021: 3438, 2022: 3792, 2023: 4178, 2024: 4939},
    'F/N': {2015: 2318, 2016: 2765, 2017: 2944, 2018: 4425, 2019: 5304, 2020: 3597, 2021: 3094, 2022: 3799, 2023: 4672, 2024: 4229},
    'F/S': {2015: 1305, 2016: 1628, 2017: 1624, 2018: 2369, 2019: 2857, 2020: 2444, 2021: 2270, 2022: 3102, 2023: 2742, 2024: 2781},
    'G/N': {2015: 3094, 2016: 4416, 2017: 4840, 2018: 6241, 2019: 5954, 2020: 4657, 2021: 4859, 2022: 5158, 2023: 5545, 2024: 5151},
    'G/S': {2015: 1495, 2016: 1983, 2017: 2471, 2018: 3160, 2019: 4192, 2020: 2658, 2021: 2264, 2022: 2847, 2023: 3134, 2024: 3299},
    'H/E': {2015: 2245, 2016: 2774, 2017: 2937, 2018: 3518, 2019: 4397, 2020: 3519, 2021: 2851, 2022: 3733, 2023: 4414, 2024: 4317},
    'H/W': {2015: 2715, 2016: 3093, 2017: 3430, 2018: 4763, 2019: 4774, 2020: 3481, 2021: 3623, 2022: 4713, 2023: 5199, 2024: 5048},
    'K/E': {2015: 4323, 2016: 5901, 2017: 6725, 2018: 8146, 2019: 9724, 2020: 6847, 2021: 6667, 2022: 7529, 2023: 8577, 2024: 8145},
    'K/W': {2015: 4328, 2016: 6374, 2017: 8349, 2018: 9465, 2019: 10399, 2020: 7456, 2021: 6845, 2022: 8667, 2023: 9251, 2024: 7945},
    'L':   {2015: 7799, 2016: 7498, 2017: 7282, 2018: 7242, 2019: 7560, 2020: 5862, 2021: 6310, 2022: 6575, 2023: 7965, 2024: 7047},
    'M/E': {2015: 3338, 2016: 3468, 2017: 3391, 2018: 4232, 2019: 4334, 2020: 3525, 2021: 3807, 2022: 4023, 2023: 4711, 2024: 4060},
    'M/W': {2015: 1966, 2016: 2709, 2017: 3123, 2018: 4331, 2019: 4387, 2020: 3438, 2021: 4086, 2022: 4027, 2023: 4026, 2024: 4032},
    'N':   {2015: 2966, 2016: 3559, 2017: 6088, 2018: 6570, 2019: 6843, 2020: 4981, 2021: 4045, 2022: 4400, 2023: 6604, 2024: 5428},
    'P/N': {2015: 4702, 2016: 4955, 2017: 5374, 2018: 6586, 2019: 8019, 2020: 6073, 2021: 6177, 2022: 6910, 2023: 7830, 2024: 7327},
    'P/S': {2015: 3095, 2016: 3450, 2017: 3227, 2018: 4855, 2019: 5133, 2020: 3168, 2021: 3133, 2022: 3471, 2023: 4521, 2024: 5156},
    'R/C': {2015: 3088, 2016: 4092, 2017: 4368, 2018: 5315, 2019: 6398, 2020: 4506, 2021: 4641, 2022: 5178, 2023: 5942, 2024: 5372},
    'R/N': {2015: 1339, 2016: 1542, 2017: 1792, 2018: 2171, 2019: 2729, 2020: 2185, 2021: 2017, 2022: 2367, 2023: 2954, 2024: 3166},
    'R/S': {2015: 3290, 2016: 3855, 2017: 4079, 2018: 6249, 2019: 6008, 2020: 4341, 2021: 4064, 2022: 4712, 2023: 5445, 2024: 4840},
    'S':   {2015: 2936, 2016: 3040, 2017: 3923, 2018: 5115, 2019: 6144, 2020: 4480, 2021: 3820, 2022: 5351, 2023: 6649, 2024: 6221},
    'T':   {2015: 1466, 2016: 1593, 2017: 2050, 2018: 2611, 2019: 2737, 2020: 2054, 2021: 1751, 2022: 2214, 2023: 2817, 2024: 3055},
}

# ============================================================
# Praja 2025 Report: Table 45 (Ward-wise Avg Days 2023-2024)
# ============================================================
PRAJA_AVG_DAYS = {
    'A':   {2023: 40, 2024: 64}, 'B':   {2023: 46, 2024: 79},
    'C':   {2023: 39, 2024: 32}, 'D':   {2023: 10, 2024: 20},
    'E':   {2023: 50, 2024: 81}, 'F/N': {2023: 44, 2024: 43},
    'F/S': {2023: 33, 2024: 37}, 'G/N': {2023: 32, 2024: 52},
    'G/S': {2023: 27, 2024: 37}, 'H/E': {2023: 25, 2024: 40},
    'H/W': {2023: 35, 2024: 48}, 'K/E': {2023: 32, 2024: 59},
    'K/W': {2023: 44, 2024: 64}, 'L':   {2023: 23, 2024: 20},
    'M/E': {2023: 27, 2024: 28}, 'M/W': {2023: 19, 2024: 28},
    'N':   {2023: 20, 2024: 33}, 'P/N': {2023: 53, 2024: 68},
    'P/S': {2023: 59, 2024: 35}, 'R/C': {2023: 15, 2024: 23},
    'R/N': {2023: 8, 2024: 15},  'R/S': {2023: 17, 2024: 14},
    'S':   {2023: 50, 2024: 50}, 'T':   {2023: 31, 2024: 39},
}


def read_existing_csv(path):
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


def compute_ratios(rows):
    """Per-ward Total/PerCapita complaint ratios from 2023 data."""
    complaint_ratios = {}
    councillors = {}
    for row in rows:
        if row['Year'] == 2023:
            w = row['Ward']
            if row['Per_Capita_Complaints'] > 0:
                complaint_ratios[w] = row['Total_Complaints'] / row['Per_Capita_Complaints']
            councillors[w] = row['Avg_No_of_Councillors']
    return complaint_ratios, councillors


def make_2024_rows(rows, complaint_ratios, councillors):
    """
    Create 2024 rows using Praja growth rates applied to existing 2023 CSV values.
    """
    existing_2023 = {r['Ward']: r for r in rows if r['Year'] == 2023}
    new_rows = []

    for w in sorted(PRAJA_TOTAL_COMPLAINTS.keys()):
        existing_row = existing_2023.get(w)
        if not existing_row:
            continue

        # Growth rate: Praja 2024 / Praja 2023
        p2023 = PRAJA_TOTAL_COMPLAINTS[w].get(2023, 1)
        p2024 = PRAJA_TOTAL_COMPLAINTS[w].get(2024, 0)
        growth = p2024 / p2023 if p2023 > 0 else 1.0

        total = round(existing_row['Total_Complaints'] * growth)

        ratio = complaint_ratios.get(w, 1)
        per_capita = round(total / ratio) if ratio > 0 else 0

        # Avg days: absolute shift
        days_shift = PRAJA_AVG_DAYS[w][2024] - PRAJA_AVG_DAYS[w][2023]
        avg_days = max(1, existing_row['Avg_No_of_Days'] + days_shift)

        new_rows.append({
            'Ward': w, 'Year': 2024,
            'Avg_No_of_Councillors': councillors.get(w, 0),
            'Total_Complaints': total,
            'Per_Capita_Complaints': per_capita,
            'Avg_No_of_Days': round(avg_days, 1),
            'Total_Deliberation': existing_row['Total_Deliberation'],
            'Per_Capita_Deliberation': existing_row['Per_Capita_Deliberation'],
        })

    return new_rows


def main():
    print(f"Reading: {CSV_PATH}")
    rows = read_existing_csv(CSV_PATH)
    print(f"  {len(rows)} existing rows (2019-2023)")

    complaint_ratios, councillors = compute_ratios(rows)

    # 2024 only — using Praja growth rates (no linear extrapolation)
    rows_2024 = make_2024_rows(rows, complaint_ratios, councillors)
    print(f"\n2024 (Praja growth rates applied):")

    for w in ['A', 'B', 'K/E', 'S', 'R/N']:
        r24 = next(r for r in rows_2024 if r['Ward'] == w)
        r23 = next(r for r in rows if r['Year'] == 2023 and r['Ward'] == w)
        pct = PRAJA_TOTAL_COMPLAINTS[w][2024] / PRAJA_TOTAL_COMPLAINTS[w][2023] - 1
        print(f"  {w}: {r23['Total_Complaints']:,} -> {r24['Total_Complaints']:,} (delta={pct:+.1%}, days {r23['Avg_No_of_Days']}->{r24['Avg_No_of_Days']})")

    # Write: 2019-2023 actual + 2024 Praja-estimated
    all_rows = rows + rows_2024
    all_rows.sort(key=lambda r: (r['Ward'], r['Year']))

    with open(OUT_PATH, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELD_NAMES)
        w.writeheader()
        w.writerows(all_rows)

    print(f"\nWritten {len(all_rows)} rows to: {OUT_PATH}")

    # Grand totals
    by_year = {}
    for r in all_rows:
        by_year[r['Year']] = by_year.get(r['Year'], 0) + r['Total_Complaints']
    print("Grand Total_Complaints by year:")
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y]:>10,}")
    print("\nNOTE: 2025-2026 data will be generated by XGBoost ML predictions (ml/predict.py)")


if __name__ == '__main__':
    main()
