from typing import Optional
from dataclasses import dataclass

from services.embedding_service import get_embedding_service, EmbeddingService
from services.vector_store_service import get_vector_store, VectorStoreService
from utils.chunking import chunk_note, Chunk


@dataclass
class IngestionResult:
    note_id: str
    chunks_created: int
    success: bool
    error: Optional[str] = None


class IngestionService:
    """Service for ingesting notes into the vector store."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService = None,
        vector_store: VectorStoreService = None
    ):
        self.embedder = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store()
    
    async def ingest_note(
        self,
        note_id: str,
        title: str,
        content: str,
        user_id: str,
        folder_id: Optional[str] = None,
        tags: Optional[list] = None
    ) -> IngestionResult:
        """
        Full ingestion pipeline for a note:
        1. Chunk the content
        2. Generate embeddings
        3. Store in vector database
        """
        try:
            # Skip if content is empty or too short
            if not content or len(content.strip()) < 10:
                return IngestionResult(
                    note_id=note_id,
                    chunks_created=0,
                    success=True,
                    error=None
                )
            
            # Step 1: Chunk the note
            chunks = chunk_note(
                note_id=note_id,
                title=title,
                content=content,
                folder_id=folder_id,
                tags=tags or []
            )
            
            if not chunks:
                return IngestionResult(
                    note_id=note_id,
                    chunks_created=0,
                    success=True,
                    error=None
                )
            
            # Step 2: Generate embeddings
            texts = [chunk.content for chunk in chunks]
            embedding_results = await self.embedder.embed_texts(texts)
            embeddings = [r.embedding for r in embedding_results]
            
            # Step 3: Store in vector database
            chunk_dicts = [
                {
                    "content": c.content,
                    "chunk_index": c.chunk_index,
                    "metadata": c.metadata
                }
                for c in chunks
            ]
            
            chunks_stored = await self.vector_store.upsert_chunks(
                chunks=chunk_dicts,
                embeddings=embeddings,
                user_id=user_id,
                note_id=note_id,
                folder_id=folder_id
            )
            
            return IngestionResult(
                note_id=note_id,
                chunks_created=chunks_stored,
                success=True,
                error=None
            )
            
        except Exception as e:
            return IngestionResult(
                note_id=note_id,
                chunks_created=0,
                success=False,
                error=str(e)
            )
    
    async def delete_note(self, note_id: str, user_id: str) -> bool:
        """Remove a note from the vector store."""
        try:
            await self.vector_store.delete_note_chunks(note_id, user_id)
            return True
        except Exception:
            return False
    
    async def reindex_note(
        self,
        note_id: str,
        title: str,
        content: str,
        user_id: str,
        folder_id: Optional[str] = None
    ) -> IngestionResult:
        """Re-index a note (delete old chunks, create new ones)."""
        # Delete is handled inside ingest_note via upsert_chunks
        return await self.ingest_note(note_id, title, content, user_id, folder_id)


# Singleton
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service