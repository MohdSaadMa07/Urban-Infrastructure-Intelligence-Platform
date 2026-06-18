"""
Management command to recompute and persist health scores for all wards.

Runs compute_and_save_all() from health_score service, which uses each ward's
latest CivicMetrics row to compute a 0-100 score and saves it to Ward.health_score.

Usage:
    python manage.py update_health_scores
"""
from django.core.management.base import BaseCommand
from api.services.health_score import compute_and_save_all


class Command(BaseCommand):
    help = 'Recompute and save health scores for all wards using their latest CivicMetrics.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Recomputing health scores for all wards...'))
        updated = compute_and_save_all()
        self.stdout.write(self.style.SUCCESS(
            f'Done — updated health scores for {updated} ward(s).'
        ))
