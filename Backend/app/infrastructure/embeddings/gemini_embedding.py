"""Concrete Gemini implementation of EmbeddingProvider."""
from google import genai
from typing import List
from django.conf import settings
from Backend.app.application.embedding_provider import EmbeddingProvider


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.EMBEDDING_MODEL

    def embed(self, text: str) -> List[float]:
        result = self._client.models.embed_content(
            model=self._model,
            contents=text,
        )
        return result.embeddings[0].values

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]
