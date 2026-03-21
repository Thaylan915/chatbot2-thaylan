-- migrations/criar_indice_vetorial.sql
-- Execute este script APÓS rodar python manage.py migrate
-- para criar o índice vetorial no PostgreSQL com pgvector.
--
-- Uso:
--   docker exec -i chatbot_db psql -U chatbot_user -d chatbot < migrations/criar_indice_vetorial.sql

-- Garante que a extensão está habilitada
CREATE EXTENSION IF NOT EXISTS vector;

-- Adiciona coluna vetorial nativa na tabela de chunks
-- (complementa o campo JSON já criado pelo Django)
ALTER TABLE documents_chunkdocumento
    ADD COLUMN IF NOT EXISTS embedding_vector vector(768);

-- Índice IVFFlat para busca aproximada de vizinhos mais próximos
CREATE INDEX IF NOT EXISTS idx_chunk_embedding_vector
    ON documents_chunkdocumento
    USING ivfflat (embedding_vector vector_cosine_ops)
    WITH (lists = 100);

-- Função auxiliar para busca semântica por cosine similarity
CREATE OR REPLACE FUNCTION buscar_chunks_similares(
    query_embedding vector(768),
    top_k integer DEFAULT 5
)
RETURNS TABLE (
    chunk_id    integer,
    documento   text,
    tipo        text,
    conteudo    text,
    similaridade float
)
LANGUAGE sql AS $$
    SELECT
        c.id,
        d.nome,
        d.tipo,
        c.conteudo,
        1 - (c.embedding_vector <=> query_embedding) AS similaridade
    FROM documents_chunkdocumento c
    JOIN documents_documento d ON d.id = c.documento_id
    WHERE c.embedding_vector IS NOT NULL
    ORDER BY c.embedding_vector <=> query_embedding
    LIMIT top_k;
$$;
