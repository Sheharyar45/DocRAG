"""
Cross-encoder reranker service.

Takes top-K candidates from hybrid search and re-scores them using
a cross-encoder model for more accurate relevance ranking.

Scores are normalized via sigmoid so they sit in the 0-1 range,
and a minimum threshold is applied to drop irrelevant chunks
before they reach the LLM.
"""

from typing import List, Optional
from dataclasses import dataclass
import math
from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)

# Minimum relevance probability (after sigmoid).
# Chunks below this are considered irrelevant and dropped.
DEFAULT_MIN_SCORE = 0.10


def _sigmoid(x: float) -> float:
    """Convert a raw logit to a 0-1 probability."""
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class RerankResult:
    """A search result with an additional reranker score."""
    chunk_id: str
    note_id: str
    content: str
    original_score: float
    rerank_score: float          # sigmoid-normalized, 0-1
    metadata: dict


class RerankerService:
    """
    Reranks search results using a cross-encoder model.
    Cross-encoders jointly encode (query, passage) pairs for
    much more accurate relevance scores than bi-encoders.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model_name = model_name
        logger.info(f"Loading reranker model: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info("Reranker model loaded successfully")

    def rerank(
        self,
        query: str,
        results: list,  # List[SearchResult] from vector_store_service
        top_k: int = 5,
        min_score: float = DEFAULT_MIN_SCORE,
    ) -> List[RerankResult]:
        """
        Rerank search results using the cross-encoder.

        Args:
            query: The user's search query.
            results: List of SearchResult objects from the retrieval step.
            top_k: Number of top results to return after reranking.
            min_score: Minimum sigmoid-normalized score (0-1). Results
                       below this threshold are dropped entirely.

        Returns:
            Top-K results sorted by reranker score (descending),
            with irrelevant results removed.
        """
        if not results:
            return []

        # Build (query, passage) pairs for the cross-encoder
        pairs = [(query, r.content) for r in results]

        # Score all pairs in one batch — returns raw logits
        raw_scores = self.model.predict(pairs, show_progress_bar=False)

        # Combine original results with sigmoid-normalized scores
        reranked = []
        for result, raw in zip(results, raw_scores):
            prob = _sigmoid(float(raw))
            reranked.append(
                RerankResult(
                    chunk_id=result.chunk_id,
                    note_id=result.note_id,
                    content=result.content,
                    original_score=result.score,
                    rerank_score=prob,
                    metadata=result.metadata,
                )
            )

        # Sort by reranker score descending
        reranked.sort(key=lambda r: r.rerank_score, reverse=True)

        # Drop anything below the minimum relevance threshold
        before_count = len(reranked)
        reranked = [r for r in reranked if r.rerank_score >= min_score]

        if before_count != len(reranked):
            logger.info(
                f"Threshold filter ({min_score}): {before_count} → {len(reranked)} results"
            )

        # Always keep at least 1 result if anything survived the threshold
        final = reranked[:top_k]

        if final:
            logger.info(
                f"Reranked {len(results)} candidates → {len(final)} returned. "
                f"Score range: [{final[-1].rerank_score:.3f}, {final[0].rerank_score:.3f}]"
            )
        else:
            logger.info(
                f"Reranked {len(results)} candidates → 0 survived threshold {min_score}"
            )

        return final


# Singleton
_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService()
    return _reranker_service
