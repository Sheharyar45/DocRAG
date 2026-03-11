"""
Chat router — API endpoints for the RAG chat pipeline.

POST /api/chat/           → Global chat across all user notes
POST /api/chat/note/{id}  → Chat scoped to a specific note
"""

from fastapi import APIRouter, Depends, HTTPException
from database import supabase
from deps.auth import get_current_user
from schemas import ChatRequest, ChatResponse, SourceCitationOut
from services.retrieval_service import get_retrieval_service
from services.query_service import get_query_service
from services.llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


def _load_folder_map(user_id: str) -> dict:
    """Fetch the user's folders and build a {name_lower: id} mapping."""
    try:
        res = supabase.table("folders").select("id, name").eq("user_id", user_id).execute()
        if res.data:
            return {row["name"]: row["id"] for row in res.data}
    except Exception as e:
        logger.warning(f"Failed to load folder map: {e}")
    return {}


@router.post("/", response_model=ChatResponse)
async def global_chat(
    payload: ChatRequest,
    user=Depends(get_current_user),
):
    """
    Chat across ALL of the user's notes.
    Uses hybrid search + reranking + Gemini to generate an answer.
    """
    user_id = user["id"]
    logger.info(
        f"Global chat: user={user_id}, mode={payload.search_mode}, "
        f"query={payload.query[:80]}..."
    )

    # Hydrate folder map so query_service can resolve "folder:X" directives
    folder_map = _load_folder_map(user_id)
    get_query_service().set_folder_map(folder_map)

    return await _run_chat_pipeline(
        query=payload.query,
        user_id=user_id,
        note_id=None,
        folder_id=payload.folder_id,
        search_mode=payload.search_mode,
        top_k=payload.top_k,
        conversation_history=payload.conversation_history,
    )


@router.post("/note/{note_id}", response_model=ChatResponse)
async def note_chat(
    note_id: str,
    payload: ChatRequest,
    user=Depends(get_current_user),
):
    """
    Chat scoped to a SPECIFIC note.
    Retrieval is filtered to only chunks belonging to this note.
    """
    user_id = user["id"]
    logger.info(
        f"Note chat: user={user_id}, note={note_id}, "
        f"query={payload.query[:80]}..."
    )

    return await _run_chat_pipeline(
        query=payload.query,
        user_id=user_id,
        note_id=note_id,
        folder_id=payload.folder_id,
        search_mode=payload.search_mode,
        top_k=payload.top_k,
        conversation_history=payload.conversation_history,
    )


async def _run_chat_pipeline(
    query: str,
    user_id: str,
    note_id: str | None,
    folder_id: str | None,
    search_mode: str,
    top_k: int,
    conversation_history: list | None,
) -> ChatResponse:
    """Shared pipeline logic for both global and note-scoped chat."""

    retrieval = get_retrieval_service()
    llm = get_llm_service()

    # ── Retrieve ────────────────────────────────────────────────
    retrieval_result = await retrieval.retrieve(
        query=query,
        user_id=user_id,
        note_id=note_id,
        folder_id=folder_id,
        search_mode=search_mode,
        search_top_k=max(top_k * 4, 20),   # fetch more candidates for reranking
        rerank_top_k=top_k,
    )

    # ── Generate answer ─────────────────────────────────────────
    history_dicts = None
    if conversation_history:
        history_dicts = [{"role": m.role, "content": m.content} for m in conversation_history]

    llm_result = await llm.generate_answer(
        query=query,
        reranked_results=retrieval_result.results,
        note_id=note_id,
        conversation_history=history_dicts,
    )

    # ── Build response ──────────────────────────────────────────
    sources = [
        SourceCitationOut(
            note_id=s.note_id,
            title=s.title,
            snippet=s.snippet,
            score=round(s.score, 4),
        )
        for s in llm_result.sources
    ]

    return ChatResponse(
        answer=llm_result.answer,
        sources=sources,
        search_mode=retrieval_result.search_mode,
        chunks_retrieved=retrieval_result.total_candidates,
        cache_hit=retrieval_result.cache_hit,
    )
