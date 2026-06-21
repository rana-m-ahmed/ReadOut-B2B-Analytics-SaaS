from __future__ import annotations

from app.datasets.schema_inference import slugify_column_name


def test_slugifies_spaces_and_punctuation() -> None:
    assert slugify_column_name("Customer Name (%)", set()) == "customer_name"


def test_prefixes_pure_number_header() -> None:
    assert slugify_column_name("2024", set()) == "col_2024"


def test_deduplicates_colliding_headers() -> None:
    existing = {"revenue"}
    assert slugify_column_name("Revenue!", existing) == "revenue_2"


def test_avoids_reserved_sql_word() -> None:
    assert slugify_column_name("select", set()) == "select_col"


def test_passes_through_clean_header() -> None:
    assert slugify_column_name("customer_id", set()) == "customer_id"
