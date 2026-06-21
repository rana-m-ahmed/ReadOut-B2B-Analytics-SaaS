"""Deterministic demo dataset generation."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from faker import Faker


DEMO_DATASET_SEED = 20260417
DEMO_YEAR = 2025
ANOMALY_WEEK_START = date(2025, 4, 14)
ANOMALY_WEEK_END = date(2025, 4, 20)
ANOMALY_REGION = "West"
ANOMALY_CATEGORY = "Electronics"
ANOMALY_REVENUE_MULTIPLIER = 0.55
DEMO_DATASET_FILENAME = "demo-sales-orders.csv"

REGIONS = ["North", "South", "East", "West", "Central"]
PRODUCT_CATEGORIES = ["Electronics", "Apparel", "Home", "Beauty", "Sports", "Accessories"]
CUSTOMER_TYPES = ["New", "Returning"]
MARKETING_CHANNELS = ["Organic", "Paid Search", "Social", "Email", "Referral"]
PAYMENT_METHODS = ["Card", "Wallet", "COD", "Bank Transfer"]
COLUMNS = [
    "order_id",
    "order_date",
    "revenue",
    "region",
    "product_category",
    "customer_type",
    "marketing_channel",
    "units",
    "discount_percent",
    "gross_margin",
    "payment_method",
]

REGION_PROBABILITIES = np.array([0.22, 0.18, 0.20, 0.24, 0.16], dtype=float)
CATEGORY_PROBABILITIES_BY_REGION = {
    "North": np.array([0.18, 0.16, 0.23, 0.11, 0.17, 0.15], dtype=float),
    "South": np.array([0.12, 0.20, 0.18, 0.16, 0.19, 0.15], dtype=float),
    "East": np.array([0.20, 0.15, 0.17, 0.15, 0.18, 0.15], dtype=float),
    "West": np.array([0.36, 0.11, 0.16, 0.10, 0.14, 0.13], dtype=float),
    "Central": np.array([0.15, 0.14, 0.26, 0.12, 0.17, 0.16], dtype=float),
}
WEEKDAY_MULTIPLIERS = {0: 1.00, 1: 1.05, 2: 1.08, 3: 1.12, 4: 1.18, 5: 0.82, 6: 0.70}
CHANNEL_PROBABILITIES_BY_CUSTOMER_TYPE = {
    "New": np.array([0.16, 0.30, 0.24, 0.12, 0.18], dtype=float),
    "Returning": np.array([0.29, 0.17, 0.14, 0.26, 0.14], dtype=float),
}
PAYMENT_METHOD_PROBABILITIES = np.array([0.56, 0.20, 0.10, 0.14], dtype=float)
BASE_PRICE_BY_CATEGORY = {
    "Electronics": 210.0,
    "Apparel": 58.0,
    "Home": 95.0,
    "Beauty": 42.0,
    "Sports": 88.0,
    "Accessories": 28.0,
}
BASE_MARGIN_BY_CATEGORY = {
    "Electronics": 0.29,
    "Apparel": 0.46,
    "Home": 0.38,
    "Beauty": 0.52,
    "Sports": 0.41,
    "Accessories": 0.55,
}


@dataclass(slots=True)
class DemoDatasetArtifacts:
    csv_bytes: bytes
    metadata: dict[str, object]
    row_count: int


def generate_demo_dataset(seed: int = DEMO_DATASET_SEED) -> DemoDatasetArtifacts:
    """Generate a deterministic order-level demo sales CSV and metadata."""

    rng = np.random.default_rng(seed)
    Faker.seed(seed)
    fake = Faker()
    fake.seed_instance(seed)

    start_date = date(DEMO_YEAR, 1, 1)
    end_date = date(DEMO_YEAR, 12, 31)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)

    order_counter = 1
    current_day = start_date
    while current_day <= end_date:
        month_growth = 1.0 + ((current_day.month - 1) * 0.028)
        weekday_multiplier = WEEKDAY_MULTIPLIERS[current_day.weekday()]
        noise = float(rng.normal(1.0, 0.08))
        planned_orders = int(round(48 * month_growth * weekday_multiplier * noise))
        daily_order_count = max(28, min(92, planned_orders))

        for _ in range(daily_order_count):
            region = str(rng.choice(REGIONS, p=REGION_PROBABILITIES))
            category = str(rng.choice(PRODUCT_CATEGORIES, p=CATEGORY_PROBABILITIES_BY_REGION[region]))

            returning_probability = min(0.78, 0.56 + (current_day.month * 0.018))
            customer_type = "Returning" if rng.random() < returning_probability else "New"
            marketing_channel = str(
                rng.choice(MARKETING_CHANNELS, p=CHANNEL_PROBABILITIES_BY_CUSTOMER_TYPE[customer_type])
            )
            payment_method = str(rng.choice(PAYMENT_METHODS, p=PAYMENT_METHOD_PROBABILITIES))

            units = int(rng.choice([1, 2, 3, 4, 5], p=[0.42, 0.29, 0.15, 0.09, 0.05]))
            base_price = BASE_PRICE_BY_CATEGORY[category] * month_growth
            channel_multiplier = {
                "Organic": 0.98,
                "Paid Search": 1.04,
                "Social": 0.94,
                "Email": 1.01,
                "Referral": 1.02,
            }[marketing_channel]
            customer_multiplier = 1.03 if customer_type == "Returning" else 0.97
            unit_price = max(8.0, base_price * channel_multiplier * customer_multiplier * float(rng.normal(1.0, 0.12)))

            discount_percent = float(
                np.clip(
                    rng.normal(11.0 if customer_type == "New" else 8.0, 4.0),
                    0.0,
                    35.0,
                )
            )
            revenue = units * unit_price * (1.0 - (discount_percent / 100.0))
            margin_rate = BASE_MARGIN_BY_CATEGORY[category] - (discount_percent / 170.0) + float(rng.normal(0.0, 0.018))
            gross_margin = revenue * max(0.08, margin_rate)

            if (
                ANOMALY_WEEK_START <= current_day <= ANOMALY_WEEK_END
                and region == ANOMALY_REGION
                and category == ANOMALY_CATEGORY
            ):
                revenue *= ANOMALY_REVENUE_MULTIPLIER
                gross_margin *= 0.62

            writer.writerow(
                [
                    f"ORD-{fake.lexify(text='????').upper()}-{order_counter:06d}",
                    current_day.isoformat(),
                    f"{revenue:.2f}",
                    region,
                    category,
                    customer_type,
                    marketing_channel,
                    str(units),
                    f"{discount_percent:.2f}",
                    f"{gross_margin:.2f}",
                    payment_method,
                ]
            )
            order_counter += 1

        current_day += timedelta(days=1)

    csv_bytes = buffer.getvalue().encode("utf-8")
    metadata = build_generation_metadata(seed=seed)
    metadata["row_count"] = order_counter - 1
    return DemoDatasetArtifacts(csv_bytes=csv_bytes, metadata=metadata, row_count=order_counter - 1)


def build_generation_metadata(seed: int = DEMO_DATASET_SEED) -> dict[str, object]:
    """Return deterministic demo generation metadata."""

    return {
        "seed": seed,
        "dataset_year": DEMO_YEAR,
        "anomaly": {
            "week_start": ANOMALY_WEEK_START.isoformat(),
            "week_end": ANOMALY_WEEK_END.isoformat(),
            "region": ANOMALY_REGION,
            "product_category": ANOMALY_CATEGORY,
            "revenue_drop_percent_vs_trailing_baseline": 45,
            "true_reason": (
                "A short-lived West-region electronics fulfillment outage coincided with a paused paid push, "
                "cutting sell-through for one week in April."
            ),
        },
        "columns": COLUMNS,
    }


def write_generation_outputs(
    output_csv_path: Path,
    metadata_path: Path,
    *,
    seed: int = DEMO_DATASET_SEED,
) -> DemoDatasetArtifacts:
    """Write deterministic dataset and metadata files to disk."""

    artifacts = generate_demo_dataset(seed=seed)
    output_csv_path.write_bytes(artifacts.csv_bytes)
    metadata_path.write_text(json.dumps(artifacts.metadata, indent=2, sort_keys=True), encoding="utf-8")
    return artifacts
