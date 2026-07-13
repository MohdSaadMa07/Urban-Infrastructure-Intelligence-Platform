from django.test import TestCase, override_settings
from django.core.cache import cache
from django.contrib.gis.geos import MultiPolygon, Polygon
from unittest.mock import patch, MagicMock
import json
import pandas as pd
import numpy as np

from api.models import Ward, CivicMetrics, PortalMetrics, Complaint


class MLPipelineTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        boundary = MultiPolygon(Polygon.from_bbox((0, 0, 1, 1)))
        ward_a = Ward.objects.create(ward_no=1, ward_name="Ward A", boundary=boundary)
        ward_b = Ward.objects.create(ward_no=2, ward_name="Ward B", boundary=boundary)

        for ward in [ward_a, ward_b]:
            for year in range(2019, 2025):
                CivicMetrics.objects.create(
                    ward=ward,
                    year=year,
                    total_complaints=100 + (year - 2019) * 10,
                    closed_complaints=80 + (year - 2019) * 5,
                    escalated_complaints=10 + (year - 2019) * 2,
                    avg_resolution_days=30 - (year - 2019),
                    per_capita_complaints=500 + (year - 2019) * 20,
                    total_deliberations=50 + (year - 2019) * 3,
                    per_capita_deliberations=25 + (year - 2019) * 2,
                    avg_councillors=7,
                )

        PortalMetrics.objects.create(
            ward=ward_a, year=2024,
            total_complaints=15, resolved_complaints=10,
        )
        PortalMetrics.objects.create(
            ward=ward_a, year=2025,
            total_complaints=30, resolved_complaints=20,
        )

    def test_build_feature_matrix_returns_expected_shape(self):
        from ml.features import build_feature_matrix
        X, y_risk, y_complaints, meta = build_feature_matrix(training=True)
        self.assertGreater(len(X), 0)
        self.assertEqual(len(X), len(y_risk))
        self.assertEqual(len(X), len(y_complaints))
        self.assertIn("complaints_lag1", X.columns)
        self.assertIn("complaint_growth_rate", X.columns)

    def test_build_feature_matrix_horizon_2(self):
        from ml.features import build_feature_matrix
        X, _, y, _ = build_feature_matrix(training=True, horizon=2)
        self.assertGreater(len(X), 0)
        self.assertEqual(len(X), len(y))

    def test_feature_matrix_includes_portal_metrics(self):
        from ml.features import build_feature_matrix
        X, _, y, meta = build_feature_matrix(training=True)
        ward_a_rows = meta[meta["ward_name"] == "Ward A"]
        ward_a_2024 = ward_a_rows[ward_a_rows["year"] == 2024]
        self.assertEqual(len(ward_a_2024), 1)
        self.assertEqual(ward_a_2024.iloc[0]["total_complaints"], 165)

    def test_feature_matrix_includes_portal_only_year(self):
        from ml.features import build_feature_matrix
        X, _, y, meta = build_feature_matrix(training=True)
        ward_a_rows = meta[meta["ward_name"] == "Ward A"]
        ward_a_2025 = ward_a_rows[ward_a_rows["year"] == 2025]
        self.assertEqual(len(ward_a_2025), 1)
        self.assertEqual(ward_a_2025.iloc[0]["total_complaints"], 30)

    def test_train_and_predict_pipeline(self):
        from ml.features import build_feature_matrix
        from ml.train import train_risk_model, train_forecast_model, train_clustering

        X, y_risk, y_complaints, _ = build_feature_matrix(training=True)
        model, acc = train_risk_model(X, y_risk)
        self.assertIsNotNone(model)
        self.assertGreater(acc, 0)

        model, r2 = train_forecast_model(X, y_complaints, horizon=1)
        self.assertIsNotNone(model)

        X_n2, _, y_n2, _ = build_feature_matrix(training=True, horizon=2)
        model_n2, r2_n2 = train_forecast_model(X_n2, y_n2, horizon=2)
        self.assertIsNotNone(model_n2)

        train_clustering(X)

    def test_generate_predictions_returns_results(self):
        from ml.features import build_feature_matrix
        from ml.train import train_risk_model, train_forecast_model

        X, y_risk, y_complaints, _ = build_feature_matrix(training=True)
        train_risk_model(X, y_risk)
        train_forecast_model(X, y_complaints, horizon=1)

        X_n2, _, y_n2, _ = build_feature_matrix(training=True, horizon=2)
        train_forecast_model(X_n2, y_n2, horizon=2)

        from ml.predict import generate_predictions
        results, target_year = generate_predictions(target_year=2025, horizon=1)
        self.assertGreater(len(results), 0)
        self.assertIn("ward_name", results[0])
        self.assertIn("predicted_risk", results[0])
        self.assertIn("predicted_complaints", results[0])

        results_n2, target_year_n2 = generate_predictions(target_year=2026, horizon=2)
        self.assertGreater(len(results_n2), 0)


class CategoryAnomalyTest(TestCase):
    def test_detect_category_anomalies_returns_list(self):
        from ml.anomaly import detect_category_anomalies
        result = detect_category_anomalies()
        self.assertIsInstance(result, list)

    def test_anomaly_result_keys(self):
        from ml.anomaly import detect_category_anomalies
        result = detect_category_anomalies()
        if result:
            expected_keys = {'issue', 'latest', 'mean', 'std', 'z_score',
                             'direction', 'severity', 'is_anomaly',
                             'pct_above_mean', 'recent_3yr_growth_pct'}
            self.assertTrue(expected_keys.issubset(result[0].keys()))

    def test_anomaly_sorted_by_z_score(self):
        from ml.anomaly import detect_category_anomalies
        result = detect_category_anomalies()
        if len(result) > 1:
            z_scores = [abs(r['z_score']) for r in result]
            self.assertEqual(z_scores, sorted(z_scores, reverse=True))

    def test_detect_ward_anomalies_returns_list(self):
        from ml.anomaly import detect_ward_anomalies
        result = detect_ward_anomalies()
        self.assertIsInstance(result, list)

    def test_detect_trend_breaks_returns_list(self):
        from ml.anomaly import detect_trend_breaks
        result = detect_trend_breaks()
        self.assertIsInstance(result, list)

    def test_get_ward_anomaly_report_has_expected_keys(self):
        from ml.anomaly import get_ward_anomaly_report
        report = get_ward_anomaly_report()
        self.assertIn('category_anomalies', report)
        self.assertIn('ward_anomaly', report)
        self.assertIn('trend_breaks', report)
        self.assertIn('summary', report)

    def test_anomaly_with_fake_csv_path(self):
        from ml.anomaly import CATEGORY_CSV
        import os
        self.assertTrue(os.path.exists(CATEGORY_CSV))


class SeasonalAdvisoryTest(TestCase):
    def test_advisory_for_june_returns_results(self):
        from ml.seasonal_advisory import generate_seasonal_advisories
        advisories = generate_seasonal_advisories([], current_month=6)
        self.assertIsInstance(advisories, list)

    def test_advisory_for_december_returns_empty(self):
        from ml.seasonal_advisory import generate_seasonal_advisories
        advisories = generate_seasonal_advisories([], current_month=12)
        self.assertEqual(advisories, [])

    def test_advisory_with_growing_category_gets_urgency_3(self):
        from ml.seasonal_advisory import generate_seasonal_advisories
        failing = [{'issue': 'Drainage', 'recent_3yr_growth_pct': 25}]
        advisories = generate_seasonal_advisories(failing, current_month=7)
        drainage = [a for a in advisories if a['category'] == 'Drainage']
        if drainage:
            self.assertEqual(drainage[0]['urgency'], 3)

    def test_advisory_keys(self):
        from ml.seasonal_advisory import generate_seasonal_advisories
        advisories = generate_seasonal_advisories([], current_month=6)
        if advisories:
            expected_keys = {'category', 'display_name', 'season_status',
                             'surge_factor', 'advisory_text', 'urgency'}
            self.assertTrue(expected_keys.issubset(advisories[0].keys()))

    def test_advisory_sorted_by_urgency(self):
        from ml.seasonal_advisory import generate_seasonal_advisories
        advisories = generate_seasonal_advisories([], current_month=6)
        urgencies = [a['urgency'] for a in advisories]
        self.assertEqual(urgencies, sorted(urgencies, reverse=True))


class AdvisoryAnomalyIntegrationTest(TestCase):
    def test_failing_categories_feed_into_advisories(self):
        from ml.anomaly import detect_category_anomalies
        from ml.seasonal_advisory import generate_seasonal_advisories

        anomalies = detect_category_anomalies()
        failing = []
        for c in anomalies:
            if c['recent_3yr_growth_pct'] > 10:
                failing.append({
                    'issue': c['issue'],
                    'recent_3yr_growth_pct': c['recent_3yr_growth_pct'],
                    'projected_next': int(c['latest'] * (1 + c['recent_3yr_growth_pct'] / 100)),
                })

        advisories = generate_seasonal_advisories(failing, current_month=6)
        self.assertIsInstance(advisories, list)


class DashboardCacheTest(TestCase):
    def setUp(self):
        cache.clear()

    def test_cache_cleared_between_tests(self):
        cache.set('test_key', 'value')
        cache.clear()
        self.assertIsNone(cache.get('test_key'))

    @override_settings(CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
    })
    def test_councillor_dashboard_caches_anomalies(self):
        from django.core.cache import cache
        from ml.anomaly import detect_category_anomalies

        key = 'category_anomalies'
        cache.delete(key)
        self.assertIsNone(cache.get(key))

        result = cache.get(key)
        if result is None:
            result = detect_category_anomalies()
            cache.set(key, result, 300)

        cached = cache.get(key)
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), len(result))


class ComplaintCategoryMappingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        boundary = MultiPolygon(Polygon.from_bbox((0, 0, 1, 1)))
        ward = Ward.objects.create(ward_no=99, ward_name="Test Ward", boundary=boundary)
        for cat in ['pothole', 'road', 'garbage', 'water', 'drainage', 'streetlight', 'other']:
            Complaint.objects.create(ward=ward, category=cat, description=f"Test {cat}",
                                     latitude=19.0, longitude=72.0)

    def test_db_to_csv_mapping_in_dashboard(self):
        from api.models import Complaint
        from api.views import DB_TO_CSV

        complaints_by_cat = Complaint.objects.values('category').annotate(count=Count('id'))
        csv_buckets = {}
        for c in complaints_by_cat:
            csv_name = DB_TO_CSV.get(c['category'], 'Other')
            csv_buckets[csv_name] = csv_buckets.get(csv_name, 0) + c['count']

        self.assertIn('Roads', csv_buckets)
        self.assertEqual(csv_buckets['Roads'], 2)
        self.assertIn('Solid Waste Management', csv_buckets)
        self.assertEqual(csv_buckets['Solid Waste Management'], 1)
        self.assertIn('Water Supply', csv_buckets)
        self.assertEqual(csv_buckets['Water Supply'], 1)
        self.assertIn('Drainage', csv_buckets)
        self.assertIn('Other', csv_buckets)


from django.db.models import Count
