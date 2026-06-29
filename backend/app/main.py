from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

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
    school,
    students,
    users,
)
from app.services.bootstrap import ensure_default_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_default_admin()
    yield


app = FastAPI(title="School Management System", lifespan=lifespan)

if settings.jwt_secret == "change-this-secret-in-production":
    logger.warning(
        "JWT_SECRET is still the default placeholder value — set a real secret "
        "via the JWT_SECRET environment variable before going to production."
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


@app.get("/api/ping")
def ping():
    return {"status": "ok"}


_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
