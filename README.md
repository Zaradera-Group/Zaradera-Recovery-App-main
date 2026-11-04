# Zaradera Recovery Unit — PDL Dashboard

A web app for the recovery unit at Zaradera Credit. Upload the weekly
"Past Due Loans" Excel export and it:

- Segments past-due loans **by product**, **by days past due** (highest first),
  and **by risk category** (Performing / Watchlist / Substandard / Doubtful / Lost)
- Calculates risk categories from days past due using the configured day bands; stores the sheet Performance Classification separately as a reference tag
- Keeps uploads as dated snapshots. A correction for the same date replaces
  that date's batch; snapshots for other dates remain intact.
- Tracks each loan's trajectory across weeks (matched by Loan ID), flags loans
  that vanish from a new sheet (paid off / written off), and shows a
  worsening/improving trend view week over week

## How it's built

- **Backend**: Python (FastAPI) + SQLite via SQLAlchemy, pandas/openpyxl for
  parsing the Excel sheet
- **Frontend**: React + Vite
- **Tests**: pytest (backend) — tests covering categorization, parsing,
  history/trend logic, and the API endpoints

No login is required yet. The `users` table and `uploaded_by` fields are
already in the schema so auth can be added later without restructuring
anything.

## Project layout

```
zaradera-recovery-app/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app + routers
│   │   ├── models.py          SQLAlchemy tables (Upload, Snapshot, User)
│   │   ├── parser.py          Excel -> canonical rows, tolerant of header variations
│   │   ├── categorization.py  Fallback day-band risk categories
│   │   ├── crud.py            Snapshot storage, history, trend, disappeared-loan logic
│   │   ├── routers/           uploads.py, dashboard.py, loans.py
│   │   └── config.py          Settings from environment variables
│   ├── tests/                 pytest suite
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx             Tabs, date selector, data fetching
    │   ├── api.js               Fetch wrapper for the backend
    │   └── components/          UploadPanel, SummaryStrip, LoanTable, GroupedView,
    │                             TrendView, LoanHistoryDrawer, CategoryBadge
    ├── package.json
    └── .env.example
```

## Running it locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # adjust if needed — defaults work for local dev

uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`. A SQLite file (`zaradera.db`) is
created automatically on first run. Interactive API docs: `http://localhost:8000/docs`.

Run the tests:

```bash
cd backend
python3 -m pytest -v
```

### Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. In dev, requests to `/api/*` are proxied to the
backend on port 8000 (see `vite.config.js`) — no extra setup needed.

## Uploading a sheet

The uploader expects an `.xlsx` export with at least `Loan ID`,
`Loan Product`, and `Days Past Due` columns; everything else (Borrower,
Performance Classification, amounts, dates, account manager, etc.) is picked
up automatically if present. Column matching is tolerant of spacing/case
differences, so a slightly reformatted export won't break the upload.

Uploading again on the **same day** replaces that day's batch (handles
correcting a sheet you just uploaded). Uploading on a **new day** adds a new
weekly snapshot and keeps every prior week intact.

## Deploying

Nothing is hardcoded — configuration is entirely environment-driven:

**Backend** (`backend/.env` or your host's env var settings):
- `DATABASE_URL` — defaults to a local SQLite file. Point this at a persistent
  disk/volume in production, or swap in Postgres
  (`postgresql://user:pass@host:5432/dbname`) if you outgrow SQLite.
- `CORS_ORIGINS` — comma-separated list of frontend URL(s) allowed to call the API.

**Frontend** (`frontend/.env` or build-time env var):
- `VITE_API_BASE_URL` — set to your deployed backend's URL. Leave blank for
  local dev (uses the Vite proxy).

Typical deploy: run the backend (`uvicorn app.main:app`) behind your platform
of choice (Render, Railway, a VPS with systemd, etc.), and build the frontend
(`npm run build`) to static files served from any static host or the same
server. Make sure `DATABASE_URL` points at storage that persists across
deploys — a SQLite file on an ephemeral filesystem will lose history on
every redeploy.

## Adding login later

The schema already has a `users` table (`app/models.py`) and every `Upload`
has an `uploaded_by` field, currently unused. To add auth: wire up a real
auth library (e.g. `fastapi-users` or a custom JWT flow) against that table,
start populating `uploaded_by` on upload, and gate routes with a dependency —
no schema changes needed.

## Risk categories: CBN Deposit Money Bank bands

The app classifies every loan by **days past due** using the CBN prudential
guideline bands for Deposit Money Banks (confirmed against the published
guideline, not assumed):

| Category | Days past due |
|---|---|
| Performing | 0–30 |
| Watchlist | 31–90 |
| Substandard | 91–180 |
| Doubtful | 181–360 |
| Lost | 361+ |

This is the only file that computes it: `app/categorization.py`. If the
bands ever need to change, that's the one place to edit.

Zaradera's own sheet also carries a `Performance Classification` column,
which the app stores and displays alongside as **Snapshot.sheet_classification**
for reference — but it does not drive the category, sorting, grouping, or
trend logic. Worth knowing: in the real export tested against this app, that
column doesn't track days-past-due the way CBN bands do (loans a few days
past due were already tagged "Doubtful" internally), so expect the two
columns to disagree on many rows — that's expected, not a bug.


## Corrections and deployment checks

Historical summaries and trends follow the selected upload date. Comparisons use the preceding available snapshot. Uploads accept .xlsx only (default limit: 10 MiB); duplicate IDs and invalid numeric/date values are rejected before replacing any stored batch. Blank days-past-due cells retain the existing zero default.

See [DEPLOYMENT.md](DEPLOYMENT.md) for production configuration, backups, restore, and release checks.

