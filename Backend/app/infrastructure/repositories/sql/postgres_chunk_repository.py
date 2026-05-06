"""
PostgreSQL implementation of ChunkRepository using pgvector.

O campo `embedding` é armazenado como JSONField (JSONB no PostgreSQL).
O cast `embedding::text::vector` converte o array JSON para o tipo nativo
do pgvector, permitindo usar o operador `<=>` (distância de cosseno).
"""

import json
from typing import List

from django.db import connection

from Backend.app.documents.models import ChunkDocumento
from Backend.app.domain.repositories.chunk_repository import ChunkRepository

# Busca simples — retorna apenas os campos necessários para montar o contexto
_SQL_SIMILARES = """
    SELECT
        c.id,
        c.conteudo,
        c.numero_pagina,
        d.id   AS documento_id,
        d.nome AS documento_nome,
        d.tipo AS documento_tipo
    FROM documents_chunkdocumento c
    INNER JOIN documents_documento d ON d.id = c.documento_id
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding::text::vector <=> %s::vector
    LIMIT %s
"""

# Busca para re-ranking — retorna score de similaridade e o embedding completo
# (1 - distância de cosseno = similaridade; o operador <=> é passado duas vezes)
_SQL_CANDIDATOS = """
    SELECT
        c.id,
        c.conteudo,
        c.numero_pagina,
        d.id   AS documento_id,
        d.nome AS documento_nome,
        d.tipo AS documento_tipo,
        1 - (c.embedding::text::vector <=> %s::vector) AS score,
        c.embedding
    FROM documents_chunkdocumento c
    INNER JOIN documents_documento d ON d.id = c.documento_id
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding::text::vector <=> %s::vector
    LIMIT %s
"""


class PostgresChunkRepository(ChunkRepository):

    def buscar_similares(self, query_embedding: List[float], top_k: int) -> List[dict]:
        """
        Executa busca vetorial por cosseno diretamente no PostgreSQL via pgvector.

        Args:
            query_embedding: vetor da pergunta (gerado com task_type='retrieval_query').
            top_k:           número máximo de chunks a retornar.

        Returns:
            Lista de dicts com chaves: id, conteudo, documento_id, documento_nome.
        """
        vec = json.dumps(query_embedding)
        with connection.cursor() as cursor:
            cursor.execute(_SQL_SIMILARES, [vec, top_k])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def buscar_candidatos(self, query_embedding: List[float], fetch_k: int) -> List[dict]:
        """
        Busca *fetch_k* candidatos com score de similaridade e embedding completo.

        Usado pelo pipeline de re-ranking (MMR) em answer_question.py.

        Args:
            query_embedding: vetor da pergunta.
            fetch_k:         número de candidatos a buscar antes do re-ranking.

        Returns:
            Lista de dicts com chaves: id, conteudo, documento_id, documento_nome,
            documento_tipo, score (float 0-1), embedding (List[float]).
        """
        vec = json.dumps(query_embedding)
        with connection.cursor() as cursor:
            cursor.execute(_SQL_CANDIDATOS, [vec, vec, fetch_k])
            columns = [col[0] for col in cursor.description]
            rows = []
            for row in cursor.fetchall():
                item = dict(zip(columns, row))
                # O embedding vem do JSONB como lista Python — garantir tipo correto
                if isinstance(item["embedding"], str):
                    item["embedding"] = json.loads(item["embedding"])
                item["score"] = float(item["score"])
                rows.append(item)
            return rows

    def buscar_por_tipo_documento(self, tipo_documento: str, limit: int) -> List[dict]:
        """Retorna chunks diretamente filtrados pelo tipo do documento."""
        chunks = (
            ChunkDocumento.objects
            .select_related("documento")
            .filter(documento__tipo=tipo_documento)
            .order_by("documento_id", "numero_chunk")[:limit]
        )

        resultados: List[dict] = []
        for indice, chunk in enumerate(chunks, start=1):
            resultados.append({
                "id": chunk.id,
                "conteudo": chunk.conteudo,
                "numero_pagina": chunk.numero_pagina,
                "documento_id": chunk.documento_id,
                "documento_nome": chunk.documento.nome,
                "documento_tipo": chunk.documento.tipo,
                "score": float(1.0 - (indice * 0.001)),
                "embedding": chunk.embedding or [],
            })
        return resultados
