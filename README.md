# Breathe ESG Platform

> **Enterprise ESG Operations Platform** — ingest, normalize, validate, review, and report on Scope 1/2/3 emissions data at scale.

![Platform Status](https://img.shields.io/badge/status-production--ready-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Stack](https://img.shields.io/badge/stack-Django%20%2B%20React%20%2B%20PostgreSQL-brightgreen)

---

## Architecture Overview

```
breathe-esg-platform/
├── backend/                  # Django REST API
│   ├── core/                 # Settings, URLs, middleware, Celery
│   ├── apps/
│   │   ├── authentication/   # Custom User model, JWT auth
│   │   ├── tenants/          # Multi-tenancy, plan management
│   │   ├── ingestion/        # Upload, parsing, pipeline orchestration
│   │   ├── emissions/        # EmissionRecord CRUD, review workflow
│   │   ├── audit/            # Immutable audit trail
│   │   └── analytics/        # Aggregation, trend, scope summaries
│   ├── utils/                # Unit normalizer, emission factors, date parser
│   └── requirements.txt
├── frontend/                 # React + TypeScript + TailwindCSS
│   └── src/
│       ├── pages/            # Login, Dashboard, Upload, Review, Flagged, Audit, Sources
│       ├── components/       # Reusable UI: badges, layout, charts
│       ├── services/         # Axios client + API layer
│       ├── store/            # Zustand auth store
│       └── types/            # TypeScript types
├── sample_data/              # Realistic CSV test files
└── docs/                     # Extended documentation
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + DRF 3.14 |
| Auth | JWT (SimpleJWT) with refresh + blacklist |
| Database | PostgreSQL (SQLite for dev) |
| Data Processing | Pandas + custom parsers |
| Frontend | React 18 + TypeScript |
| State | Zustand + React Query v5 |
| Styling | TailwindCSS 3 |
| Charts | Recharts |
| Upload | react-dropzone |
| Background Tasks | Celery + Redis |

---

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: set DATABASE_URL, SECRET_KEY

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_data

# Start dev server
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env

# Start dev server
npm run dev
```

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@breathe.io | Admin@123! |
| Analyst | analyst@breathe.io | Analyst@123! |
| Reviewer | reviewer@breathe.io | Review@123! |
| Viewer | viewer@breathe.io | View@123! |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/` | JWT login |
| POST | `/api/v1/auth/register/` | User registration |
| GET | `/api/v1/auth/me/` | Current user |
| POST | `/api/v1/ingestion/uploads/upload/` | Upload ESG file |
| GET | `/api/v1/ingestion/uploads/` | List source files |
| GET | `/api/v1/emissions/records/` | List emission records |
| POST | `/api/v1/emissions/records/{id}/review/` | Approve/reject/note |
| POST | `/api/v1/emissions/records/bulk-action/` | Bulk operations |
| GET | `/api/v1/emissions/summary/` | Dashboard stats |
| GET | `/api/v1/audit/logs/` | Audit trail |
| GET | `/api/v1/analytics/scope-trend/` | Monthly scope breakdown |

---

## Environment Variables

See `.env.example` for full list. Key variables:

```
SECRET_KEY=...
DATABASE_URL=postgres://user:pass@host:5432/dbname
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
REDIS_URL=redis://localhost:6379/0
```

---

## Deployment

### Backend → Render

1. Connect GitHub repo to Render
2. Create Web Service from `backend/` directory
3. Build command: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
4. Start command: `gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
5. Add PostgreSQL database addon
6. Set all environment variables

### Frontend → Vercel

1. Import GitHub repo
2. Set root directory to `frontend/`
3. Framework preset: Vite
4. Set `VITE_API_BASE_URL=https://your-render-backend.onrender.com/api/v1`

---

## Supported Data Formats

| Source | Format | Example File |
|--------|--------|--------------|
| SAP Fuel/Procurement | CSV/XLSX | `sample_data/sap_fuel_export_q1_2024.csv` |
| Utility Electricity | CSV/XLSX | `sample_data/utility_electricity_q1_2024.csv` |
| Corporate Travel (Concur) | CSV/XLSX | `sample_data/corporate_travel_q1_2024.csv` |

---

## Screenshots

_[Coming soon — deploy and screenshot]_

---

## Assumptions

1. Single fiscal year per reporting cycle
2. All emissions calculated in kgCO2e; UI converts to tCO2e above 1000 kg
3. GHG Protocol 2023 emission factors used as defaults
4. Celery/Redis are optional; background threading is used as fallback
5. S3 file storage is optional; local media/ used for dev

