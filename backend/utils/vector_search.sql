-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- ================================================================
-- SEMANTIC SEARCH: across all user's notes
-- ================================================================
CREATE OR REPLACE FUNCTION match_note_chunks(
    query_embedding vector(768),
    match_user_id uuid,
    match_count int DEFAULT 5,
    match_threshold float DEFAULT 0.5
)
RETURNS TABLE (
    id uuid,
    note_id uuid,
    folder_id uuid,
    content text,
    chunk_index int,
    metadata jsonb,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        nc.id,
        nc.note_id,
        nc.folder_id,
        nc.content,
        nc.chunk_index,
        nc.metadata,
        1 - (nc.embedding <=> query_embedding) AS similarity
    FROM note_chunks nc
    INNER JOIN notes n ON nc.note_id = n.id
    WHERE nc.user_id = match_user_id
      AND n.is_trashed = false
      AND 1 - (nc.embedding <=> query_embedding) > match_threshold
    ORDER BY nc.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- ================================================================
-- SEMANTIC SEARCH: within a specific note
-- ================================================================
CREATE OR REPLACE FUNCTION match_note_chunks_by_note(
    query_embedding vector(768),
    match_user_id uuid,
    match_note_id uuid,
    match_count int DEFAULT 5,
    match_threshold float DEFAULT 0.3
)
RETURNS TABLE (
    id uuid,
    note_id uuid,
    folder_id uuid,
    content text,
    chunk_index int,
    metadata jsonb,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        nc.id,
        nc.note_id,
        nc.folder_id,
        nc.content,
        nc.chunk_index,
        nc.metadata,
        1 - (nc.embedding <=> query_embedding) AS similarity
    FROM note_chunks nc
    WHERE nc.user_id = match_user_id
      AND nc.note_id = match_note_id
      AND 1 - (nc.embedding <=> query_embedding) > match_threshold
    ORDER BY nc.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- ================================================================
-- KEYWORD SEARCH: full-text search via tsvector
-- Joins notes to exclude trashed, returns metadata + note_id
-- ================================================================
CREATE OR REPLACE FUNCTION keyword_search_chunks(
    query_text text,
    user_id uuid,
    limit_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    note_id uuid,
    content text,
    metadata jsonb,
    score float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        nc.id,
        nc.note_id,
        nc.content,
        nc.metadata,
        ts_rank(nc.fts, plainto_tsquery('english', query_text)) AS score
    FROM note_chunks nc
    INNER JOIN notes n ON nc.note_id = n.id
    WHERE nc.user_id = keyword_search_chunks.user_id
      AND n.is_trashed = false
      AND nc.fts @@ plainto_tsquery('english', query_text)
    ORDER BY score DESC
    LIMIT limit_count;
$$;

-- ================================================================
-- HYBRID SEARCH: semantic + keyword with RRF fusion
-- Joins notes to exclude trashed, returns metadata
-- ================================================================
CREATE OR REPLACE FUNCTION hybrid_search_chunks(
    query_embedding vector(768),
    query_text text,
    match_user_id uuid,
    match_limit int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    note_id uuid,
    content text,
    metadata jsonb,
    score float
)
LANGUAGE sql STABLE
AS $$
WITH semantic AS (
    SELECT
        nc.id,
        nc.note_id,
        nc.content,
        nc.metadata,
        ROW_NUMBER() OVER (ORDER BY nc.embedding <=> query_embedding) AS rank
    FROM note_chunks nc
    INNER JOIN notes n ON nc.note_id = n.id
    WHERE nc.user_id = match_user_id
      AND n.is_trashed = false
    LIMIT 50
),
keyword AS (
    SELECT
        nc.id,
        nc.note_id,
        nc.content,
        nc.metadata,
        ROW_NUMBER() OVER (
            ORDER BY ts_rank(nc.fts, plainto_tsquery('english', query_text)) DESC
        ) AS rank
    FROM note_chunks nc
    INNER JOIN notes n ON nc.note_id = n.id
    WHERE nc.user_id = match_user_id
      AND n.is_trashed = false
      AND nc.fts @@ plainto_tsquery('english', query_text)
    LIMIT 50
),
combined AS (
    SELECT id, note_id, content, metadata,
           1.0 / (60 + rank) AS score
    FROM semantic
    UNION ALL
    SELECT id, note_id, content, metadata,
           1.0 / (60 + rank) AS score
    FROM keyword
)
SELECT
    id,
    note_id,
    content,
    metadata,
    SUM(score) AS score
FROM combined
GROUP BY id, note_id, content, metadata
ORDER BY score DESC
LIMIT match_limit;
$$;

-- ================================================================
-- INDEXES
-- ================================================================
-- Vector similarity index (IVFFlat for ANN search)
CREATE INDEX IF NOT EXISTS note_chunks_embedding_idx 
ON note_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Filter indexes
CREATE INDEX IF NOT EXISTS note_chunks_user_id_idx ON note_chunks(user_id);
CREATE INDEX IF NOT EXISTS note_chunks_note_id_idx ON note_chunks(note_id);
CREATE INDEX IF NOT EXISTS note_chunks_folder_id_idx ON note_chunks(folder_id);

-- Full-text search index (requires the fts tsvector column)
CREATE INDEX IF NOT EXISTS note_chunks_fts_idx ON note_chunks USING GIN(fts);

-- JSONB metadata index for tag filtering
CREATE INDEX IF NOT EXISTS note_chunks_metadata_idx ON note_chunks USING GIN(metadata);