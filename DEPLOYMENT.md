# Deployment preparation

Login is intentionally deferred. Keep this deployment on a private network or
behind your hosting platform's access controls when using borrower data.

## Configuration

### Render Free + Netlify Free + Neon Free

Repository configuration is supplied in `render.yaml` and `netlify.toml`.
Do not use SQLite or Render's expiring free Postgres for this setup.

1. Put this project in a private GitHub repository, including both configuration
   files, but excluding `.env`, `.venv`, `node_modules`, and database files.
2. In Neon, create a Free project named `zaradera-recovery`. Choose a region
   near your Render region. Retain the full connection string, including SSL
   settings; store it only in backend environment settings. The application
   accepts `postgresql://` and selects the installed psycopg driver automatically.
3. If preserving local history, stop local uploads, back up the SQLite file,
   then migrate before allowing uploads to the hosted application (see below).
4. In Render, create a Blueprint from the repository using `render.yaml`.
   Confirm the service plan is Free. Enter `DATABASE_URL` from Neon and initially
   set `CORS_ORIGINS` to your planned Netlify production origin, or localhost
   until Netlify assigns the final URL. No database or paid disk is declared.
   Check the build logs and `/api/health` after deployment.
5. In Netlify, import the same repository. The supplied configuration uses
   `frontend` as base, `npm run build`, and `dist` as publish directory. Select
   the Free plan and set `VITE_API_BASE_URL` to the Render HTTPS origin, without
   `/api` at the end. Deploy; the value is embedded at build time.
6. Set Render `CORS_ORIGINS` to the exact Netlify HTTPS origin, without a trailing
   slash, then restart/redeploy the API. Add localhost origins only if needed.
7. Upload two test snapshots, check historical summaries and loan history, then
   redeploy Render and confirm counts/history survive. This live persistence
   check is required in addition to local tests.

Render's Free service sleeps when idle, so initial requests may take about a
minute. Check current Render, Netlify, and Neon usage limits in their dashboards.
Database persistence does not replace independent backups.

### Preserve local SQLite history

Run these in `backend` with uploads stopped:

```powershell
.\.venv\Scripts\python.exe backup_sqlite.py .\before-neon-migration.db
```

Set `DATABASE_URL` privately in `backend/.env` to the Neon connection string
(or in your terminal environment), then run:

```powershell
.\.venv\Scripts\python.exe migrate_sqlite.py --source .\zaradera.db
```

The source is opened read-only. All target inserts share one transaction and
row counts are verified before committing. IDs and PostgreSQL sequences are
preserved. The target must contain no users, uploads, or snapshots; the utility
refuses to merge or overwrite records. Stop hosted uploads while it runs.
If a migration fails, do not paste a traceback containing a connection string
into a public issue. Keep the original SQLite file and backup until live
verification and a PostgreSQL restore drill are complete.

### PostgreSQL backups

Install PostgreSQL client tools matching the server major version (or newer).
Use Neon's direct connection, rather than its pooler, for backup and restore.
Provide credentials privately with libpq environment settings or a password
file; never put them in Git or frontend settings. With `PGHOST`, `PGDATABASE`,
`PGUSER`, `PGPASSWORD` and `PGSSLMODE=require` set in the terminal:

```sh
pg_dump --format=custom --no-owner --no-acl --file=zaradera-backup.dump
```

Schedule this from a trusted machine or backup service; Render Free has no
persistent backup disk. Store encrypted copies outside Neon. To test recovery,
point the libpq environment settings at a separate empty database, then run:

```sh
pg_restore --no-owner --no-acl --exit-on-error --dbname=neondb zaradera-backup.dump
```

Compare upload/snapshot counts and sample histories before relying on a backup.
`backup_sqlite.py` is only for local SQLite and cannot back up Neon.

### Other hosting configurations

Run the API with `backend` as its working directory. Set:

- `DATABASE_URL=sqlite:////absolute/persistent/path/zaradera.db` on Linux.
  Create the parent directory on a persistent volume before starting the API.
  The default relative database path is suitable for local development.
- `CORS_ORIGINS=https://your-frontend-domain` (exact origins, comma separated).
- `MAX_UPLOAD_BYTES=10485760` for a 10 MiB workbook limit.

Install `backend/requirements.txt`, then start a single API worker:

```sh
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use the platform's assigned port when required. Terminate HTTPS at the hosting
platform or reverse proxy. Configure a request-body limit there too: the API's
workbook limit is applied after multipart parsing. Do not use `--reload` in production.
Use `/api/health` for process health checks; it does not check database connectivity.

In `frontend`, set `VITE_API_BASE_URL=https://your-api-domain` before `npm run build`.
Serve `frontend/dist` through a static host. Alternatively, route `/api` to the
backend on the same origin and leave `VITE_API_BASE_URL` empty. Vite's development
proxy does not run in the production build.

The provided requirements include psycopg for PostgreSQL as well as SQLite support.

## Backups and restore

From `backend`, use the same environment and database settings as the server:

```sh
python backup_sqlite.py /backup-volume/zaradera-2026-11-04.db
```

The utility uses SQLite's backup API so an active database can be copied
consistently. It refuses to overwrite existing files. Schedule daily backups
and a backup before every deployment. Keep copies outside the application
volume with restricted access and an agreed retention policy.

To restore: stop the API, preserve the current database and any SQLite journal
files, and restore a backup to a clean database location. Set `DATABASE_URL` to
that location, restart, and verify historical dates and loan counts. Rehearse
this procedure on a separate database before launch.

## Release checks

1. Run `python -m pytest -v` in `backend` and `npm run build` in `frontend`.
2. Test two dated uploads, historical summaries and trends, loan history, and a
   corrected upload for the same date with representative non-sensitive data.
3. Restart/redeploy and confirm stored history survives.
4. Verify HTTPS, access restrictions, production origins, health checks, and logs.
5. Confirm a backup restores successfully and retain the prior application build.

Startup creates missing tables; it does not migrate existing schemas. This
correction changes no tables. Introduce versioned migrations before a future
release changes the database schema. Hosting, scheduled backups, monitoring,
and access controls must still be configured on the chosen platform.
