"""Plain-English query routes."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.analytics.chart_recommender import recommend_chart_type
from app.analytics.duckdb_engine import execute_dataset_query
from app.analytics.query_compiler import compile_analytics_intent
from app.analytics.result_formatter import format_results
from app.core.config import Settings, get_settings
from app.core.errors import QueryCompilationError, UpstreamLLMError
from app.api.routes_datasets import _resolve_current_workspace
from app.db.models import AskMessageCreate, AskSessionCreate
from app.db.repositories import AskMessageRepository, AskSessionRepository, DatasetColumnRepository, WorkspaceRepository, DatasetRepository
from app.nlq.groq_client import generate_summary, get_intent
from app.nlq.schemas import IntentType
from app.nlq.intent_validator import IntentValidationRejected, validate_analytics_intent
from app.security.auth_guard import CurrentUser, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    dataset_id: UUID
    question: str
    session_id: UUID | None = None


class ChartPayload(BaseModel):
    type: str
    title: str
    description: str
    x_key: str
    y_keys: list[str]
    series: list[dict] | None = None
    data: list[dict]
    meta: dict


class ClarificationRejection(BaseModel):
    code: str
    message: str


class AskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_id: UUID | None = None
    summary: str | None = None
    chart: dict | None = None
    query_plan: dict | None = None
    confidence: str | None = None
    suggested_followups: list[str] = Field(default_factory=list)
    clarification_required: ClarificationRejection | None = None


@router.post("", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AskResponse:
    workspace_repo = WorkspaceRepository()
    workspace = _resolve_current_workspace(current_user, workspace_repo)
    workspace_id = workspace.id

    # 2. Load dataset columns
    col_repo = DatasetColumnRepository()
    dataset_repo = DatasetRepository()
    demo_ds = dataset_repo.get_demo_dataset()
    
    if demo_ds and request.dataset_id == demo_ds.id:
        dataset_columns = col_repo.list_for_dataset(demo_ds.workspace_id, demo_ds.id)
    else:
        dataset_columns = col_repo.list_for_dataset(workspace_id, request.dataset_id)
        
    if not dataset_columns:
        print(f"DEBUG: demo_ds={demo_ds}, request.dataset_id={request.dataset_id}, workspace_id={workspace_id}")
        if demo_ds:
            print(f"DEBUG: demo_ds.workspace_id={demo_ds.workspace_id}, demo_ds.id={demo_ds.id}")
            ds_get_by_id = dataset_repo.get_by_id(demo_ds.workspace_id, demo_ds.id)
            print(f"DEBUG: ds_get_by_id={ds_get_by_id}")
        raise ValueError(f"Dataset not found or has no columns (id={request.dataset_id})")

    # 3. Load ask session history
    msg_repo = AskMessageRepository()
    session_repo = AskSessionRepository()
    history = []
    
    if request.session_id:
        # TODO(phase-5): implement full context-merging logic via context_resolver.py
        messages = msg_repo.list_for_session(workspace_id, request.session_id)
        # simplistic translation for now
        for m in sorted(messages, key=lambda x: x.created_at)[-settings.ASK_CONTEXT_TURN_LIMIT:]:
            history.append({"role": m.role, "content": m.content})
    else:
        # create new session
        session = session_repo.create(
            workspace_id,
            AskSessionCreate(dataset_id=request.dataset_id, created_by=current_user.user_id, title=request.question[:50]),
        )
        request.session_id = session.id

    # 4. Generate Intent
    try:
        raw_intent = await get_intent(request.question, dataset_columns, history, settings)
    except UpstreamLLMError as e:
        # Graceful degradation
        logger.warning(f"UpstreamLLMError during get_intent: {e}")
        return AskResponse(
            summary="I'm having trouble connecting to my analysis engine right now. Please try again in a moment.",
        )

    # 5. Validate Intent
    # intent_validator expects a slightly different shape for DatasetIntentColumn
    # let's adapt dataset_columns:
    from app.nlq.intent_validator import DatasetIntentColumn
    adapted_columns = [
        DatasetIntentColumn(
            name=c.name, 
            data_type=c.data_type, 
            unique_count=len(c.sample_values) if c.sample_values else None
        )
        for c in dataset_columns
    ]

    validation_result = validate_analytics_intent(raw_intent, adapted_columns, settings)

    if isinstance(validation_result, IntentValidationRejected):
        return AskResponse(
            clarification_required=ClarificationRejection(
                code=validation_result.rejection.code.value,
                message=validation_result.rejection.message,
            ),
            suggested_followups=["Can you rephrase your question?"],
        )

    validated_intent = validation_result
    if validated_intent.intent.intent == IntentType.CLARIFICATION_REQUIRED:
        return AskResponse(
            question=request.question,
            summary="I need more information to answer your question.",
            chart=None,
            query_plan=None,
            clarification_required=ClarificationRejection(
                code="clarification_required",
                message="The question is ambiguous. Please specify what metrics or dimensions you want to see.",
            ),
        )

    # Determine execution workspace (demo dataset is in its own workspace)
    execution_workspace_id = demo_ds.workspace_id if (demo_ds and request.dataset_id == demo_ds.id) else workspace_id
    
    # 6. Compile, Execute, Format
    try:
        compiled = compile_analytics_intent(validated_intent)
        query = compiled.sql
        params = compiled.params
        result_df = execute_dataset_query(
            workspace_id=execution_workspace_id,
            dataset_id=request.dataset_id,
            sql=query,
            parameters=params,
            settings=settings,
        )
        
        result_shape = "single_value"
        if len(result_df.columns) > 1:
            result_shape = "time_series" if "bucket" in result_df.columns else "grouped"
            
        chart_type = recommend_chart_type(result_df)
        
        chart_payload = format_results(
            result=result_df,
            title="Analysis Result",
            description=request.question,
            settings=settings,
        )
    except QueryCompilationError as e:
        logger.error(f"Query compilation failed: {e}")
        return AskResponse(
            summary="I couldn't process that query. Please try rephrasing.",
        )
    except Exception as e:
        logger.error(f"Execution or formatting failed: {e}")
        return AskResponse(
            summary="An error occurred while analyzing the data. Please try rephrasing.",
        )

    # 7. Generate one-sentence summary
    try:
        # pass chart_payload data subset to save tokens
        summary = await generate_summary(request.question, chart_payload.data[:10], settings)
    except UpstreamLLMError:
        summary = "Here is the chart you requested."

    # 8. Persist the turn
    answer_id = uuid4()
    
    # Save the user message
    msg_repo.create(
        workspace_id,
        AskMessageCreate(
            session_id=request.session_id,
            role="user",
            content=request.question,
        )
    )
    
    # Save the assistant message
    msg_repo.create(
        workspace_id,
        AskMessageCreate(
            id=answer_id,
            session_id=request.session_id,
            role="assistant",
            content=summary,
            sql_text=query,
            chart_spec=chart_payload.model_dump(),
        )
    )

    # 9. Return Response
    return AskResponse(
        answer_id=answer_id,
        summary=summary,
        chart=chart_payload.model_dump(),
        query_plan=validated_intent.intent.model_dump(),
        confidence="high",
        suggested_followups=["What else can you tell me?", "Show me a different metric."],
    )
