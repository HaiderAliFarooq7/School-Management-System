from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import logger
from app.routers import (
    attendance,
    auth,
    backup,
    dashboard,
    extra_charges,
    fee_reports,
    fee_vouchers,
    grades,
    master,
    school,
    students,
    users,
)
from app.services.bootstrap import (
    ensure_default_admin,
    ensure_default_logo,
    init_master,
    verify_database_ready,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init_master self-provisions the multi-tenant control plane (master DB,
    # super admin, first-school registration) and migrates every active
    # school database — a fresh deploy or an in-place conversion both boot
    # with zero manual steps.
    init_master()
    verify_database_ready()
    ensure_default_admin()
    ensure_default_logo()
    logger.info("Application Started")
    yield


app = FastAPI(title="School Management System", lifespan=lifespan)

# A forgeable signing key means anyone can mint an Admin token, so this is a
# hard failure, not a warning. DEPLOYMENT.md documents JWT_SECRET as required.
if settings.jwt_secret == "change-this-secret-in-production":
    raise RuntimeError(
        "JWT_SECRET is still the default placeholder value. Generate a real "
        "secret (e.g. python -c \"import secrets; print(secrets.token_hex(32))\") "
        "and set it as the JWT_SECRET environment variable before starting."
    )

# Needed whenever the frontend is hosted on a different origin than this API
# (e.g. Vercel frontend + Render backend). Harmless when the frontend is
# instead served by the StaticFiles mount below, since same-origin requests
# never trigger a CORS check.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    # Render terminates TLS at its proxy, so the original scheme arrives in
    # X-Forwarded-Proto rather than request.url.scheme.
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
    # API responses are data, never a document to render or cache. Scoped to
    # /api so the interactive /docs page (which loads Swagger's JS) still works.
    if request.url.path.startswith("/api"):
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    if request.url.path.startswith("/api/auth"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Logs the full traceback server-side (rotating file) and returns a
    clean, generic message to the client instead of leaking a stack trace."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong. Please try again."},
    )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(students.router)
app.include_router(grades.router)
app.include_router(school.router)
app.include_router(fee_vouchers.router)
app.include_router(extra_charges.router)
app.include_router(dashboard.router)
app.include_router(fee_reports.router)
app.include_router(attendance.router)
app.include_router(backup.router)
app.include_router(master.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "School Management API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/ping")
def ping():
    return {"status": "ok"}
