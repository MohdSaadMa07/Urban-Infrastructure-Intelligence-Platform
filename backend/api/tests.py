from django.test import TestCase
from django.contrib.gis.geos import MultiPolygon, Polygon
from api.models import Ward, CivicMetrics, PortalMetrics


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

        # Add portal complaints for 2024 (augments CivicMetrics)
        PortalMetrics.objects.create(
            ward=ward_a, year=2024,
            total_complaints=15, resolved_complaints=10,
        )

        # Add portal-only year 2025 for Ward A (carry-forward test)
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
        # 2024 base was 150 (2019=100, 5 years of +10), plus 15 portal = 165
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
