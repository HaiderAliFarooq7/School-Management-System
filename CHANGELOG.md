# Changelog

## [Unreleased] — Production Readiness Pass (Phase 1)

Full audit and cleanup pass to prepare the app for production. No deployment was performed — this work was done and verified entirely against the local Postgres database and local dev servers, per explicit instruction.

### Removed — Notification / Communication System (entire feature, v1 scope decision)

This was a fully-built, working feature (WhatsApp Cloud API integration, SMS gateway placeholder, queue/retry worker, templates, history, analytics) — removed wholesale per product decision for v1, not because it was broken.

**Backend files deleted:**
- `app/models/notification_log.py`, `notification_queue.py`, `notification_template.py`, `communication_provider.py`
- `app/routers/communication.py`
- `app/schemas/communication.py`
- `app/services/notification_service.py`, `app/services/crypto.py`
- `app/services/providers/` (entire package: `base.py`, `android_gateway_provider.py`, `whatsapp_cloud_provider.py`)

**Backend files modified** (stripped of notification/communication references):
- `app/main.py` — removed the `/api/communication` router, the background notification-queue worker (`_notification_queue_worker`, asyncio task in `lifespan`), and the leftover `/api/debug-db` diagnostic endpoint.
- `app/models/__init__.py` — removed the four deleted model imports.
- `app/models/school.py` / `app/schemas/school.py` / `app/routers/school.py` — removed all `sms_*`, `email_*`/`smtp_*`, and `auto_notify_absent` fields and the `/school/notification-settings` and `/school/communication-settings` endpoints.
- `app/routers/attendance.py` — removed `_queue_absent_notifications` and the background task that queued an Absent notification after `mark_attendance`.
- `app/routers/backup.py`, `app/routers/students.py`, `app/services/student_import_service.py` — removed `NotificationQueue`/`NotificationLog` from bulk-delete/reset/wipe operations.
- `app/config.py` — removed `credentials_encryption_key` (was only used to encrypt WhatsApp tokens).
- `backend/.env` — removed `CREDENTIALS_ENCRYPTION_KEY`.
- `backend/requirements.txt` — removed `httpx` and the standalone `cryptography` pin (both were only needed by the WhatsApp provider/crypto module; `python-jose[cryptography]` still pulls in `cryptography` transitively for JWT).
- `backend/tests/conftest.py`, `backend/tests/test_smoke.py` — removed all WhatsApp/communication fixtures and the 8 tests that exercised the removed feature (templates/providers, queueing, analytics, WhatsApp account CRUD, test-message). 15 of the original test count remain and pass.

**Frontend files deleted:**
- `src/pages/CommunicationPage.tsx`, `src/pages/WhatsAppAccountsPage.tsx`
- `src/components/BulkSendPanel.tsx`, `ProviderDialog.tsx`, `TemplateEditor.tsx`, `QueueTable.tsx`, `HistoryTable.tsx`, `MessagePreviewDialog.tsx`, `WhatsAppAccountDialog.tsx`, `WhatsAppTestMessageDialog.tsx`
- `src/api/communication.ts`, `src/api/whatsappAccounts.ts`

**Frontend files modified:**
- `src/App.tsx`, `src/components/layout/AppShell.tsx` — removed the `/communication` and `/whatsapp-accounts` routes and their nav items.
- `src/api/school.ts` — removed `sms_*`/`email_*`/`auto_notify_absent` fields from the `School` interface and the two settings-update functions.
- `src/pages/SchoolSettingsPage.tsx` — removed the "Communication" section (auto-notify toggle).
- `src/pages/DashboardPage.tsx` — removed the admin-only "Communication Overview" analytics card.
- `src/pages/StudentFeePage.tsx` — removed the "Send Custom/Attendance/Fee Reminder/WhatsApp" compose buttons and the message-preview/queue flow.
- `src/pages/BackupPage.tsx`, `src/pages/PromoteStudentsPage.tsx`, `src/components/StudentImportWizard.tsx` — updated wording in danger-zone copy that referenced "notification history."

**Database migration** (`backend/alembic/versions/c3d4e5f6a7b8_remove_notification_system.py`):
- Drops tables: `notification_queue`, `notification_template`, `communication_provider`, `notification_log`.
- Drops columns on `school`: `sms_enabled`, `sms_gateway`, `sms_api_key`, `sms_api_secret`, `sms_sender_id`, `email_enabled`, `smtp_server`, `smtp_port`, `smtp_email`, `smtp_password`, `auto_notify_absent`.
- Applied to the local dev database; `downgrade()` recreates the full prior schema if ever needed.

### Fixed

- Removed a leftover `/api/debug-db` diagnostic endpoint in `main.py` that exposed the database name and full table list with no auth — a real, if minor, information-disclosure issue. Introduced during recent debugging (see git history) and never removed.
- Removed dead `absent_student_ids` bookkeeping in `attendance.py` now that nothing consumes it.

### Added

- `app/services/bootstrap.py` (`ensure_default_admin`) — on startup, if the `user_account` table has zero rows (a brand-new database), creates the `Admin` role and an `admin`/`admin123` account automatically. No-ops the instant any user exists, so it never touches a database that's already been used (dev or prod). Wired into `app.main`'s `lifespan`, replacing the removed notification-worker startup task.

### Verified

- Backend boots with no startup exceptions, no SQLAlchemy warnings, no background task errors (confirmed via fresh `uvicorn` run + log inspection).
- All 12 remaining backend routers respond as expected (spot-checked `/api/ping`, `/api/auth/login`, `/api/students`, `/api/school`, `/api/grades`, `/api/dashboard/stats`; the removed `/api/communication/*` routes correctly 404).
- `python -m pytest -q` — 15/15 passing after the notification-test removal.
- `npm run build` (`tsc -b && vite build`) — zero TypeScript errors.
- `npm run lint` (oxlint) — no new warnings (one pre-existing, unrelated fast-refresh warning in `AuthContext.tsx`).
- Manually exercised in a running browser session against the local dev servers: Login (admin/admin123), Dashboard (stats + attendance status + analytics charts), Students, Attendance, Fee Vouchers, School Settings (save works, no Communication section), Backup page. No console errors, no failed network requests, no `/communication` or `/whatsapp` references left anywhere in the UI or nav.

### Recommendations before deployment

1. **Rotate `JWT_SECRET`** for production — the current value in `backend/.env` is a local dev secret and must not be reused.
2. **Set a real `DATABASE_URL`** pointing at the production Postgres instance (e.g. Neon) — not yet connected, per instruction.
3. **Set `CORS_ORIGINS`** to the exact production frontend origin(s) before deploying frontend/backend to separate hosts (e.g. Vercel + Render).
4. **Change the default admin password** immediately after first deploying to a fresh database — `ensure_default_admin` logs a warning every time it fires specifically to make this visible.
5. **Run `alembic upgrade head`** against the production database as part of the deploy step — the migration history is linear and verified locally (`b7c8d9e0f1a2` → `c3d4e5f6a7b8`).
6. **Re-run the full manual test pass** (Phase 9 list: Login, Dashboard, Students, Attendance, Fees, Reports, School Settings, Backup, Restore, Import, Export) against a staging environment before going live, since this pass was done against local Postgres only.
7. Phases 6 (full model/migration/DB diff), 7 (every endpoint), 8 (full frontend page-by-page pass), and 10 (broader refactor: folder structure, naming, performance) were scoped to this removal + stabilization pass and were verified only for the areas this change touched. A follow-up pass should re-run those phases against the now-smaller surface area before the next milestone.
