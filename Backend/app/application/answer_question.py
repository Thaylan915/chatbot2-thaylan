"""Caso de uso: responder pergunta do usuário usando o banco de documentos."""
import math
import re
from typing import List

import google.generativeai as genai
from django.conf import settings

from Backend.app.application.embedding_provider import EmbeddingProvider
from Backend.app.documents.models import Conversa, Mensagem, Documento
from Backend.app.domain.repositories.chunk_repository import ChunkRepository

_PROMPT_TEMPLATE = (
    "Você é um assistente especializado em documentos institucionais. "
    "Responda à pergunta usando exclusivamente o contexto abaixo. "
    "Se a resposta não estiver no contexto, informe que não há informação suficiente.\n\n"
    "Contexto:\n{contexto}\n\n"
    "Pergunta: {pergunta}\n\n"
    "Resposta:"
)


# ─── Pré-processamento ────────────────────────────────────────────────────────

def preprocessar_pergunta(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.lower()
    texto = re.sub(r'[^\w\s\?\!\.\,\á\é\í\ó\ú\ã\õ\â\ê\ô\ç]', '', texto)
    return texto


# ─── MMR (Maximal Marginal Relevance) re-ranking ─────────────────────────────

def _cosine(a: List[float], b: List[float]) -> float:
    """Similaridade de cosseno entre dois vetores."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _mmr_rerank(
    candidates: List[dict],
    top_k: int,
    lambda_mult: float = 0.6,
) -> List[dict]:
    """
    Maximal Marginal Relevance: seleciona *top_k* chunks equilibrando
    relevância para a query (score pgvector) e diversidade entre si.

    Args:
        candidates:  Saída de buscar_candidatos() — cada item tem 'score' e 'embedding'.
        top_k:       Número final de chunks a retornar.
        lambda_mult: Peso da relevância vs diversidade (0 = só diversidade, 1 = só relevância).

    Returns:
        Lista de dicts (mesma estrutura de candidates, sem o campo 'embedding').
    """
    if len(candidates) <= top_k:
        selected = candidates
    else:
        selected: List[dict] = []
        remaining = list(candidates)

        while len(selected) < top_k and remaining:
            if not selected:
                # Primeira seleção: chunk mais relevante para a query
                best = max(remaining, key=lambda c: c["score"])
            else:
                # MMR: relevância ponderada pela redundância em relação aos já selecionados
                def mmr_score(c: dict) -> float:
                    max_sim = max(
                        _cosine(c["embedding"], s["embedding"]) for s in selected
                    )
                    return lambda_mult * c["score"] - (1 - lambda_mult) * max_sim

                best = max(remaining, key=mmr_score)

            selected.append(best)
            remaining.remove(best)

    # Remove o campo 'embedding' antes de retornar (não é necessário downstream)
    return [{k: v for k, v in c.items() if k != "embedding"} for c in selected]


# ─── Caso de uso principal ────────────────────────────────────────────────────

class ResponderPergunta:
    """
    Caso de uso: pipeline RAG completo.

    Fluxo:
        1. Gera embedding da pergunta com task_type='retrieval_query'.
        2. Busca os top RERANK_FETCH_K candidatos via pgvector (cosine distance).
        3. Re-ranking MMR para selecionar TOP_K chunks diversos e relevantes.
        4. Monta o contexto e gera resposta com o Gemini.
        5. Retorna resposta + fontes deduplicas.
    """

    def __init__(
        self,
        chunk_repository: ChunkRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._chunk_repo = chunk_repository
        self._embedding_provider = embedding_provider

    def executar(self, pergunta_processada: str) -> dict:
        """
        Retorna dict com:
            - resposta:  str — texto gerado pelo Gemini
            - fontes:    list[dict] — documentos únicos usados, cada um com id e nome
        """
        # 1. Embedding da query com task_type correto
        query_embedding = self._embedding_provider.embed(
            pergunta_processada,
            task_type="retrieval_query",
        )

        # 2. Busca vetorial — mais candidatos do que o necessário (para re-ranking)
        fetch_k = getattr(settings, "RERANK_FETCH_K", settings.TOP_K * 4)
        candidates = self._chunk_repo.buscar_candidatos(query_embedding, fetch_k)

        if not candidates:
            return {
                "resposta": "Não encontrei documentos indexados para responder à sua pergunta.",
                "fontes": [],
            }

        # 3. Re-ranking MMR
        chunks = _mmr_rerank(candidates, top_k=settings.TOP_K)

        # 4. Monta contexto
        contexto = "\n\n---\n\n".join(
            f"[{chunk['documento_nome']}]\n{chunk['conteudo']}" for chunk in chunks
        )

        prompt = _PROMPT_TEMPLATE.format(contexto=contexto, pergunta=pergunta_processada)

        # 5. Geração de resposta
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.CHAT_MODEL)
        resposta = model.generate_content(prompt).text

        # 6. Deduplica documentos mantendo a ordem de relevância
        seen: set = set()
        fontes: List[dict] = []
        for chunk in chunks:
            doc_id = chunk["documento_id"]
            if doc_id not in seen:
                seen.add(doc_id)
                fontes.append({"id": doc_id, "nome": chunk["documento_nome"]})

        return {"resposta": resposta, "fontes": fontes}


# ─── Helpers de conversa ──────────────────────────────────────────────────────

def iniciar_conversa(user=None) -> Conversa:
    """Cria e retorna uma nova conversa. #34"""
    return Conversa.objects.create(user=user)


def registrar_mensagem(conversa: Conversa, pergunta_original: str) -> Mensagem:
    """Registra a pergunta original (#36) e a processada (#37)."""
    pergunta_processada = preprocessar_pergunta(pergunta_original)
    mensagem = Mensagem.objects.create(
        conversa=conversa,
        role="user",
        conteudo_original=pergunta_original,
        conteudo_processado=pergunta_processada,
    )
    return mensagem


def registrar_resposta(
    conversa: Conversa,
    resposta: str,
    ids_fontes: List[int] | None = None,
) -> Mensagem:
    """
    Registra a resposta do assistente e vincula os documentos de origem.

    Args:
        conversa:   sessão de chat.
        resposta:   texto gerado pelo modelo.
        ids_fontes: IDs dos Documentos usados como contexto RAG.
    """
    mensagem = Mensagem.objects.create(
        conversa=conversa,
        role="assistant",
        conteudo_original=resposta,
        conteudo_processado=resposta,
    )
    if ids_fontes:
        documentos = Documento.objects.filter(id__in=ids_fontes)
        mensagem.fontes.set(documentos)
    return mensagem
