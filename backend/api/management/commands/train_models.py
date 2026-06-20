"""
Management command to train ML models from historical CivicMetrics data.

Trains:
  - XGBClassifier (risk)
  - XGBRegressor (forecast)
  - DBSCAN (clustering)

Usage:
    python manage.py train_models
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train ML models from historical CivicMetrics data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Building feature matrix...'))
        from ml.features import build_feature_matrix
        from ml.train import train_risk_model, train_forecast_model, train_clustering

        X, y_risk, y_complaints, meta = build_feature_matrix()
        self.stdout.write(f'  Rows: {len(X)}, Features: {len(X.columns)}')
        self.stdout.write(f'  Feature columns: {list(X.columns)}')

        self.stdout.write(self.style.NOTICE('\nTraining risk classification model (XGBoost)...'))
        train_risk_model(X, y_risk)

        self.stdout.write(self.style.NOTICE('\nTraining forecast model (XGBoost)...'))
        train_forecast_model(X, y_complaints)

        self.stdout.write(self.style.NOTICE('\nRunning DBSCAN clustering...'))
        train_clustering(X)

        self.stdout.write(self.style.SUCCESS('\nAll models trained and saved to ml/models/.'))
