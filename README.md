# Store Locator Service (FastAPI)

Production-style Store Locator API implementing public search, authentication, RBAC, admin CRUD, and CSV upsert import.

## Implemented Requirements

- FastAPI + SQLAlchemy + PostgreSQL compatible setup
- Public search endpoint: `POST /api/stores/search`
  - Search by `address` / `postal_code` / `latitude+longitude`
  - Bounding box pre-filter + Haversine distance (`geopy`)
  - Filters: `radius_miles`, `services[]` (AND), `store_types[]` (OR), `open_now`
  - Response sorted by nearest distance with `is_open_now`
- Rate limiting with `slowapi` (100/hour + 10/minute)
- Geocoding integration with Nominatim + cache (Redis or in-memory fallback)
- Auth: JWT access token (15 min) + refresh token (7 days), login/refresh/logout
- OAuth2 password flow endpoint for Swagger authorize: `POST /api/auth/token`
- Refresh token persistence and revocation in database
- RBAC via users/roles/permissions/role_permissions
- Admin store APIs: create (auto-geocode when coordinates missing), list (pagination), get, patch, soft delete
- Admin CSV import endpoint: upsert + row validation report + transaction rollback on any row error
- Admin user APIs: create/list/update/deactivate
- Health endpoint: `GET /health`
- Unit tests for distance, bounding box, hours validation, password hashing

## Project Structure

- `app/main.py`: app bootstrap + middleware + router registration
- `app/models/`: SQLAlchemy models
- `app/schemas/`: request/response schemas
- `app/api/`: endpoint routers
- `app/services/geocoding.py`: geocoding + caching
- `app/utils/`: distance + hours utilities
- `scripts/seed_data.py`: seed roles/permissions/users
- `scripts/load_csv.py`: load or upsert stores CSV
- `tests/`: test suite

## Setup

1. Copy env file

```bash
cp .env.example .env
```

2. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Ensure PostgreSQL exists and update `DATABASE_URL` in `.env`

4. Run app (creates tables on startup)

```bash
uvicorn app.main:app --reload
```

5. Run migrations

```bash
alembic upgrade head
```

6. Seed RBAC + test users

```bash
python -m scripts.seed_data
```

7. Load stores data

```bash
python -m scripts.load_csv --file /Users/yutingbu/Downloads/stores_1000.csv
```

## Authentication Flow

1. Login with JSON body via `POST /api/auth/login` or use Swagger OAuth2 popup (`/api/auth/token`).
2. Use returned `access_token` (15 minutes) for protected endpoints.
3. When access token expires, call `POST /api/auth/refresh` with `refresh_token`.
4. Call `POST /api/auth/logout` to revoke refresh token in database.

## Distance Calculation Method

Search uses required **Bounding Box + Haversine** flow:

1. Compute latitude/longitude bounding box by `radius_miles`.
2. Query stores within box in SQL with active status filter.
3. Compute exact distance in Python with `geopy.geodesic`.
4. Filter by radius and sort by nearest.

## Database Schema Overview

Core tables:

- `stores`, `store_services`
- `users`, `roles`, `permissions`, `role_permissions`
- `refresh_tokens`

Required indexes included:

- `stores(latitude, longitude)`
- `stores(status)` partial index for active rows
- `stores(store_type)`
- `stores(address_postal_code)`
- `users(email)`
- `refresh_tokens(token_hash)`

## Sample Requests

- Public search: `POST /api/stores/search`
- OAuth2 login for docs: `POST /api/auth/token`
- JSON login: `POST /api/auth/login`
- Import stores CSV: `POST /api/admin/stores/import`

## Deployment (Render)

This repository includes `render.yaml` for the web service.

### Steps

1. Push repository to GitHub.
2. In Render, create:
   - PostgreSQL instance
   - Redis instance
3. Create a new Web Service from this repo (Blueprint or standard service).
4. Set required environment variables:
   - `DATABASE_URL` = Render Postgres connection string
   - `REDIS_URL` = Render Redis connection string
   - `SECRET_KEY` = strong random secret
   - `APP_ENV=production`
   - `ACCESS_TOKEN_EXPIRE_MINUTES=15`
   - `REFRESH_TOKEN_EXPIRE_DAYS=7`
   - `CORS_ORIGINS=*` (or your frontend domain)
5. Deploy. Start command runs migrations automatically:
   - `alembic upgrade head && gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT`
6. After first deploy, run one-time seed in Render shell:

```bash
python -m scripts.seed_data
```

7. Import store CSV using deployed API endpoint:
   - `POST /api/admin/stores/import`
   - Upload your local `stores_1000.csv` via Swagger UI on deployed `/docs`.

### Post-deploy verification

- `GET /health` returns status ok
- `GET /docs` is accessible
- Login + search + admin import work on production URL

## Default Seed Users

- Admin: `admin@test.com` / `TestPassword123!`
- Marketer: `marketer@test.com` / `TestPassword123!`
- Viewer: `viewer@test.com` / `TestPassword123!`

## Run Tests

```bash
pytest -q --cov=app --cov-report=term-missing
```

## API Docs

- Swagger UI: `http://localhost:8000/docs`
- Architecture doc: `docs/ARCHITECTURE.md`
- Schema doc: `docs/SCHEMA.md`
