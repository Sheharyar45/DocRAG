"""
Retrieval service — the orchestrator.

Pipeline:  query → analyze → cache check → search → rerank → return
"""

from typing import List, Optional
from dataclasses import dataclass, field
import logging

from services.query_service import (
    QueryService,
    AnalyzedQuery,
    SearchMode,
    get_query_service,
)
from services.cache_service import CacheService, get_cache_service
from services.embedding_service import EmbeddingService, get_embedding_service
from services.vector_store_service import (
    VectorStoreService,
    SearchResult,
    get_vector_store,
)
from services.reranker_service import (
    RerankerService,
    RerankResult,
    get_reranker_service,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Final output of the retrieval pipeline."""
    query: str
    search_mode: str
    results: List[RerankResult]
    total_candidates: int          # how many came back from search before reranking
    cache_hit: bool = False


class RetrievalService:
    """
    Orchestrates the full retrieval pipeline:
    1. Query analysis  →  structured filters
    2. Cache check      →  return early on hit
    3. Embed query      →  dense vector
    4. Search           →  semantic / keyword / hybrid
    5. Rerank           →  cross-encoder scoring
    6. Cache store      →  save for next time
    """

    def __init__(
        self,
        query_service: QueryService = None,
        cache_service: CacheService = None,
        embedding_service: EmbeddingService = None,
        vector_store: VectorStoreService = None,
        reranker: RerankerService = None,
    ):
        self.query_svc = query_service or get_query_service()
        self.cache = cache_service or get_cache_service()
        self.embedder = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store()
        self.reranker = reranker or get_reranker_service()

    async def retrieve(
        self,
        query: str,
        user_id: str,
        note_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        search_mode: str = "hybrid",
        search_top_k: int = 20,
        rerank_top_k: int = 5,
    ) -> RetrievalResult:
        """
        Run the full retrieval pipeline and return reranked results.
        """
        # ── 1. Query analysis ──────────────────────────────────────
        analyzed: AnalyzedQuery = self.query_svc.analyze(
            query=query,
            user_id=user_id,
            note_id=note_id,
            folder_id=folder_id,
            search_mode=search_mode,
        )
        mode = analyzed.search_mode
        filters = analyzed.filters

        # ── 2. Cache check ─────────────────────────────────────────
        cache_kwargs = dict(
            note_id=filters.note_id,
            folder_id=filters.folder_id,
            tags=",".join(sorted(filters.tags)) if filters.tags else None,
            search_mode=mode.value,
        )
        cached = self.cache.get(analyzed.cleaned_query, user_id, **cache_kwargs)
        if cached is not None:
            logger.info("Returning cached retrieval result")
            cached.cache_hit = True
            return cached

        # ── 3. Embed the query ─────────────────────────────────────
        query_embedding = None
        if mode in (SearchMode.SEMANTIC, SearchMode.HYBRID):
            embed_result = await self.embedder.embed_query(analyzed.cleaned_query)
            query_embedding = embed_result.embedding

        # ── 4. Search ──────────────────────────────────────────────
        candidates: List[SearchResult] = []

        if mode == SearchMode.SEMANTIC:
            candidates = await self.vector_store.semantic_search(
                query_embedding=query_embedding,
                user_id=user_id,
                top_k=search_top_k,
                note_id=filters.note_id,
                folder_id=filters.folder_id,
                tags=filters.tags,
                similarity_threshold=0.3,
            )

        elif mode == SearchMode.KEYWORD:
            candidates = await self.vector_store.keyword_search(
                query_text=analyzed.cleaned_query,
                user_id=user_id,
                top_k=search_top_k,
                note_id=filters.note_id,
                folder_id=filters.folder_id,
                tags=filters.tags,
            )

        elif mode == SearchMode.HYBRID:
            candidates = await self.vector_store.hybrid_search(
                query_embedding=query_embedding,
                query_text=analyzed.cleaned_query,
                user_id=user_id,
                top_k=search_top_k,
                note_id=filters.note_id,
                folder_id=filters.folder_id,
                tags=filters.tags,
            )

        total_candidates = len(candidates)
        logger.info(
            f"Search returned {total_candidates} candidates (mode={mode.value})"
        )

        if not candidates:
            result = RetrievalResult(
                query=analyzed.cleaned_query,
                search_mode=mode.value,
                results=[],
                total_candidates=0,
                cache_hit=False,
            )
            return result

        # ── 5. Rerank ─────────────────────────────────────────────
        reranked = self.reranker.rerank(
            query=analyzed.cleaned_query,
            results=candidates,
            top_k=rerank_top_k,
        )

        result = RetrievalResult(
            query=analyzed.cleaned_query,
            search_mode=mode.value,
            results=reranked,
            total_candidates=total_candidates,
            cache_hit=False,
        )

        # ── 6. Cache store ─────────────────────────────────────────
        self.cache.set(analyzed.cleaned_query, user_id, result, **cache_kwargs)

        return result


# Singleton
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
