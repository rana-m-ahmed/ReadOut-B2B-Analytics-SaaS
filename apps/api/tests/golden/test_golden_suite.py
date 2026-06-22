"""Golden regression harness for the real /ask endpoint and real demo dataset.

This suite is intentionally quota-consuming because its purpose is to verify the
real LLM + real backend integration. Run it manually before each deploy or other
major release candidate, not on every push.

Enable with:
    READOUT_RUN_GOLDEN_SUITE=1 pytest apps/api/tests/golden/test_golden_suite.py -v -rs
"""

from __future__ import annotations

import logging
import os
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from unittest.mock import patch
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.db.repositories import DatasetColumnRepository, DatasetRepository, WorkspaceRepository
from app.nlq.groq_client import get_intent as real_get_intent
from app.analytics.duckdb_engine import execute_dataset_query as real_execute_dataset_query


RUN_FLAG = "READOUT_RUN_GOLDEN_SUITE"
API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
RESULTS_FILE = Path(__file__).resolve().parents[4] / "progress" / "08-golden-suite-results.md"


@dataclass(frozen=True, slots=True)
class GoldenQuestion:
    index: int
    question: str
    followup_to_session_key: str | None = None
    store_session_key: str | None = None
    expected_intents: tuple[str, ...] = ()
    required_columns: tuple[str, ...] = ()
    expected_chart_hint: str | None = None


@dataclass(slots=True)
class GoldenQuestionResult:
    index: int
    question: str
    response_status: int | None = None
    model_answered: str = "not_called"
    chart_returned: bool = False
    clarification_required: dict[str, Any] | None = None
    query_plan: dict[str, Any] | None = None
    compiled_sql: str | None = None
    summary: str | None = None
    answer_id: str | None = None
    session_id: str | None = None
    chart_type: str | None = None
    chart_preview: list[dict[str, Any]] = field(default_factory=list)
    hallucinated_columns: list[str] = field(default_factory=list)
    engine_error: str | None = None
    auto_pass: bool = False
    fail_reasons: list[str] = field(default_factory=list)
    manual_review_note: str = "Review chart preview and SQL for final semantic correctness."


QUESTIONS: tuple[GoldenQuestion, ...] = (
    GoldenQuestion(1, "Show revenue over time.", expected_intents=("time_series",), required_columns=("revenue", "order_date")),
    GoldenQuestion(2, "Show orders by region.", expected_intents=("grouped_metric", "top_n"), required_columns=("region", "order_id")),
    GoldenQuestion(3, "Revenue by product category last quarter.", expected_intents=("grouped_metric", "top_n"), required_columns=("revenue", "product_category", "order_date")),
    GoldenQuestion(4, "Best month this year.", expected_intents=("time_series", "grouped_metric", "top_n"), required_columns=("revenue", "order_date")),
    GoldenQuestion(5, "Worst performing channel.", expected_intents=("grouped_metric", "bottom_n"), required_columns=("marketing_channel",)),
    GoldenQuestion(6, "Compare new vs returning customers.", expected_intents=("grouped_metric", "comparison", "proportion"), required_columns=("customer_type",)),
    GoldenQuestion(7, "Average order value by region.", expected_intents=("grouped_metric",), required_columns=("revenue", "region")),
    GoldenQuestion(8, "Which category grew fastest?", expected_intents=("grouped_metric", "comparison", "time_series"), required_columns=("product_category", "revenue", "order_date")),
    GoldenQuestion(9, "Show revenue for the West region.", store_session_key="west_chain", expected_intents=("single_metric", "time_series"), required_columns=("revenue", "region")),
    GoldenQuestion(10, "Break that down by product category.", followup_to_session_key="west_chain", expected_intents=("grouped_metric",), required_columns=("revenue", "region", "product_category")),
    GoldenQuestion(11, "Compare that with the previous period.", followup_to_session_key="west_chain", expected_intents=("comparison",), required_columns=("revenue", "region", "product_category")),
    GoldenQuestion(12, "Show as a line chart.", followup_to_session_key="west_chain", expected_intents=("comparison",), expected_chart_hint="line"),
    GoldenQuestion(13, "What caused the April dip?", expected_intents=("anomaly_explanation", "grouped_metric"), required_columns=("order_date", "revenue")),
    GoldenQuestion(14, "Top 5 categories by revenue.", expected_intents=("top_n", "grouped_metric"), required_columns=("product_category", "revenue")),
    GoldenQuestion(15, "Bottom 3 channels by orders.", expected_intents=("bottom_n", "grouped_metric"), required_columns=("marketing_channel", "order_id")),
    GoldenQuestion(16, "Revenue share by region.", expected_intents=("proportion", "grouped_metric"), required_columns=("revenue", "region")),
    GoldenQuestion(17, "Which weekday has the most orders?", expected_intents=("grouped_metric", "top_n", "time_series"), required_columns=("order_date", "order_id")),
    GoldenQuestion(18, "Show discount impact on revenue.", expected_intents=("correlation", "grouped_metric"), required_columns=("discount_percent", "revenue")),
    GoldenQuestion(19, "Compare paid search and organic.", expected_intents=("comparison", "grouped_metric"), required_columns=("marketing_channel",)),
    GoldenQuestion(20, "Which region had the highest AOV?", expected_intents=("top_n", "grouped_metric"), required_columns=("region", "revenue")),
    GoldenQuestion(21, "Show returning customer revenue trend.", expected_intents=("time_series", "grouped_metric"), required_columns=("customer_type", "revenue", "order_date")),
    GoldenQuestion(22, "What changed last month?", expected_intents=("comparison", "grouped_metric", "single_metric"), required_columns=("order_date",)),
    GoldenQuestion(23, "Any unusual drops?", expected_intents=("anomaly_explanation", "time_series", "grouped_metric"), required_columns=("order_date", "revenue")),
    GoldenQuestion(24, "Show revenue and orders together.", expected_intents=("grouped_metric", "time_series", "comparison"), required_columns=("revenue", "order_id")),
    GoldenQuestion(25, "Summarize the dataset.", expected_intents=("single_metric", "grouped_metric", "time_series"), required_columns=()),
)


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


def _has_live_credentials() -> bool:
    env = _load_env_file(API_ENV_FILE)
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET", "GROQ_API_KEY")
    return all(env.get(name, "").strip() for name in required)


def _build_auth_token(env: dict[str, str], user_id: UUID) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "app_metadata": {"is_anonymous": False},
        },
        env["SUPABASE_JWT_SECRET"],
        algorithm="HS256",
    )


def _override_settings(env: dict[str, str]) -> Settings:
    def env_int(name: str, default: int) -> int:
        raw = (env.get(name) or "").strip()
        return int(raw) if raw else default

    return Settings(
        SUPABASE_URL=env["SUPABASE_URL"],
        SUPABASE_SERVICE_ROLE_KEY=env["SUPABASE_SERVICE_ROLE_KEY"],
        SUPABASE_JWT_SECRET=env["SUPABASE_JWT_SECRET"],
        SUPABASE_ANON_KEY=env["SUPABASE_ANON_KEY"],
        GROQ_API_KEY=env["GROQ_API_KEY"],
        GROQ_PRIMARY_MODEL=env.get("GROQ_PRIMARY_MODEL", "llama-3.3-70b-versatile"),
        GROQ_FALLBACK_MODEL=env.get("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant"),
        ALLOWED_ORIGINS=[],
        ENVIRONMENT=(env.get("ENVIRONMENT") or "development"),
        MAX_UPLOAD_MB=env_int("MAX_UPLOAD_MB", 25),
        QUERY_TIMEOUT_SECONDS=env_int("QUERY_TIMEOUT_SECONDS", 10),
        MAX_RESULT_ROWS=env_int("MAX_RESULT_ROWS", 500),
        MAX_CHART_PAYLOAD_KB=env_int("MAX_CHART_PAYLOAD_KB", 50),
        ANON_SESSION_TTL_HOURS=env_int("ANON_SESSION_TTL_HOURS", 72),
        ASK_CONTEXT_TURN_LIMIT=env_int("ASK_CONTEXT_TURN_LIMIT", 4),
        ASK_RATE_LIMIT_REQUESTS=200,
        ASK_RATE_LIMIT_WINDOW_SECONDS=60,
        UPLOAD_URL_RATE_LIMIT_REQUESTS=50,
        UPLOAD_URL_RATE_LIMIT_WINDOW_SECONDS=60,
    )


class _GroqTraceHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _extract_referenced_columns(query_plan: dict[str, Any] | None) -> set[str]:
    if not isinstance(query_plan, dict):
        return set()

    referenced: set[str] = set()
    metric = query_plan.get("metric")
    if isinstance(metric, str):
        referenced.add(metric)

    for group_name in query_plan.get("group_by", []):
        if isinstance(group_name, str):
            referenced.add(group_name)

    date_range = query_plan.get("date_range")
    if isinstance(date_range, dict):
        column = date_range.get("column")
        if isinstance(column, str):
            referenced.add(column)

    for filter_clause in query_plan.get("filters", []):
        if isinstance(filter_clause, dict) and isinstance(filter_clause.get("column"), str):
            referenced.add(filter_clause["column"])

    sort = query_plan.get("sort")
    if isinstance(sort, dict) and isinstance(sort.get("column"), str):
        referenced.add(sort["column"])

    return referenced


def _model_from_logs(messages: Iterable[str]) -> str:
    joined = "\n".join(messages)
    if "Groq request succeeded using FALLBACK model" in joined:
        return "fallback"
    if "Groq request succeeded using PRIMARY model" in joined:
        return "primary"
    if "Both primary and fallback LLM requests failed" in joined:
        return "failed"
    return "unknown"


def _evaluate_result(
    question: GoldenQuestion,
    result: GoldenQuestionResult,
    allowed_columns: set[str],
) -> None:
    reasons: list[str] = []

    if result.response_status != 200:
        reasons.append(f"unexpected HTTP {result.response_status}")
    if result.clarification_required is not None:
        reasons.append(f"unexpected clarification: {result.clarification_required.get('message')}")
    if not result.chart_returned:
        reasons.append("chart missing")
    if result.query_plan is None:
        reasons.append("query_plan missing")
    if result.compiled_sql is None:
        reasons.append("compiled SQL missing")
    if result.engine_error is not None:
        reasons.append(f"engine error: {result.engine_error}")

    referenced_columns = _extract_referenced_columns(result.query_plan)
    hallucinated = sorted(column for column in referenced_columns if column not in allowed_columns)
    if hallucinated:
        result.hallucinated_columns = hallucinated
        reasons.append(f"hallucinated columns: {', '.join(hallucinated)}")

    if question.expected_intents and result.query_plan is not None:
        intent_name = result.query_plan.get("intent")
        if intent_name not in question.expected_intents:
            reasons.append(f"unexpected intent '{intent_name}'")

    for required_column in question.required_columns:
        if required_column not in referenced_columns:
            reasons.append(f"missing expected column '{required_column}'")

    if question.expected_chart_hint is not None and result.query_plan is not None:
        if result.query_plan.get("chart_hint") != question.expected_chart_hint:
            reasons.append(f"expected chart_hint '{question.expected_chart_hint}'")

    if question.index == 10 and result.query_plan is not None:
        group_by = result.query_plan.get("group_by") or []
        filters = result.query_plan.get("filters") or []
        if "product_category" not in group_by:
            reasons.append("follow-up 10 did not group by product_category")
        if not any(
            isinstance(filter_clause, dict)
            and filter_clause.get("column") == "region"
            and str(filter_clause.get("value", "")).lower() == "west"
            for filter_clause in filters
        ):
            reasons.append("follow-up 10 lost the West region filter")

    if question.index == 11 and result.query_plan is not None:
        if result.query_plan.get("intent") != "comparison":
            reasons.append("follow-up 11 did not resolve to comparison")
        if "product_category" not in (result.query_plan.get("group_by") or []):
            reasons.append("follow-up 11 lost the product_category grouping")

    if question.index == 12:
        if result.model_answered != "deterministic_context":
            reasons.append("follow-up 12 unexpectedly used the LLM")

    result.fail_reasons = reasons
    result.auto_pass = not reasons


def _render_results_markdown(
    *,
    started_at: datetime,
    pass_count: int,
    results: list[GoldenQuestionResult],
    pass_bar_hit: bool,
    demo_dataset_id: UUID,
) -> str:
    lines = [
        "# Golden Suite Results",
        "",
        f"- Run date: `{started_at.isoformat()}`",
        f"- Dataset: demo dataset `{demo_dataset_id}`",
        f"- Auto pass count: `{pass_count}/{len(results)}`",
        f"- Pass bar hit (`>= 20/25`): `{'yes' if pass_bar_hit else 'no'}`",
        "- Scope: real `/ask` endpoint, real demo dataset, real Groq calls.",
        "- Review note: auto-pass is structural/plausibility-oriented. A human should still glance through the saved SQL, chart preview, and summary text before deploy.",
        "",
        "## Failures",
    ]

    failures = [result for result in results if not result.auto_pass]
    if not failures:
        lines.append("- None on this run.")
    else:
        for result in failures:
            lines.append(f"- Q{result.index}: {result.question}")
            lines.append(f"  Reasons: {', '.join(result.fail_reasons)}")

    lines.append("")
    lines.append("## Per Question")

    for result in results:
        lines.extend(
            [
                "",
                f"### Q{result.index}. {result.question}",
                f"- Auto judgment: `{'PASS' if result.auto_pass else 'FAIL'}`",
                f"- Model answered: `{result.model_answered}`",
                f"- HTTP status: `{result.response_status}`",
                f"- Session ID: `{result.session_id}`",
                f"- Answer ID: `{result.answer_id}`",
                f"- Chart returned: `{result.chart_returned}`",
                f"- Chart type: `{result.chart_type}`",
                f"- Clarification required: `{result.clarification_required is not None}`",
                f"- Manual review note: {result.manual_review_note}",
                "",
                "Summary:",
                "```text",
                (result.summary or "").strip(),
                "```",
                "",
                "Query plan:",
                "```json",
                json.dumps(result.query_plan, indent=2, default=str) if result.query_plan is not None else "null",
                "```",
                "",
                "Compiled SQL:",
                "```sql",
                (result.compiled_sql or "").strip(),
                "```",
                "",
                "Chart preview:",
                "```json",
                json.dumps(result.chart_preview, indent=2, default=str),
                "```",
            ]
        )
        if result.fail_reasons:
            lines.append("")
            lines.append(f"Fail reasons: {', '.join(result.fail_reasons)}")

    lines.append("")
    return "\n".join(lines) + "\n"


def test_golden_suite_real_ask_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    if os.getenv(RUN_FLAG) != "1":
        pytest.skip(f"set {RUN_FLAG}=1 to run the quota-consuming golden suite manually before deploy")

    if not _has_live_credentials():
        pytest.skip("requires populated apps/api/.env with live Supabase and Groq credentials")

    env = _load_env_file(API_ENV_FILE)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    settings = _override_settings(env)

    from app.main import create_app
    from app.db.supabase_client import reset_supabase_client

    get_settings.cache_clear()
    reset_supabase_client()

    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    client = TestClient(app)

    workspace_repo = WorkspaceRepository()
    dataset_repo = DatasetRepository()
    dataset_column_repo = DatasetColumnRepository()
    ask_message_repo = __import__("app.db.repositories", fromlist=["AskMessageRepository"]).AskMessageRepository()
    supabase = workspace_repo._client

    demo_dataset = dataset_repo.get_demo_dataset()
    if demo_dataset is None:
        pytest.skip("Demo dataset not seeded. Run the demo seed flow before the golden suite.")

    demo_columns = dataset_column_repo.list_for_dataset(demo_dataset.workspace_id, demo_dataset.id)
    allowed_columns = {column.name for column in demo_columns}

    user_id: UUID | None = None
    workspace_id: UUID | None = None
    started_at = datetime.now(UTC)
    results: list[GoldenQuestionResult] = []
    session_map: dict[str, str] = {}
    active_result: GoldenQuestionResult | None = None
    groq_handler = _GroqTraceHandler()
    groq_logger = logging.getLogger("app.nlq.groq_client")
    groq_logger.addHandler(groq_handler)
    groq_logger.setLevel(logging.INFO)

    async def traced_get_intent(*args, **kwargs):
        nonlocal active_result
        start_idx = len(groq_handler.messages)
        try:
            return await real_get_intent(*args, **kwargs)
        finally:
            if active_result is not None:
                active_result.model_answered = _model_from_logs(groq_handler.messages[start_idx:])

    def traced_execute_dataset_query(*args, **kwargs):
        nonlocal active_result
        sql = kwargs.get("sql")
        if sql is None and len(args) >= 3:
            sql = args[2]
        try:
            result = real_execute_dataset_query(*args, **kwargs)
        except Exception as exc:
            if active_result is not None:
                active_result.compiled_sql = str(sql) if sql is not None else None
                active_result.engine_error = f"{type(exc).__name__}: {exc}"
            raise
        if active_result is not None:
            active_result.compiled_sql = str(sql) if sql is not None else None
        return result

    pass_count = 0
    try:
        email = f"golden-suite-{uuid4().hex}@example.com"
        password = f"T3st!{uuid4().hex}"
        user_response = supabase.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
        )
        user_id = UUID(user_response.user.id)
        workspace = workspace_repo.create(
            user_id,
            __import__("app.db.models", fromlist=["WorkspaceCreate"]).WorkspaceCreate(
                name="Golden Suite Workspace",
                slug=f"golden-suite-{uuid4().hex[:8]}",
            ),
        )
        workspace_id = workspace.id
        headers = {"Authorization": f"Bearer {_build_auth_token(env, user_id)}"}

        with (
            patch("app.api.routes_ask.get_intent", new=traced_get_intent),
            patch("app.api.routes_ask.execute_dataset_query", new=traced_execute_dataset_query),
        ):
            for question in QUESTIONS:
                result = GoldenQuestionResult(index=question.index, question=question.question)
                results.append(result)
                active_result = result

                payload: dict[str, Any] = {
                    "dataset_id": str(demo_dataset.id),
                    "question": question.question,
                }
                if question.followup_to_session_key is not None:
                    chained_session_id = session_map.get(question.followup_to_session_key)
                    if chained_session_id is None:
                        result.fail_reasons.append(
                            f"missing chained session '{question.followup_to_session_key}' from prerequisite question"
                        )
                        result.model_answered = "deterministic_context"
                        continue
                    payload["session_id"] = chained_session_id

                try:
                    response = client.post("/ask", json=payload, headers=headers, timeout=180.0)
                    result.response_status = response.status_code
                    body = response.json()
                    result.summary = body.get("summary")
                    result.answer_id = body.get("answer_id")
                    result.session_id = body.get("session_id")
                    result.query_plan = body.get("query_plan")
                    result.clarification_required = body.get("clarification_required")
                    result.chart_returned = body.get("chart") is not None
                    if isinstance(body.get("chart"), dict):
                        result.chart_type = body["chart"].get("type")
                        chart_data = body["chart"].get("data")
                        if isinstance(chart_data, list):
                            result.chart_preview = chart_data[:3]

                    if result.model_answered == "not_called" and result.query_plan is not None:
                        result.model_answered = "deterministic_context"

                    if result.answer_id and result.session_id and workspace_id is not None:
                        ask_message = ask_message_repo.get_by_id(workspace_id, UUID(result.session_id), UUID(result.answer_id))
                        if ask_message is not None and ask_message.sql_text:
                            result.compiled_sql = ask_message.sql_text

                    if question.store_session_key and result.session_id:
                        session_map[question.store_session_key] = result.session_id
                except Exception as exc:
                    result.fail_reasons.append(f"request exception: {type(exc).__name__}: {exc}")
                finally:
                    _evaluate_result(question, result, allowed_columns)

    finally:
        pass_count = sum(1 for item in results if item.auto_pass)
        if results:
            rendered = _render_results_markdown(
                started_at=started_at,
                pass_count=pass_count,
                results=results,
                pass_bar_hit=pass_count >= 20,
                demo_dataset_id=demo_dataset.id,
            )
            if RESULTS_FILE.exists() and RESULTS_FILE.read_text(encoding="utf-8").strip():
                existing = RESULTS_FILE.read_text(encoding="utf-8").rstrip() + "\n\n---\n\n"
                RESULTS_FILE.write_text(existing + rendered, encoding="utf-8")
            else:
                RESULTS_FILE.write_text(rendered, encoding="utf-8")
        groq_logger.removeHandler(groq_handler)
        if user_id is not None and workspace_id is not None:
            workspace_repo.delete(user_id, workspace_id)
        if user_id is not None:
            supabase.auth.admin.delete_user(str(user_id))

    assert len(results) == 25
    assert RESULTS_FILE.exists()
