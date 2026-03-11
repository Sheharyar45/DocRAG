from typing import List, Optional
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import time
import logging
import numpy as np


logger = logging.getLogger(__name__)
max_retries = 3


@dataclass
class EmbeddingResult:
    text: str
    embedding: List[float]
    model: str
    token_count: Optional[int] = None

def normalize_embedding(v: List[float]) -> List[float]:
    """Normalize a vector to unit length for cosine similarity."""
    arr = np.array(v)
    norm = np.linalg.norm(arr)
    if norm == 0:
        logger.warning("Zero-norm embedding detected, returning as-is")
        return v
    return (arr / norm).tolist()

class EmbeddingService:
    """Service for generating text embeddings using Sentence Transformers."""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5"
    ):
        self.model_name = model_name
        self.dimensions = 768  # bge-base-en-v1.5 output dimensions
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"Embedding model loaded successfully")
    
    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text."""
        # BGE models recommend prepending "Represent this sentence:" for retrieval
        prefixed_text = "Represent this sentence: " + text
        embedding = self.model.encode(prefixed_text, normalize_embeddings=True)
        
        return EmbeddingResult(
            text=text,
            embedding=embedding.tolist(),
            model=self.model_name,
            token_count=None
        )
    
    async def embed_texts(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        
        # BGE models recommend prepending instruction for retrieval passages
        prefixed_texts = ["Represent this sentence: " + t for t in texts]
        # sentence-transformers handles batching internally
        embeddings = self.model.encode(
            prefixed_texts,
            normalize_embeddings=True,
            batch_size=64,
            show_progress_bar=False
        )
        results = []
        for i, embedding in enumerate(embeddings):
            results.append(EmbeddingResult(
                text=texts[i],
                embedding=embedding.tolist(),
                model=self.model_name,
                token_count=None
            ))
        
        return results
    

    async def embed_query(self, query: str) -> EmbeddingResult:
        """Generate embedding for a search query (uses query-specific instruction)."""
        # BGE models use a different instruction for queries vs passages
        prefixed_query = "Represent this sentence for searching relevant passages: " + query
        embedding = self.model.encode(prefixed_query, normalize_embeddings=True)
        
        return EmbeddingResult(
            text=query,
            embedding=embedding.tolist(),
            model=self.model_name,
            token_count=None
        )


        


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service