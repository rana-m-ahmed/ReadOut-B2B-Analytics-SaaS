from __future__ import annotations

from app.core.config import Settings
from app.datasets.profiler import DatasetProfileFailure, DatasetProfileSuccess, profile_csv_bytes


def _settings(max_upload_mb: int = 25) -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-role-key",
        SUPABASE_JWT_SECRET="jwt-secret",
        SUPABASE_ANON_KEY="anon-key",
        GROQ_API_KEY="groq-key",
        MAX_UPLOAD_MB=max_upload_mb,
    )


def test_clean_csv_produces_expected_types_and_high_quality_score() -> None:
    result = profile_csv_bytes(
        b"order_id,order_date,revenue,is_active\n1,2026-01-01,100.5,true\n2,2026-01-02,120.0,false\n",
        _settings(),
    )

    assert isinstance(result, DatasetProfileSuccess)
    columns = {column.name: column for column in result.columns}
    assert columns["order_id"].data_type == "number"
    assert columns["order_id"].semantic_role == "identifier"
    assert columns["order_date"].data_type == "date"
    assert columns["order_date"].semantic_role == "time"
    assert columns["revenue"].data_type == "number"
    assert columns["revenue"].semantic_role == "metric"
    assert columns["is_active"].data_type == "boolean"
    assert result.quality_score >= 85


def test_missing_values_surface_warning_and_missing_percent() -> None:
    result = profile_csv_bytes(
        b"customer,notes\nalice,\nbob,\ncarol,follow up\n",
        _settings(),
    )

    assert isinstance(result, DatasetProfileSuccess)
    notes_column = next(column for column in result.columns if column.name == "notes")
    assert notes_column.missing_percent == 66.67
    assert any("column 'notes' is 67% missing" == warning for warning in result.warnings)


def test_duplicateish_headers_get_deduplicated_internal_names() -> None:
    result = profile_csv_bytes(
        b"Revenue,revenue ,Revenue!\n100,101,102\n200,201,202\n",
        _settings(),
    )

    assert isinstance(result, DatasetProfileSuccess)
    assert [column.name for column in result.columns] == ["revenue", "revenue_2", "revenue_3"]
    assert [column.display_name for column in result.columns] == ["Revenue", "revenue ", "Revenue!"]


def test_malformed_csv_returns_structured_failure() -> None:
    result = profile_csv_bytes(
        b'name,amount\n"alice,100\nbob,200,extra\n',
        _settings(),
    )

    assert isinstance(result, DatasetProfileFailure)
    assert result.success is False
    assert result.error_code == "malformed_csv"
    assert "CSV parsing failed" in result.error_message
