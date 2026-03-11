from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from database import supabase
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chunk_id: str
    note_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class VectorStoreService:
    """Service for storing and retrieving embeddings from Supabase pgvector."""
    
    def __init__(self):
        self.client = supabase
    
    async def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        user_id: str,
        note_id: str,
        folder_id: Optional[str] = None
    ) -> int:
        """Store chunk embeddings in Supabase."""
        # Delete existing chunks for this note first
        await self.delete_note_chunks(note_id, user_id)
        
        # Prepare records for insertion
        records = []
        for chunk, embedding in zip(chunks, embeddings):
            records.append({
                "user_id": user_id,
                "note_id": note_id,
                "folder_id": folder_id,
                "content": chunk["content"],
                "chunk_index": chunk["chunk_index"],
                "metadata": chunk["metadata"],
                "embedding": embedding
            })
        
        # Insert in batches
        batch_size = 50
        total_inserted = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            res = self.client.table("note_chunks").insert(batch).execute()
            if res.data:
                total_inserted += len(res.data)
        
        return total_inserted
    
    async def delete_note_chunks(self, note_id: str, user_id: str) -> None:
        """Delete all chunks for a note."""
        self.client.table("note_chunks").delete().eq(
            "note_id", note_id
        ).eq(
            "user_id", user_id
        ).execute()

    # ------------------------------------------------------------------ #
    #  RETRIEVAL METHODS
    # ------------------------------------------------------------------ #

    def _apply_metadata_filters(
        self,
        results: List[SearchResult],
        note_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Post-retrieval metadata filtering.

        Applied client-side after the Supabase RPC returns results.
        This is the safety net for filters that the SQL functions
        don't support natively (tags, folder_id on hybrid/keyword).
        """
        filtered = results

        if note_id:
            filtered = [r for r in filtered if r.note_id == note_id]

        if folder_id:
            filtered = [
                r for r in filtered
                if r.metadata.get("folder_id") == folder_id
            ]

        if tags:
            tags_lower = {t.lower() for t in tags}
            filtered = [
                r for r in filtered
                if tags_lower & {
                    t.lower() for t in (r.metadata.get("tags") or [])
                }
            ]

        if len(filtered) < len(results):
            logger.info(
                f"Metadata filter: {len(results)} → {len(filtered)} results "
                f"(note_id={note_id}, folder_id={folder_id}, tags={tags})"
            )

        return filtered

    async def semantic_search(
        self,
        query_embedding: List[float],
        user_id: str,
        top_k: int = 20,
        note_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        similarity_threshold: float = 0.3,
    ) -> List[SearchResult]:
        """
        ANN search via pgvector cosine distance.
        Uses the Supabase RPC functions defined in vector_search.sql.
        """
        try:
            # Fetch more than top_k so post-filtering still has enough
            fetch_k = top_k * 3 if (folder_id or tags) else top_k

            if note_id:
                res = self.client.rpc(
                    "match_note_chunks_by_note",
                    {
                        "query_embedding": query_embedding,
                        "match_user_id": user_id,
                        "match_note_id": note_id,
                        "match_count": fetch_k,
                        "match_threshold": similarity_threshold,
                    },
                ).execute()
            else:
                res = self.client.rpc(
                    "match_note_chunks",
                    {
                        "query_embedding": query_embedding,
                        "match_user_id": user_id,
                        "match_count": fetch_k,
                        "match_threshold": similarity_threshold,
                    },
                ).execute()

            if not res.data:
                return []

            results = [
                SearchResult(
                    chunk_id=row["id"],
                    note_id=row["note_id"],
                    content=row["content"],
                    score=float(row["similarity"]),
                    metadata=row.get("metadata", {}),
                )
                for row in res.data
            ]

            # Apply metadata filters and trim to requested top_k
            results = self._apply_metadata_filters(
                results, note_id=note_id, folder_id=folder_id, tags=tags,
            )
            return results[:top_k]

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def keyword_search(
        self,
        query_text: str,
        user_id: str,
        top_k: int = 20,
        note_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Full-text keyword search via pg tsvector.
        Calls the keyword_search_chunks RPC function.
        """
        try:
            fetch_k = top_k * 3 if (note_id or folder_id or tags) else top_k

            res = self.client.rpc(
                "keyword_search_chunks",
                {
                    "query_text": query_text,
                    "user_id": user_id,
                    "limit_count": fetch_k,
                },
            ).execute()

            if not res.data:
                return []

            results = [
                SearchResult(
                    chunk_id=row["id"],
                    note_id=row.get("note_id", ""),
                    content=row["content"],
                    score=float(row["score"]),
                    metadata=row.get("metadata", {}),
                )
                for row in res.data
            ]

            results = self._apply_metadata_filters(
                results, note_id=note_id, folder_id=folder_id, tags=tags,
            )
            return results[:top_k]

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    async def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        user_id: str,
        top_k: int = 20,
        note_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Hybrid search combining semantic + keyword via RRF.
        Calls the hybrid_search_chunks RPC function.
        """
        try:
            fetch_k = top_k * 3 if (note_id or folder_id or tags) else top_k

            res = self.client.rpc(
                "hybrid_search_chunks",
                {
                    "query_embedding": query_embedding,
                    "query_text": query_text,
                    "match_user_id": user_id,
                    "match_limit": fetch_k,
                },
            ).execute()

            if not res.data:
                return []

            results = [
                SearchResult(
                    chunk_id=row["id"],
                    note_id=row["note_id"],
                    content=row["content"],
                    score=float(row["score"]),
                    metadata=row.get("metadata", {}),
                )
                for row in res.data
            ]

            results = self._apply_metadata_filters(
                results, note_id=note_id, folder_id=folder_id, tags=tags,
            )
            return results[:top_k]

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    # Keep the old search() as a convenience alias
    async def search(
        self,
        query_embedding: List[float],
        user_id: str,
        top_k: int = 5,
        note_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        similarity_threshold: float = 0.5,
    ) -> List[SearchResult]:
        """Convenience wrapper — delegates to semantic_search."""
        return await self.semantic_search(
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=top_k,
            note_id=note_id,
            folder_id=folder_id,
            tags=tags,
            similarity_threshold=similarity_threshold,
        )


# Singleton
_vector_store: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store