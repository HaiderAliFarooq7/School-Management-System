import datetime
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings


def _pg_conn_parts() -> dict:
    # database_url looks like postgresql+psycopg://user:pass@host:port/dbname
    raw = settings.database_url.replace("+psycopg", "")
    parsed = urlparse(raw)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "dbname": parsed.path.lstrip("/"),
    }


def _bin_path(name: str) -> str:
    if settings.pg_bin_dir:
        return str(Path(settings.pg_bin_dir) / f"{name}.exe")
    return name


def backup_filename() -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"sms_backup_{timestamp}.dump"


def backup_database() -> str:
    """Runs pg_dump into a fresh OS temp file and returns its path. The caller
    is responsible for streaming it to the client and deleting it afterwards
    (see the backup router) — nothing is retained on the server."""
    fd, dest_path = tempfile.mkstemp(suffix=".dump", prefix="sms_backup_")
    os.close(fd)
    conn = _pg_conn_parts()

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


def restore_database(src_path: str) -> None:
    conn = _pg_conn_parts()
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
