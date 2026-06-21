import pytest
from pathlib import Path

API_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

@pytest.fixture(scope="module")
def live_env():
    return _load_env_file(API_ENV_FILE)
