# Kiro Build Plan: Lean LTL TMS (from fleet-management-testing)

How to use this file:
1. Put this file in the repo at `docs/KIRO_TMS_PLAN.md`.
2. Run **Batch 0** first. It creates Kiro steering files so every later batch has the same context.
3. Run one batch at a time. Paste the batch's prompt into Kiro chat. For Batches 3 to 7 and 10, use **Spec mode** so Kiro writes requirements, design, and tasks before coding. Review the spec before letting it implement.
4. Do not start the next batch until the current batch's acceptance criteria pass and the app runs.
5. Replace `{{APP_NAME}}` with your new brand name everywhere.

---

## GLOBAL RULES (paste at the top of every batch prompt)

```
Global rules for this task:
- This repo is being converted into {{APP_NAME}}, a lean, practical TMS (transportation management system) for an LTL (less-than-truckload) carrier. It will later be used as the system of record for an AI agent that detects and fixes shipment data gaps (missing milestones, wrong equipment IDs, broken telematics links) and API exceptions (bad payloads, expired auth, IP not allowlisted).
- Read docs/KIRO_TMS_PLAN.md and the files in .kiro/steering/ before making changes.
- Only do the work in the current batch. Do not start work from later batches.
- Keep the app runnable at the end of the batch: backend starts, frontend builds, tests pass.
- Prefer boring, readable code over clever code. No decorative animations, 3D, particle effects, glow, or marketing visuals.
- Every data change made by the system must be traceable (see audit_log from Batch 4 onward).
- Do not hardcode customer names like "Polaris" or "Coca-Cola" in code. Use them only in seed data.
- If something is ambiguous, list your assumption in the summary instead of guessing silently. If a deletion is risky, ask before deleting.
- At the end, output: (1) files added/changed/deleted, (2) how to run and test, (3) assumptions, (4) anything left undone.
```

---

## BATCH 0: Repo audit and steering files (no feature code)

```
[Paste GLOBAL RULES]

Goal: Understand the current repo and create Kiro steering files. Do not change application code in this batch.

Tasks:
1. Audit the repo and write docs/AUDIT.md containing:
   - Every page, component, hook, util, backend module, and dependency, with one line on what it does.
   - For each, a verdict: KEEP, SIMPLIFY, REPLACE, or REMOVE, based on the target described below.
   - A list of all data currently coming from src/data/mockData.js and which future backend table it maps to.
   - Note that orders.csv in the repo root is LTL-shaped (freight class, skids, stackable, origin/dest country) and will seed the shipments table later.

2. Create .kiro/steering/product.md:
   - {{APP_NAME}} is a TMS for an LTL carrier operating terminals in Canada with cross-border US lanes.
   - Users: Admin, Dispatcher, Terminal/Dock operator, Customer (shipper) via portal, Customer systems via API.
   - Core objects: customers, locations/terminals, shipments (probills), handling units, equipment (tractors, trailers), telematics devices, drivers, pickups, trips/linehaul, manifests, milestones (status events), documents, exceptions (OS&D), rates, freight bills, API keys, webhooks, integration logs, audit log.
   - Downstream purpose: clean, auditable data and APIs that an AI agent can read and correct.

3. Create .kiro/steering/tech.md:
   - Frontend: React + Vite + React Router. Plain CSS variables, one neutral light theme with a dark option. Leaflet for maps. No Three.js.
   - Backend: FastAPI, Pydantic v2, SQLAlchemy 2.x ORM, Alembic migrations. SQLite for local dev, Postgres-ready (no SQLite-only SQL).
   - Auth: JWT for users (roles), API keys for customer systems.
   - Testing: pytest (+ httpx TestClient) for backend, Vitest for frontend.
   - Timestamps stored in UTC ISO 8601. Weights in lbs, dimensions in inches (store unit fields where relevant).

4. Create .kiro/steering/structure.md describing the target layout:
   backend/
     app/main.py, app/config.py, app/db.py
     app/models/        (SQLAlchemy models, one file per domain)
     app/schemas/       (Pydantic schemas)
     app/routers/       (one router per domain)
     app/services/      (business logic, state machine, rating, webhooks)
     app/integrations/  (telematics ingest, customer API, outbound webhooks)
     alembic/
     tests/
   data/
     generator/         (dataset generator, Batch 10)
     output/            (generated CSVs, gitignored)
   src/
     api/               (typed API client)
     pages/ops/         (internal screens)
     pages/portal/      (customer portal)
     components/        (tables, forms, timeline, map)

Acceptance criteria:
- docs/AUDIT.md exists and covers every file in src/ and backend/.
- Three steering files exist.
- No application code changed.
```

---

## BATCH 1: Strip the flashy features

```
[Paste GLOBAL RULES]

Goal: Remove decorative and out-of-scope features so what remains is a plain internal app shell. Use docs/AUDIT.md verdicts.

Remove completely:
- 3D Digital Twin: FleetTwin page, TruckModel component, and the dependencies three, @react-three/fiber, @react-three/drei, @react-three/postprocessing.
- Backhaul Load Marketplace: LoadMarketplace page, src/utils/marketplace.js and its tests, backend/matching.py, the /marketplace/match endpoint, marketplace.db tables (opportunities, bids, awards), and backend/seed.py marketplace seeding.
- Marketing landing page: animated freight network map, pricing tiers, FAQ, CTAs. Replace with a direct redirect to the login page.
- Simulated OCR terminal animation in BillingPipeline.
- Cost Intelligence page (will be replaced by simple reports later if needed).
- "AI-scored" dispatch scoring, fake AI recommended actions in alerts, and any randomized fake live data.
- Any bloom, glow, pulse, particle, or animated background CSS.

Simplify:
- Replace the amber dark "premium" theme with a neutral, readable theme: white/gray surfaces, one accent color, clear table styles, a dark mode toggle using CSS variables. Keep {{APP_NAME}} branding.
- Keep the Sidebar and layout shell. Sidebar sections for now: Shipments, Dispatch, Equipment, Drivers, Customers, Integrations, Settings. Pages that don't exist yet show a simple "Coming in a later batch" placeholder.
- Keep the login chooser, admin login, and customer login screens visually, but they can stay mock for now (real auth is Batch 2).
- Remove the vite base '/Load-Lorry/' unless it's needed for deployment; document the decision.

Keep:
- Leaflet and react-leaflet (used for maps later).
- src/data/mockData.js for now, but trim it to what remaining pages still use. It will be deleted in Batch 9.
- US_CITIES list: keep, and add major Canadian cities with lat/lng (Toronto, Mississauga, Montreal, Ottawa, Winnipeg, Regina, Calgary, Edmonton, Vancouver, Halifax, Quebec City, London ON, Windsor, Hamilton, Moncton).

Acceptance criteria:
- npm install, npm run build, npm run lint, npm test all pass.
- uvicorn backend starts and GET /health works.
- No references remain to three.js, marketplace, landing animations, or OCR animation (verify with a grep and include the grep command in your summary).
- package.json no longer lists removed dependencies.
```

---

## BATCH 2: Backend foundation and real auth

```
[Paste GLOBAL RULES]

Goal: Restructure the backend into the layout in .kiro/steering/structure.md and add real authentication.

Tasks:
1. Create backend/app/ with main.py, config.py (pydantic-settings, reads .env), db.py (SQLAlchemy engine + session dependency).
2. Set up Alembic with an initial migration. DATABASE_URL defaults to sqlite:///./tms.db and must work with Postgres.
3. Users and roles:
   - users table: id, email, password_hash (bcrypt/argon2), full_name, role (admin, dispatcher, dock, customer_user), customer_id (nullable, required for customer_user), is_active, created_at, updated_at.
   - POST /auth/login returns JWT access token. GET /auth/me.
   - Role-based dependency: require_role("admin", "dispatcher", ...).
   - customer_user can only ever see data for their own customer_id. Enforce this in a shared query helper, not per endpoint.
4. Standard error format for all endpoints: {"error": {"code": "...", "message": "...", "details": {...}}}.
5. Request ID middleware: every request gets an X-Request-ID (generate if missing), included in logs and error responses.
6. CORS configured from settings.
7. Seed script backend/app/seed_users.py creating one user per role (document credentials in README, dev only).
8. Frontend: replace sessionStorage mock auth with real login against the API. Store the token in memory plus a refresh-on-load call to /auth/me. Route guards by role. Customer users go to the portal, staff go to ops.
9. pytest setup with a test database and fixtures for each role.

Acceptance criteria:
- Login works for each role from the UI.
- A customer_user calling a staff endpoint gets 403.
- Tests cover login success, bad password, role checks.
```

---

## BATCH 3: Core master data (use Spec mode)

```
[Paste GLOBAL RULES]

Goal: Build the master data every TMS needs, with full CRUD APIs and simple list/detail/edit screens.

Tables (SQLAlchemy models + Alembic migration + Pydantic schemas + routers + tests):

customers
- id, account_number (unique), name, type (shipper, consignee, both, third_party_payer), billing_address fields, contact name/email/phone, payment_terms, credit_hold (bool), status (active/inactive), notes, created_at, updated_at.

locations
- id, customer_id (nullable), name, type (customer_site, terminal, cross_dock, customs_point), address fields, city, province_state, postal_zip, country (CA/US), lat, lng, timezone, dock_hours, appointment_required (bool), geofence_radius_m (default 300).
- Seed terminals: Mississauga (hub), Montreal, Ottawa, Winnipeg, Calgary, Edmonton, Vancouver, plus 3 US cross-border points.

tractors
- id, unit_number (unique), vin, plate, home_terminal_id, status (available, in_use, maintenance, out_of_service), telematics_device_id (nullable FK).

trailers
- id, trailer_number (unique), type (dry_van, reefer, flatbed, pup, straight_truck_box), length_ft, capacity_lbs, capacity_cuft, home_terminal_id, current_location_id, status, telematics_device_id (nullable FK).

telematics_devices
- id, provider (e.g. samsara, geotab, mock), device_serial (unique), attached_to_type (tractor/trailer/none), attached_to_id, status (active, inactive, unassigned), last_ping_at, installed_at.

drivers
- id, employee_number, full_name, phone, license_number, license_province_state, license_expiry, home_terminal_id, type (city_pd, linehaul), status, hos_hours_remaining (simple number for now).

Validation rules:
- Unit numbers, trailer numbers, device serials, and account numbers are unique and trimmed; normalize to uppercase.
- A telematics device can be attached to only one asset at a time. Attaching a new one detaches the old one (record this in audit_log once it exists in Batch 4; for now leave a TODO).
- Soft delete (status inactive) instead of hard delete for all master data.

Frontend:
- Customers, Locations, Equipment (tabs: Tractors, Trailers, Devices), Drivers pages.
- Each: searchable, sortable, paginated table; detail view; create/edit form with inline validation errors from the API.

Acceptance criteria:
- CRUD endpoints with pagination (?page=&page_size=), search (?q=), and filters work and are tested.
- Unique-constraint violations return a 409 with the standard error format.
```

---

## BATCH 4: Shipments, milestones, state machine, audit log (use Spec mode)

This is the heart of the system. Take time on the spec.

```
[Paste GLOBAL RULES]

Goal: Model LTL shipments (probills), their handling units, their status history (milestones), and a full audit log.

Tables:

shipments
- id, probill_number (unique, format like P0000123), bol_number, customer_id (bill-to), shipper_location_id, consignee_location_id, service_level (standard, guaranteed, expedited), pickup_date, pickup_window_start/end, delivery_appointment_start/end (nullable), requested_delivery_date, estimated_delivery_at, actual_delivery_at,
- total_pieces, total_weight_lbs, total_cuft, freight_class (50 to 500), nmfc (nullable), hazmat (bool), stackable (bool), is_urgent (bool),
- reference numbers: po_numbers (JSON list), customer_reference,
- cross-border: is_cross_border (bool), customs_broker (nullable), pars_paps_number (nullable),
- current_status (see state machine), current_location_id, current_trailer_id (nullable), current_trip_id (nullable, FK added in Batch 5),
- created_at, updated_at, created_by, source (portal, api, edi, manual, import).

handling_units
- id, shipment_id, type (skid, pallet, crate, loose), quantity, length_in, width_in, height_in, weight_lbs, stackable, description, label_barcode (unique).

milestones
- id, shipment_id, event_code, event_at (when it happened), recorded_at (when the system learned about it), location_id (nullable), lat/lng (nullable), trailer_id (nullable), tractor_id (nullable), driver_id (nullable),
- source (driver_scan, dock_scan, telematics, manual, api, edi, agent, system),
- edi_214_code (nullable mapping, e.g. X3, AF, X6, X1, D1, SD, AG),
- notes, created_by, is_voided (bool), voided_reason.
- Milestones are append-only. Corrections happen by voiding and adding, never by editing in place.

event_code enum (internal):
PICKUP_REQUESTED, PICKUP_DISPATCHED, ARRIVED_AT_PICKUP, PICKED_UP, ARRIVED_AT_TERMINAL, LOADED_ON_TRAILER, DEPARTED_TERMINAL, IN_TRANSIT, ARRIVED_AT_DESTINATION_TERMINAL, UNLOADED, OUT_FOR_DELIVERY, ARRIVED_AT_DELIVERY, DELIVERED, DELIVERY_ATTEMPTED, APPOINTMENT_SET, DELAYED, EXCEPTION, CUSTOMS_HOLD, CUSTOMS_RELEASED, CANCELLED.

audit_log
- id, entity_type, entity_id, action (create, update, void, attach, detach, delete), changed_fields (JSON: {field: [old, new]}), actor_type (user, system, api_client, agent), actor_id, reason (nullable), request_id, created_at.
- Implement as a service/SQLAlchemy event hook so every create/update on shipments, milestones, assignments, equipment, and devices writes an audit row automatically. Backfill the Batch 3 TODO for device attach/detach.

State machine (services/shipment_state.py):
- Define allowed transitions of shipments.current_status driven by milestones, e.g. BOOKED -> PICKUP_DISPATCHED -> PICKED_UP -> AT_ORIGIN_TERMINAL -> IN_LINEHAUL -> AT_DESTINATION_TERMINAL -> OUT_FOR_DELIVERY -> DELIVERED, plus EXCEPTION, CANCELLED.
- Adding a milestone updates current_status only if the transition is valid.
- Out-of-order milestones (event_at earlier than the latest one) are accepted but flagged: store them, recompute status from the full ordered history, and log a warning. Late data is normal in trucking; do not reject it.
- Impossible sequences (DELIVERED before PICKED_UP with no pickup event) are accepted and create an exception record later (Batch 8); for now, flag with a data_quality_flags JSON field on shipments.

Endpoints:
- CRUD for shipments (no hard delete; cancel instead).
- GET /shipments with filters: status, customer, origin/destination terminal, date ranges, has_data_quality_flags, stale_for_hours (no milestone in N hours while not delivered).
- POST /shipments/{id}/milestones, POST /milestones/{id}/void.
- GET /shipments/{id}/timeline returns milestones ordered by event_at plus audit entries.
- GET /audit?entity_type=&entity_id=.

Import:
- Script to import orders.csv into customers, locations, and shipments (map columns; document any mapping assumptions).

Frontend:
- Shipments list with the filters above and status chips.
- Shipment detail: header info, handling units, a vertical timeline of milestones (show source and recorded_at vs event_at difference), audit tab, and "Add milestone" / "Void milestone" actions for staff.

Acceptance criteria:
- Tests for valid transitions, out-of-order handling, voiding, and audit rows being created.
- The stale_for_hours filter works (this is the first data-gap detector).
```

---

## BATCH 5: Operations: pickups, trips, manifests, equipment assignment (use Spec mode)

```
[Paste GLOBAL RULES]

Goal: Model how freight physically moves in LTL: picked up locally, consolidated at a terminal, moved on linehaul trips, delivered locally. This is where the shipment-to-equipment link lives, which the agent depends on.

Tables:

pickup_requests
- id, customer_id, location_id, requested_date, window_start/end, expected_pieces, expected_weight_lbs, status (requested, dispatched, completed, missed, cancelled), assigned_driver_id, assigned_tractor_id, notes, created_via (portal, api, phone, manual).

trips
- id, trip_number (unique), type (pickup_delivery, linehaul), origin_location_id, destination_location_id, planned_departure_at, planned_arrival_at, actual_departure_at, actual_arrival_at, tractor_id, driver_id, status (planned, dispatched, in_progress, completed, cancelled).

trip_trailers
- id, trip_id, trailer_id, position (lead, pup), hooked_at, dropped_at.

manifests
- id, trailer_id, trip_id (nullable), origin_location_id, destination_location_id, status (open, closed, in_transit, arrived, unloaded), closed_at.

manifest_items
- id, manifest_id, shipment_id, handling_units_loaded, loaded_at, loaded_by, unloaded_at, unloaded_by.

Business rules (services/operations.py):
- Loading a shipment on a manifest sets shipments.current_trailer_id and writes a LOADED_ON_TRAILER milestone (source=dock_scan), both audited.
- Dispatching a trip writes DEPARTED_TERMINAL for every shipment on its trailers' open manifests. Arriving writes ARRIVED_AT_DESTINATION_TERMINAL.
- Unloading clears current_trailer_id and writes UNLOADED.
- Equipment IDs entered by users are normalized (trim, uppercase). If a trailer_number does not resolve, return 422 with code UNKNOWN_EQUIPMENT_ID and include up to 5 closest matches (Levenshtein distance <= 2) in details. Do not auto-pick one.
- A trailer cannot be on two open manifests at once (409).

Endpoints:
- CRUD for pickups, trips, manifests.
- POST /manifests/{id}/load {shipment_id or probill_number, trailer_number}
- POST /manifests/{id}/unload
- POST /trips/{id}/dispatch, POST /trips/{id}/arrive
- GET /equipment/trailers/{id}/contents (shipments currently on the trailer)
- GET /equipment/tractors/{id}/current-trip

Frontend:
- Dispatch board: today's pickups (by terminal), trips grouped by status, drag or select to assign driver/tractor.
- Dock screen: pick a trailer, scan/type probill numbers to load/unload (a simple input with Enter to submit; show fuzzy-match suggestions on unknown IDs).
- Trip detail: trailers, manifests, shipments, timeline.

Acceptance criteria:
- End-to-end test: create shipment -> pickup -> load at origin terminal -> dispatch linehaul -> arrive -> unload -> out for delivery -> delivered, with correct milestones and audit rows at each step.
```

---

## BATCH 6: Telematics ingestion and live positions (use Spec mode)

```
[Paste GLOBAL RULES]

Goal: Receive GPS data from telematics providers and tie it to equipment, and through equipment, to shipments.

Tables:

gps_pings
- id, device_id, received_at, recorded_at, lat, lng, speed_kph, heading, odometer_km (nullable), engine_on (nullable), raw_payload (JSON).
- Index on (device_id, recorded_at).

telematics_ingest_log
- id, received_at, provider, http_status_returned, device_serial (as sent), resolved_device_id (nullable), error_code (nullable: UNKNOWN_DEVICE, DEVICE_UNASSIGNED, MALFORMED_PAYLOAD, AUTH_FAILED, DUPLICATE), raw_payload.

Endpoints:
- POST /integrations/telematics/{provider}/webhook
  - Authenticated by a shared secret header per provider (store in settings).
  - Accepts a batch of pings. Validates each; stores valid ones; logs every attempt (success or failure) in telematics_ingest_log. Never drop an event silently.
  - Updates telematics_devices.last_ping_at.
- GET /equipment/tractors/{id}/positions?from=&to=
- GET /equipment/trailers/{id}/positions?from=&to=
- GET /shipments/{id}/positions: resolve via manifest/trip history (which trailer and tractor carried this shipment during which time window) and return the pings for that window. Document the resolution logic clearly; the agent will reuse it.
- GET /telematics/health: devices with no ping in N hours while their asset is on an in_progress trip.

Geofencing (services/geofence.py):
- When a tractor's ping enters a location's geofence_radius_m while on a trip toward it, create an ARRIVED_AT_... milestone with source=telematics. Departure similarly. Make this behavior toggleable by setting (the agent may take this over later).

Frontend:
- Map page (Leaflet): latest position of every active tractor, colored by staleness (fresh, stale, no signal).
- Shipment detail: map tab showing its route from positions.
- Integrations > Telematics: ingest log table filterable by error_code.

Acceptance criteria:
- Tests for valid batch, unknown device, unassigned device, malformed payload, bad secret.
- /shipments/{id}/positions correct across a trailer change at a terminal.
```

---

## BATCH 7: Customer API, API keys, IP allowlist, webhooks, integration logs (use Spec mode)

This batch creates Mayur's problem space (data, auth, whitelisting) in a realistic, observable way.

```
[Paste GLOBAL RULES]

Goal: A public-style API that customer systems call, plus outbound status webhooks to customers, with complete logging of every request and delivery attempt.

Tables:

api_clients
- id, customer_id, name, status (active, suspended), created_at.

api_keys
- id, api_client_id, key_prefix (first 8 chars, shown in UI), key_hash, scopes (JSON: tracking:read, shipments:write, pickups:write, documents:read), expires_at, last_used_at, revoked_at.

ip_allowlist
- id, api_client_id, cidr, label, created_at, created_by.

api_request_log
- id, request_id, received_at, api_client_id (nullable), key_prefix (nullable), source_ip, method, path, query, request_body (JSON, redact secrets), response_status, error_code (nullable), latency_ms, user_agent.
- error_code values at minimum: MISSING_API_KEY, INVALID_API_KEY, EXPIRED_API_KEY, REVOKED_API_KEY, INSUFFICIENT_SCOPE, IP_NOT_ALLOWED, RATE_LIMITED, VALIDATION_ERROR, UNKNOWN_PROBILL, UNKNOWN_EQUIPMENT_ID, DUPLICATE_REQUEST, INTERNAL_ERROR.

webhook_subscriptions
- id, api_client_id, target_url, event_types (JSON list of milestone event_codes), secret (for HMAC signing), status (active, paused, failing), consecutive_failures, created_at.

webhook_deliveries
- id, subscription_id, shipment_id, milestone_id, payload (JSON), attempt_number, sent_at, response_status (nullable), response_body_snippet, error (nullable: TIMEOUT, CONNECTION_ERROR, HTTP_4XX, HTTP_5XX, AUTH_REJECTED), next_retry_at, delivered (bool).

Middleware for /api/v1/*:
- Order: request ID -> log start -> API key auth (header X-API-Key) -> expiry/revocation check -> IP allowlist check -> scope check -> rate limit (simple per-key token bucket) -> handler -> log completion.
- Every rejection returns the standard error format with a clear, actionable message, e.g. "API key abc12345 expired on 2026-09-20T00:00:00Z. Generate a new key in the portal." and "Request from 203.0.113.7 is not in the allowlist for client Acme."
- Every request, accepted or rejected, lands in api_request_log.

Public endpoints (/api/v1):
- GET /tracking/{probill_number}: status, milestones (non-voided), ETA, last known position (city-level only, not raw GPS).
- GET /tracking?po_number= or ?bol_number=
- POST /shipments (create/book), POST /pickups (request pickup). Strict validation with field-level error details, e.g. {"field": "pickup_date", "issue": "expected YYYY-MM-DD", "received": "09/24/26"}.
- Idempotency-Key header support on POSTs (duplicate -> return original response, log DUPLICATE_REQUEST).

Outbound webhooks (services/webhooks.py):
- On every new non-voided milestone, enqueue deliveries for matching subscriptions. Sign payload with HMAC-SHA256 header.
- Background worker (simple asyncio task or APScheduler) sends and retries with exponential backoff (e.g. 1m, 5m, 30m, 2h, 6h). After 5 consecutive failures mark subscription failing.
- Manual "resend" endpoint for a delivery or for all deliveries of a shipment.

Mock customer receiver:
- A tiny separate FastAPI app at tools/mock_customer/ that receives webhooks and exposes its own simple "customer dashboard" page. It can be configured to simulate failures: reject with 401, 403, 500, timeout, or wrong signature. This is how we'll demo the Coca-Cola side.

Frontend:
- Integrations > API Clients: clients, keys (create shows full key once; list shows prefix, scopes, expiry, last used), IP allowlist editor, webhook subscriptions.
- Integrations > API Logs: filter by client, status, error_code, time range. Click a row to see full request/response.
- Integrations > Webhook Deliveries: filter by delivered/failed, error; resend button.
- Customer portal: "Developer" tab where a customer user sees their own keys (prefix/expiry), allowlist, and their recent failed requests with the error messages.

Acceptance criteria:
- Tests for each error_code path in the middleware.
- Webhook retries tested with the mock receiver set to fail then succeed.
- No secrets (full keys, webhook secrets) ever appear in logs or API responses after creation.
```

---

## BATCH 8: Documents, exceptions (OS&D), rating, freight bills

```
[Paste GLOBAL RULES]

Goal: The remaining everyday TMS essentials, kept simple.

documents
- id, shipment_id, type (BOL, POD, customs, photo, other), filename, storage_path, uploaded_by, uploaded_at, source.
- Local file storage under backend/storage/ (gitignored); interface designed so S3 can replace it later.
- POD upload on a shipment with no DELIVERED milestone creates a data_quality_flag.

exceptions
- id, shipment_id, type (overage, shortage, damage, refused, missed_pickup, missed_delivery, delay, customs_hold, data_quality), severity (low, medium, high), status (open, investigating, resolved), description, opened_at, opened_by, resolved_at, resolved_by, resolution_notes, source (user, system, agent).
- Convert Batch 4 data_quality_flags into exception rows of type data_quality (keep the flag field for quick filtering).

Rating (services/rating.py):
- rate_tables: lane (origin terminal -> destination terminal), weight breaks (e.g. <500, 500-999, 1000-1999, 2000-4999, 5000-9999, 10000+), rate per cwt by freight class, minimum charge.
- fuel_surcharge_percent setting (table by effective date).
- accessorials catalog: liftgate, residential, inside delivery, appointment, hazmat, limited access, detention (per hour). Shipments get shipment_accessorials rows.
- POST /quotes returns a line-item breakdown. Shipments store a rated_total snapshot at booking.

freight_bills
- id, shipment_id, bill_number, bill_to_customer_id, line_items (JSON), subtotal, fuel_surcharge, accessorials_total, tax (simple config), total, status (draft, issued, paid, void), issued_at.
- Generate draft on DELIVERED; staff reviews and issues. Simple PDF export is optional.

Frontend:
- Shipment detail tabs: Documents, Exceptions, Charges.
- Exceptions queue page: filter by type, severity, status, source. This is where the agent's work will surface later.
- Billing page: drafts to review, issued bills.

Acceptance criteria:
- Rating unit tests for class, weight break, minimum charge, FSC, accessorials.
- Exceptions queue filters and status changes tested.
```

---

## BATCH 9: Frontend cleanup and consistency

```
[Paste GLOBAL RULES]

Goal: Make the UI consistent and remove all remaining mock data.

Tasks:
- Delete src/data/mockData.js. Every screen reads from the API through a typed client in src/api/ (one module per domain, shared fetch wrapper with auth header, error parsing into the standard error format, and request ID display on errors).
- Shared components: DataTable (sort, paginate, filters, column chooser, CSV export), FormField with API error binding, StatusChip, Timeline, MapView, ConfirmDialog, EmptyState, ErrorBanner.
- Ops home page: counts that link to filtered lists: shipments in transit, stale shipments (no milestone > 6h), open exceptions by severity, failed webhooks (24h), API errors (24h) by error_code, telematics devices with no signal.
- Global search box: probill, BOL, PO, trailer number, unit number, customer.
- Loading and error states on every page. Keyboard-friendly dock screen.
- Customer portal: My Shipments, Shipment detail (timeline, documents, charges), Request Pickup, Book Shipment, Developer tab.

Acceptance criteria:
- grep shows no import of mockData anywhere.
- Every page handles empty, loading, and error states.
- Vitest tests for DataTable, Timeline, and the API client error handling.
```

---

## BATCH 10: Dataset generator, fault injection, and replayer (use Spec mode)

```
[Paste GLOBAL RULES]

Goal: A reproducible synthetic dataset that looks like 30 days of real LTL operations, with injected faults and a ground-truth answer key, plus a replayer that streams it into the running system.

Location: data/generator/. Python, CLI via argparse or Typer. Deterministic with --seed.

Generation (clean "truth" first):
- Scale from orders.csv: default 2,000 shipments, 60 customers, 10 terminals (from Batch 3 seed), 120 tractors, 350 trailers, 150 drivers, devices on all tractors and ~60% of trailers.
- For each shipment, simulate the real journey: pickup -> origin terminal -> 1 to 2 linehaul legs -> destination terminal -> delivery. Realistic dwell times at terminals, business hours for P&D, transit times from distance.
- GPS pings every 5 minutes for tractors on trips, along road-like paths (interpolate between waypoints with slight noise; optional OSRM routing if available offline, not required).
- Customer API traffic: tracking calls, bookings, pickup requests at realistic rates per customer. Webhook deliveries for every milestone.

Outputs to data/output/<run_name>/ as CSV (and optionally Parquet):
customers, locations, tractors, trailers, telematics_devices, drivers, shipments, handling_units, trips, trip_trailers, manifests, manifest_items, milestones_truth, gps_pings_truth, api_requests_truth, webhook_deliveries_truth.

Fault injection (applied on top of truth, default ~6% of shipments affected; each fault type has its own configurable rate):
Data faults:
- MISSING_MILESTONE: drop a milestone (pickup, departure, delivery most common).
- WRONG_EQUIPMENT_ID: typo in trailer_number on load (digit swap, off-by-one, extra/missing char).
- UNKNOWN_EQUIPMENT_ID: trailer number that doesn't exist.
- LATE_MILESTONE: recorded_at hours after event_at.
- DUPLICATE_MILESTONE.
- WRONG_TIMESTAMP_TZ: event_at shifted by a timezone offset.
Telematics faults:
- DEVICE_OFFLINE: pings stop for a window while the trip continues.
- DEVICE_UNASSIGNED: device detached from the tractor in the TMS while still sending pings.
- DEVICE_SWAPPED: device moved to a different tractor without the TMS being updated.
API faults:
- EXPIRED_API_KEY, IP_NOT_ALLOWED (client changes egress IP), MALFORMED_PAYLOAD (bad date format, missing field, wrong type), UNKNOWN_PROBILL (typo in probill), WEBHOOK_ENDPOINT_DOWN (customer receiver returning 5xx or timing out for a window), WEBHOOK_AUTH_REJECTED.

Outputs after injection:
- milestones_recorded, gps_pings_recorded, api_requests_recorded, assignments_recorded, and the modified master data.
- fault_labels.csv: fault_id, fault_type, entity_type, entity_id, shipment_id (if any), injected_at, affected_window_start/end, truth_value, recorded_value, correct_fix (machine-readable JSON), difficulty (easy/medium/hard).
- A summary report (markdown): counts by fault type, affected shipments, a few example stories.

Loaders and replayer:
- load_to_db.py: loads a run's recorded (faulty) data into the TMS database as the "as-of end of period" state, for batch evaluation.
- replay.py: streams events in timestamp order into the running system through the real interfaces (telematics webhook endpoint, milestone endpoints, /api/v1 calls from simulated customer clients with their keys and source IPs), with --speed (e.g. 288 = one day in 5 minutes), --start/--end, and --pause-on-fault for demos.
- The mock customer receiver from Batch 7 is configured from the run so WEBHOOK_ENDPOINT_DOWN and WEBHOOK_AUTH_REJECTED faults actually happen during replay.

Evaluation helper:
- evaluate.py compares a list of detected/fixed items (JSON produced later by the agent) against fault_labels.csv and reports precision, recall, and fix accuracy per fault type.

Acceptance criteria:
- Same --seed produces byte-identical outputs.
- Every injected fault appears exactly once in fault_labels.csv.
- Replay of 1 day at high speed runs end to end without crashing the backend, and faults are visible in the UI (stale shipments, unknown equipment errors, API errors by code, failed webhooks).
```

---

## BATCH 11: Agent-ready interfaces (do not build the agent yet)

```
[Paste GLOBAL RULES]

Goal: Give a future AI agent a clean, safe surface to read state and propose or apply fixes. Do not implement any LLM logic in this batch.

Tasks:
1. Service account role "agent" with its own API key type. All writes by it are audited with actor_type=agent.
2. Read endpoints (/agent/v1), optimized and documented for tool use:
   - shipments/stale?hours=
   - shipments/{id}/full-context (shipment, handling units, milestones incl. voided, manifests/trips/equipment history, positions summary, exceptions, recent API and webhook activity for its customer)
   - equipment/resolve?number= (exact match + fuzzy candidates with scores)
   - equipment/{type}/{id}/activity?from=&to= (trips, manifests, pings summary)
   - telematics/anomalies (offline, unassigned-but-pinging, possible swaps where a device's positions match a different tractor's trip)
   - api/errors?client_id=&since= grouped by error_code
   - webhooks/failing
3. Write endpoints, each requiring: reason (text), evidence (JSON), confidence (0-1), and a dry_run flag that returns the exact changes without applying them:
   - correct-equipment-assignment, add-milestone (source=agent), void-milestone, reattach-device, resend-webhooks, open-exception, resolve-exception, draft-customer-message (stored, not sent).
4. Policy config (settings table): minimum confidence for auto-apply per action type; below it, the action becomes a proposed_fix row that a human approves in the UI.
5. proposed_fixes table + UI page: pending fixes with evidence, approve/reject buttons; approving applies the change and audits both the agent proposal and the human approval.
6. OpenAPI docs for /agent/v1 with clear descriptions and examples for every endpoint (these descriptions will become tool descriptions).

Acceptance criteria:
- dry_run never changes data (tested).
- Every agent write has reason, evidence, confidence, and an audit row.
- Proposed fixes flow tested end to end.
```

---

## Suggested team split

- Batches 3, 4, 5: TMS core (one person owns the data model and state machine).
- Batches 6, 7: integrations (telematics, customer API, webhooks, mock customer receiver).
- Batch 10 and 11: dataset, replayer, evaluation, agent surface (fits whoever will build the agent).
- Batches 1, 2, 9 can be split or done by whoever is free.
