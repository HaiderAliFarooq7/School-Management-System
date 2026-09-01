# School Management System — Web App

A browser-based rewrite of the SMS_Python desktop app: FastAPI backend, React + TypeScript + MUI frontend.

**This application is production-only.** It is deployed exclusively to:

```
GitHub → Render (backend) → Neon (PostgreSQL) → Vercel (frontend)
```

There is no supported local/dev runtime — the backend refuses to start without a real Neon `DATABASE_URL` and a real `CORS_ORIGINS`, and the frontend build refuses to call anything but the `VITE_API_URL` configured in Vercel. See [DEPLOYMENT.md](DEPLOYMENT.md) for the full deploy procedure.

## Features

- **Auth & roles**: JWT login, Admin / Accountant / Teacher roles. Teachers default to their assigned class but may take/view attendance for any class.
- **Students**: CRUD, search, advanced search, admission form with an optional **per-student default fee** (overrides the class fee for that student in all future voucher generation).
- **Grades**: CRUD with in-use delete guard.
- **Fees**: vouchers (generate/pay/delete), **bulk voucher generation class-wise**, extra charges (add/pay/delete), fee reports (monthly collection, class summary, overdue list, balance sheet), dashboard stats.
- **Expenses & salaries** (Admin only): record money going out — salaries (with staff name and the month the salary covers), utilities, rent, supplies, maintenance, transport. Shows fees collected vs expenses vs **net profit/loss** for any date range, a per-category breakdown, and a monthly income-vs-expenses chart. Income is read from the same `fee_audit_log` payment rows the **Collections** page reconciles against, so the two never disagree.
- **Attendance**: per-class/date marking grid (Present/Absent/Late/Leave), monthly summary. Admin, Teachers and Accountants can mark/view attendance for **all classes** (Teachers default to their own class).
- **Backup & restore**: on-demand `pg_dump` that streams straight to the browser and is never stored on the server, restore from an uploaded `.dump`, Excel export/import of students, full data reset (keeps school settings/users).
- **User management**: create/deactivate users, assign roles and (for Teachers) a class. Any user can change their own password from the account menu.
- **School settings**: school info, bank details, fee due day, logo upload.
- **Parent module** (read-only companion, powers the **BFHS Parent** Android app): parents log in with **mobile number + password** (no OTP) and view their children's attendance, monthly fee, extra charges, and notifications — one mobile number can be linked to several students. Admins manage parent accounts and devices under **Parents** (incl. one-click *Sync from Students*); the **Notification Center** sends absent alerts / fee reminders / announcements to a student, class, or the whole school (Admin all types, Accountant fee reminders only, Teachers never), delivered via Firebase Cloud Messaging with full history. Marking a student **Absent** notifies their parents automatically. Parent tables are per-school (tenant DB); mobile→school login routing lives in the master DB. See [DEPLOYMENT.md](DEPLOYMENT.md) Step 6 for Firebase setup.

> **Security note:** on a brand-new (empty) database, the backend auto-creates a bootstrap admin account `admin` / `admin123` on first startup. Change this password immediately after first login via the account menu → **Change Password**.

## Architecture

| Layer | Service | Notes |
| --- | --- | --- |
| Source control | GitHub | Pushes to `main` trigger Render/Vercel auto-deploys. |
| Backend | Render | FastAPI + uvicorn. Reads config exclusively from Render environment variables. |
| Database | Neon | Managed PostgreSQL. Connected via `DATABASE_URL`, normalized to the psycopg v3 driver automatically. |
| Frontend | Vercel | Static Vite/React build. Talks to the Render backend via `VITE_API_URL`, never a relative path. |

## Health checks

| Endpoint | Returns |
| --- | --- |
| `GET /` | `{"status":"ok","service":"School Management API"}` |
| `GET /health` | `{"status":"healthy"}` |

Startup logs print `Connected to Neon`, `Database Ready`, and `Application Started` in sequence — useful for confirming a Render deploy actually reached a healthy database.

## Environment variables

### Backend (Render) — see `backend/.env.example`

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string. Accepted as `postgres://`, `postgresql://`, or `postgresql+psycopg://` — all are normalized to the psycopg v3 driver. Missing this raises a `RuntimeError` at startup. |
| `CORS_ORIGINS` | Yes | Comma-separated list of allowed frontend origins (the Vercel production domain, plus any custom domain). Missing this raises a `RuntimeError` at startup. |
| `JWT_SECRET` | Yes | Long random string that signs auth tokens. |
| `JWT_ALGORITHM` | No | Defaults to `HS256`. |
| `JWT_EXPIRE_MINUTES` | No | Defaults to `480` (8 hours). |
| `PG_BIN_DIR` | No | Only needed if `pg_dump`/`pg_restore` aren't already on PATH. |
| `DATA_DIR` | No | Where the school logo and student photos are stored. Defaults to an ephemeral path; set to a Render persistent disk mount (e.g. `/var/data/sms`) to survive restarts. |

### Frontend (Vercel) — see `frontend/.env.example`

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | Yes | The deployed Render backend's bare origin (no trailing slash, no `/api` suffix), e.g. `https://school-management-backend-1t21.onrender.com`. The app appends `/api` itself. Missing this throws a clear error in the browser at load time. |

## Tests

The backend smoke suite runs in CI against a real PostgreSQL database (export `DATABASE_URL`, `CORS_ORIGINS`, and `JWT_SECRET` as environment variables before running):

```
pytest -q
```

It creates and tears down its own throwaway users/class/students — it never touches the bootstrap admin or real data.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full Render + Neon + Vercel setup, migration steps, and the production readiness checklist.
