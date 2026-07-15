"""Canonical class ordering (Playgroup → Grade 10).

Classes are stored as free-text names (`Student.class_name`), so ordering them
alphabetically puts "Grade 10" before "Grade 2" and "Playgroup" after every
"Grade". This helper gives the natural educational order schools expect on
printed challans and reports.

Mirrors the frontend `CLASS_SEQUENCE` in `frontend/src/api/students.ts`.
"""

import re

# Pre-primary stages first, then Grade 1..10. Anything not listed sorts after
# these by the trailing number in its name (so custom names like "Grade 11" or
# "Class 12" still slot in sensibly), then alphabetically as a last resort.
_CLASS_SEQUENCE = [
    "playgroup", "nursery", "prep",
    "grade 1", "grade 2", "grade 3", "grade 4", "grade 5",
    "grade 6", "grade 7", "grade 8", "grade 9", "grade 10",
]
_CLASS_INDEX = {name: i for i, name in enumerate(_CLASS_SEQUENCE)}


def class_sort_key(class_name: str) -> tuple:
    """Sort key that yields Playgroup → Nursery → Prep → Grade 1 … Grade 10."""
    name = (class_name or "").strip().lower()
    if name in _CLASS_INDEX:
        return (0, _CLASS_INDEX[name], 0, name)
    match = re.search(r"(\d+)", name)
    if match:
        return (1, 0, int(match.group(1)), name)
    return (2, 0, 0, name)
