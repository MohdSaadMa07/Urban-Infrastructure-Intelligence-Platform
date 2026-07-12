# UrbanIQ — Mumbai Urban Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=fff)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django)](https://www.djangoproject.com/)
[![PostGIS](https://img.shields.io/badge/PostGIS-3-316192?logo=postgresql&logoColor=fff)](https://postgis.net/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=000)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite)](https://vite.dev/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1-EC1C24)](https://xgboost.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff)](https://www.docker.com/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9-199900?logo=leaflet)](https://leafletjs.com/)
[![Twilio](https://img.shields.io/badge/Twilio-F22F46?logo=twilio)](https://www.twilio.com/)

UrbanIQ is an open civic-tech platform that tracks infrastructure health across Mumbai's 24 municipal wards. It aggregates public complaint data from the Praja Foundation, lets citizens file new complaints via web or WhatsApp, computes ward-level health scores, and uses machine learning to forecast complaint volumes and risk levels 1–2 years ahead.

---

## Key Features

- **Geospatial Ward Map** — Interactive Leaflet map of Mumbai's 24 wards colour-coded by health score
- **Ward Health Scores** — Composite 0–100 score based on per-capita complaints, resolution speed, and civic engagement
- **ML Predictions** — XGBoost models forecast complaint volumes with prediction intervals and risk classification for 1 and 2 years ahead
- **Anomaly Detection** — Z-score-based anomaly detection flags unusual complaint spikes across 18 categories
- **WhatsApp Complaint Bot** — Step-by-step complaint filing via Twilio WhatsApp with photo, location, and auto-ward-matching
- **Citizen Complaint Portal** — File complaints with geo-tagging, upload photos, and track resolution status
- **Councillor Dashboard** — Per-ward performance metrics, rankings, engagement scores, and PDF report generation
- **Public Dashboard** — No-auth view of city-wide health summary and ward rankings
- **Automated Retraining** — Daily cron endpoint syncs portal complaints and retrains ML models
- **PDF Reports** — Weekly ward summary PDFs with health score, category breakdown, and recent complaints

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.2, Django REST Framework 3.17, Python 3.12 |
| **Database** | PostgreSQL 16 + PostGIS 3 (via Neon) |
| **ML** | XGBoost 2.1, scikit-learn 1.5, pandas 2.2, numpy 1.26, joblib 1.4 |
| **Frontend** | React 19, Vite 8, React Router 7, Leaflet 1.9, Recharts 3.8 |
| **Auth** | SimpleJWT (access + refresh tokens), token blacklisting |
| **Background Tasks** | Celery 5.6, Redis 8 (optional) |
| **WhatsApp** | Twilio 9.10 |
| **PDF** | fpdf2 2.8 |
| **Deployment** | Docker (multi-stage), Render, Gunicorn 23 |
| **Static Files** | WhiteNoise 6.12 |
| **CORS** | django-cors-headers 4.9 |

---

## System Architecture

```
┌──────────────┐     ┌───────────────────────────────────────┐
│  Browser/    │────▶│          Django (Gunicorn)            │
│  Mobile      │     │  DRF API + JWT Auth + WhiteNoise      │
│              │     │                                       │
│  React SPA   │     │  ┌─────────────────────────────────┐  │
│  (Vite)      │     │  │  ML Module                      │  │
│              │     │  │  ┌──────────┐ ┌──────────────┐  │  │
└──────────────┘     │  │  │features.py│ │ train.py     │  │  │
                     │  │  │predict.py │ │ anomaly.py   │  │  │
┌──────────────┐     │  │  │briefing.py│ │ ward_insights│  │  │
│  WhatsApp    │────▶│  │  └──────────┘ └──────────────┘  │  │
│  (Twilio)    │     │  └─────────────────────────────────┘  │
│              │     │                                       │
└──────────────┘     │  ┌────────────┐ ┌──────────────────┐  │
                     │  │ api/views  │ │ api/services/    │  │
┌──────────────┐     │  │ api/tasks  │ │ health_score.py  │  │
│  Cron Job    │────▶│  │ api/auth   │ │ report_generator │  │
│  (cron-job)  │     │  └────────────┘ └──────────────────┘  │
└──────────────┘     └──────────┬────────────────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │  PostgreSQL + PostGIS│
                     │  (Neon on Render)     │
                     │                      │
                     │  Ward (MultiPolygon) │
                     │  CivicMetrics        │
                     │  Complaint (Point)   │
                     │  PortalMetrics       │
                     │  WardPrediction      │
                     └─────────────────────┘
```

---

## Request Flow

```
┌──────────┐    GET /api/wards-geojson/
│  Browser │──────────────────────────────▶┐
│          │                               │
│  React   │   1. Django SPA catch-all     │
│  SPA     │      serves index.html        │
│          │   2. React Router loads page   │
│  Vite    │   3. Component fetches /api/*  │
│  dev:3000│   4. DRF returns JSON          │
└──────────┘◀──────────────────────────────┘
  proxy: /api ───┬──▶ Django :8000
                 │
                 └──▶ WhiteNoise serves /assets/*
```

---

## Project Structure

```
MumbaiUI/
├── Dockerfile                      # Multi-stage: Python backend + Node frontend
├── backend/
│   ├── build.sh                    # Render build script
│   ├── Dockerfile                  # Backend-only Docker image
│   ├── entrypoint.sh               # Startup: migrate, seed, train, gunicorn
│   ├── Procfile                    # Render process definition
│   ├── runtime.txt                 # Python 3.12.4
│   ├── requirements.txt            # Python dependencies
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py             # Django config (DB, auth, CORS, Twilio)
│   │   ├── urls.py                 # Root URL conf (SPA catch-all)
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py               # Celery app config
│   ├── api/
│   │   ├── models.py               # Ward, CivicMetrics, Complaint, PortalMetrics, WardPrediction, UserProfile
│   │   ├── serializers.py          # DRF serializers (Ward, User, Register, Login, WardPrediction)
│   │   ├── views.py                # 15+ API endpoints
│   │   ├── urls.py                 # API URL routing
│   │   ├── auth_views.py           # Register, login, profile, logout
│   │   ├── twilio_views.py         # WhatsApp conversation state machine
│   │   ├── tasks.py                # Celery tasks (sync, predict, retrain, reports)
│   │   ├── tests.py                # ML pipeline tests
│   │   ├── admin.py                # Django admin configuration
│   │   ├── services/
│   │   │   ├── health_score.py     # Sigmoid-weighted 0-100 health score
│   │   │   └── report_generator.py # fpdf2 PDF ward reports
│   │   └── management/commands/
│   │       ├── load_wards.py
│   │       ├── load_metrics.py
│   │       ├── update_health_scores.py
│   │       ├── train_models.py
│   │       ├── seed_complaints.py
│   │       └── generate_synthetic_2025.py
│   ├── ml/
│   │   ├── utils.py                # Model I/O, path constants
│   │   ├── features.py             # build_feature_matrix() with lag/rolling features
│   │   ├── train.py                # XGBoost risk, forecast, DBSCAN training + expanding-window CV
│   │   ├── predict.py              # generate_predictions() for both horizons
│   │   ├── preprocess.py           # scale_features() for inference
│   │   ├── anomaly.py              # Category/ward z-score anomaly detection
│   │   ├── briefing.py             # Template-based ward briefing generator
│   │   ├── recommendations.py      # Rule-based recommendation engine
│   │   ├── ward_insights.py        # Category-ward affinity scoring
│   │   └── models/                 # Trained .pkl files (gitignored)
│   ├── data/                       # CSV datasets (ward_metrics, escalation, category)
│   └── mumbai_wards.geojson        # 24-ward boundary polygons
├── frontend/
│   ├── package.json                # React 19, Leaflet, Recharts, React Router 7
│   ├── vite.config.js              # Vite 8 with /api proxy
│   ├── index.html
│   ├── _routes.json                # Cloudflare Pages route config
│   ├── functions/                  # Cloudflare serverless function
│   └── src/
│       ├── main.jsx                # App entry
│       ├── App.jsx                 # Router + Landing page (7 routes)
│       ├── config.js               # API_BASE url
│       ├── context/AuthContext.jsx  # Auth state management
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── TrackComplaint.jsx
│       │   ├── AdminPortal.jsx
│       │   ├── CouncillorPortal.jsx
│       │   ├── Login.jsx
│       │   ├── Signup.jsx
│       │   ├── PublicDashboard.jsx
│       │   └── ComplaintsMap.jsx
│       └── components/
│           ├── Navbar.jsx
│           ├── MumbaiMap.jsx        # Leaflet ward map
│           ├── WardDetailPanel.jsx  # Ward popup card
│           ├── ComplaintModal.jsx   # Complaint form modal
│           └── CouncillorTable.jsx  # Sortable councillor table
└── scripts/
    └── UrbanIQ_Interview_Cheat_Sheet.pdf
```

---

## Installation & Local Setup

### Prerequisites

- Python 3.12
- PostgreSQL 16 + PostGIS 3
- Node.js 20
- GDAL (for local PostGIS)

### 1. Clone the repository

```bash
git clone https://github.com/MohdSaadMa07/Urban-Infrastructure-Intelligence-Platform.git
cd Urban-Infrastructure-Intelligence-Platform
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database setup

```bash
# Create a PostGIS-enabled database
createdb muip
psql muip -c "CREATE EXTENSION postgis;"

# Run migrations
python manage.py migrate
```

### 4. Load seed data

```bash
python manage.py load_wards
python manage.py load_metrics --csv data/ward_metrics_multiyear_2025.csv
python manage.py update_health_scores
python manage.py seed_complaints
```

### 5. Train ML models

```bash
python manage.py train_models
```

### 6. Frontend setup

```bash
cd ../frontend
npm install
```

---

## Environment Variables

Create `backend/.env` from the template:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True

# Database (PostGIS on localhost)
DB_NAME=muip
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# On Render: set DATABASE_URL instead
# DATABASE_URL=postgres://user:pass@host:5432/db?sslmode=require

# Celery / Redis (optional for dev)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Cron API key (for daily retrain endpoint)
CRON_API_KEY=your-random-key

# GDAL paths (Windows only)
GDAL_LIBRARY_PATH=C:\Program Files\PostgreSQL\18\bin\libgdal-35.dll
GEOS_LIBRARY_PATH=C:\Program Files\PostgreSQL\18\bin\libgeos_c.dll
```

---

## Running the Backend

```bash
cd backend
python manage.py runserver
# API available at http://localhost:8000/api/
```

## Running the Frontend

```bash
cd frontend
npm run dev
# App available at http://localhost:5173
# Vite proxies /api/* to Django :8000
```

---

## Database Design

```
Ward
├── ward_no: Integer
├── ward_name: CharField
├── boundary: MultiPolygonField (PostGIS)
└── health_score: FloatField (nullable)

CivicMetrics
├── ward: FK → Ward (related_name='metrics')
├── year: PositiveSmallIntegerField
├── total_complaints: IntegerField
├── closed_complaints: IntegerField
├── escalated_complaints: IntegerField
├── avg_resolution_days: FloatField
├── per_capita_complaints: IntegerField
├── total_deliberations: IntegerField
├── per_capita_deliberations: IntegerField
└── avg_councillors: IntegerField
└── Unique: (ward, year)

Complaint
├── ward: FK → Ward
├── category: CharField (pothole, water, garbage, ...)
├── description: TextField
├── latitude: FloatField (nullable)
├── longitude: FloatField (nullable)
├── image: ImageField (nullable)
├── status: CharField (open, in_progress, resolved)
├── created_at: DateTimeField
├── resolved_at: DateTimeField (nullable)
├── sender_phone: CharField (nullable)
└── source: CharField (portal, whatsapp)

PortalMetrics
├── ward: FK → Ward
├── year: PositiveSmallIntegerField
├── total_complaints: IntegerField
└── resolved_complaints: IntegerField
└── Unique: (ward, year)

WardPrediction
├── ward: FK → Ward
├── prediction_date: DateField
├── predicted_risk: CharField (low, medium, high)
├── predicted_complaints: IntegerField
├── predicted_complaints_lower: IntegerField (nullable)
├── predicted_complaints_upper: IntegerField (nullable)
├── predicted_health_score: FloatField (nullable)
├── recommendation: TextField
├── top_features: JSONField (nullable)
└── model_version: CharField

UserProfile
├── user: OneToOne → auth.User
├── role: CharField (citizen, councillor, admin)
├── ward: FK → Ward (nullable)
└── phone: CharField
```

---

## API Documentation

### Public Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/` | API health check | — |
| `GET` | `/api/wards/` | List all wards | — |
| `GET` | `/api/wards-geojson/` | Ward boundaries as GeoJSON FeatureCollection | — |
| `GET` | `/api/identify-ward/?lat=&lng=` | Find ward by coordinates (PostGIS spatial query) | — |
| `GET` | `/api/health-scores/` | Ward health scores with breakdown | — |
| `GET` | `/api/trends/` | 5-year historical complaint trends | — |
| `GET` | `/api/hotspots/` | DBSCAN-clustered complaint hotspots | — |
| `GET` | `/api/councillors/` | Ward councillor deliberation scores | — |
| `GET` | `/api/complaints/` | Paginated complaint list (50/page) | — |
| `GET` | `/api/complaints/:id/` | Single complaint detail | — |
| `POST` | `/api/complaints/submit/` | File a new complaint | — |
| `GET` | `/api/public/wards/` | Public ward health summary | — |
| `GET` | `/api/public/summary/` | City-wide health aggregation | — |
| `GET` | `/api/public/config/` | WhatsApp config (number, link, status) | — |

### Authenticated Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/register/` | Create account (citizen/councillor) | — |
| `POST` | `/api/auth/login/` | Login, returns JWT tokens | — |
| `POST` | `/api/auth/login/refresh/` | Refresh JWT access token | — |
| `GET` | `/api/auth/profile/` | Current user profile | JWT |
| `POST` | `/api/auth/logout/` | Blacklist refresh token | JWT |
| `GET` | `/api/councillor/dashboard/` | Full ward dashboard with predictions, rankings, briefing | JWT (councillor) |
| `PATCH` | `/api/complaints/:id/status/` | Update complaint status, sends WhatsApp notification | JWT |
| `GET` | `/api/reports/download/` | Download ward PDF report | JWT (councillor) |

### Cron / Maintenance

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET/POST` | `/api/cron/retrain/?key=` | Sync complaints → retrain models → regenerate predictions | API key |

### WhatsApp Webhook

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/twilio/webhook/` | Twilio inbound message handler (XML TwiML response) |

---

## Geospatial Components

- **Ward boundaries** stored as `MultiPolygonField` (PostGIS) loaded from `mumbai_wards.geojson`
- **Spatial queries**: `boundary__contains=Point(lng, lat)` for coordinate-to-ward matching
- **Complaint hotspot clustering**: DBSCAN (`eps=0.005`, `min_samples=2`) on complaint coordinates
- **GeoJSON endpoint**: `/api/wards-geojson/` serves ward boundaries for Leaflet rendering
- **Frontend map**: `react-leaflet` with OpenStreetMap/CARTO tiles

---

## Authentication & Authorization

- **JWT-based** using `djangorestframework-simplejwt`
- Access token lifetime: 7 days; Refresh token: 30 days (with blacklisting)
- Three roles: `citizen`, `councillor`, `admin`
- Councillor dashboard restricted to users with `role=councillor` and a ward assignment
- Public endpoints use `AllowAny`; councillor endpoints use `IsAuthenticated` + role check

---

## ML Pipeline

### Models

| Model | Algorithm | Purpose | Outputs |
|-------|-----------|---------|---------|
| Risk | XGBClassifier | Ward risk classification | Low / Medium / High |
| Forecast N+1 | XGBRegressor (3 quantiles) | 1-year ahead complaint forecast | Point + 10th/90th percentile bounds |
| Forecast N+2 | XGBRegressor (3 quantiles) | 2-year ahead complaint forecast | Point + 10th/90th percentile bounds |
| Clustering | DBSCAN | Ward pattern/outlier detection | Cluster labels |

### Features

- Lag features: `complaints_lag1`, `complaints_lag2`, `resolution_days_lag1`
- Rolling features: `complaints_rolling_mean_3yr`, `complaint_growth_rate`
- Health: `prev_year_health_score`
- Engineered: `resolution_rate`, `escalation_rate`, `pending_complaints`
- Portal data: PortalMetrics totals merged into CivicMetrics at train time

### Training Pipeline

1. `build_feature_matrix(training=True)` → queries CivicMetrics + PortalMetrics, computes lag features
2. StandardScaler fit + save
3. XGBClassifier for risk (stratified 80/20 split)
4. XGBRegressor for N+1 forecast (3 quantile models)
5. XGBRegressor for N+2 forecast (3 quantile models)
6. DBSCAN clustering
7. Expanding-window time-series validation (folds: 2020–2024)

### Retraining Schedule

- **On deploy**: `entrypoint.sh` runs `python manage.py train_models`
- **Daily**: cron-job.org hits `/api/cron/retrain/?key=...` → syncs portal complaints → retrains all models → regenerates predictions

---

## Screenshots

> Screenshots are not included in this repository.  
> Visit the live deployment at [urban-infrastructure-intelligence-c000.onrender.com](https://urban-infrastructure-intelligence-c000.onrender.com) to see the platform in action.

| Page | Description |
|------|-------------|
| Landing | Hero section with Mumbai stats, how-it-works steps, interactive ward map, WhatsApp QR code, councillor table |
| Dashboard | Ward health score, complaint trends chart, prediction data, anomaly alerts |
| Ward Map | Leaflet choropleth with 24 ward polygons colour-coded by health score |
| Councillor Portal | Ward-specific dashboard with complaints, predictions, briefing, rankings, PDF export |
| Public Dashboard | City-wide health summary, best/worst wards |
| Admin Portal | User management (if implemented) |

---

## Future Improvements

- **Celery worker on Render** — Move retraining and PDF generation to a background worker instead of inline cron endpoint
- **Model versioning** — Store historical model snapshots for rollback if a retrain degrades performance
- **Prediction monitoring** — Track drift between predicted and actual complaint counts over time
- **Unit test coverage** — Expand test suite beyond the ML pipeline to cover API endpoints and auth flows
- **Performance budgets** — Add Lighthouse CI or similar to catch frontend regressions
- **CI/CD pipeline** — GitHub Actions for automated tests + linting on PR
- **Spatial index optimisation** — Ensure PostGIS GiST indexes on `Ward.boundary` for production-scale spatial queries

---

## Contributing

Contributions are welcome. Please open an issue first to discuss the change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

*Built for Mumbai. Powered by open civic data from the [Praja Foundation](https://praja.org/).*
