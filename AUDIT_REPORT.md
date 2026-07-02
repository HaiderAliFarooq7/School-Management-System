# SMS_Web — Complete Project Audit

Date: 2026-07-02 · Scope: full stack (FastAPI + SQLAlchemy + PostgreSQL backend; React 19 + TypeScript + MUI v7 frontend) · Deployment: Render (API) + Neon (DB) + Vercel (frontend), production-only.

## 1. Architecture assessment

**What is already good**

- Clean layering: `routers/` → `services/` → `models/` + `schemas/`, Alembic migrations, Pydantic settings with fail-fast validation of `DATABASE_URL`/`CORS_ORIGINS`.
- JWT auth with role-based access (`require_role`) and teacher class-scoping (`scope_class_filter`) applied on the student roster.
- Global exception handler that logs the traceback and returns a generic message (no stack-trace leaks); rotating file logs sized for free hosting.
- Ephemeral-host discipline: PDFs/exports/backups are streamed from memory or temp files and deleted; only logo + photos persist.
- Literal routes declared before `/{id}` routes (no shadowing); parameterized queries everywhere (no SQL injection found); CORS restricted to explicit origins; upload size caps with streaming writes.
- Self-cleaning backend smoke-test suite.

**Structural gaps**

- No pagination on any list endpoint (students, vouchers, filters all return unbounded result sets).
- No API versioning, no OpenAPI tags/descriptions beyond defaults (acceptable for an internal tool, noted as debt).
- `repositories/` package exists but is empty (dead scaffolding).
- Legacy duplicate import/export endpoints in `backup.py` overlap the newer import wizard in `students.py`.

## 2. Security findings

| # | Severity | Finding |
|---|----------|---------|
| S1 | **High** | Teacher scope not enforced in `attendance.py`: `POST /mark`, `GET /api/attendance`, `GET /summary`, and `GET /student/{id}` let a Teacher read or write attendance for **any** class/student, not just their assigned class. |
| S2 | **High** | No rate limiting: `POST /api/auth/login` is brute-forceable without restriction. |
| S3 | Medium | No security headers on API responses (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `HSTS`, `Cache-Control: no-store` on auth). |
| S4 | Medium | Weak password policy: 6-char minimum on self change-password; **no minimum at all** on admin user-create / password-reset. |
| S5 | Medium | Default `JWT_SECRET` only logs a warning instead of refusing to start; 8-hour tokens with no revocation (role changes only apply at next login — `is_active` *is* re-checked per request). |
| S6 | Low | JWT in `localStorage` — XSS-stealable. Accepted trade-off for the cross-origin Vercel/Render split; mitigated by React's output encoding and no `dangerouslySetInnerHTML` usage (verified). |
| S7 | Low | `GET /api/school` is unauthenticated (school name/phone/address/challan note exposed publicly). `GET /api/school/logo` must stay public (used in `<img src>`), the rest should not. |
| S8 | Low | No audit logging of sensitive actions (payments, deletes, restore, reset). `PaymentHistory` records amounts but not the acting user. |
| S9 | Low | Payment race: `pay_voucher`/`pay_charge` read-check-write without row locking — two concurrent payments can overshoot the balance check. |
| S10 | Low | Registration-number generation is read-increment-write — two simultaneous admissions can collide on the unique constraint (500 instead of graceful retry). |

## 3. Performance findings

| # | Impact | Finding |
|---|--------|---------|
| P1 | **High** | N+1 queries in `list_students`/`search_advanced`: 3 extra queries per student (fee status + pending totals). 300 students ⇒ ~900 queries per page view. |
| P2 | **High** | Same pattern in `search_vouchers` (2/row), `filter_vouchers` (1/student), `fee_reports/pending` (2/student), `attendance/summary` (1/student), `attendance/daily-status` (2/class), `students/pending-fee-names` (2/student). |
| P3 | Medium | `bulk_generate` runs one SELECT + one COMMIT per student (not transactional as a batch). |
| P4 | Medium | Missing indexes: `extra_charge.student_id`, `student.class_name`, `student.status`, `payment_history(target_type, target_id)`, `attendance_record(class_name, attendance_date)`, `fee_voucher.status`. |
| P5 | Medium | Frontend ships one monolithic bundle — all 17 pages + MUI DataGrid + Charts loaded eagerly, even for a Teacher who only ever sees Attendance. No route-level code splitting. |
| P6 | Medium | Students search fires one API request per keystroke (no debounce) — each triggering the P1 N+1 storm. |
| P7 | Low | React Query has no `staleTime` — every remount/focus refetches everything. |
| P8 | Low | No response compression (gzip) on the API. |
| P9 | Low | `fee-reports/analytics` loads every voucher row into Python to aggregate (fine at current scale, poor at 10k+ vouchers). |

## 4. UI/UX findings

| # | Finding |
|---|---------|
| U1 | **Mobile is broken**: `AppShell` uses a *persistent* 250px drawer with no breakpoint handling — on a 360px phone the drawer overlays/squeezes all content. No temporary drawer, no responsive variant anywhere (`useMediaQuery` appears 0 times in the codebase). |
| U2 | 31 native `alert()`/`confirm()` calls across 8 files — blocking, unstyled, unprofessional. |
| U3 | No toast/snackbar system; success/error feedback is stale inline text or nothing. |
| U4 | No loading skeletons ("Loading…" plain text), no designed empty states. |
| U5 | Default MUI theme, `index.html` title is literally "frontend", no dark mode, no brand typography. |
| U6 | Filter toolbars use fixed widths without wrapping on some pages — overflow at small widths. |
| U7 | No 404 route — unknown URLs render a blank shell. No app-level error boundary (only the dashboard charts have one). |
| U8 | Login page: no loading state on submit, no show-password toggle, no `autocomplete` attributes, `height: 100vh` (keyboard-overlap issues on mobile). |
| U9 | Accessibility: **zero** `aria-label`s in the app; icon-only buttons unlabeled; status conveyed by color-only chips; heading levels skipped (h5→h6 without h1–h4). |
| U10 | Tables: mixed usage of DataGrid (good) and static `Table` (no sorting/pagination/sticky headers). Wide grids on mobile rely on inner scrolling with no visual affordance. |

## 5. Database findings

- Schema is sound: FKs with correct `ondelete` behavior, unique constraints on natural keys, check constraint on attendance status, `NUMERIC(12,2)` for money.
- Missing performance indexes (P4 above).
- `PaymentHistory` is intentionally FK-free (survives voucher deletion) — good design, but rows never record *who* took the payment (S8).
- No soft deletes — deliberate and documented (Admin hard-delete is a feature); promote-all prunes history by design.

## 6. Testing / docs

- Backend: 22-test self-cleaning smoke suite (good). No frontend tests, no E2E (app is production-only, no local runtime — E2E would need a staging environment).
- Docs: README, DEPLOYMENT, CHANGELOG, RELEASE_REPORT exist at repo root.

## 7. Remediation plan (this branch, in order)

1. **Security** — enforce Teacher scoping in attendance; login rate limiting; security headers + gzip; password policy (8+ chars everywhere); harden JWT-secret startup behavior; authenticate `GET /api/school`; row-locking on payments.
2. **Backend performance** — replace all N+1 patterns with aggregate joins/subqueries; batch `bulk_generate`; add missing indexes via Alembic migration.
3. **Frontend foundation** — professional theme + dark/light mode with persistence; route-level code splitting; React Query tuning; app metadata; 404 page; global error boundary.
4. **Responsive shell** — mobile temporary drawer / desktop persistent drawer, labeled controls, user identity in the top bar.
5. **UX systems** — snackbar/toast provider and styled confirm dialog replacing every `alert()`/`confirm()`; debounced search; loading skeletons and empty states.
6. **Docs + verification** — build/lint/type-check clean; updated documentation; final report of everything changed and remaining debt.

Items deliberately **not** changed (business logic preserved): role permission matrix, Admin hard-delete semantics, voucher/discount/status rules, promote-all pruning, ephemeral-file constraints, production-only deployment model.
