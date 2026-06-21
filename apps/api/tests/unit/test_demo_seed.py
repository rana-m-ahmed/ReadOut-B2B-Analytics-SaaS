from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta

from app.datasets.demo_generation import (
    ANOMALY_CATEGORY,
    ANOMALY_REGION,
    ANOMALY_WEEK_END,
    ANOMALY_WEEK_START,
    DEMO_DATASET_SEED,
    generate_demo_dataset,
)


def _weekly_revenue_by_region_category(csv_bytes: bytes) -> dict[tuple[datetime.date, str, str], float]:
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    weekly_totals: dict[tuple[datetime.date, str, str], float] = defaultdict(float)
    for row in reader:
        order_day = datetime.strptime(row["order_date"], "%Y-%m-%d").date()
        week_start = order_day - timedelta(days=order_day.weekday())
        weekly_totals[(week_start, row["region"], row["product_category"])] += float(row["revenue"])
    return weekly_totals


def test_generator_is_byte_identical_for_same_seed() -> None:
    first = generate_demo_dataset(seed=DEMO_DATASET_SEED)
    second = generate_demo_dataset(seed=DEMO_DATASET_SEED)

    assert first.csv_bytes == second.csv_bytes
    assert first.metadata == second.metadata
    assert 10_000 <= first.row_count <= 30_000


def test_seeded_anomaly_week_matches_expected_drop_magnitude() -> None:
    artifacts = generate_demo_dataset(seed=DEMO_DATASET_SEED)
    weekly_totals = _weekly_revenue_by_region_category(artifacts.csv_bytes)

    anomaly_revenue = weekly_totals[(ANOMALY_WEEK_START, ANOMALY_REGION, ANOMALY_CATEGORY)]
    trailing_weeks = [
        ANOMALY_WEEK_START - timedelta(days=7),
        ANOMALY_WEEK_START - timedelta(days=14),
        ANOMALY_WEEK_START - timedelta(days=21),
        ANOMALY_WEEK_START - timedelta(days=28),
    ]
    baseline = sum(weekly_totals[(week, ANOMALY_REGION, ANOMALY_CATEGORY)] for week in trailing_weeks) / len(
        trailing_weeks
    )
    drop_percent = ((baseline - anomaly_revenue) / baseline) * 100

    assert ANOMALY_WEEK_END == ANOMALY_WEEK_START + timedelta(days=6)
    assert 39.0 <= drop_percent <= 51.0
