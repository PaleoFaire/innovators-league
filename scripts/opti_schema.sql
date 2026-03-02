-- ============================================================
-- OPTI PHASE 2: RAG Document Store
-- Run in Supabase SQL Editor:
--   https://supabase.com/dashboard/project/imxrdesbozbxmlffewyr/sql/new
-- ============================================================

-- Step 1: Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Document chunks table
CREATE TABLE IF NOT EXISTS opti_documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  embedding VECTOR(384),                -- gte-small produces 384 dimensions
  metadata JSONB DEFAULT '{}',           -- flexible metadata storage
  source_file TEXT NOT NULL,             -- original filename
  source_type TEXT NOT NULL,             -- 'podcast', 'research', 'notes', 'optimism'
  chunk_index INTEGER NOT NULL DEFAULT 0,-- position within the source document
  token_count INTEGER,                   -- number of tokens in this chunk
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 3: Create HNSW index for fast similarity search
-- HNSW is preferred over IVFFlat for datasets under 1M rows
CREATE INDEX IF NOT EXISTS opti_documents_embedding_idx
  ON opti_documents
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Step 4: Indexes for filtered queries
CREATE INDEX IF NOT EXISTS opti_documents_source_type_idx
  ON opti_documents (source_type);

CREATE INDEX IF NOT EXISTS opti_documents_source_file_idx
  ON opti_documents (source_file);

-- Step 5: GIN index on metadata JSONB for flexible filtering
CREATE INDEX IF NOT EXISTS opti_documents_metadata_idx
  ON opti_documents
  USING gin (metadata);

-- Step 6: Similarity search function (called by Edge Function via RPC)
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding VECTOR(384),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 8,
  filter_source_type TEXT DEFAULT NULL
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  metadata JSONB,
  source_file TEXT,
  source_type TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    od.id,
    od.content,
    od.metadata,
    od.source_file,
    od.source_type,
    1 - (od.embedding <=> query_embedding) AS similarity
  FROM opti_documents od
  WHERE
    (filter_source_type IS NULL OR od.source_type = filter_source_type)
    AND 1 - (od.embedding <=> query_embedding) > match_threshold
  ORDER BY od.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Step 7: Row-level security
ALTER TABLE opti_documents ENABLE ROW LEVEL SECURITY;

-- Documents: readable by all (via the match function), writable only by service role
CREATE POLICY "Documents are readable by all" ON opti_documents
  FOR SELECT USING (true);

-- Allow anonymous invocation of match_documents
GRANT EXECUTE ON FUNCTION match_documents TO anon;
GRANT EXECUTE ON FUNCTION match_documents TO authenticated;
