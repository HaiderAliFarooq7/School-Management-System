import datetime
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings


def _pg_conn_parts(database_url: str | None = None) -> dict:
    # database_url looks like postgresql+psycopg://user:pass@host:port/dbname
    # (Neon, in production). DATABASE_URL is required and validated at
    # startup, so a missing hostname here means the connection string itself
    # is malformed — fail loudly rather than silently guessing localhost.
    raw = (database_url or settings.database_url).replace("+psycopg", "")
    parsed = urlparse(raw)
    if not parsed.hostname:
        raise RuntimeError("DATABASE_URL has no hostname — check the Neon connection string.")
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname,
        "port": str(parsed.port or 5432),
        "dbname": parsed.path.lstrip("/"),
    }


def _bin_path(name: str) -> str:
    """Render runs Linux, where pg_dump/pg_restore are just on PATH — PG_BIN_DIR
    only needs to be set if they're installed somewhere non-standard."""
    if settings.pg_bin_dir:
        return str(Path(settings.pg_bin_dir) / name)
    return name


def backup_filename() -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"sms_backup_{timestamp}.dump"


def backup_database(database_url: str | None = None) -> str:
    """Runs pg_dump (of the given tenant database — defaults to the original
    school) into a fresh OS temp file and returns its path. The caller is
    responsible for streaming it to the client and deleting it afterwards
    (see the backup router) — nothing is retained on the server."""
    fd, dest_path = tempfile.mkstemp(suffix=".dump", prefix="sms_backup_")
    os.close(fd)
    conn = _pg_conn_parts(database_url)

    env = os.environ.copy()
    env["PGPASSWORD"] = conn["password"]
    cmd = [
        _bin_path("pg_dump"),
        "-h", conn["host"], "-p", conn["port"], "-U", conn["user"],
        "-F", "c", "-f", dest_path, conn["dbname"],
    ]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise RuntimeError(f"pg_dump failed: {result.stderr}")
    return dest_path


def restore_database(src_path: str, database_url: str | None = None) -> None:
    conn = _pg_conn_parts(database_url)
    env = os.environ.copy()
    env["PGPASSWORD"] = conn["password"]
    cmd = [
        _bin_path("pg_restore"),
        "-h", conn["host"], "-p", conn["port"], "-U", conn["user"],
        "-d", conn["dbname"], "--clean", "--if-exists", "--single-transaction", src_path,
    ]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pg_restore failed: {result.stderr}")
