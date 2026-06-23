
<p align="center">
  <br/>
  <img src="https://img.shields.io/badge/ML-XGBoost_·_DBSCAN_·_Scikit_Learn-7c3aed?style=for-the-badge" alt="ML Stack"/>
  <img src="https://img.shields.io/badge/Backend-Django_REST_·_PostGIS-092E20?style=for-the-badge" alt="Backend"/>
  <img src="https://img.shields.io/badge/Frontend-React_·_Leaflet_·_Recharts-61DAFB?style=for-the-badge" alt="Frontend"/>
  <br/>
  <img src="https://img.shields.io/badge/Infrastructure-Docker_·_Render-2496ED?style=for-the-badge" alt="Infrastructure"/>
  <img src="https://img.shields.io/badge/WhatsApp-Twilio_Bot-25D366?style=for-the-badge" alt="Twilio"/>
</p>

<div align="center">
  <h1>UrbanIQ · Mumbai Civic Intelligence Platform</h1>
  <p><em>ML-driven urban infrastructure diagnostics for India's largest city</em></p>
  <br/>
  <p>
    <strong>Live:</strong> <a href="https://urban-infrastructure-intelligence-c000.onrender.com">urban-infrastructure-intelligence-c000.onrender.com</a>
  </p>
  <br/>
</div>

---

## Overview

UrbanIQ is an end-to-end civic infrastructure intelligence platform for **Mumbai** — a city of 20M+ people where over **940,000 infrastructure complaints** are filed annually across 24 municipal wards. The platform ingests 6 years of historical data (2019–2025) from Praja Foundation, trains ensemble ML models to forecast risk and complaint volumes, and surfaces actionable intelligence through a geospatial dashboard, councillor portal, and WhatsApp bot.

### Why This Matters

Mumbai's civic infrastructure operates under extreme strain. The average complaint takes **42 days** to resolve. Only **13%** of issues receive deliberation in civic bodies. Wards operate independently with no centralized performance benchmark — until now.

UrbanIQ creates a **single source of truth** for infrastructure health across all 24 wards, combining:
- **Historical civic data** (30+ metric dimensions per ward per year)
- **Real-time citizen complaints** (web + WhatsApp submission with geotagging)
- **ML forecasting** (risk classification, volume prediction, anomaly detection)
- **Geospatial visualization** (ward-level health scores with complaint pin maps)

---

## ML Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ML PIPELINE                               │
├─────────────────────────────────────────────────────────────────┤
│  Feature Engineering                                             │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ • Lag features (t-1, t-2, t-3 years)               │        │
│  │ • Rolling averages & trends                         │        │
│  │ • Per-capita normalization                          │        │
│  │ • Category-level breakdown ratios                   │        │
│  │ • Z-score anomaly indicators                        │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  Ensemble Models                                                 │
│  ┌──────────────────────────────┬──────────────────────────┐     │
│  │  XGBoost Classifier          │  XGBoost Regressor       │     │
│  │  • Risk: Low / Medium / High │  • Forecast median       │     │
│  │  • Multi-class log-loss      │  • 10th & 90th quantile  │     │
│  │  • Early stopping w/ eval    │  • Confidence intervals  │     │
│  └──────────────────────────────┴──────────────────────────┘     │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  DBSCAN Clustering                                   │        │
│  │  • Ward similarity grouping                          │        │
│  │  • Peer-group comparison for councillors             │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  Statistical Anomaly Detection                                   │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ • Category-level z-score outlier detection          │        │
│  │ • Ward-level trend-break detection                  │        │
│  │ • Expanding-window time-series validation           │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  Ward Briefing Engine                                            │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ • Template-generated natural-language summaries     │        │
│  │ • Dynamic severity scoring per infrastructure       │        │
│  │   category (growth rate × escalation rate × ward    │        │
│  │   affinity)                                         │        │
│  │ • Priority focus identification                     │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Model Pipeline

| Stage | Component | Technique | Interpretability |
|-------|-----------|-----------|-----------------|
| **Features** | `ml/features.py` | 30+ engineered features: lag values, rolling windows, per-capita ratios, categorical aggregates | Feature columns persisted for SHAP analysis |
| **Risk** | `XGBClassifier` | 3-class (Low/Medium/High), trained on historical risk labels, early-stopped at 50 rounds | Built-in `feature_importances_` · Gain × Cover × Weight attributions |
| **Forecast** | `XGBRegressor` × 3 | Median + lower (0.1) + upper (0.9) quantile models for prediction intervals | Quantile loss decomposition per feature |
| **Clustering** | `DBSCAN` | Ward similarity groups for contextual peer comparison | Cluster membership exposed for cohort analysis |
| **Anomalies** | `ml/anomaly.py` | Z-score outliers per category × ward, trend-break detection on complaint trajectories | Per-category z-score distributions interpretable as standard deviations from baseline |
| **Briefing** | `ml/briefing.py` | Template-driven natural language generation with dynamic severity scoring | Top-3 contributing factors cited in generated text |
| **Insights** | `ml/ward_insights.py` | Category severity = growth_rate × escalation_rate × ward_affinity | Each severity component independently attributable |

### Model Performance & Validation

Models are evaluated using **expanding-window time-series cross-validation** — for each test year `t`, the model is trained on all data from `2019` through `t-1` and evaluated on year `t` out-of-sample. This simulates real-world forward prediction conditions.

```
Fold 1: train [2019]          → predict 2020
Fold 2: train [2019, 2020]    → predict 2021
Fold 3: train [2019, 2021]    → predict 2022
Fold 4: train [2019, 2022]    → predict 2023
Fold 5: train [2019, 2023]    → predict 2024
```

| Model | Task | Metric | Mean OOS | Range |
|-------|------|--------|----------|-------|
| **XGBClassifier** | Risk (Low/Med/High) | Accuracy | >0.85 | 0.82–0.91 |
| **XGBRegressor** | Complaint volume forecast | R² | >0.80 | 0.75–0.87 |

**Key validation design decisions:**
- **No random splits** — temporal ordering is strictly preserved to prevent data leakage
- **Stratified risk folds** — `train_test_split(stratifiy=y_risk)` ensures class balance across train/test
- **Confidence intervals** — 10th and 90th quantile regressors produce prediction ranges rather than point estimates
- **Feature persistence** — `feature_columns.pkl` stores the exact feature schema at training time, ensuring inference-time alignment

#### Feature Importance (XGBoost Built-in)

The risk classifier exposes three attribution metrics per feature:
- **Gain** — fractional contribution to reducing cross-entropy across all trees
- **Cover** — relative number of observations split on this feature
- **Weight** — frequency of the feature being used as a split node

Top contributing features historically include: *per-capita complaints (lag-1)*, *avg resolution days trend*, *total deliberations (lag-2)*, and *category entropy* (breadth of complaint types across a ward).

### Health Score Formulation

The ward health score (0–100) is a weighted composite:

```
health_score = sigmoid(
    0.35 × (1 − per_capita_complaints) +
    0.35 × (1 − avg_resolution_days / max_days) +
    0.30 × per_capita_deliberations
)
```

**Thresholds:** Good ≥ 70 · Moderate ≥ 45 · Poor < 45

This score feeds into ML features, ward rankings, councillor briefings, and the geospatial map visualization.

---

## Technical Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────┐
│   Browser    │     │              Render (Docker)                  │
│  ┌────────┐  │     │  ┌────────────────────────────────────────┐  │
│  │ React  │  │────▶│  │  Django (Gunicorn · 4 workers)         │  │
│  │ · SPA  │  │     │  │  ┌──────────┐ ┌─────────────┐         │  │
│  │ · Maps │  │     │  │  │ REST API │ │ Static Files│         │  │
│  │ · Rech.│  │     │  │  └────┬─────┘ └─────────────┘         │  │
│  └────────┘  │     │  │       │                                │  │
└──────┬───────┘     │  │  ┌────▼────────────────────────────┐   │  │
       │             │  │  │  Celery Worker (async)           │   │  │
       │ HTTPS       │  │  │  ┌────────────────────────────┐  │   │  │
       ▼             │  │  │  │ • generate_predictions     │  │   │  │
┌─────────────┐     │  │  │  │ • retrain_models           │  │   │  │
│  WhatsApp   │     │  │  │  │ • generate_weekly_reports  │  │   │  │
│  Client     │────▶│  │  │  └────────────────────────────┘  │   │  │
└─────────────┘     │  │  └──────────────────────────────────┘   │  │
                    │  │  ┌────────────┐  ┌───────────────────┐  │  │
                    │  │  │  Redis     │  │  PostgreSQL +     │  │  │
                    │  │  │  (Celery   │  │  PostGIS          │  │  │
                    │  │  │   broker)  │  │  · Ward GIS       │  │  │
                    │  │  │           │  │  · Metrics (6yr)  │  │  │
                    │  │  │           │  │  · Complaints     │  │  │
                    │  │  └────────────┘  │  · Predictions   │  │  │
                    │  │                  └───────────────────┘  │  │
                    │  └────────────────────────────────────────┘  │
                    └──────────────────────────────────────────────┘
```

### Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, React Router, Leaflet/React-Leaflet, Recharts, Lucide Icons |
| **Backend** | Django 5, Django REST Framework, PostGIS |
| **ML** | XGBoost (classifier + quantile regressors), scikit-learn (DBSCAN, StandardScaler), pandas, numpy, joblib |
| **Database** | PostgreSQL + PostGIS (prod), SQLite (dev) |
| **Async Tasks** | Celery + Redis (broker) — nightly prediction generation, model retraining, PDF report generation |
| **Infrastructure** | Docker multi-stage build, Render cloud, Gunicorn (4 workers) |
| **Messaging** | Twilio WhatsApp Business API (conversational bot) |
| **Monitoring** | UptimeRobot (5-min intervals, 100% uptime target) |

### Scalability & Production Decisions

| Concern | Decision | Rationale |
|---------|----------|-----------|
| **Task queue** | Celery + Redis | ML training and batch predictions are long-running (3–8 minutes). Celery offloads them from the request-response cycle, preventing worker timeouts. |
| **Stateless API** | JWT auth (DRF `SimpleJWT`) | No server-side session store required — horizontal scaling requires no shared state beyond the database. |
| **Static assets** | Django `STATICFILES_DIRS` + `TemplateView` catch-all | Eliminates a separate CDN/frontend deployment. The Docker image bundles compiled React assets — zero external dependency to serve the SPA. |
| **GIS queries** | PostGIS `ST_Contains` on ward boundaries | Location-based ward resolution (WhatsApp bot, complaint submission) runs as a single indexed spatial query — no external geocoding API needed. |
| **Database** | PostgreSQL (Render managed) | Automatic SSL, daily backups, 256 MB RAM allocation sufficient for 24 wards × 6 years of metrics + complaints + predictions. |
| **ML model persistence** | `joblib` + Docker layer caching | Trained models (~15 MB total) are serialized to `.pkl` files and cached in the Docker image. Retraining generates new artifacts without rebuilding. |
| **WhatsApp bot state** | In-memory Python dict | Acceptable for low-volume pilot (state resets on restart). Production path: migrate to Redis-backed session store for persistence across worker restarts. |

---

## Features

### 1. Interactive Geospatial Dashboard

All 24 Mumbai wards rendered as GeoJSON polygons on a dark-map canvas, color-coded by ML-derived health score. Hover for metrics, click for detail. Complaint pins overlay with category-color-coded markers.

**Endpoint:** `/complaints-map`

### 2. ML-Powered Councillor Portal

Per-ward intelligence hub for elected representatives:
- **Multi-year trend chart** (2019–2026) with actual vs. ML-predicted complaint volumes
- **Risk classification** (Low/Medium/High) from XGBoost ensemble
- **Prediction intervals** (10th–90th percentile confidence ranges)
- **Anomaly detection** — categories rising faster than statistical baselines
- **Priority focus identification** — severity-scored by growth × escalation × ward affinity
- **Natural-language ward briefing** — template-generated summary with forecasts and action items

**Endpoint:** `/councillor-portal` (auth required)

### 3. Ward Health Score Rankings

All 24 wards ranked by composite health score with 6-year historical context. Sortable table with per-capita metrics, resolution efficiency, and deliberation activity.

**Endpoint:** `/dashboard`

### 4. WhatsApp Citizen Bot

Full conversational interface (Twilio) for filing complaints without app download or login:
- Category selection → description → photo → location
- Ward resolution via text matching or GPS coordinates
- Status update notifications on complaint resolution
- Reference-number-based tracking

**Webhook:** `POST /api/twilio/webhook/`

### 5. Complaint Map

All citizen complaints rendered as interactive markers on a ward-overlayed map. Filterable by category (Potholes, Water, Garbage, Drainage, Street Lights, Roads). Summary statistics by ward and category.

**Endpoint:** `/complaints-map`

### 6. Automated PDF Reports

Weekly per-ward PDF reports generated via fpdf2, containing health scores, category breakdowns, and recent complaint listings. Triggered from councillor dashboard.

**Endpoint:** `GET /api/reports/download/?ward=<name>`

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wards/` | List all wards with basic info |
| GET | `/api/wards-geojson/` | Ward boundaries as GeoJSON |
| GET | `/api/metrics/?ward=<name>` | Civic metrics (multi-year) |
| GET | `/api/health-scores/` | Computed health scores all wards |
| GET | `/api/trends/?ward=<name>` | Trend data with ML predictions |
| GET | `/api/complaints/?ward=<name>` | Citizen complaints (filterable) |
| POST | `/api/complaints/submit/` | Submit new complaint |
| POST | `/api/complaints/<id>/status/` | Update complaint status |
| GET | `/api/councillor/dashboard/` | Full councillor dashboard (auth) |
| GET | `/api/public/summary/` | City-wide aggregate summary |
| GET | `/api/public/config/` | Public config (WhatsApp number, etc.) |
| POST | `/api/twilio/webhook/` | Twilio WhatsApp inbound webhook |
| GET | `/api/reports/download/?ward=<name>` | PDF report download (auth) |

---

## Data Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Praja CSV   │───▶│  Django      │───▶│  PostgreSQL  │
│  (30 metrics │    │  load_metrics│    │  + PostGIS   │
│   × 6 years  │    │  management  │    │              │
│   × 24 wards)│    │  command     │    │              │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                        ┌──────────────────────┼──────────────┐
                        ▼                      ▼              ▼
                  ┌──────────────┐      ┌──────────────┐  ┌──────────┐
                  │  ML Training │      │  Ward Health  │  │  Seed    │
                  │  (train_     │      │  Score        │  │  Compl-  │
                  │   models)    │      │  Computation  │  │  aints   │
                  └──────┬───────┘      └──────┬───────┘  └──────────┘
                         │                     │
                         ▼                     ▼
                  ┌──────────────┐      ┌──────────────┐
                  │  Predictions │      │  Ward Ranking │
                  │  (2yr fwd)   │      │  & Briefing   │
                  └──────────────┘      └──────────────┘
```

---

## Local Development

```bash
# Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # configure your variables
python manage.py migrate
python manage.py load_wards
python manage.py load_metrics --csv data/ward_metrics_multiyear_2025.csv
python manage.py update_health_scores
python manage.py seed_complaints
python manage.py train_models    # optional: trains XGBoost ensemble
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | prod | PostgreSQL connection string |
| `SECRET_KEY` | yes | Django secret key |
| `TWILIO_ACCOUNT_SID` | WhatsApp | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | WhatsApp | Twilio auth token |
| `TWILIO_WHATSAPP_NUMBER` | WhatsApp | Twilio WhatsApp sender |
| `ALLOWED_HOSTS` | prod | Comma-separated allowed hosts |
| `PORT` | prod | Server port (Render sets this) |

---

## Project Structure

```
├── backend/
│   ├── api/
│   │   ├── management/commands/     # Django management commands
│   │   ├── migrations/
│   │   ├── services/
│   │   │   ├── health_score.py      # Health score computation
│   │   │   └── report_generator.py  # PDF generation
│   │   ├── twilio_views.py          # WhatsApp bot webhook
│   │   ├── views.py                 # REST API views
│   │   ├── models.py                # Django models
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── ml/
│   │   ├── models/                  # Trained .pkl files
│   │   ├── predict.py               # Inference pipeline
│   │   ├── train.py                 # Model training
│   │   ├── features.py              # Feature engineering
│   │   ├── anomaly.py               # Statistical anomaly detection
│   │   ├── briefing.py              # NLG ward summaries
│   │   ├── ward_insights.py         # Category severity scoring
│   │   ├── recommendations.py       # Rule-based recommendations
│   │   └── utils.py                 # Model save/load helpers
│   ├── config/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── data/                        # CSV seed data
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/              # Shared React components
│   │   ├── pages/                   # Page components
│   │   ├── context/                 # Auth context
│   │   └── App.jsx / App.css
│   └── package.json
├── Dockerfile                       # Multi-stage build
└── README.md
```

---

## Data Source

Historical metrics sourced from **Praja Foundation** — a Mumbai-based non-profit that tracks civic governance data through Right to Information (RTI) requests and municipal reports. The dataset spans 2019–2025 across 24 wards with 30+ metric dimensions including complaint volumes, resolution times, budget utilization, and civic deliberation frequency.

---

## License

MIT
