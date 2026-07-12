"""
Management command to train ML models from historical CivicMetrics data.

Trains:
  - XGBClassifier (risk)
  - XGBRegressor (forecast)
  - DBSCAN (clustering)

Also runs expanding-window time-series validation.

Usage:
    python manage.py train_models
"""

import warnings
import numpy as np
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train ML models from historical CivicMetrics data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Building feature matrix...'))
        from ml.features import build_feature_matrix
        from ml.train import (
            train_risk_model, train_forecast_model, train_clustering,
            expanding_window_validation,
        )

        X, y_risk, y_complaints, meta = build_feature_matrix(training=True)
        self.stdout.write(f'  Rows: {len(X)}, Features: {len(X.columns)}')
        self.stdout.write(f'  Feature columns: {list(X.columns)}')

        self.stdout.write(self.style.NOTICE('\nTraining risk classification model (XGBoost)...'))
        train_risk_model(X, y_risk)

        self.stdout.write(self.style.NOTICE('\nTraining forecast model N+1 (XGBoost)...'))
        train_forecast_model(X, y_complaints, horizon=1)

        self.stdout.write(self.style.NOTICE('\nTraining forecast model N+2 (XGBoost)...'))
        X_n2, _, y_complaints_n2, _ = build_feature_matrix(training=True, horizon=2)
        train_forecast_model(X_n2, y_complaints_n2, horizon=2)

        self.stdout.write(self.style.NOTICE('\nRunning DBSCAN clustering...'))
        train_clustering(X)

        # Time-series cross-validation
        self.stdout.write(self.style.NOTICE('\nRunning expanding-window validation...'))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r2_scores, acc_scores = expanding_window_validation()
        if r2_scores:
            self.stdout.write(self.style.WARNING(
                f'OOS R²: mean={np.mean(r2_scores):.3f} range=[{min(r2_scores):.3f}, {max(r2_scores):.3f}]'
            ))
        if acc_scores:
            self.stdout.write(self.style.WARNING(
                f'OOS Accuracy: mean={np.mean(acc_scores):.3f} range=[{min(acc_scores):.3f}, {max(acc_scores):.3f}]'
            ))

        self.stdout.write(self.style.SUCCESS('\nAll models trained and saved to ml/models/.'))
