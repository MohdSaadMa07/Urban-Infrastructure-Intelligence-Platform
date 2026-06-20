"""
Extend Table_1_Issue_Wise_Overall_Complaints.csv with 2022-2024 data from
Praja 2025 Report Table 43, then create escalation data from Table 55.
"""
import csv
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
CATEGORY_CSV = DATA_DIR / "Table_1_Issue_Wise_Overall_Complaints.csv"

# ── Table 43: Issue Wise Overall Complaints from 2015-2024 ──────────────────
# Values for 2022, 2023, 2024. CSV already has 2012-2021.
TABLE_43_2022_2024 = {
    'Buildings':                    (16883, 14572, 14451),
    'Colony Officer':               (981,   1056,  823),
    'Drainage':                     (17121, 18752, 15701),
    'Estate':                       (661,   553,   949),
    'Garden':                       (3529,  3644,  3293),
    'License':                      (13439, 13672, 12275),
    'MCGM Related':                 (735,   759,   765),
    'Medical Officer Health (MOH)': (1384,  1652,  1752),
    'Nuisance due to vagrants':     (1599,  2533,  3233),
    'Pest control':                 (8037,  8328,  8721),
    'Pollution':                    (292,   760,   586),
    'Roads':                        (11161, 10549, 9800),
    'School':                       (70,    72,    73),
    'Shop and Establishment':       (647,   695,   612),
    'Solid Waste Management':       (12351, 24690, 25031),
    'Storm Water Drainage':         (1550,  2713,  2304),
    'Toilet':                       (531,   544,   505),
    'Water Supply':                 (13097, 14752, 14522),
}

# ── Table 55: Issue-wise escalated complaints in 2024 ─────────────────────
ESCALATION_DATA = {
    'Buildings':                    (14451, 6839, 6712, 6572),
    'Colony Officer':               (823,   489,  489,  478),
    'Drainage':                     (15701, 3091, 3083, 2944),
    'Estate':                       (949,   201,  201,  190),
    'Garden':                       (3293,  209,  204,  191),
    'License':                      (12275, 2415, 2404, 2211),
    'MCGM Related':                 (765,   261,  261,  254),
    'Medical Officer Health (MOH)': (1752,  358,  353,  323),
    'Nuisance due to vagrants':     (3233,  2350, 2350, 2332),
    'Pest control':                 (8721,  126,  113,  75),
    'Pollution':                    (586,   290,  288,  276),
    'Roads':                        (9800,  3254, 3231, 3105),
    'School':                       (73,    59,   59,   59),
    'Shop and Establishment':       (612,   16,   16,   14),
    'Solid Waste Management':       (25031, 3082, 3071, 3015),
    'Storm Water Drainage':         (2304,  387,  380,  371),
    'Toilet':                       (505,   62,   62,   59),
    'Water Supply':                 (14522, 1,    1,    1),
}

# ── Table 55: Ward-wise total and escalated complaints in 2024 ────────────
WARD_ESCALATION_DATA = {
    'A':   (3207, 1859, 1857, 1835),
    'B':   (3019, 1720, 1713, 1657),
    'C':   (3864, 534,  527,  502),
    'D':   (3748, 168,  164,  144),
    'E':   (4939, 1266, 1245, 1201),
    'F/N': (4229, 437,  436,  400),
    'F/S': (2781, 164,  160,  144),
    'G/N': (5151, 1182, 1174, 1131),
    'G/S': (3299, 223,  219,  189),
    'H/E': (4317, 434,  425,  364),
    'H/W': (5048, 782,  773,  728),
    'K/E': (8145, 1037, 1030, 991),
    'K/W': (7945, 1498, 1490, 1451),
    'L':   (7047, 1946, 1912, 1878),
    'M/E': (4060, 303,  295,  266),
    'M/W': (4032, 281,  280,  262),
    'N':   (5428, 383,  377,  337),
    'P/N': (7327, 3229, 3208, 3171),
    'P/S': (5156, 1995, 1989, 1957),
    'R/C': (5372, 261,  257,  226),
    'R/N': (3166, 33,   31,   23),
    'R/S': (4840, 220,  220,  208),
    'S':   (6221, 3188, 3184, 3121),
    'T':   (3055, 347,  312,  284),
}


def update_category_csv():
    """Add 2022, 2023, 2024 columns to the category CSV."""
    if not CATEGORY_CSV.exists():
        print(f"ERROR: {CATEGORY_CSV} not found")
        return False

    rows = []
    with open(CATEGORY_CSV, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    existing_cols = list(rows[0].keys())  # Issue, 2012, 2013, ..., 2021
    new_cols = existing_cols + ['2022', '2023', '2024']

    for row in rows:
        issue = row['Issue']
        if issue in TABLE_43_2022_2024:
            v2022, v2023, v2024 = TABLE_43_2022_2024[issue]
            row['2022'] = str(v2022)
            row['2023'] = str(v2023)
            row['2024'] = str(v2024)
        else:
            # "Other" category or unmatched — set 0
            row['2022'] = '0'
            row['2023'] = '0'
            row['2024'] = '0'

    # "Other" category: compute as grand total minus sum of all known
    # Grand total from T43: 115396 for 2024, but we'll just set 0 for unnamed
    for row in rows:
        if row['Issue'] == 'Other':
            row['2022'] = '0'
            row['2023'] = '0'
            row['2024'] = '0'

    with open(CATEGORY_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_cols)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Updated {CATEGORY_CSV.name} - added 2022, 2023, 2024 columns, "
          f"now {len(new_cols)} columns x {len(rows)} rows")
    return True


def create_escalation_csv():
    """Create escalation_data.csv from Table 55 (issue-wise and ward-wise)."""
    out_path = DATA_DIR / "escalation_data.csv"

    fields = ['entity_type', 'entity', 'total_complaints',
              'escalated_level1', 'escalated_level2', 'escalated_level3']
    rows = []

    # Issue-wise rows
    for issue, (total, l1, l2, l3) in ESCALATION_DATA.items():
        rows.append({
            'entity_type': 'category',
            'entity': issue,
            'total_complaints': total,
            'escalated_level1': l1,
            'escalated_level2': l2,
            'escalated_level3': l3,
        })

    # Ward-wise rows
    for ward, (total, l1, l2, l3) in WARD_ESCALATION_DATA.items():
        rows.append({
            'entity_type': 'ward',
            'entity': ward,
            'total_complaints': total,
            'escalated_level1': l1,
            'escalated_level2': l2,
            'escalated_level3': l3,
        })

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Created {out_path.name} - {len(rows)} rows "
          f"({len(ESCALATION_DATA)} categories, {len(WARD_ESCALATION_DATA)} wards)")
    return True


if __name__ == '__main__':
    update_category_csv()
    create_escalation_csv()
    print("Done.")
