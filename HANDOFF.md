# 📋 Project Handoff — BFHS School Management System

Paste-ready context for continuing this project in a new session.

## Repository
- **GitHub:** `https://github.com/HaiderAliFarooq7/School-Management-System.git`
- **Local root (this IS the git repo):** `C:\Users\OTS\Desktop\School\SMS_Web`
- **Default branch:** `main`
- **Working branch:** `feature/parent-module`
- **Git workflow:** commit to `feature/parent-module` → `git merge --no-ff feature/parent-module` into `main` → push **both**. (Owner also sometimes merges via GitHub PRs.)
- **Commit trailer:** `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`

## Monorepo layout (all inside `SMS_Web/`)
```
backend/            FastAPI, SQLAlchemy 2, Alembic, psycopg v3, JOSE JWT, bcrypt
frontend/           React 19 + TypeScript + Vite + MUI (deployed on Vercel)
BFHS Parent App/    Android app — Kotlin, Jetpack Compose, Hilt, Retrofit, Room, DataStore, FCM
```

## Architecture — MULTI-TENANT (critical)
- **Master DB** holds routing/control only: `schools`, `master_users`, `user_directory` (staff username→school), `parent_directory` (parent mobile→school).
- **One tenant DB per school** holds all operational data (`user_account`, `student`, `fee_voucher`, `extra_charge`, `attendance`, parent tables, `fee_audit_log`, …).
- `db/session.py:get_db(request)` routes each request to the right tenant DB using the **signed `school_id` JWT claim**. See `db/master.py`, `db/tenants.py`, `services/provisioning.py`.
- On startup `bootstrap.init_master()` auto-creates the master DB, seeds super-admin + first school, and runs `alembic upgrade head` on **every** tenant DB.
- **Alembic migration head:** `b8c9d0e1f2a3` (fee_audit_log).
- ⚠️ Local gotcha: `import app.main` lists routes as `_IncludedRouter` (lazy inclusion) — routes ARE registered; verify via `students.router.routes`, not `app.routes`.

## Deployed URLs / config
- **Backend (Render):** `https://school-management-backend-1t21.onrender.com`
- **Frontend (Vercel):** `school-management-system-kappa-vert.vercel.app` (Vercel Root Directory = `frontend`)
- **Android `BASE_URL`:** `https://school-management-backend-1t21.onrender.com/` (in `BFHS Parent App/app/build.gradle.kts`)

## Credentials / defaults
- Super admin (master): `superadmin` / `Admin@123`
- Fresh-school admin: `admin` / `admin123`
- Parent login: **mobile number + password** (default password = the mobile number)

## Env vars
- **Render (backend):** required `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`; optional `MASTER_DATABASE_URL` (defaults to `sms_master` sibling), `FIREBASE_CREDENTIALS_JSON` (or `FIREBASE_CREDENTIALS_FILE`), `PARENT_JWT_EXPIRE_MINUTES` (43200).
- **Vercel (frontend):** `VITE_API_URL` = backend origin (no trailing slash, no `/api`).
- **Firebase (git-ignored, NEVER commit):** backend `backend/firebase/service-account.json`; Android `BFHS Parent App/app/google-services.json`.

## What's built (Parent Module + extras)
- **Parent app API** `/api/parent/*`: login (mobile→school routing via `parent_directory`), change-password, fcm-token, students, per-student attendance/fees/extra-charges, notifications (+ `/read`), school. Parent JWT `type=parent`, carries `school_id`, 30-day lifetime.
- **Admin** `/api/admin/parents/*` (list/create/sync-from-students/reset-password/devices) and `/api/admin/notifications/*` (send, log, `settings` auto-notify toggle, `absent-all` broadcast).
- **Roles:** Admin = all; Accountant = fee reminders only + no Fee Reports; Teacher = attendance only, never sends notifications.
- **Notifications:** auto-push when a student is marked Absent (respects `school.auto_notify_absent`); **short-codes** `{student}/{name} {class} {father} {amount}/{dues} {date} {reg}` (also `[..]`) filled **per student** by the backend → each parent gets their own child's real details. FCM sender reads creds from env only.
- **Web admin pages:** Parent Management, Notification Center (templates + short-code legend), **Fee Activity Log** (Admin-only audit of payments/discounts/edits/deletes — who, amount, reason).
- **Android app:** logo splash + login (mobile+password, auto-login via DataStore), dashboard (child cards, greeting by parent name), **consolidated Student Detail** (attendance calendar + pending fees + pending charges + total dues), notifications (tap to read dialog), settings, school profile (name/phone/address), language (English/اردو), FCM (registers token after login, POST_NOTIFICATIONS prompt, heads-up channels).
- **Other:** siblings panel on Student Fee page (by phone, clickable); challan **QR on the school-copy stub only**; `frontend/vercel.json` SPA rewrite for deep links; app launcher/splash use the school logo.

## Outstanding / to make things live
1. **Render must redeploy `main`** for backend changes (it already serves recent code — `/api/fee-audit` is live).
2. **Vercel must redeploy `main`** for frontend (SPA deep-link fix, Notification Center).
3. **Set `FIREBASE_CREDENTIALS_JSON` on Render** — required for push to actually deliver (without it, messages appear in the in-app Notices list but no heads-up push).
4. Migrations auto-apply on backend startup.

## Build / verify commands (Windows, PowerShell / Git-Bash)
- Backend venv: `SMS_Web\backend\.venv\Scripts\python.exe`. Compile: `python -m py_compile ...`; import test needs dummy `DATABASE_URL`/`CORS_ORIGINS`/`JWT_SECRET`. pytest needs a **live Postgres**.
- Frontend: `cd frontend; $env:VITE_API_URL="https://school-management-backend-1t21.onrender.com"; npm run build` (also `npx tsc -b --noEmit`, `npx oxlint`).
- Android: `cd "BFHS Parent App"; $env:JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"; .\gradlew.bat :app:assembleDebug` → APK at `app\build\outputs\apk\debug\app-debug.apk`. (System Java is 1.8 — MUST use the Android Studio JBR.)

## Gotchas learned
- Read-tool cache can go stale after `git reset` — re-read via `Get-Content` if content looks wrong.
- PowerShell here-strings mangle commit messages with parentheses → use `git commit -F <msgfile>`.
- LF→CRLF git warnings are harmless.
- Reinstalling the APK wipes the saved session (repeated logins) — install **over** the old app to stay logged in.
- QR / logo / notification content changes are backend+web; the Android app just displays what the backend sends.

## Related docs in repo
- `README.md`, `DEPLOYMENT.md` (Step 6 = parent module + Firebase), `PRODUCTION_CHECKLIST.md`.
