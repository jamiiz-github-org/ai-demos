"""
Chat routes — single endpoint handles all three assistant types.
Document assistant uses LangGraph; others use simple RAG + LLM.
"""
import logging
import uuid

from fastapi import APIRouter

from app.core.config import get_settings
from app.graphs.document_graph import run_document_graph
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.lead_service import log_question
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service

logger = logging.getLogger("jamiiz.routes.chat")
router = APIRouter(prefix="/chat", tags=["chat"])

# After this many assistant turns, nudge for a booking
BOOKING_NUDGE_AFTER = 3


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    session_id = request.session_id or str(uuid.uuid4())
    history = [m.model_dump() for m in request.history]

    if request.assistant_type == "document":
        return await _document_chat(request, session_id, history, settings)
    else:
        return await _simple_chat(request, session_id, history, settings)


async def _document_chat(
    request: ChatRequest,
    session_id: str,
    history: list[dict],
    settings,
) -> ChatResponse:
    """Run the LangGraph document reasoning pipeline."""
    namespace = (
        request.namespace_override
        or settings.namespace_for(request.assistant_type)
    )

    result = run_document_graph(
        question=request.message,
        namespace=namespace,
        history=history,
    )

    log_question(
        question=request.message,
        answer=result["answer"],
        assistant=request.assistant_type,
        session_id=session_id,
    )

    suggest = len(history) >= BOOKING_NUDGE_AFTER * 2

    return ChatResponse(
        answer=result["answer"],
        assistant_type=request.assistant_type,
        session_id=session_id,
        sources=result.get("sources", []),
        confidence=result.get("confidence", "high"),
        intent=result.get("intent"),
        suggest_booking=suggest,
    )


async def _simple_chat(
    request: ChatRequest,
    session_id: str,
    history: list[dict],
    settings,
) -> ChatResponse:
    """Simple RAG + LLM for website and property assistants."""
    namespace = settings.namespace_for(request.assistant_type)
    rag = get_rag_service()
    llm = get_llm_service()

    docs, context = rag.retrieve_and_format(
        query=request.message,
        namespace=namespace,
    )
    sources = list({doc.metadata.get("source", "unknown") for doc in docs})

    answer = llm.chat(
        assistant_type=request.assistant_type,
        user_message=request.message,
        context=context,
        history=history,
    )

    log_question(
        question=request.message,
        answer=answer,
        assistant=request.assistant_type,
        session_id=session_id,
    )

    suggest = len(history) >= BOOKING_NUDGE_AFTER * 2

    return ChatResponse(
        answer=answer,
        assistant_type=request.assistant_type,
        session_id=session_id,
        sources=sources,
        suggest_booking=suggest,
    )
