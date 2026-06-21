"""Generate the reproducible demo sales dataset and metadata files."""

from __future__ import annotations

from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[1]

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_CSV_PATH = SCRIPT_DIR / "demo-sales-orders.csv"
METADATA_PATH = SCRIPT_DIR / "demo-dataset-metadata.json"


def main() -> None:
    if str(API_ROOT) not in sys.path:
        sys.path.insert(0, str(API_ROOT))

    from app.datasets.demo_generation import (
        DEMO_DATASET_SEED,
        write_generation_outputs,
    )

    artifacts = write_generation_outputs(
        OUTPUT_CSV_PATH,
        METADATA_PATH,
        seed=DEMO_DATASET_SEED,
    )
    print(
        f"generated_rows={artifacts.row_count} seed={artifacts.metadata['seed']} "
        f"csv={OUTPUT_CSV_PATH.name} metadata={METADATA_PATH.name}"
    )


if __name__ == "__main__":
    main()
