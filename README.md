# School Management System — Web App

A browser-based rewrite of the SMS_Python desktop app: FastAPI + PostgreSQL backend, React + TypeScript + MUI frontend. Runs on your computer; other devices on the same WiFi/LAN can use it from any browser.

## Current status — all 5 build phases complete

- **Auth & roles**: JWT login, Admin / Accountant / Teacher roles, Teacher access scoped to their assigned class.
- **Students**: CRUD, search, advanced search, admission form with an optional **per-student default fee** (overrides the class fee for that student in all future voucher generation).
- **Grades**: CRUD with in-use delete guard.
- **Fees**: vouchers (generate/pay/delete), **bulk voucher generation class-wise** (uses each student's own default fee, falling back to the class fee), extra charges (add/pay/delete), **bulk extra-charge creation class-wise**, fee reports (monthly collection, class summary, overdue list, balance sheet), dashboard stats.
- **Attendance**: per-class/date marking grid (Present/Absent/Late/Leave), monthly summary, Teacher access scoped to their own class, optional auto-queueing of Absent notifications when attendance is finished.
- **Communication**: provider-independent notification subsystem (SMS / WhatsApp) with a pluggable provider abstraction (real gateways are placeholders for now), a background send queue with retry, editable templates with `{{variable}}` substitution, a queue/history/templates/providers console, bulk send (all absent today / pending-fee students / custom message), and per-student messaging from the fee page. Only one provider is active at a time; switching providers needs no change to Attendance/Fee/UI code.
- **Backup & restore**: on-demand `pg_dump` that streams straight to your browser and is **never stored on the server** (free-hosting friendly), restore from an uploaded `.dump`, Excel export/import of students, full data reset (keeps school settings/users).
- **User management**: create/deactivate users, assign roles and (for Teachers) a class. Any user can change their own password from the account menu (top-right).
- **School settings**: school info, bank details, fee due day, attendance auto-notify toggle.

> **Security note:** the bootstrap admin password is `admin123`. Change it immediately after first login via the account menu → **Change Password** (top-right).

All of the above verified end-to-end against a real PostgreSQL database (not just SQLite) — login, CRUD, role enforcement, the voucher-regenerate-preserves-payment fix, bulk operations, attendance marking, and `pg_dump` backups were all exercised live.

## One-time setup

1. **Install PostgreSQL** if you haven't already (postgresql.org installer, or `winget install PostgreSQL.PostgreSQL`).
2. Create the app database and user (one-time, using the `postgres` superuser):
   ```sql
   CREATE ROLE sms_user LOGIN PASSWORD 'sms_pass';
   CREATE DATABASE sms_db OWNER sms_user;
   ```
3. `cd SMS_Web/backend`, copy `.env.example` to `.env` and adjust `DATABASE_URL` / `JWT_SECRET` if you used different credentials. If `pg_dump`/`pg_restore` aren't on your system PATH, set `PG_BIN_DIR` in `.env` to your PostgreSQL `bin` folder (e.g. `C:\Program Files\PostgreSQL\18\bin`) so the Backup page works.
4. Apply migrations and seed roles/admin:
   ```powershell
   .venv\Scripts\python.exe -m alembic upgrade head
   .venv\Scripts\python.exe -m scripts.seed
   ```
   Bootstrap login: `admin` / `admin123` — change this immediately from the Users page.
5. If migrating real data from the old desktop app, run `scripts/migrate_sqlite_to_postgres.py "<path to old sms.db>"` once, after step 4 and before real use.

## Running it day to day

**Easiest — one command** (from `SMS_Web/`):
```powershell
.\start.ps1
```
This starts PostgreSQL if needed, applies any pending migrations, builds the frontend if it hasn't been built yet, and starts the server — printing both `http://localhost:8000` and your LAN address.

**Manual equivalent**:
```powershell
cd SMS_Web/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
FastAPI serves the built React app directly, so visiting `http://localhost:8000` (or `http://<this-pc-ip>:8000` from another device on the same WiFi) gives you the full app — no separate frontend server needed in production.

First time only: allow the port through Windows Firewall so other devices can reach it:
```powershell
netsh advfirewall firewall add rule name="SMS Web" dir=in action=allow protocol=TCP localport=8000
```

## Frontend development mode

```powershell
cd SMS_Web/frontend
npm run dev
```
Opens on `http://localhost:5173` with hot reload, proxying `/api` to the backend on port 8000. Rebuild with `npm run build` before relying on the backend to serve it directly.

## API reference

Browse `http://localhost:8000/docs` for the full interactive OpenAPI documentation — useful for testing any endpoint directly, including the role restrictions (try calling a Fee Vouchers endpoint with a Teacher token and confirm it's rejected). The raw OpenAPI schema is at `http://localhost:8000/openapi.json`.

## Tests

A backend smoke suite covers auth, role permissions, students, search, fees + PDF, attendance, communication, reports, and password change. It runs against the configured database, creating and cleaning up its own throwaway users/class/students (it never touches real data or the bootstrap admin):

```powershell
cd SMS_Web/backend
.venv\Scripts\python.exe -m pytest -q
```

## Environment variables

Set in `backend/.env` (see `.env.example`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://sms_user:sms_pass@localhost:5432/sms_db` | PostgreSQL connection (SQLAlchemy + psycopg v3). On most hosts this is provided for you. |
| `JWT_SECRET` | `change-this-secret-in-production` | **Must** be set to a long random string in production — it signs all auth tokens. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `JWT_EXPIRE_MINUTES` | `480` | Login session length (minutes). |
| `PG_BIN_DIR` | _(empty — rely on PATH)_ | Folder containing `pg_dump`/`pg_restore` if they aren't on PATH (e.g. `C:\Program Files\PostgreSQL\18\bin`). Required for Backup/Restore. |

## Deployment & free hosting

The app is designed to run on small/ephemeral hosting with no durable disk:

- **Nothing transient is written to disk.** Backups, generated voucher/report PDFs, QR images, and Excel exports are produced in memory or a system temp file, streamed to the client, and deleted immediately. Only the **school logo** and **student photos** persist (under the OS app-data dir, configurable via `data_dir`).
- **Logs rotate** (1 MB × 3 files) so they can't fill the disk; unhandled errors are logged server-side and return a clean generic message to the client (no stack traces leaked).
- **Database:** point `DATABASE_URL` at your managed Postgres (e.g. a free Neon/Supabase/Railway instance). Run `alembic upgrade head` and `python -m scripts.seed` once on first deploy.
- **Serving:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. FastAPI serves the built React bundle from `frontend/dist`, so a single process serves both API and UI. Build the frontend with `npm run build` as part of your deploy.
- **Backups on free hosting:** because the server keeps nothing, an admin should periodically click **Backup → Download Backup** to keep a local `.dump`, and use **Restore from Backup** to recover.
