# Deployment Guide

## Overview

This guide covers deploying the SMS Web application to production using:
- **Backend**: Render.com (or self-hosted)
- **Frontend**: Vercel or Netlify
- **Database**: Neon (PostgreSQL) or self-hosted PostgreSQL 18+
- **Storage**: File-based (school logos)

All steps assume deployment to cloud platforms with proper secrets management.

---

## Prerequisites

- Neon account (or PostgreSQL 18+ server)
- Render account (for backend) or similar hosting
- Vercel/Netlify account (for frontend)
- GitHub account with this repo
- Environment variables management (never commit `.env`)

---

## Step 1: Set Up Database (Neon)

### 1.1 Create Neon Project
1. Go to [Neon Console](https://console.neon.tech)
2. Create a new project
3. Note the connection string: `postgresql://user:password@host/dbname`
4. Create a database user if needed

### 1.2 Run Migrations

Get the `alembic` tool working locally:

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL="postgresql://..."  # Your Neon URL
alembic upgrade head
```

Verify tables exist:
```bash
DATABASE_URL="postgresql://..." alembic current
```

Expected migration history:
- `9e8f7d6c5b4a` → `b7c8d9e0f1a2` (notification removal) → `c3d4e5f6a7b8` (complete removal)

---

## Step 2: Configure Backend (Render)

### 2.1 Create Render Web Service

1. **Connect GitHub** to Render
2. **New Web Service** → Select this repository
3. **Environment variables** (set before deploying):

```
DATABASE_URL=postgresql://user:password@host.neon.tech:5432/dbname
JWT_SECRET=<generate-a-long-random-string>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://your-alternate-domain.com

# Multi-tenant (optional): master control-plane DB. Defaults to a sibling
# database 'sms_master' on the same host as DATABASE_URL — only set to override.
MASTER_DATABASE_URL=

# Parent module / Firebase Cloud Messaging (optional — see Step 6).
FIREBASE_CREDENTIALS_JSON=
FIREBASE_CREDENTIALS_FILE=
PARENT_JWT_EXPIRE_MINUTES=43200
```

`DATABASE_URL` and `CORS_ORIGINS` are both required — the app raises a `RuntimeError` and refuses to start if either is missing. `PG_BIN_DIR` can be left unset unless `pg_dump`/`pg_restore` aren't already on Render's PATH. The `MASTER_DATABASE_URL` and `FIREBASE_*` variables are all optional: without them the master DB is auto-provisioned as a sibling database and the parent app still works fully except for push delivery.

**DO NOT use default JWT_SECRET** — generate a secure random string:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.2 Build Configuration

**Build Command:**
```bash
pip install -r backend/requirements.txt
```

> Database migrations run **automatically at application startup** (the
> lifespan calls `alembic upgrade head` programmatically), so the build
> command doesn't need to run Alembic. Keeping `&& cd backend && alembic
> upgrade head` in the build command is harmless but redundant. This exists
> because a real deploy once shipped a migration while the service's build
> command only ran `pip install` — the app crashed on boot with
> `UndefinedColumn`. Startup now refuses to run with an out-of-date schema
> instead of failing halfway.

**Start Command:**
```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Health Check:**
```
/health
```

### 2.3 Deploy

Push to GitHub (e.g., to a `production` branch):
```bash
git push origin production
```

Render auto-deploys on push. Check logs for startup issues.

---

## Step 3: Configure Frontend (Vercel)

### 3.1 Prepare Frontend

The frontend reads the backend origin exclusively from `VITE_API_URL` (see `frontend/src/api/client.ts`) — there is no hardcoded or relative fallback. Set it as a Vercel project environment variable (not in a committed file):

```
VITE_API_URL=https://school-management-backend-1t21.onrender.com
```

Note: no trailing slash, no `/api` suffix — the frontend appends `/api` itself. Vite only inlines `import.meta.env.*` at build time, so changing this value requires a redeploy.

### 3.2 Deploy to Vercel

1. **GitHub Integration** → Select repository
2. **Framework**: Vite
3. **Build command**: `npm run build` (should run `tsc -b && vite build`)
4. **Output directory**: `dist`
5. **Environment Variables:**
```
VITE_API_URL=https://school-management-backend-1t21.onrender.com
```

### 3.3 Deploy

Push changes to GitHub:
```bash
git push origin main
```

Vercel auto-deploys.

---

## Step 4: Verify Production

### 4.1 Backend Health

```bash
curl https://your-backend.onrender.com/
# Expected: {"status":"ok","service":"School Management API"}

curl https://your-backend.onrender.com/health
# Expected: {"status":"healthy"}
```

Check the Render deploy logs for the startup sequence: `Connected to Neon` → `Database Ready` → `Application Started`. If you instead see a `RuntimeError` about a missing `DATABASE_URL` or `CORS_ORIGINS`, the service failed to start — fix the environment variable and redeploy.

### 4.2 Authentication

```bash
curl -X POST https://your-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# Expected: {"access_token":"...", "token_type":"bearer", ...}
```

### 4.3 Frontend Loads

Visit `https://your-frontend.vercel.app` and verify:
- Page loads without console errors
- Login form appears
- No CORS errors in browser console

### 4.4 First Login

1. Open frontend
2. Login with `admin` / `admin123`
3. Dashboard loads
4. **Change the default password immediately** in Settings → Users

---

## Step 5: Production Checklist

- [ ] Database URL set and migrations applied (`alembic current` shows latest version)
- [ ] JWT_SECRET is a long random string (not default)
- [ ] CORS_ORIGINS includes frontend domain
- [ ] Default admin password changed (Settings → Users)
- [ ] Backend responds to `/api/ping`
- [ ] Frontend loads and communicates with backend
- [ ] SSL/HTTPS is enforced
- [ ] Database backups are configured
- [ ] Logs are being collected (Render provides log streaming)
- [ ] School name and settings are configured
- [ ] At least one user account exists (beyond default admin)

---

## Step 6: Ongoing Operations

### Database Backups

**Neon** provides automatic daily backups. To restore:
1. Neon Console → Backups tab
2. Select restore point
3. Restore to a new branch or in-place

**Self-hosted PostgreSQL**: Use standard `pg_dump` / `pg_restore`:
```bash
pg_dump -U sms_user sms_db > backup.sql
pg_restore -U sms_user -d sms_db backup.sql
```

### Updating the Application

1. Make changes locally
2. Test locally (`npm run dev` + `uvicorn`)
3. Commit and push to GitHub
4. Render/Vercel auto-deploy on push
5. Verify production at `https://your-backend/api/ping`

### Rolling Back

If a deployment breaks production:

1. **Render**: Click "Manual Deploy" → select previous successful build
2. **Vercel**: Deployments tab → select previous deployment → click "Promote to Production"
3. **Database**: If migrations caused issues, restore from backup and re-run migrations

### Monitoring

- **Render Logs**: Visible in dashboard, auto-tails on deployment
- **Frontend Console**: Browser DevTools → Console tab (watch for errors)
- **Error Tracking**: Consider integrating Sentry for production error logging

---

## Troubleshooting

### "FATAL: database does not exist"
- Check `DATABASE_URL` is set correctly
- Verify Neon/PostgreSQL server is running
- Re-run `alembic upgrade head`

### "401 Unauthorized" on API calls
- Check `JWT_SECRET` matches between frontend and backend
- Verify JWT token is being sent in `Authorization: Bearer <token>` header
- Check token expiration (`JWT_EXPIRE_MINUTES` in env)

### CORS errors in browser
- Check `CORS_ORIGINS` includes the exact frontend domain
- Verify the frontend was built with the correct `VITE_API_URL` (inlined at build time — check the deployed JS bundle if unsure, or just redeploy after fixing the Vercel env var)

### "Default admin password still active"
- SSH into production or use Render shell
- Run: `curl -X POST https://your-backend/api/users/1/password -H "Authorization: Bearer <admin-token>" -d "{\"password\": \"new_password\"}"`
- Change password via UI: Settings → Users → Edit Admin

### Migrations fail
- Check `DATABASE_URL` is correct
- Verify PostgreSQL version is 18+ (Neon provides 18+)
- Review migration file error message
- If schema mismatch, consider restoring database from backup

---

## Environment Variables Reference

**Backend (Render):**

| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql://user:pass@host.neon.tech/dbname` | **Required.** Neon connection string. Missing it raises `RuntimeError` at startup. |
| `CORS_ORIGINS` | `https://frontend.vercel.app,https://other.com` | **Required.** Comma-separated. Missing it raises `RuntimeError` at startup. |
| `JWT_SECRET` | `<64-char random hex>` | Required. Generate with `secrets.token_hex(32)`. |
| `JWT_ALGORITHM` | `HS256` | Optional, defaults to `HS256`. |
| `JWT_EXPIRE_MINUTES` | `480` | Optional, defaults to `480` (8 hours). |
| `PG_BIN_DIR` | _(leave unset)_ | Optional. Only needed if `pg_dump`/`pg_restore` aren't already on PATH. |
| `DATA_DIR` | `/var/data/sms` | Optional. Only durable if backed by a Render persistent disk mounted at `/var/data`. |

**Frontend (Vercel):**

| Variable | Example | Notes |
|----------|---------|-------|
| `VITE_API_URL` | `https://school-management-backend-1t21.onrender.com` | **Required.** Bare Render origin, no `/api` suffix. Inlined at build time — changing it requires a redeploy. |

---

## Support & Rollback Plan

### If Production Goes Down

1. **Immediate**: Check Render/Vercel logs for error
2. **Backend Issue**: Use Render's "Manual Deploy" to revert to last working build
3. **Database Issue**: Restore from Neon backup, re-run migrations
4. **Frontend Issue**: Revert to last successful Vercel deployment
5. **All Else**: Contact hosting support with error logs

### Recovery Plan
- Maintain weekly backups (Neon auto-does this)
- Keep migration history clean (never squash `alembic` revisions)
- Document all production config changes
- Test migrations on a staging database before production

---

## Step 6: Parent Module & Firebase (Android app)

The parent-facing Android app ("BFHS Parent") is read-only and talks to this
same backend. Its tables are per-school (added by migration `f6a7b8c9d0e1`,
applied to every tenant database automatically at startup); the mobile→school
login routing lives in the master database (`parent_directory`, auto-created).

### 6.1 Backend — Firebase service account (optional, enables push)

Push notifications are the only part that needs Firebase. The rest of the
parent module (login, dashboard, attendance, fees, extra charges, notification
history) works without it.

1. In the [Firebase Console](https://console.firebase.google.com) create a
   project, then **Project Settings → Service accounts → Generate new private key**.
2. Provide it to the backend by **one** of:
   - **Render (recommended):** set `FIREBASE_CREDENTIALS_JSON` to the full JSON
     on one line (Render env values are durable; a file path is not).
   - **File:** set `FIREBASE_CREDENTIALS_FILE` to an absolute path, or drop the
     file at `backend/firebase/service-account.json` (git-ignored).
3. `PARENT_JWT_EXPIRE_MINUTES` (default 43200 = 30 days) controls how long a
   parent stays signed in.

> **Never commit** `service-account.json` or `google-services.json`. Both are
> git-ignored. Rotate the key immediately if it ever leaks.

### 6.2 Android app — configuration

1. In the same Firebase project add an **Android app** with package
   `com.bfhs.parent`, download `google-services.json`, and place it at
   `BFHS Parent App/app/google-services.json` (git-ignored). The Gradle
   `google-services` plugin applies only when that file is present, so the app
   still builds without it.
2. Set the backend URL: `BASE_URL` in `BFHS Parent App/app/build.gradle.kts`
   (`defaultConfig → buildConfigField`) → your Render backend origin.
3. Build: `./gradlew :app:assembleDebug` (or a release build for the Play Store).

### 6.3 Provisioning parent logins

- In the web admin open **Parents → “Sync from Students”** to create a login for
  every parent mobile number found on that school's students (default password =
  the mobile number; the parent is prompted to change it). Accounts can also be
  added individually.
- Parents log in with **mobile number + password** (no OTP). One mobile number
  linked to several students shows all of them.

### 6.4 Notifications

- **Automatic:** marking a student **Absent** pushes an alert to that child's parents.
- **Manual (Notification Center):** **Admin** sends announcements / fee reminders
  to a student, class, or the whole school; **Accountant** may send fee reminders
  only; **Teachers** cannot send. Every send is recorded in Notification History
  with delivery counts.

---

## Next Steps

After deploying:
1. Customize school logo and settings (School Settings page)
2. Create user accounts for teachers and accountants (Users page)
3. Import student data (Backup → Import Students)
4. Test all workflows with real data
5. Set up email notifications (if implementing later)

---

**Version**: Phase 1 (June 2026)  
**Last Updated**: 2026-06-29  
**Deployment Status**: Ready for production
