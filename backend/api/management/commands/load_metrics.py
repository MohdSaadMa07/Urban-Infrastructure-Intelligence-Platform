"""
Management command to load ward-wise civic metrics from CSV into CivicMetrics model.

Usage:
    python manage.py load_metrics                          # loads default CSV
    python manage.py load_metrics --csv path/to/file.csv   # loads custom CSV
    python manage.py load_metrics --year 2019              # override year (default 2021)
"""
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from api.models import Ward, CivicMetrics


class Command(BaseCommand):
    help = 'Load ward-wise civic metrics from a CSV file into the CivicMetrics table.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default=os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                'data', 'ward_complaints.csv'
            ),
            help='Path to the CSV file (default: backend/data/ward_complaints.csv)',
        )
        parser.add_argument(
            '--year',
            type=int,
            default=2021,
            help='Year to assign to the imported records (default: 2021)',
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        year = options['year']

        if not os.path.exists(csv_path):
            raise CommandError(f'CSV file not found: {csv_path}')

        # Build a lookup: ward_name -> Ward instance
        wards_by_name = {w.ward_name.strip().upper(): w for w in Ward.objects.all()}
        if not wards_by_name:
            raise CommandError('No wards found in the database. Load ward boundaries first.')

        self.stdout.write(self.style.NOTICE(
            f'Loading metrics from: {csv_path}  (year={year})'
        ))

        created_count = 0
        updated_count = 0
        skipped = []

        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ward_code = row['Ward'].strip().upper()

                ward = wards_by_name.get(ward_code)
                if not ward:
                    skipped.append(ward_code)
                    continue

                total_complaints = int(row['Total_Complaints'])
                per_capita = int(row['Per_Capita_Complaints'])
                avg_days = float(row['Avg_No_of_Days'])
                deliberations = int(row['Total_Deliberation'])
                per_capita_delib = int(row['Per_Capita_Deliberation'])
                avg_councillors = int(row['Avg_No_of_Councillors'])

                # Estimate closed & escalated from city-wide averages
                # (86% closure rate, 13% escalation rate – from the Praja 2021 report)
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

                self.stdout.write(f'  {"+" if was_created else "~"} {ward.ward_name} ({year}): '
                                  f'{total_complaints} complaints, {avg_days} avg days')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done — created {created_count}, updated {updated_count} records.'
        ))
        if skipped:
            self.stdout.write(self.style.WARNING(
                f'Skipped (no matching ward): {", ".join(skipped)}'
            ))
