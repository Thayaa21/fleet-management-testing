# {{APP_NAME}} — Backend

FastAPI + SQLAlchemy 2.x + Alembic. SQLite for local dev, Postgres-ready via
`DATABASE_URL`. JWT auth with roles.

## Setup

```bash
cd backend
pip install -r requirements.txt
python -m alembic upgrade head     # create/upgrade the schema
python -m app.seed_users           # seed dev users (see credentials below)
python -m app.seed_terminals       # seed terminals + US cross-border points
uvicorn app.main:app --reload --port 8000
```

All backend commands run from the `backend/` directory (imports are rooted there).

## Configuration

Settings load from environment / a `.env` file in `backend/` (see `app/config.py`):

- `DATABASE_URL` (default `sqlite:///./tms.db`)
- `JWT_SECRET` (override in every non-dev environment)
- `JWT_ALGORITHM` (default `HS256`), `ACCESS_TOKEN_EXPIRE_MINUTES`
- `CORS_ORIGINS` (comma-separated; default allows the Vite dev server)

## Endpoints

- `GET  /health` — liveness check.
- `POST /auth/login` — `{email, password}` → `{access_token, token_type, user}`.
- `GET  /auth/me` — current user (requires bearer token).
- `GET  /auth/staff-check` — staff-only probe used to exercise role enforcement.

Master data (staff only; all support `?page=&page_size=&q=` + filters, return
`{items,total,page,page_size}`, 409 on duplicate identifiers, soft delete):
- `/customers`, `/locations`, `/drivers`
- `/equipment/tractors`, `/equipment/trailers`, `/equipment/devices`

Shipments & history (staff only):
- `/shipments` (CRUD; `POST /shipments/{id}/cancel`; no hard delete). List filters:
  `status, customer_id, origin_terminal_id, destination_terminal_id, pickup_from,
  pickup_to, has_data_quality_flags, stale_for_hours` + `q`.
- `POST /shipments/{id}/milestones` (append-only; recomputes status),
  `GET /shipments/{id}/timeline`, `GET /shipments/{id}/handling-units`.
- `POST /milestones/{id}/void` (void + recompute).
- `GET /audit?entity_type=&entity_id=`.

Import `orders.csv` (from `backend/`, dirty data is flagged not dropped):
```bash
python -m app.import_orders            # uses repo-root orders.csv
```

All errors use the envelope `{"error": {"code", "message", "details"}}` and echo
an `X-Request-ID` header.

## Dev credentials (DEV ONLY)

Created by `python -m app.seed_users`:

| Role          | Email                     | Password      |
|---------------|---------------------------|---------------|
| admin         | admin@example.com         | admin123      |
| dispatcher    | dispatcher@example.com    | dispatch123   |
| dock          | dock@example.com          | dock123       |
| customer_user | customer@example.com      | customer123   |

The `customer_user` is linked to `customer_id = 1`.

## Tests

```bash
cd backend
python -m pytest
```

## Migrations

```bash
cd backend
python -m alembic revision --autogenerate -m "describe change"
python -m alembic upgrade head
```
