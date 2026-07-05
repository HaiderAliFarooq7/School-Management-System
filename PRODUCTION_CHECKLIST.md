# Production Checklist — BFHS Parent Module

Every step to deploy and verify the parent module (backend API, React admin
pages, and the **BFHS Parent** Android app) into production, plus rollback and
post-deployment validation.

The parent module is **additive** and **multi-tenant aware**: it reuses the
existing master-DB + database-per-school architecture. Parent tables live in
each school's tenant database; a master-side `parent_directory` (auto-created)
routes mobile-number logins to the right school; the parent JWT carries the
signed `school_id` claim so every request is pinned to one tenant DB.

> Legend: `[ ]` = do it, `[x]` = already done in code/repo. Commands assume the
> repo root unless noted. Backend commands run from `backend/`.

---

## 0. Pre-flight

- [x] Code merged/pushed to `feature/parent-module` (commits `40cd3ea`, `e939915`, `c79f838`).
- [ ] Open a PR from `feature/parent-module` and get it reviewed/merged to your deploy branch (`main`).
- [ ] Confirm you can reach: Neon console, Render dashboard, Vercel dashboard, Firebase console, and a machine with Android SDK + JDK 17.
- [ ] Take a fresh Neon backup (branch or `pg_dump`) of the master DB **and** every tenant DB before deploying.
- [ ] Verify no secrets are tracked: `git ls-files | grep -Ei "service-account|google-services|\.env$"` returns nothing.

---

## 1. Database migrations

The app runs migrations **automatically at startup**: `init_master()` creates
the master schema (including `parent_directory`) via metadata, then applies the
full Alembic chain (`alembic upgrade head`) to **every active school database**.
The parent tables come from migration **`f6a7b8c9d0e1`** (down-revision
`e5f6a7b8c9d0`).

You can also run migrations manually before/independently of deploy:

- [ ] Install deps: `pip install -r requirements.txt` (adds `firebase-admin`, `httpx`).
- [ ] Confirm current head is the parent migration:
  ```bash
  DATABASE_URL="postgresql://…"  alembic heads      # expect: f6a7b8c9d0e1 (head)
  DATABASE_URL="postgresql://…"  alembic current    # per-tenant DB
  ```
- [ ] Apply to the default/first tenant DB: `DATABASE_URL="postgresql://…tenant…" alembic upgrade head`
- [ ] For each additional school DB, either let startup migrate them (default) or run `alembic upgrade head` against each `tenant_database_url`.
- [ ] Verify the four tenant tables exist in a school DB: `parent_account`, `parent_device`, `parent_notification`, `notification_log`.
- [ ] Verify the master table exists in the master DB: `parent_directory` (created by `init_master_schema`, no Alembic step).

**Post-migration sanity**: existing staff endpoints must be unaffected — additive migration only, no columns dropped/altered.

---

## 2. Environment variables (backend / Render)

Set in **Render → Service → Environment**. Never commit these.

**Required (already in use — unchanged):**
- [ ] `DATABASE_URL` — Neon connection string of the first/default tenant DB.
- [ ] `JWT_SECRET` — long random string (`python -c "import secrets; print(secrets.token_hex(32))"`). App refuses to start on the placeholder value.
- [ ] `CORS_ORIGINS` — comma-separated Vercel/prod frontend origins.
- [ ] `JWT_ALGORITHM=HS256`, `JWT_EXPIRE_MINUTES=480` (staff token lifetime).

**Multi-tenant (optional):**
- [ ] `MASTER_DATABASE_URL` — only if the master DB is not the default sibling `sms_master` on the same host.

**Parent module (optional — push only):**
- [ ] `FIREBASE_CREDENTIALS_JSON` — service-account JSON on one line (**preferred on Render**), OR
- [ ] `FIREBASE_CREDENTIALS_FILE` — absolute path to the JSON file, OR leave both unset and ship `backend/firebase/service-account.json`.
- [ ] `PARENT_JWT_EXPIRE_MINUTES=43200` — parent session length (default 30 days).

> Without any `FIREBASE_*` value the parent module still works fully — only push
> delivery is skipped (logged as "Firebase not configured. Push disabled").

---

## 3. Firebase setup

**Backend (sending push):**
- [ ] Firebase console → create/select project.
- [ ] **Project Settings → Service accounts → Generate new private key** → download JSON.
- [ ] Provide it via `FIREBASE_CREDENTIALS_JSON` (Render) or the git-ignored `backend/firebase/service-account.json`. **Never commit it.**
- [ ] Confirm at startup the log reads `Firebase Cloud Messaging initialized.` (not "Push disabled").

**Android (receiving push):**
- [ ] Firebase console → **Add app → Android**, package name **`com.bfhs.parent`**.
- [ ] Download `google-services.json` → place at `BFHS Parent App/app/google-services.json` (git-ignored).
- [ ] Enable **Cloud Messaging** API for the project.
- [ ] Rotate keys immediately if either JSON leaks.

---

## 4. Render deployment (backend)

- [ ] Push the merged branch; Render auto-deploys (or **Manual Deploy**).
- [ ] Build command: `pip install -r backend/requirements.txt`.
- [ ] Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- [ ] Watch logs for, in order: `Connected to Neon` → `Database Ready` → `All school databases migrated` → `Application Started`.
- [ ] Health check green: `GET /health` → `{"status":"healthy"}`.
- [ ] Smoke the parent surface is mounted: `GET /docs` shows the `parent` and `parent-admin` tags.

---

## 5. Vercel deployment (frontend / admin panel)

The parent **admin** pages (Parents, Notification Center) ship with the existing
React app. No new frontend env var is needed.

- [ ] Confirm `VITE_API_URL` points at the Render backend origin (no trailing slash, no `/api`).
- [ ] Redeploy the frontend (Vite inlines env at build time).
- [ ] Log in as **Admin** → nav shows **Parents** and **Notifications**.
- [ ] Log in as **Accountant** → nav shows **Notifications** (fee reminders only); **Parents** hidden.
- [ ] Log in as **Teacher** → neither appears.

---

## 6. Android build

- [ ] Set `BASE_URL` in `BFHS Parent App/app/build.gradle.kts` (`defaultConfig → buildConfigField`) to the Render backend origin (with trailing slash).
- [ ] Ensure `app/google-services.json` is present.
- [ ] Debug build: `./gradlew :app:assembleDebug` → APK at `app/build/outputs/apk/debug/app-debug.apk`.
- [ ] Release build (Play Store): configure signing, `./gradlew :app:bundleRelease` → AAB.
- [ ] Install on a device, confirm splash → login renders.

---

## 7. Provision parent logins

- [ ] Web admin → **Parents → “Sync from Students”** (per school) → creates a `parent_account` for every parent mobile on that school's students (default password = mobile number) and registers each in the master `parent_directory`.
- [ ] Spot-check a few rows: correct mobile, `Default pwd` chip present, student count > 0.
- [ ] (Optional) Add an individual parent via **Add Parent**.

---

## 8. Login testing

- [ ] **Default password**: app login with a synced mobile number + that same number as password → success; response indicates `must_change_password = true`.
- [ ] **Change password** from the app (or `POST /api/parent/change-password`) → `must_change_password` clears.
- [ ] **Wrong password** → 401.
- [ ] **Multiple children**: a mobile linked to 2+ students shows all of them on the dashboard (`GET /api/parent/students`).
- [ ] **Auto-login**: reopen the app → lands on dashboard using the stored JWT (DataStore).
- [ ] **Token separation**: a staff JWT is rejected by `/api/parent/*` (401); a parent JWT is rejected by staff endpoints like `/api/students` (401).

---

## 9. Notification testing

**Automatic (absent):**
- [ ] As Teacher/Admin, mark a student **Absent** for **today** via the attendance grid.
- [ ] That student's parent receives a push (if Firebase configured) and an inbox row (`GET /api/parent/notifications`, type `absent`).
- [ ] Re-saving the same absent record does **not** produce a duplicate alert.

**Manual (Notification Center):**
- [ ] **Admin** sends an **Announcement** to *Whole School* → history row shows recipients/delivered/failed; parents see it in-app.
- [ ] **Admin** sends a **Fee Reminder** to a *Class* / a single *Student*.
- [ ] **Accountant** can send **Fee Reminder** but is blocked (403) from Announcement/Absent.
- [ ] **Teacher** is blocked (403) from sending anything.
- [ ] Notification deep-link: tapping a fee/absent push opens the correct screen for the right child.

**Firebase-off path:**
- [ ] With Firebase unconfigured, sends still succeed (inbox + log written), `delivered=0`, no crash.

---

## 10. Multi-tenant verification

- [ ] Two schools exist in the master DB (School A, School B), each its own tenant database.
- [ ] A parent whose children are in **School A** logs in → sees only School A students; `GET /api/parent/students` never returns School B data.
- [ ] Inspect the parent JWT (jwt.io) → carries `type=parent` and the correct `school_id`; there is no way to pass a different school_id (it is signed).
- [ ] Admin of School A, in **Parents**, sees only School A parents; a notification “Whole School” reaches only School A parents.
- [ ] `parent_directory` in the master DB maps each mobile’s `mobile_core` to exactly one `school_id`.
- [ ] Confirm no cross-tenant leakage: request a School B student id on a School A parent token → 404 (not another family's data).

---

## 11. Rollback

Rollback is safe because the change is additive.

**Application / code:**
- [ ] Render → **Manual Deploy → Rollback** to the previous image, OR `git revert` the three commits and redeploy.
- [ ] Frontend: Vercel → redeploy the previous successful build (parent nav items disappear; nothing else affected).

**Database (only if you must remove the parent tables):**
- [ ] Per tenant DB: `alembic downgrade e5f6a7b8c9d0` (drops `parent_account`, `parent_device`, `parent_notification`, `notification_log`).
- [ ] Master `parent_directory` is harmless to leave; to drop it, remove the table manually (it is not managed by Alembic).
- [ ] Because startup re-migrates to head, **pin the old code first** before downgrading, or the next boot will re-create the tables.

**Android:** revert `BASE_URL` / re-publish the prior APK/AAB if needed. The app is read-only, so no data cleanup is required.

**Firebase:** to fully disable push, unset `FIREBASE_*` and redeploy — the module keeps working without it.

---

## 12. Post-deployment validation

- [ ] Existing staff flows unchanged: staff login, students, fees, attendance, reports, backup all still pass (run `pytest` against a staging DB).
- [ ] `pytest backend/tests/test_parent_module.py` green against a live DB (parent login, multiple children, tenant isolation, role rules).
- [ ] Render logs show no unhandled exceptions after the first parent logins and sends.
- [ ] A real parent installs the app, logs in, and can view attendance / monthly fee / extra charges / notifications / school profile.
- [ ] One real absent-marking produces a real push on a real device.
- [ ] Bootstrap/super-admin passwords rotated (`admin`, `superadmin`) if not already.
- [ ] Monitoring: watch `failed_count` in Notification History for a spike (indicates bad/expired tokens — invalid tokens are auto-deactivated).
- [ ] Confirm backups still run and include the new tables.

---

## Quick reference

| Item | Value |
| --- | --- |
| Parent tenant migration | `f6a7b8c9d0e1` (down: `e5f6a7b8c9d0`) |
| Master routing table | `parent_directory` (auto-created) |
| Parent API base | `/api/parent/*` |
| Admin API base | `/api/admin/parents/*`, `/api/admin/notifications/*` |
| Android package | `com.bfhs.parent` |
| Firebase (backend) | `FIREBASE_CREDENTIALS_JSON` / `_FILE` / `backend/firebase/service-account.json` |
| Firebase (Android) | `BFHS Parent App/app/google-services.json` |
| Never commit | `service-account.json`, `google-services.json`, `.env` |
