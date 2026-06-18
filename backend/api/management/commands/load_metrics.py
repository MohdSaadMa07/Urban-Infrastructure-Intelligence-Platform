"""
Management command to load ward-wise civic metrics from CSV into CivicMetrics model.

Supports both the legacy single-year CSV (ward_complaints.csv) and
the multi-year CSV (ward_metrics_multiyear.csv).

Usage:
    python manage.py load_metrics                            # loads multiyear CSV (default)
    python manage.py load_metrics --csv path/to/file.csv    # loads custom CSV
    python manage.py load_metrics --year 2021               # override year (single-year CSVs only)
    python manage.py load_metrics --clear                   # delete all CivicMetrics rows first
"""
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from api.models import Ward, CivicMetrics

# Default to multi-year CSV
DEFAULT_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    'data', 'ward_metrics_multiyear.csv'
)


class Command(BaseCommand):
    help = 'Load ward-wise civic metrics from a CSV file into the CivicMetrics table.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default=DEFAULT_CSV,
            help='Path to the CSV file (default: backend/data/ward_metrics_multiyear.csv)',
        )
        parser.add_argument(
            '--year',
            type=int,
            default=None,
            help='Override year for all rows (only used if CSV has no Year column)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            default=False,
            help='Delete all existing CivicMetrics rows before loading',
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        year_override = options['year']
        clear = options['clear']

        if not os.path.exists(csv_path):
            raise CommandError(f'CSV file not found: {csv_path}')

        # Build a lookup: normalised ward_name -> Ward instance
        # Normalise: strip whitespace, uppercase
        wards_by_name = {w.ward_name.strip().upper(): w for w in Ward.objects.all()}
        if not wards_by_name:
            raise CommandError('No wards found in the database. Load ward boundaries first.')

        if clear:
            deleted, _ = CivicMetrics.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} existing CivicMetrics rows.'))

        self.stdout.write(self.style.NOTICE(f'Loading metrics from: {csv_path}'))

        created_count = 0
        updated_count = 0
        skipped = []

        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            has_year_col = 'Year' in (reader.fieldnames or [])

            for row in reader:
                ward_code = row['Ward'].strip().upper()

                # Try exact match first, then try replacing / with common variants
                ward = wards_by_name.get(ward_code)
                if not ward:
                    skipped.append(ward_code)
                    continue

                # Determine year
                if has_year_col:
                    year = int(row['Year'])
                elif year_override is not None:
                    year = year_override
                else:
                    year = 2021  # fallback for legacy single-year CSV

                total_complaints = int(row['Total_Complaints'])
                per_capita = int(row['Per_Capita_Complaints'])
                avg_days = float(row['Avg_No_of_Days'])
                deliberations = int(row['Total_Deliberation'])
                per_capita_delib = int(row['Per_Capita_Deliberation'])
                avg_councillors = int(row['Avg_No_of_Councillors'])

                # Estimate closed & escalated from Praja Foundation city-wide averages
                # (86% closure rate, 13% escalation rate)
                closed_estimate = int(total_complaints * 0.86)
                escalated_estimate = int(total_complaints * 0.13)

                obj, was_created = CivicMetrics.objects.update_or_create(
                    ward=ward,
                    year=year,
                    defaults={
                        'total_complaints': total_complaints,
                        'closed_complaints': closed_estimate,
                        'escalated_complaints': escalated_estimate,
                        'avg_resolution_days': avg_days,
                        'per_capita_complaints': per_capita,
                        'total_deliberations': deliberations,
                        'per_capita_deliberations': per_capita_delib,
                        'avg_councillors': avg_councillors,
                    },
                )

                if was_created:
                    created_count += 1
                else:
                    updated_count += 1

                self.stdout.write(
                    f'  {"+" if was_created else "~"} {ward.ward_name} ({year}): '
                    f'{total_complaints:,} complaints, {avg_days} avg days'
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done -- created {created_count}, updated {updated_count} records.'
        ))
        if skipped:
            self.stdout.write(self.style.WARNING(
                f'Skipped (no matching ward in DB): {", ".join(skipped)}'
            ))
