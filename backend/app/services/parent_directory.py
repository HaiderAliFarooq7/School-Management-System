"""Master-side parent routing: mobile number -> school_id.

The parent equivalent of the staff ``user_directory``. Parent login is by
mobile number and the app doesn't know the school up front, so this directory
(in the master database) maps a normalized mobile number to the school whose
tenant database holds that parent's account. Passwords are never stored here —
after routing, the mobile+password is verified against the school's own
``parent_account`` table.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.master import ParentDirectory
from app.services.parent_linking import normalize_mobile


def lookup_school_id(mdb: Session, mobile_number: str) -> int | None:
    core = normalize_mobile(mobile_number)
    if not core:
        return None
    row = mdb.execute(
        select(ParentDirectory).where(ParentDirectory.mobile_core == core)
    ).scalar_one_or_none()
    return row.school_id if row else None


def upsert(mdb: Session, mobile_number: str, school_id: int) -> None:
    """Point a mobile number at a school. Idempotent; updates the school on an
    existing row (e.g. a parent's account was moved). The caller commits."""
    core = normalize_mobile(mobile_number)
    if not core:
        return
    row = mdb.execute(
        select(ParentDirectory).where(ParentDirectory.mobile_core == core)
    ).scalar_one_or_none()
    if row is None:
        mdb.add(ParentDirectory(mobile_core=core, mobile_number=mobile_number, school_id=school_id))
    else:
        row.mobile_number = mobile_number
        row.school_id = school_id
