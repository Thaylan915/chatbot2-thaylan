"""Abstract interface for embedding providers."""
from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """Gera representações vetoriais (embeddings) para textos."""

    @abstractmethod
    def embed(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Retorna o vetor de embedding para um texto.

        Args:
            text:      Texto a ser vetorizado.
            task_type: Tipo de tarefa para otimizar o embedding.
                       Use 'retrieval_document' ao indexar chunks.
                       Use 'retrieval_query' ao vetorizar perguntas.
        """

    @abstractmethod
    def embed_batch(self, texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
        """
        Retorna vetores de embedding para uma lista de textos.

        Args:
            texts:     Lista de textos a serem vetorizados.
            task_type: Tipo de tarefa (ver embed()).
        """