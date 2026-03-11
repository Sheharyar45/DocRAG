"""
Query analysis and filter construction service.

Parses user queries, extracts implicit metadata filters,
and builds structured filter objects for the retrieval pipeline.
"""

from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class SearchMode(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@dataclass
class QueryFilters:
    """Structured filters extracted from a query context."""
    user_id: str
    note_id: Optional[str] = None        # single-note chat mode
    folder_id: Optional[str] = None       # folder-scoped search
    tags: Optional[List[str]] = None      # tag-based filtering
    exclude_trashed: bool = True


@dataclass
class AnalyzedQuery:
    """Result of query analysis."""
    original_query: str
    cleaned_query: str                    # query with filter directives removed
    filters: QueryFilters
    search_mode: SearchMode = SearchMode.HYBRID


# ── Tag / directive patterns ──────────────────────────────────────

# Matches  tag:machine-learning  or  #machine-learning  in the query text
_TAG_PATTERN = re.compile(
    r'(?:tag:|#)([a-zA-Z0-9_-]+)',
    re.IGNORECASE,
)

# Matches  folder:Work  or  in:Work  in the query text
_FOLDER_PATTERN = re.compile(
    r'(?:folder:|in:)([a-zA-Z0-9_ -]+)',
    re.IGNORECASE,
)

# Matches  mode:semantic  or  mode:keyword  or  mode:hybrid
_MODE_PATTERN = re.compile(
    r'mode:(semantic|keyword|hybrid)',
    re.IGNORECASE,
)


class QueryService:
    """
    Analyzes incoming queries to:
    1. Extract inline metadata directives (tag:, #, folder:, in:, mode:)
    2. Remove those directives from the cleaned query text
    3. Build structured QueryFilters for the downstream search layer
    4. Select an optimal SearchMode
    """

    def __init__(self):
        # folder name → id map, populated from DB when available
        self._folder_cache: dict = {}

    def set_folder_map(self, folder_map: dict) -> None:
        """
        Optionally inject a {folder_name_lower: folder_id} mapping
        so that 'folder:Work' can be resolved to a UUID.
        The chat router can call this once per request using the user's folders.
        """
        self._folder_cache = {k.lower(): v for k, v in folder_map.items()}

    # ── public API ────────────────────────────────────────────────

    def analyze(
        self,
        query: str,
        user_id: str,
        note_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        search_mode: str = "hybrid",
    ) -> AnalyzedQuery:
        """
        Full query analysis:
        1. Extract tag directives  →  filters.tags
        2. Extract folder directive →  filters.folder_id  (if not already set)
        3. Extract mode directive   →  overrides search_mode
        4. Clean the query text     →  directives stripped out
        5. Heuristics               →  short queries → keyword, etc.
        """
        working = query.strip()

        # ── Extract tags ──────────────────────────────────────────
        extracted_tags: List[str] = _TAG_PATTERN.findall(working)
        working = _TAG_PATTERN.sub("", working)

        # ── Extract folder name ───────────────────────────────────
        folder_match = _FOLDER_PATTERN.search(working)
        extracted_folder_name: Optional[str] = None
        if folder_match:
            extracted_folder_name = folder_match.group(1).strip()
            working = _FOLDER_PATTERN.sub("", working)

        # ── Extract mode override ─────────────────────────────────
        mode_match = _MODE_PATTERN.search(working)
        if mode_match:
            search_mode = mode_match.group(1).lower()
            working = _MODE_PATTERN.sub("", working)

        # ── Clean up whitespace left by removals ──────────────────
        cleaned = re.sub(r'\s{2,}', ' ', working).strip()

        # ── Resolve folder name → id ──────────────────────────────
        resolved_folder_id = folder_id  # explicit param takes priority
        if not resolved_folder_id and extracted_folder_name:
            resolved_folder_id = self._folder_cache.get(
                extracted_folder_name.lower()
            )
            if resolved_folder_id:
                logger.info(
                    f"Resolved folder '{extracted_folder_name}' → {resolved_folder_id}"
                )
            else:
                logger.warning(
                    f"Folder '{extracted_folder_name}' not found in cache — ignoring"
                )

        # ── Build filters ─────────────────────────────────────────
        filters = QueryFilters(
            user_id=user_id,
            note_id=note_id,
            folder_id=resolved_folder_id,
            tags=extracted_tags if extracted_tags else None,
            exclude_trashed=True,
        )

        # ── Determine search mode ─────────────────────────────────
        mode = (
            SearchMode(search_mode)
            if search_mode in SearchMode._value2member_map_
            else SearchMode.HYBRID
        )

        # Heuristic: single-note mode → prefer semantic (small corpus)
        if note_id and mode == SearchMode.HYBRID:
            mode = SearchMode.SEMANTIC

        # Heuristic: very short queries (≤3 words) often work better
        # with keyword search included
        word_count = len(cleaned.split())
        if word_count <= 2 and mode == SearchMode.SEMANTIC:
            mode = SearchMode.HYBRID

        logger.info(
            f"Query analyzed: mode={mode.value}, note_id={note_id}, "
            f"folder_id={resolved_folder_id}, tags={extracted_tags}, "
            f"cleaned_query='{cleaned[:80]}'"
        )

        return AnalyzedQuery(
            original_query=query,
            cleaned_query=cleaned,
            filters=filters,
            search_mode=mode,
        )


# Singleton
_query_service: Optional[QueryService] = None


def get_query_service() -> QueryService:
    global _query_service
    if _query_service is None:
        _query_service = QueryService()
    return _query_service
