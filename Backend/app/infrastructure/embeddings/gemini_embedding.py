"""Concrete Gemini implementation of EmbeddingProvider."""
from typing import List

from django.conf import settings
from google import genai
from google.genai import types

from Backend.app.application.embedding_provider import EmbeddingProvider

# Mapeamento de aliases curtos para o valor aceito pela API
_TASK_TYPE_MAP = {
    "retrieval_document": "RETRIEVAL_DOCUMENT",
    "retrieval_query": "RETRIEVAL_QUERY",
    "semantic_similarity": "SEMANTIC_SIMILARITY",
    "classification": "CLASSIFICATION",
    "clustering": "CLUSTERING",
}


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Gera embeddings via Google Gemini (google-genai SDK).

    task_type diferencia vetores de documento (indexação) de vetores de
    consulta (busca), o que melhora significativamente a qualidade do
    retrieval com modelos como text-embedding-004.
    """

    def __init__(self) -> None:
        self._client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={"api_version": "v1"},
        )
        self._model = settings.EMBEDDING_MODEL

    def embed(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """Vetoriza um único texto com o task_type informado."""
        api_task = _TASK_TYPE_MAP.get(task_type, task_type.upper())
        result = self._client.models.embed_content(
            model=self._model,
            contents=text,
            config=types.EmbedContentConfig(task_type=api_task),
        )
        return list(result.embeddings[0].values)

    def embed_batch(self, texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
        """
        Vetoriza uma lista de textos.

        Chama a API em sequência — a API Gemini não oferece endpoint de
        batch verdadeiro para embeddings, mas cada chamada é leve (~200 ms).
        """
        return [self.embed(t, task_type=task_type) for t in texts]
