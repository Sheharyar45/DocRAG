"""
Cross-encoder reranker service.

Takes top-K candidates from hybrid search and re-scores them using
a cross-encoder model for more accurate relevance ranking.

Improvements over basic rerankers:
- Uses raw logits (better ranking signal)
- Supports batching
- Device auto-detection (CPU/GPU)
- Per-note diversity constraint
- Safe fallback if threshold removes all results
- Optional passage truncation for stability
"""

from typing import List, Optional
from dataclasses import dataclass
from sentence_transformers import CrossEncoder
import logging
import torch

logger = logging.getLogger(__name__)

DEFAULT_MIN_SCORE = -10.0
DEFAULT_BATCH_SIZE = 32
MAX_CHARS = 1500
MAX_PER_NOTE = 2


@dataclass
class RerankResult:
    """Search result with reranker score."""
    chunk_id: str
    note_id: str
    content: str
    original_score: float
    rerank_score: float
    metadata: dict


class RerankerService:
    """
    Cross-encoder reranker.

    Cross-encoders jointly encode (query, passage) pairs and produce
    significantly better relevance signals than embedding similarity.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        self.model_name = model_name
        self.batch_size = batch_size

        device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Loading reranker model: {model_name} on {device}")
        self.model = CrossEncoder(model_name, device=device)
        logger.info("Reranker model loaded successfully")

    def _truncate(self, text: str) -> str:
        """Prevent extremely long passages from slowing reranking."""
        if len(text) > MAX_CHARS:
            return text[:MAX_CHARS]
        return text

    def rerank(
        self,
        query: str,
        results: list,
        top_k: int = 5,
        min_score: float = DEFAULT_MIN_SCORE,
        max_per_note: int = MAX_PER_NOTE,
    ) -> List[RerankResult]:
        """
        Rerank search results using cross-encoder scoring.

        Args:
            query: User query
            results: candidates from retrieval step
            top_k: results to return
            min_score: minimum reranker logit
            max_per_note: max chunks allowed per note

        Returns:
            Top-K reranked results
        """

        if not results:
            return []

        logger.info(f"Reranking {len(results)} candidates")

        # Build input pairs
        pairs = [(query, self._truncate(r.content)) for r in results]

        # Predict logits
        raw_scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        reranked: List[RerankResult] = []

        for result, score in zip(results, raw_scores):
            reranked.append(
                RerankResult(
                    chunk_id=result.chunk_id,
                    note_id=result.note_id,
                    content=result.content,
                    original_score=result.score,
                    rerank_score=float(score),
                    metadata=result.metadata,
                )
            )

        # Sort by reranker score
        reranked.sort(key=lambda r: r.rerank_score, reverse=True)

        # Apply score threshold
        filtered = [r for r in reranked if r.rerank_score >= min_score]

        if not filtered:
            logger.warning(
                "All results removed by threshold — falling back to retrieval ranking"
            )
            filtered = reranked

        # Enforce diversity (max chunks per note)
        final: List[RerankResult] = []
        note_counts = {}

        for r in filtered:
            count = note_counts.get(r.note_id, 0)

            if count >= max_per_note:
                continue

            final.append(r)
            note_counts[r.note_id] = count + 1

            if len(final) >= top_k:
                break

        logger.info(
            f"Rerank completed: {len(results)} → {len(final)} returned "
            f"(score range: {final[-1].rerank_score:.2f} - {final[0].rerank_score:.2f})"
        )
        print(f"Final reranked results: {[f'{r.content[:50]}... ({r.rerank_score:.2f})' for r in final]}")
        return final


# Singleton instance
_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    global _reranker_service

    if _reranker_service is None:
        _reranker_service = RerankerService()

    return _reranker_service