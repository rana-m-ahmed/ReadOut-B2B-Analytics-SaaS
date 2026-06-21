from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.datasets.demo_seed import seed_demo_dataset
from app.datasets.storage_service import DatasetStorageService


API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _has_live_supabase_credentials() -> bool:
    if not API_ENV_FILE.exists():
        return False
    values = _load_env_file(API_ENV_FILE)
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    return all(values.get(name, "").strip() for name in required)


def test_demo_seed_live_end_to_end_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _has_live_supabase_credentials():
        pytest.skip("requires populated apps/api/.env with live Supabase credentials and storage bucket access")

    env = _load_env_file(API_ENV_FILE)
    monkeypatch.setenv("GROQ_API_KEY", env.get("GROQ_API_KEY") or "test-groq-placeholder")

    result = seed_demo_dataset()
    storage = DatasetStorageService()
    profile_payload = json.loads(storage.download_bytes(result.upload_result.storage_paths.profile_json).decode("utf-8"))

    assert result.workspace.slug == "demo"
    assert result.dataset.source_type == "demo_seed"
    assert result.status == "ready"
    assert result.quality_score is not None
    assert profile_payload["quality_score"] == result.quality_score
