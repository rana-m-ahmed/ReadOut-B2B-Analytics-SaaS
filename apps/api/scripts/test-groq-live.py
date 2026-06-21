"""Manual smoke test to verify live integration with the Groq API.

Run this directly from the `apps/api` directory using:
`python scripts/test-groq-live.py`

This test spends real quota, so it is omitted from the default CI suite.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Setup basic logging to see the fallback/retry behavior in stdout
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Ensure app modules can be imported
sys.path.append(".")

from app.core.config import get_settings
from app.db.models import DatasetColumn
from app.nlq.groq_client import get_intent


async def run_smoke_test() -> None:
    settings = get_settings()
    if not settings.GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY is not set in your environment or .env file.")
        print("Please configure it before running the live smoke test.")
        sys.exit(1)

    print(f"Using primary model: {settings.GROQ_PRIMARY_MODEL}")
    
    # A tiny fake schema just to give the model something to match against
    schema = [
        DatasetColumn(
            id=uuid4(),
            dataset_id=uuid4(),
            name="total_revenue",
            display_name="Total Revenue",
            data_type="number",
            ordinal_position=1,
            is_nullable=True,
            semantic_role="metric",
            created_at=datetime.now(timezone.utc),
        ),
        DatasetColumn(
            id=uuid4(),
            dataset_id=uuid4(),
            name="order_date",
            display_name="Date",
            data_type="date",
            ordinal_position=2,
            is_nullable=False,
            semantic_role="time",
            created_at=datetime.now(timezone.utc),
        )
    ]

    question = "What is the total revenue by day for the last 30 days?"
    
    print(f"Sending question: '{question}'")
    
    try:
        intent = await get_intent(question, schema, settings=settings)
        print("\nSuccess! The model returned:")
        print(intent.model_dump_json(indent=2))
    except Exception as e:
        print(f"\nFailed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
