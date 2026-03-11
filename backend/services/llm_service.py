"""
LLM service — context assembly + answer generation via Qwen3-8B-Instruct (Ollama).

Builds a structured context window from reranked chunks, calls the
Ollama OpenAI-compatible API, and returns a cited answer.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass, field
import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from openai import AsyncOpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

# Ollama runs locally — no API key needed (placeholder satisfies the SDK)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")


@dataclass
class SourceCitation:
    """A single source reference for the answer."""
    note_id: str
    title: str
    snippet: str          # short excerpt from the chunk
    score: float          # reranker score


@dataclass
class LLMResponse:
    """Final response from the LLM service."""
    answer: str
    sources: List[SourceCitation]
    model: str
    context_chunks_used: int


# ── System prompts ──────────────────────────────────────────────────

SINGLE_NOTE_SYSTEM = """You are a helpful AI assistant for a note-taking app called NotaRAG.
The user is asking about a SPECIFIC note. You have been given relevant excerpts from that note.

Rules:
- Answer ONLY based on the provided note context. Do not make up information.
- If the answer is not in the provided context, say "I couldn't find that information in this note."
- Be concise and direct.
- Use markdown formatting for readability when appropriate.
- Reference specific parts of the note when relevant."""

GLOBAL_SYSTEM = """You are a helpful AI assistant for a note-taking app called NotaRAG.
The user is asking a question across ALL their notes. You have been given relevant excerpts from multiple notes.

Rules:
- Answer based on the provided note contexts. Do not make up information.
- When referencing information, mention which note it came from (use the note title).
- If the answer spans multiple notes, synthesize the information coherently.
- If the context doesn't contain enough information, say so honestly.
- Be concise and direct.
- Use markdown formatting for readability when appropriate."""


class LLMService:
    """Builds context from reranked results and generates answers via Qwen3 (Ollama)."""

    def __init__(self, base_url: str = None, model_name: str = "qwen3:8b"):
        url = base_url or OLLAMA_BASE_URL
        self.client = AsyncOpenAI(
            base_url=url,
            api_key="ollama",          # Ollama ignores this but the SDK requires it
        )
        self.model_name = model_name
        logger.info(f"LLM service initialized — model: {model_name}, endpoint: {url}")

    def _build_context(self, results: list) -> str:
        """
        Assemble reranked chunks into a structured context string.
        Deduplicates chunks and groups by note title.
        """
        if not results:
            return "No relevant context found."

        # Deduplicate by chunk_id
        seen_ids = set()
        unique = []
        for r in results:
            if r.chunk_id not in seen_ids:
                seen_ids.add(r.chunk_id)
                unique.append(r)

        # Group by note title for cleaner context
        note_groups: Dict[str, list] = {}
        for r in unique:
            title = r.metadata.get("title", "Untitled")
            note_groups.setdefault(title, []).append(r)

        # Build the context string
        parts = []
        for title, chunks in note_groups.items():
            # Sort chunks by chunk_index within a note for coherence
            chunks.sort(key=lambda c: c.metadata.get("chunk_index", 0))
            parts.append(f"=== Note: {title} ===")
            for chunk in chunks:
                parts.append(chunk.content)
            parts.append("")  # blank line between notes

        return "\n".join(parts)

    def _extract_sources(self, results: list) -> List[SourceCitation]:
        """Extract source citations from reranked results."""
        seen = set()
        sources = []
        for r in results:
            note_id = r.note_id
            if note_id in seen:
                continue
            seen.add(note_id)
            # Take first ~150 chars as snippet
            snippet = r.content[:150].strip()
            if len(r.content) > 150:
                snippet += "..."
            sources.append(
                SourceCitation(
                    note_id=note_id,
                    title=r.metadata.get("title", "Untitled"),
                    snippet=snippet,
                    score=r.rerank_score,
                )
            )
        return sources

    async def generate_answer(
        self,
        query: str,
        reranked_results: list,
        note_id: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
    ) -> LLMResponse:
        """
        Generate an LLM answer from reranked retrieval results.

        Args:
            query: The user's question.
            reranked_results: List of RerankResult from the retrieval service.
            note_id: If set, we're in single-note mode.
            conversation_history: Optional prior messages for multi-turn chat.
        """
        # Pick the right system prompt
        system_prompt = SINGLE_NOTE_SYSTEM if note_id else GLOBAL_SYSTEM

        # Build context
        context = self._build_context(reranked_results)

        # Build messages in OpenAI chat format
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if present (for multi-turn)
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        # Current turn: inject context + question
        user_message = (
            f"Context from notes:\n\n{context}\n\n"
            f"---\n\n"
            f"User question: {query}"
        )
        messages.append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            answer = response.choices[0].message.content or "I wasn't able to generate a response."
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            answer = "Sorry, I encountered an error generating a response. Please try again."

        sources = self._extract_sources(reranked_results)

        return LLMResponse(
            answer=answer,
            sources=sources,
            model=self.model_name,
            context_chunks_used=len(reranked_results),
        )


# Singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
