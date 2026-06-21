"""Dataset schema inference helpers."""

from __future__ import annotations

import re

_NON_SAFE_CHARS = re.compile(r"[^a-z0-9_]+")
_REPEATED_UNDERSCORES = re.compile(r"_+")
_RESERVED_WORDS = {
    "all",
    "and",
    "as",
    "between",
    "by",
    "case",
    "column",
    "create",
    "delete",
    "desc",
    "distinct",
    "drop",
    "else",
    "end",
    "exists",
    "false",
    "from",
    "group",
    "having",
    "in",
    "insert",
    "into",
    "is",
    "join",
    "left",
    "like",
    "limit",
    "not",
    "null",
    "offset",
    "on",
    "or",
    "order",
    "right",
    "select",
    "set",
    "table",
    "then",
    "true",
    "union",
    "update",
    "values",
    "when",
    "where",
}


def slugify_column_name(raw_header: str, existing: set[str]) -> str:
    """Convert a raw CSV header into a safe internal column identifier."""

    slug = raw_header.lower()
    slug = _NON_SAFE_CHARS.sub("_", slug)
    slug = _REPEATED_UNDERSCORES.sub("_", slug).strip("_")

    if not slug or slug[0].isdigit():
        slug = f"col_{slug}" if slug else "col_"

    if slug in _RESERVED_WORDS:
        slug = f"{slug}_col"

    candidate = slug
    suffix = 2
    while candidate in existing:
        candidate = f"{slug}_{suffix}"
        suffix += 1

    return candidate
