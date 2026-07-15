"""Shared, forgiving text search used by every search bar in the app.

Two problems to solve for names people type differently:

1. **Separators / case** — "Abdul Hadi", "abdul-hadi" and "abdulhadi" should all
   match each other. Handled deterministically by comparing a *normalized* form
   (lowercased, non-alphanumerics removed) on both sides, in SQL.

2. **Spelling / typos** — "abdulhady" should still surface "Abdul Hadi". Handled
   by a Python fuzzy pass (``fuzzy_pick``) over candidate names, used as a
   supplement when the query looks like a name.
"""
import re
from difflib import SequenceMatcher

from sqlalchemy import ColumnElement, func, or_

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(text: str | None) -> str:
    """Lowercase and drop everything that isn't a letter or digit."""
    return _NON_ALNUM.sub("", (text or "").lower())


def _normalized_col(col: ColumnElement) -> ColumnElement:
    """SQL side of :func:`normalize` — lowercased, non-alphanumerics stripped."""
    return func.regexp_replace(func.lower(col), "[^a-z0-9]", "", "g")


def text_search_condition(query: str, *cols: ColumnElement) -> ColumnElement:
    """OR condition matching ``query`` against each column, tolerant of spacing,
    hyphens, dots and case. Combines a plain case-insensitive contains with a
    separator-insensitive normalized contains."""
    q = (query or "").strip()
    like = f"%{q}%"
    conds: list[ColumnElement] = []
    nq = normalize(q)
    for col in cols:
        conds.append(col.ilike(like))
        if nq:
            conds.append(_normalized_col(col).like(f"%{nq}%"))
    return or_(*conds)


def looks_like_name(query: str) -> bool:
    """True when a fuzzy name pass is worthwhile — i.e. the query has letters and
    enough length. Pure-digit queries (reg no / phone / CNIC) skip fuzzy."""
    nq = normalize(query)
    return len(nq) >= 3 and any(c.isalpha() for c in nq)


def _score(nq: str, name: str) -> float:
    nk = normalize(name)
    if not nk:
        return 0.0
    if nq in nk or nk in nq:
        return 0.96
    best = SequenceMatcher(None, nq, nk).ratio()
    # Also compare against each word, so a one-word query can match a single
    # part of a full name despite typos ("hady" → "Abdul Hadi").
    for token in _NON_ALNUM.split(name.lower()):
        if token:
            best = max(best, SequenceMatcher(None, nq, token).ratio())
    return best


def fuzzy_pick(
    query: str,
    id_name_pairs,
    exclude_ids=(),
    limit: int = 25,
    threshold: float = 0.75,
) -> list[int]:
    """Rank ``(id, name)`` pairs by fuzzy similarity to ``query`` and return the
    ids scoring at or above ``threshold`` (best first), excluding ``exclude_ids``."""
    nq = normalize(query)
    if len(nq) < 3:
        return []
    exclude = set(exclude_ids)
    scored: list[tuple[float, int]] = []
    for row_id, name in id_name_pairs:
        if row_id in exclude:
            continue
        score = _score(nq, name)
        if score >= threshold:
            scored.append((score, row_id))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [row_id for _, row_id in scored[:limit]]
