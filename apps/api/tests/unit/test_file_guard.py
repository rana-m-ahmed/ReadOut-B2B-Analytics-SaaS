from __future__ import annotations

import asyncio
import io

import pytest
from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import ValidationError
from app.security.file_guard import validate_csv_upload


def _settings(max_upload_mb: int = 1) -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role-key",
        SUPABASE_JWT_SECRET="jwt-secret",
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
        MAX_UPLOAD_MB=max_upload_mb,
    )


def _upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


def test_rejects_oversized_file() -> None:
    upload = _upload("big.csv", b"a,b\n" + (b"1,2\n" * 400_000))

    with pytest.raises(ValidationError, match="MAX_UPLOAD_MB"):
        asyncio.run(validate_csv_upload(upload, _settings(max_upload_mb=1)))


def test_rejects_non_csv_content_even_with_csv_extension() -> None:
    upload = _upload("renamed.csv", b"MZfake-executable-content")

    with pytest.raises(ValidationError, match="not a valid CSV"):
        asyncio.run(validate_csv_upload(upload, _settings()))


def test_rejects_path_traversal_filename() -> None:
    upload = _upload("../../etc/passwd.csv", b"name,value\nalice,1\n")

    with pytest.raises(ValidationError, match="path traversal"):
        asyncio.run(validate_csv_upload(upload, _settings()))


def test_accepts_valid_small_csv() -> None:
    upload = _upload("Quarterly Revenue.csv", b"month,revenue\nJan,100\nFeb,120\n")

    validated = asyncio.run(validate_csv_upload(upload, _settings()))

    assert validated.sanitized_filename == "Quarterly_Revenue.csv"
    assert validated.size_bytes == len(b"month,revenue\nJan,100\nFeb,120\n")
    assert validated.content.startswith(b"month,revenue")
