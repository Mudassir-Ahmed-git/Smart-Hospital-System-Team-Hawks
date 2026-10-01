# Smart Hospital Bed & Emergency Capacity System: Backend

FastAPI + SQLAlchemy + PostgreSQL + JWT + scikit-learn. Built to plug straight into the React frontend
(`smart-hospital-frontend`) and to cover every endpoint in the project brief.

## Run it

### Option A: Docker (Postgres included)
```bash
docker compose up --build
```
API: http://localhost:8000  ·  Swagger: http://localhost:8000/docs

### Option B: local Python 3.11
```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit DATABASE_URL (Postgres) or use the SQLite line for zero setup
alembic upgrade head            # create tables
python -m app.seed              # demo hospitals, beds, users, history   (--reset to wipe & reseed)
uvicorn app.main:app --reload --port 8000
```

### Connect the frontend
In `smart-hospital/.env`:
```
VITE_API_URL=http://localhost:8000/api
```
then `npm run dev`. The frontend falls back to its built-in demo data when the API is unreachable, so if you
see mock data, check this URL and the backend logs.

## Demo accounts (password `demo1234`)
| Email | Role | Notes |
|---|---|---|
| patient@demo.com | patient | has 3 sample referrals |
| staff@demo.com | hospital | staff of Riverside General (id 1), has 4 pending emergencies |
| staff2@demo.com | hospital | staff of St. Mary (id 2) |
| ambulance@demo.com | ambulance | fleet A-12, A-07, A-03, A-15 |
| admin@demo.com | admin | full access |

Role names: `patient`, `hospital` (= Hospital Staff), `ambulance` (= Ambulance Coordinator), `admin`.
The long forms from the brief ("Hospital Staff", "Ambulance Coordinator") are accepted on input.

## Project layout
```
app/
  main.py            app, CORS, error handlers, WebSocket, /health
  config.py          settings (env vars)
  seed.py            sample data
  database/          engine + session
  models/            user, hospital, bed, patient, emergency, referral, capacity_history, ambulance
  schemas/           Pydantic request/response models (JSON is camelCase for React)
  routers/           auth, hospitals, beds, patients, emergency, referrals, analytics, ai
  services/          hospital, bed, referral, notification, ai, analytics   (all business logic)
  ai/                recommender (scoring), predictor (scikit-learn), chatbot
  utils/             security (JWT, bcrypt, RBAC), validators, helpers
migrations/          Alembic (0001_initial_schema)
tests/               13 end-to-end tests (pytest)
```

## Endpoints
All under `/api`. 🔒 = needs `Authorization: Bearer <token>`.

| Area | Endpoint | Who |
|---|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` 🔒 | public / any |
| Hospitals | `GET /hospitals`, `GET /hospitals/{id}` 🔒 | any |
| | `POST /hospitals` | admin |
| | `PUT /hospitals/{id}/capacity` | staff of that hospital, admin |
| Beds | `GET /beds/available` | any |
| | `GET /beds`, `POST /beds`, `PUT /beds/{id}` | staff (own hospital), admin |
| Patient | `POST /patient/request-bed` (alias `POST /bed-requests`), `GET /patient/status` | patient |
| Emergency | `POST /emergency/request` | patient, ambulance, hospital |
| | `GET /emergency/nearby-hospitals` | any |
| | `GET /emergency-requests`, `PUT /emergency/{id}/status` | hospital (+ambulance read) |
| Referrals | `POST /referral/create`, `PUT /referral/{id}/status` | ambulance, hospital |
| | `GET /referrals` | any (scoped to the caller) |
| Ambulances | `GET /ambulances`, `PUT /ambulances/{id}` | ambulance, hospital |
| Analytics | `GET /analytics/dashboard`, `/capacity`, `/occupancy`, `/alerts`, `GET /reports` | hospital/ambulance (own scope), admin (network) |
| AI | `POST /ai/recommend`, `GET /ai/predict`, `POST /ai/chat` (alias `POST /assistant`) | any |
| Live | `WS /ws/capacity?token=<JWT>` | any |

Admin passes every role check. Hospital staff are always restricted to their own hospital.

## How the business rules work
- **Capacity is derived, never stored.** Every bed is a row; "available" = count of `Available` beds. So
  availability can't drift. Admit → bed `Occupied` (available −1), discharge → `Available` (+1).
  `PUT /hospitals/{id}/capacity` (the "Update capacity" page) flips bed statuses to match what staff enter.
- **Reservation.** Accepting a request reserves a real bed (`Reserved`) using `SELECT … FOR UPDATE SKIP LOCKED`,
  so two staff accepting at once never get the same bed. Reject/cancel releases it; handover marks it `Occupied`.
- **Recommendation score** (`app/ai/recommender.py`):
  `0.40·availability + 0.30·distance + 0.20·emergency capability + 0.10·waiting time`, each 0–1.
  Hospitals with no free bed of the requested type are excluded, and so are closed-ER hospitals for Critical
  patients. Responses include the score breakdown and a plain-English `reason`.
- **Critical first.** Emergency lists sort Critical → Urgent → Normal (oldest first). A non-critical request
  can't take the last free bed while Critical patients are waiting for that bed type (409; `force: true` overrides).
- **Capacity monitoring** (`GET /analytics/alerts`, also in the dashboard): bed shortage (<15% free),
  ICU overload (≥85% occupied), emergency spike (≥3 in 2h and ≥2× normal).
- **Forecast** (`GET /ai/predict`): Ridge regression on daily occupancy (trend + weekly seasonality) from
  `capacity_history`, giving e.g. *"ICU demand may increase 6% tomorrow (to ~80% occupied)"*. History is written
  automatically whenever capacity changes.
- **Chatbot** is rule-based over live data, so it can't invent beds. Swap `ai/chatbot.detect` for an LLM if wanted.
- **Live updates.** `capacity_updated`, `new_request`, `status_changed` events are pushed over the WebSocket.

## Notes on matching the frontend
- JSON is camelCase (`distanceKm`, `bedType`); snake_case input is also accepted.
- Priorities: the brief says Normal/Urgent/Critical, the UI sends Normal/High/Critical. Both are accepted;
  `High` is stored as `Urgent`.
- Bed statuses include `Cleaning` (the Manage Beds page uses it) besides Available/Occupied/Reserved.
- Added an `ambulances` table (the Ambulance dashboard needs a fleet list), and an optional `Operation Theater`
  bed type from the brief (only shown for hospitals that have OTs).
- Distances are measured from `?lat=&lng=` if sent, otherwise from `DEFAULT_LATITUDE/LONGITUDE` (Karachi).

## Before production
- Set a strong `SECRET_KEY` and `ALLOW_OPEN_ROLE_REGISTRATION=false` (right now anyone can register as admin, for the demo).
- Restrict `CORS_ORIGINS`; add rate limiting on `/auth/login`; serve behind HTTPS.
- Reports are aggregated in Python (fine for a hackathon-scale DB); move to SQL aggregates/materialised views at scale.

## Tests
```bash
pytest -q          # uses a temporary SQLite DB; set DATABASE_URL to run against Postgres
```
