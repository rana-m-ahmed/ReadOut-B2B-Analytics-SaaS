"""Groq LLM client for structured intent generation with resilient fallback logic."""

from __future__ import annotations

import asyncio
import json
import logging
import random

import httpx
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import UpstreamLLMError
from app.db.models import DatasetColumn
from app.nlq.prompt_builder import build_intent_prompt
from app.nlq.schemas import AnalyticsIntent, analytics_intent_adapter

logger = logging.getLogger(__name__)


def _get_retry_delay(response: httpx.Response) -> float:
    """Extract backoff delay from Groq headers, with jitter."""
    delay = 1.0  # default if headers missing

    # Check standard Retry-After
    if "retry-after" in response.headers:
        try:
            delay = float(response.headers["retry-after"])
        except ValueError:
            pass
    # Groq-specific reset header (e.g. x-ratelimit-reset)
    elif "x-ratelimit-reset" in response.headers:
        try:
            val = response.headers["x-ratelimit-reset"]
            if val.endswith("s"):
                val = val[:-1]
            delay = float(val)
        except ValueError:
            pass

    jitter = random.uniform(0.1, 0.5)
    final_delay = delay + jitter
    return min(final_delay, 30.0)


async def _make_call(
    client: httpx.AsyncClient, messages: list[dict[str, str]], model: str, api_key: str
) -> tuple[httpx.Response | None, AnalyticsIntent | None]:
    try:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": 0.0,
            },
            timeout=15.0,
        )
    except httpx.RequestError as e:
        logger.error(f"HTTP request to Groq failed: {e}")
        return None, None

    if response.status_code >= 400:
        return response, None

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]

        raw_intent = json.loads(content)
        intent = analytics_intent_adapter.validate_python(raw_intent)
        return response, intent
    except (json.JSONDecodeError, KeyError, ValidationError) as e:
        # We catch malformed outputs early so we can trigger a retry instead of crashing downstream
        logger.error(
            f"malformed_llm_output: Failed to parse LLM output. Error: {e}. Output: {response.text}"
        )
        return response, None


async def get_intent(
    question: str,
    schema: list[DatasetColumn],
    history: list[dict[str, str]] | None = None,
    settings: Settings | None = None,
) -> AnalyticsIntent:
    """Call Groq to map a natural language question into an AnalyticsIntent JSON payload."""
    resolved_settings = settings or get_settings()
    api_key = resolved_settings.GROQ_API_KEY
    if not api_key:
        raise UpstreamLLMError("Groq API key is missing")

    primary_model = resolved_settings.GROQ_PRIMARY_MODEL
    fallback_model = resolved_settings.GROQ_FALLBACK_MODEL

    messages = build_intent_prompt(question, schema)
    if history:
        messages = [messages[0]] + history + [messages[-1]]

    async with httpx.AsyncClient() as client:
        # Attempt 1: Primary Model
        resp, intent = await _make_call(client, messages, primary_model, api_key)

        if intent is not None:
            logger.info(f"Groq request succeeded using PRIMARY model: {primary_model}")
            return intent

        # Attempt 2: Primary Model Retry (if Attempt 1 failed)
        delay = 1.0 + random.uniform(0.1, 0.5)
        if resp is not None and resp.status_code == 429:
            delay = _get_retry_delay(resp)
            logger.warning(
                f"Groq primary model {primary_model} rate limited. Retrying after {delay:.2f}s"
            )
        else:
            status_desc = resp.status_code if resp else "network/malformed"
            logger.warning(
                f"Groq primary model {primary_model} failed (status {status_desc}). Retrying after {delay:.2f}s"
            )

        await asyncio.sleep(delay)

        resp, intent = await _make_call(client, messages, primary_model, api_key)
        if intent is not None:
            logger.info(
                f"Groq request succeeded using PRIMARY model (after retry): {primary_model}"
            )
            return intent

        # Attempt 3: Fallback Model
        logger.warning(
            f"Groq primary model {primary_model} failed a second time. Falling back to {fallback_model}"
        )
        resp, intent = await _make_call(client, messages, fallback_model, api_key)

        if intent is not None:
            logger.info(
                f"Groq request succeeded using FALLBACK model: {fallback_model}"
            )
            return intent

        # All attempts failed
        logger.error("Both primary and fallback LLM requests failed")
        raise UpstreamLLMError("Upstream LLM request failed or returned invalid JSON")


async def generate_summary(
    question: str,
    result_payload: dict,
    settings: Settings | None = None,
) -> str:
    """Generate a one-sentence summary of the computed result using the fallback model."""
    resolved_settings = settings or get_settings()
    api_key = resolved_settings.GROQ_API_KEY
    if not api_key:
        raise UpstreamLLMError("Groq API key is missing")

    # Specifically use the fallback model (e.g. 8b) for summarization
    model = resolved_settings.GROQ_FALLBACK_MODEL

    system_prompt = (
        "You are a helpful data analyst. The user asked a question, and the system computed the exact result data. "
        "Your task is to write a single, clear, conversational sentence summarizing the data provided below. "
        "Do NOT perform any calculations. Do NOT describe the JSON structure. Just summarize the numbers in plain English."
    )

    user_prompt = f"Question: {question}\n\nComputed Data:\n{json.dumps(result_payload, indent=2)}\n\nOne-sentence summary:"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 100,
                },
                timeout=10.0,
            )
        except httpx.RequestError as e:
            logger.error(f"HTTP request to Groq for summary failed: {e}")
            raise UpstreamLLMError("Upstream LLM request failed during summarization")

        if response.status_code >= 400:
            logger.error(f"Groq summary model failed with status {response.status_code}")
            raise UpstreamLLMError("Upstream LLM request failed during summarization")

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
