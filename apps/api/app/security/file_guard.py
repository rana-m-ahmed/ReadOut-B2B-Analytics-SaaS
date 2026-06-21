"""Dataset upload file validation helpers."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import ValidationError

_SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_CSV_DELIMITERS = (",", ";", "\t", "|")
_BINARY_SIGNATURES = (
    b"MZ",
    b"\x7fELF",
    b"PK\x03\x04",
    b"%PDF-",
)


@dataclass(slots=True)
class ValidatedCsvUpload:
    """Validated CSV upload payload."""

    original_filename: str
    sanitized_filename: str
    content: bytes
    size_bytes: int


def sanitize_filename(filename: str | None) -> str:
    """Normalize an uploaded filename into a storage-safe basename."""

    original_name = filename or ""
    if "/" in original_name or "\\" in original_name or ".." in original_name:
        raise ValidationError("Filename must not contain path traversal segments")

    raw_name = original_name
    raw_name = _CONTROL_CHARS.sub("", raw_name).strip().strip(". ")
    if not raw_name:
        raise ValidationError("Filename is required")

    stem, dot, suffix = raw_name.rpartition(".")
    if not dot:
        raise ValidationError("Uploaded file must use a .csv extension")

    safe_stem = _SAFE_FILENAME_CHARS.sub("_", stem).strip("._-")
    if not safe_stem:
        safe_stem = "upload"

    safe_suffix = _SAFE_FILENAME_CHARS.sub("", suffix.lower())
    if safe_suffix != "csv":
        raise ValidationError("Uploaded file must use a .csv extension")

    return f"{safe_stem}.csv"


def _looks_like_text_csv(content: bytes) -> bool:
    if not content:
        return False
    if content.startswith(_BINARY_SIGNATURES):
        return False
    if b"\x00" in content:
        return False

    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False

    sample = decoded[:8192]
    if not sample.strip():
        return False

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_CSV_DELIMITERS))
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = None

    lines = [line for line in sample.splitlines() if line.strip()]
    if len(lines) < 2:
        return False

    if delimiter is None:
        delimiter = next((candidate for candidate in _CSV_DELIMITERS if candidate in lines[0]), None)
        if delimiter is None:
            return False

    try:
        rows = list(csv.reader(io.StringIO("\n".join(lines[:5])), delimiter=delimiter))
    except csv.Error:
        return False

    column_counts = [len(row) for row in rows if row]
    return bool(column_counts) and max(column_counts) > 1


async def validate_csv_upload(upload: UploadFile, settings: Settings) -> ValidatedCsvUpload:
    """Validate size, extension, filename safety, and actual CSV content."""

    sanitized_filename = sanitize_filename(upload.filename)
    content = await upload.read()
    await upload.seek(0)

    size_bytes = len(content)
    max_size_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if size_bytes > max_size_bytes:
        raise ValidationError(f"Uploaded file exceeds MAX_UPLOAD_MB ({settings.MAX_UPLOAD_MB} MB)")

    if not _looks_like_text_csv(content):
        raise ValidationError("Uploaded file content is not a valid CSV")

    return ValidatedCsvUpload(
        original_filename=upload.filename or sanitized_filename,
        sanitized_filename=sanitized_filename,
        content=content,
        size_bytes=size_bytes,
    )
