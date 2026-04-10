"""
Caso de uso: indexar um documento no banco de dados.

Fluxo:
    1. Recupera o Documento pelo ID (já persistido pelo CreateDocument).
    2. Divide o conteúdo em chunks.
    3. Gera embeddings para cada chunk via EmbeddingProvider.
    4. Persiste os ChunkDocumento com embeddings no PostgreSQL.

Esse caso de uso é chamado pelo CreateDocument após o upload no Gemini.
"""

from typing import List

from Backend.app.application.embedding_provider import EmbeddingProvider
from Backend.app.documents.models import Documento, ChunkDocumento

# Tamanho máximo de cada chunk em caracteres
CHUNK_SIZE = 1000
# Sobreposição entre chunks consecutivos (contexto compartilhado)
CHUNK_OVERLAP = 100


class IndexDocument:

    def __init__(self, embedding_provider: EmbeddingProvider) -> None:
        self._embedding_provider = embedding_provider

    def executar(self, id_documento: int, conteudo: str) -> dict:
        """
        Divide o conteúdo em chunks, gera embeddings e persiste no banco.

        Args:
            id_documento: ID do Documento já salvo no banco.
            conteudo:     Texto extraído do PDF.

        Returns:
            dict com id do documento e quantidade de chunks gerados.

        Raises:
            LookupError: se o documento não existir no banco.
            ValueError:  se o conteúdo estiver vazio.
        """
        if not conteudo or not conteudo.strip():
            raise ValueError("O conteúdo do documento está vazio.")

        try:
            documento = Documento.objects.get(id=id_documento)
        except Documento.DoesNotExist:
            raise LookupError(f"Documento com id={id_documento} não encontrado.")

        # Remove chunks anteriores (caso seja uma re-indexação)
        ChunkDocumento.objects.filter(documento=documento).delete()

        chunks = self._dividir_em_chunks(conteudo)
        textos = [chunk["conteudo"] for chunk in chunks]
        # task_type='retrieval_document' otimiza o vetor para busca semântica
        embeddings = self._embedding_provider.embed_batch(textos, task_type="retrieval_document")

        objetos = [
            ChunkDocumento(
                documento=documento,
                numero_chunk=i,
                numero_pagina=None,      # pode ser preenchido se o extrator retornar páginas
                conteudo=chunk["conteudo"],
                embedding=embedding,
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]

        ChunkDocumento.objects.bulk_create(objetos)

        return {
            "id_documento": id_documento,
            "total_chunks": len(objetos),
        }

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _dividir_em_chunks(self, texto: str) -> List[dict]:
        """
        Divide o texto em chunks de tamanho fixo com sobreposição.
        Retorna lista de dicts com campo 'conteudo'.
        """
        chunks = []
        inicio = 0

        while inicio < len(texto):
            fim = inicio + CHUNK_SIZE
            trecho = texto[inicio:fim]

            # Tenta quebrar no último espaço para não cortar palavras
            if fim < len(texto):
                ultimo_espaco = trecho.rfind(" ")
                if ultimo_espaco > CHUNK_SIZE // 2:
                    trecho = trecho[:ultimo_espaco]

            chunks.append({"conteudo": trecho.strip()})
            inicio += len(trecho) - CHUNK_OVERLAP

        return [c for c in chunks if c["conteudo"]]