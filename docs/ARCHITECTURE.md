# Architecture Overview

## Request Flow

1. Client calls FastAPI endpoint.
2. Public search endpoints run validation, optional geocoding, bounding-box SQL filter, then exact distance calculation.
3. Protected endpoints validate JWT access token, then RBAC permission.
4. SQLAlchemy handles persistence to PostgreSQL.
5. Geocoding cache uses Redis first, with in-memory fallback for local development.

## Main Components

- `app/main.py`: app creation, middleware, routers.
- `app/api/`: endpoint layer (auth, stores, users).
- `app/api/dependencies.py`: auth + permission checks.
- `app/services/geocoding.py`: external geocoding + caching.
- `app/utils/distance.py`: bounding box + geodesic distance.
- `app/utils/hours.py`: store-hours parsing and open-now logic.
- `app/models/`: database entities and indexes.
- `scripts/`: operational scripts for seed/import.

## Security Design

- Password hashing via `bcrypt`.
- Access token (15m) + refresh token (7d).
- Refresh token hash stored for revocation.
- Permission-based RBAC checks on internal APIs.
- Rate limiting on public search endpoint.
