"""Unit tests for the Groq client, using a mocked HTTP layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import UpstreamLLMError
from app.db.models import DatasetColumn
from app.nlq.groq_client import get_intent
from app.nlq.schemas import IntentType


@pytest.fixture
def dummy_settings() -> Settings:
    return Settings(
        GROQ_API_KEY="test-key",
        GROQ_PRIMARY_MODEL="primary-model",
        GROQ_FALLBACK_MODEL="fallback-model",
    )


@pytest.fixture
def dummy_schema() -> list[DatasetColumn]:
    return [
        DatasetColumn(
            id=uuid4(),
            dataset_id=uuid4(),
            name="revenue",
            data_type="number",
            ordinal_position=1,
            is_nullable=True,
            semantic_role="metric",
            created_at=datetime.now(timezone.utc),
        )
    ]


def _mock_response(
    status_code: int, content_dict: dict | None = None, headers: dict | None = None
) -> httpx.Response:
    if content_dict is None:
        content_dict = {}
    return httpx.Response(
        status_code=status_code,
        json=content_dict,
        headers=headers or {},
        request=httpx.Request(
            "POST", "https://api.groq.com/openai/v1/chat/completions"
        ),
    )


def _valid_intent_payload() -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "intent": "single_metric",
                            "metric": "revenue",
                            "aggregation": "sum",
                        }
                    )
                }
            }
        ]
    }


def _malformed_payload() -> dict:
    return {"choices": [{"message": {"content": "this is not json"}}]}


@pytest.mark.anyio
async def test_primary_model_succeeds_first_try(
    dummy_settings: Settings, dummy_schema: list[DatasetColumn]
) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_response(200, _valid_intent_payload())

        intent = await get_intent(
            "What is total revenue?", dummy_schema, settings=dummy_settings
        )

        assert intent.intent == IntentType.SINGLE_METRIC
        assert mock_post.call_count == 1
        assert mock_post.call_args[1]["json"]["model"] == "primary-model"


@pytest.mark.anyio
async def test_primary_model_rate_limited_retries_and_succeeds(
    dummy_settings: Settings,
    dummy_schema: list[DatasetColumn],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_post.side_effect = [
                _mock_response(429, headers={"retry-after": "0.1"}),
                _mock_response(200, _valid_intent_payload()),
            ]

            intent = await get_intent("Q", dummy_schema, settings=dummy_settings)

            assert intent.intent == IntentType.SINGLE_METRIC
            assert mock_post.call_count == 2
            assert mock_sleep.call_count == 1
            # Both calls used primary model
            assert mock_post.call_args_list[0][1]["json"]["model"] == "primary-model"
            assert mock_post.call_args_list[1][1]["json"]["model"] == "primary-model"
            assert "rate limited" in caplog.text


@pytest.mark.anyio
async def test_primary_model_fails_twice_uses_fallback(
    dummy_settings: Settings,
    dummy_schema: list[DatasetColumn],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        with patch("asyncio.sleep", new_callable=AsyncMock):
            mock_post.side_effect = [
                _mock_response(500),  # first try fails
                _mock_response(500),  # retry fails
                _mock_response(200, _valid_intent_payload()),  # fallback succeeds
            ]

            intent = await get_intent("Q", dummy_schema, settings=dummy_settings)

            assert intent.intent == IntentType.SINGLE_METRIC
            assert mock_post.call_count == 3
            assert mock_post.call_args_list[0][1]["json"]["model"] == "primary-model"
            assert mock_post.call_args_list[1][1]["json"]["model"] == "primary-model"
            assert mock_post.call_args_list[2][1]["json"]["model"] == "fallback-model"
            assert "Falling back" in caplog.text


@pytest.mark.anyio
async def test_both_models_fail_raises_upstream_error(
    dummy_settings: Settings, dummy_schema: list[DatasetColumn]
) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        with patch("asyncio.sleep", new_callable=AsyncMock):
            mock_post.side_effect = [
                _mock_response(500),
                _mock_response(500),
                _mock_response(500),
            ]

            with pytest.raises(UpstreamLLMError) as exc_info:
                await get_intent("Q", dummy_schema, settings=dummy_settings)

            assert "Upstream LLM request failed" in str(exc_info.value)
            assert mock_post.call_count == 3


@pytest.mark.anyio
async def test_malformed_json_triggers_retry_and_fallback(
    dummy_settings: Settings,
    dummy_schema: list[DatasetColumn],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        with patch("asyncio.sleep", new_callable=AsyncMock):
            mock_post.side_effect = [
                _mock_response(200, _malformed_payload()),  # primary malformed
                _mock_response(200, _malformed_payload()),  # primary retry malformed
                _mock_response(200, _valid_intent_payload()),  # fallback succeeds
            ]

            intent = await get_intent("Q", dummy_schema, settings=dummy_settings)

            assert intent.intent == IntentType.SINGLE_METRIC
            assert mock_post.call_count == 3
            assert "malformed_llm_output" in caplog.text
            assert "Falling back" in caplog.text
