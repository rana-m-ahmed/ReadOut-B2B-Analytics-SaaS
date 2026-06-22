"""Plain-English query routes."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

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
    session_id: UUID | None = None


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
    raw_intent = None
    
    if request.session_id:
        messages = msg_repo.list_for_session(workspace_id, request.session_id)
        prior_intent_dict = None
        for m in sorted(messages, key=lambda x: x.created_at):
            history.append({"role": m.role, "content": m.content})
            if m.role == "assistant" and m.chart_spec and "meta" in m.chart_spec and "intent" in m.chart_spec["meta"]:
                prior_intent_dict = m.chart_spec["meta"]["intent"]
                
        if prior_intent_dict:
            try:
                from app.nlq.schemas import analytics_intent_adapter
                parsed_prior_intent = analytics_intent_adapter.validate_python(prior_intent_dict)
                from app.nlq.context_resolver import resolve_context
                resolved = resolve_context(parsed_prior_intent, request.question, dataset_columns)
                if resolved != "treat_as_fresh":
                    raw_intent = resolved
            except Exception as e:
                logger.warning(f"Failed to resolve context: {e}")
        
        # limit history sent to LLM
        history = history[-settings.ASK_CONTEXT_TURN_LIMIT:]
    else:
        # create new session
        session = session_repo.create(
            workspace_id,
            AskSessionCreate(dataset_id=request.dataset_id, created_by=current_user.user_id, title=request.question[:50]),
        )
        request.session_id = session.id

    # 4. Generate Intent
    try:
        if raw_intent is None:
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
            session_id=request.session_id,
        )

    validated_intent = validation_result
    if validated_intent.intent.intent == IntentType.CLARIFICATION_REQUIRED:
        return AskResponse(
            summary="I need more information to answer your question.",
            chart=None,
            query_plan=None,
            clarification_required=ClarificationRejection(
                code="clarification_required",
                message="The question is ambiguous. Please specify what metrics or dimensions you want to see.",
            ),
            session_id=request.session_id,
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
        
        chart_payload = format_results(
            result=result_df,
            title="Analysis Result",
            description=request.question,
            settings=settings,
            override_chart_type=validated_intent.intent.chart_hint,
            meta={"intent": validated_intent.intent.model_dump()},
        )
    except QueryCompilationError as e:
        logger.error(f"Query compilation failed: {e}")
        return AskResponse(
            summary="I couldn't process that query. Please try rephrasing.",
            session_id=request.session_id,
        )
    except Exception as e:
        logger.error(f"Execution or formatting failed: {e}")
        return AskResponse(
            summary="An error occurred while analyzing the data. Please try rephrasing.",
            session_id=request.session_id,
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

    # Generate suggested followups deterministically
    followups = []
    used_cols = set(validated_intent.intent.group_by)
    unused_dims = [c for c in dataset_columns if (c.semantic_role == "dimension" or c.data_type == "category") and c.name not in used_cols]
    
    if validated_intent.intent.intent in (IntentType.SINGLE_METRIC, IntentType.TIME_SERIES):
        if unused_dims:
            followups.append(f"Break that down by {unused_dims[0].display_name or unused_dims[0].name.replace('_', ' ')}")
        followups.append("Compare with previous period")
        if len(unused_dims) > 1:
            followups.append(f"Only for a specific {unused_dims[1].display_name or unused_dims[1].name.replace('_', ' ')}")
    elif validated_intent.intent.intent == IntentType.GROUPED_METRIC:
        followups.append("Show as a pie chart")
        if unused_dims:
            followups.append(f"Break it down by {unused_dims[0].display_name or unused_dims[0].name.replace('_', ' ')} instead")
        followups.append("What caused that?")
    else:
        followups.append("What caused that?")
        followups.append("Show as a table")
        if unused_dims:
            followups.append(f"Filter by {unused_dims[0].display_name or unused_dims[0].name.replace('_', ' ')}")
            
    suggested_followups = list(dict.fromkeys(followups))[:3]

    # 9. Return Response
    return AskResponse(
        answer_id=answer_id,
        summary=summary,
        chart=chart_payload.model_dump(),
        query_plan=validated_intent.intent.model_dump(),
        confidence="high",
        suggested_followups=suggested_followups,
        session_id=request.session_id,
    )
