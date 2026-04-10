"""Abstract repository interface for chunk similarity search."""
from abc import ABC, abstractmethod
from typing import List


class ChunkRepository(ABC):

    @abstractmethod
    def buscar_similares(self, query_embedding: List[float], top_k: int) -> List[dict]:
        """
        Retorna os *top_k* chunks mais próximos ao *query_embedding*.

        Cada dict contém:
            - id:             int
            - conteudo:       str
            - documento_id:   int
            - documento_nome: str
        """

    @abstractmethod
    def buscar_candidatos(self, query_embedding: List[float], fetch_k: int) -> List[dict]:
        """
        Retorna *fetch_k* candidatos com score de similaridade e embedding,
        para uso em etapas de re-ranking (ex.: MMR).

        Cada dict contém:
            - id:             int
            - conteudo:       str
            - documento_id:   int
            - documento_nome: str
            - score:          float  (similaridade de cosseno, 0–1, maior = mais relevante)
            - embedding:      List[float]
        """
