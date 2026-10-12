# Repo Audit — Batch 0

Audit of the current `fleet-management-testing` repo ahead of converting it into a
lean, practical LTL TMS. No application code was changed in this batch.

The current app is a React 19 + Vite SPA (branded "TruckerPath" / qBotica "qubi",
deployed under base path `/Load-Lorry/`) with a small FastAPI + SQLite backend that
only serves backhaul-marketplace matching. Auth is entirely mock. There is a lot of
decorative/marketing surface (3D truck via Three.js, animated canvas hero, simulated
OCR billing) that is out of scope for the target system.

Verdict legend: **KEEP** (fits target as-is or nearly), **SIMPLIFY** (keep the shell,
strip the flash), **REPLACE** (idea stays, implementation is rebuilt against the real
backend), **REMOVE** (out of scope / decorative — delete).

---

## Frontend core

| File | What it does | Verdict |
|---|---|---|
| `src/main.jsx` | App entry. Mounts `<App/>` in `<StrictMode>`, `<BrowserRouter basename={BASE_URL}>`, wrapped in `<FleetProvider>`. | SIMPLIFY — keep entry; drop `/Load-Lorry/` base unless needed for deploy; provider will be replaced by real API state later. |
| `src/App.jsx` | View state machine persisted to `sessionStorage` (landing → chooser → logins → dashboards) plus admin `<Routes>` for dispatch/drivers/fleet-twin/alerts/billing/cost/companies/marketplace. Login is view-state only, no real auth. | REPLACE — routing shell stays; mock view-state auth replaced by real JWT/role guards (Batch 2); remove routes for deleted pages. |
| `src/index.css` | Global tokens. Imports IBM Plex from Google Fonts. qBotica orange `#FF7705` palette, status colors. Light theme with legacy amber aliases. | SIMPLIFY — collapse to one neutral light theme + dark toggle via CSS vars; keep branding; remove any glow/pulse/particle styles. |

## Pages (`src/pages/`)

| File | What it does | Verdict |
|---|---|---|
| `AlertsFeed.jsx` | Fleet alerts feed from `ALERTS` mock (HOS relay, etc.); dismiss pushes a notification. | REPLACE — becomes exceptions/alerts fed by real data (Batch 8); remove fake AI recommended actions. |
| `BillingPipeline.jsx` | **Simulated OCR** invoice pipeline: streams pre-written `ocrLines` on a 120ms interval, fake variance checks. | SIMPLIFY/REPLACE — remove the OCR animation entirely; real billing arrives in Batch 8. |
| `Companies.jsx` | Company/account list from `COMPANIES`; revenue/status helpers; links to profile. | REPLACE — becomes Customers list backed by the customers API (Batch 3). |
| `CompanyProfile.jsx` | Single-company detail + per-company mocked `orders`. | REPLACE — becomes customer detail from API (Batch 3). |
| `CostIntelligence.jsx` | Revenue-vs-cost analytics from hard-coded `WEEK_DATA`/`DRIVER_COSTS`. | REMOVE — out of scope; simple reports may return later. |
| `DispatchBoard.jsx` | Main dispatch screen; DriverPill, ReturnBar, BackhaulBadge, CompanyTag; surfaces faked AI scores. | SIMPLIFY — keep a dispatch board concept (Batch 5) but remove AI scoring, return-probability, backhaul badges. |
| `DriverProfile.jsx` | Driver detail (HOS, inspection, fatigue, score, docs). | REPLACE — becomes driver detail from drivers API (Batch 3). |
| `Drivers.jsx` | Driver roster from `DRIVERS`. | REPLACE — drivers list from API (Batch 3). |
| `FleetTwin.jsx` | **3D digital twin** truck telemetry (Three.js scene in a WebGL error boundary). | REMOVE — decorative; delete page + 3D deps. |
| `Landing.jsx` | Marketing landing: animated canvas freight-network hero, count-up stats, CTAs. | REMOVE — replace with a direct redirect to login. |
| `LoadMarketplace.jsx` | Backhaul load marketplace w/ Leaflet map; runs `localMatchCompute`. | REMOVE — out of scope; delete page + marketplace utils/backend. |
| `UserDashboard.jsx` | Customer portal: booking form + shipment tracking from `USER_SHIPMENTS`. | REPLACE — becomes the real customer portal (Batches 7/9) against the API. |

## Components (`src/components/`)

| File | What it does | Verdict |
|---|---|---|
| `AdminLogin.jsx` | **Mock auth**: hard-coded `admin@truckerpath.com/admin123`, fake delay, autofill button, marketing panel. | SIMPLIFY then REPLACE — keep the screen visually (Batch 1), wire to real `/auth/login` (Batch 2). |
| `UserLogin.jsx` | **Mock auth**: hard-coded `user@company.com/user123`; login + signup forms (signup not persisted). | SIMPLIFY then REPLACE — same as above. |
| `LoadCreationDrawer.jsx` | Admin create-load drawer; city autocomplete, mileage/return-prob heuristics. | REPLACE — becomes real shipment booking form (Batches 4/9); drop return-prob heuristic. |
| `LoginChooser.jsx` | Overlay to pick Admin vs Customer login. | KEEP — visually kept (Batch 1), stays useful. |
| `NotificationPanel.jsx` | Topbar bell + dropdown from FleetState notifications. | SIMPLIFY — keep pattern; feed from real alerts/exceptions later. |
| `OrderDetailPanel.jsx` | Modal rendering mock shipping docs (BOL/POD/Invoice) via `createPortal`. | REPLACE — becomes real documents view (Batch 8). |
| `Sidebar.jsx` | Admin left-nav. | SIMPLIFY — retarget sections to Shipments, Dispatch, Equipment, Drivers, Customers, Integrations, Settings. |
| `TpLogo.jsx` | Inline SVG brand logo. | KEEP — rebrand as needed. |
| `TruckModel.jsx` | **3D truck model** (@react-three/fiber + drei), pulsing emissive material. | REMOVE — decorative; delete with FleetTwin and 3D deps. |

## Hooks

| File | What it does | Verdict |
|---|---|---|
| `src/hooks/useFleetState.jsx` | Global in-memory Context: loads, alerts, notifications, userShipments + actions (book, confirm, deliver, invoice, backhaul broadcast). Resets on reload. | REPLACE — superseded by a typed API client + server state (Batches 2/9). Remove `awardBackhaul`/backhaul broadcast logic. |

## Utils + tests

| File | What it does | Verdict |
|---|---|---|
| `src/utils/marketplace.js` | Backhaul pure functions: haversine, detour cost, 4-gate eligibility, net-value ranking, `localMatchCompute`. | REMOVE — marketplace is out of scope. |
| `src/utils/marketplace.test.js` | Vitest + fast-check property tests for the above. | REMOVE — with marketplace. |
| `src/test/setup.js` | `import '@testing-library/jest-dom'`. | KEEP — Vitest setup stays. |

## Backend (`backend/`)

| File | What it does | Verdict |
|---|---|---|
| `main.py` | FastAPI "Backhaul Load Marketplace" v1: `POST /marketplace/match`, `GET /health`. CORS for Vite dev. | REPLACE — restructure into `backend/app/*` (Batch 2). Keep only `/health`; drop `/marketplace/match`. |
| `models.py` | Pydantic models for bid/match request/response. | REMOVE — marketplace-specific. |
| `matching.py` | 4-gate eligibility + net-value ranking (Python twin of marketplace.js). | REMOVE — marketplace. |
| `database.py` | SQLite `marketplace.db`; creates opportunities/bids/awards tables (not used by the match endpoint). | REMOVE — replaced by SQLAlchemy + Alembic (Batch 2). |
| `seed.py` | Seeds marketplace demo opportunity + bids. | REMOVE — replaced by `seed_users.py` and later seeders. |
| `requirements.txt` | Backend deps. | REPLACE — rewrite for FastAPI/Pydantic v2/SQLAlchemy 2.x/Alembic/auth/testing (Batch 2). |

## Config

| File | What it does | Verdict |
|---|---|---|
| `package.json` | name "truckerpath"; scripts dev/build/lint/preview/test. Deps incl. **three, @react-three/fiber, @react-three/drei, @react-three/postprocessing** (3D — REMOVE), **leaflet, react-leaflet** (KEEP for maps), lucide-react, react 19, react-router-dom 7. | SIMPLIFY — remove 3D deps and any marketplace-only deps; keep leaflet/react-leaflet. |
| `vite.config.js` | React plugin; **base `/Load-Lorry/`**; Vitest config (jsdom, setup file). | SIMPLIFY — remove/justify the base path; keep Vitest config. |
| `eslint.config.js` | Flat config; ignores dist; react-hooks + react-refresh; `no-unused-vars` allows constant-cased. | KEEP. |

---

## mockData.js → future backend tables

`src/data/mockData.js` will be trimmed in Batch 1 and deleted in Batch 9. Mapping of
each export to the target schema:

| mockData export | Represents | Future table(s) |
|---|---|---|
| `DRIVERS` | Driver roster (HOS, inspection, fatigue, **faked score/reasons/warnings**) | `drivers` (Batch 3). Drop the AI score/reasons/warnings fields. |
| `INITIAL_LOADS` | Loads (pickup/delivery, rate, miles, cargo, weight, status, returnProb, tags) | `shipments` (Batch 4); assignment via `trips`/`manifests` (Batch 5). Drop returnProb/AI tags. |
| `ALERTS` | Fleet alerts (HOS relay) | `exceptions` (Batch 8). |
| `TRUCK_DB` | Truck telemetry (tire PSI, engine, fuel, HOS, brakes) | `tractors` + `telematics_devices`/`gps_pings` (Batches 3/6). |
| `INITIAL_HISTORY` | Billing history (invoice/margin/status) | `freight_bills` (Batch 8). |
| `US_CITIES` | US city gazetteer (label/lat/lng) | `locations` seed (Batch 3). Add Canadian cities (Batch 1). |
| `CARGO_TYPES` | Commodity strings | Reference values on `shipments`/`handling_units` (Batch 4). |
| `DRIVER_DOCS` | Driver compliance docs (CDL/medical/drug test) | `drivers` fields / `documents` (Batches 3/8). |
| `USER_SHIPMENTS` | Customer shipment tracking + event timeline | `shipments` + `milestones` (Batch 4). |
| `LOAD_QUEUE` | Billing queue with **fake OCR ocrLines** | `freight_bills` (Batch 8); OCR text removed. |
| `TRUCK_GVWR` | Truck GVWR (backhaul capacity gate) | `tractors`/`trailers` capacity fields (Batch 3). |
| `TRUCK_CERTIFICATIONS` | Allowed commodities per truck (marketplace) | n/a — marketplace-specific, dropped. |
| `TRUCK_TRAILER_SPECS` | Trailer volume cuft (marketplace) | `trailers.capacity_cuft` (Batch 3). |
| `BACKHAUL_OPPORTUNITIES` | Marketplace demo opportunity + bids | n/a — marketplace-specific, dropped. |
| `COMPANIES` | Account address-book (AS/400-style: terms, credit, hold, Rec-Type LTL, geocode, order history) | `customers` + `locations` (Batch 3). |

## orders.csv (repo root) — LTL-shaped seed source

`orders.csv` is confirmed **LTL-shaped** and will seed the `shipments` table (and derived
`customers`/`locations`) in Batch 4. Header (21 columns):

`shipment_id, origin_zip, dest_zip, weight_lbs, status, freight_class,
base_rate_per_mile_cwt, fuel_surcharge_percent, accessorial_charges, driver_id,
vendor_id, created_at, last_updated_timestamp, skid_details, is_stackable, is_urgent,
delivery_appointment, origin_country, dest_country, Quote, skid_dims`

LTL signals present: NMFC `freight_class` (50–155), CWT pricing (`base_rate_per_mile_cwt`),
`fuel_surcharge_percent`, `accessorial_charges`, `is_stackable`, `skid_dims` (e.g.
`100x43x52`), `is_urgent`, `delivery_appointment`, and cross-border `origin_country` /
`dest_country` (US/CA). Origin/dest are ZIP / Canadian postal codes.

Data-quality caveats to handle on import (Batch 4):
- Inconsistent country spellings: `US` / `USA` / `United States`, `CA` / `Canada`.
- Dirty free-text `Quote` field: `$4228`, `$640.27`, `6867.8`, blank, `$97.06`.
- Messy `skid_dims`: `30x20x40 inches`, `unknown`, blank.
- Empty `driver_id` / `vendor_id`.
- At least one obviously bad `dest_zip` (`285347`).

These are useful: they are exactly the kind of data gaps the downstream AI agent is meant
to detect and fix, so import should preserve/flag them rather than silently clean them.
