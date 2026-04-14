"""Caso de uso: responder pergunta do usuário usando o banco de documentos."""
import math
import re
from typing import List, Optional

import google.generativeai as genai
from django.conf import settings

from Backend.app.application.embedding_provider import EmbeddingProvider
from Backend.app.documents.models import Conversa, Mensagem, Documento
from Backend.app.domain.repositories.chunk_repository import ChunkRepository

# Instrui o modelo a responder sempre com citações explícitas do documento de origem
_PROMPT_TEMPLATE = """\
Você é um assistente especializado em documentos institucionais do IFES.
Responda à pergunta usando exclusivamente os trechos abaixo, em português.

Regras obrigatórias:
1. Sempre cite o documento de origem na resposta, usando o formato:
   "Segundo o documento [NOME DO DOCUMENTO], página [N], ..."
   ou "Conforme [NOME DO DOCUMENTO] (pág. [N]), ..."
2. Se uma informação vier de mais de um documento, cite todos.
3. Se a informação não estiver no contexto, responda EXATAMENTE:
   "Não encontrei a informação nos documentos disponíveis."

Contexto:
{contexto}

Pergunta: {pergunta}

Resposta:"""

# Frases que indicam que o modelo não soube responder
_FRASES_SEM_RESPOSTA = [
    "não encontrei a informação", "não encontrou a informação", "não há informações",
    "não tenho informações", "não está no contexto", "não foi encontrado",
    "não consta", "sem informações", "não possuo informações", "não disponho de informações",
]
_MENSAGEM_SEM_RESPOSTA = (
    "Não encontrei informações suficientes nos documentos disponíveis para responder "
    "a essa pergunta. Tente reformular ou consulte diretamente os documentos institucionais."
)
_MENSAGEM_SEM_DOCUMENTOS = (
    "Ainda não há documentos indexados na base de conhecimento. "
    "Adicione documentos antes de fazer perguntas."
)
_MENSAGEM_ERRO_API = (
    "Não foi possível processar sua pergunta no momento. "
    "Verifique sua conexão e tente novamente."
)

# Tamanho máximo do trecho de citação exibido no frontend
_TRECHO_MAX_CHARS = 220


# ─── Pré-processamento ────────────────────────────────────────────────────────

def preprocessar_pergunta(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.lower()
    texto = re.sub(r'[^\w\s\?\!\.\,\á\é\í\ó\ú\ã\õ\â\ê\ô\ç]', '', texto)
    return texto


def _nao_soube_responder(texto: str) -> bool:
    """Verifica se o modelo indicou que não encontrou resposta no contexto."""
    texto_lower = texto.lower()
    return any(frase in texto_lower for frase in _FRASES_SEM_RESPOSTA)


def _extrair_trecho(conteudo: str, max_chars: int = _TRECHO_MAX_CHARS) -> str:
    """Extrai um trecho representativo do chunk para exibir como citação."""
    conteudo = conteudo.strip()
    if len(conteudo) <= max_chars:
        return conteudo
    trecho = conteudo[:max_chars]
    ultimo_espaco = trecho.rfind(' ')
    if ultimo_espaco > max_chars // 2:
        trecho = trecho[:ultimo_espaco]
    return trecho + "…"


def _label_pagina(numero_pagina: Optional[int]) -> str:
    """Retorna a label de página para o contexto do prompt."""
    return f"Página {numero_pagina}" if numero_pagina else "Página N/A"


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
    """
    if len(candidates) <= top_k:
        selected = candidates
    else:
        selected: List[dict] = []
        remaining = list(candidates)

        while len(selected) < top_k and remaining:
            if not selected:
                best = max(remaining, key=lambda c: c["score"])
            else:
                def mmr_score(c: dict) -> float:
                    max_sim = max(
                        _cosine(c["embedding"], s["embedding"]) for s in selected
                    )
                    return lambda_mult * c["score"] - (1 - lambda_mult) * max_sim

                best = max(remaining, key=mmr_score)

            selected.append(best)
            remaining.remove(best)

    return [{k: v for k, v in c.items() if k != "embedding"} for c in selected]


# ─── Montagem do contexto com rótulos de documento/página ────────────────────

def _montar_contexto(chunks: List[dict]) -> str:
    """
    Monta o bloco de contexto para o prompt, rotulando cada trecho com
    o nome do documento e a página — informações que o modelo usará para
    produzir as citações.
    """
    blocos = []
    for chunk in chunks:
        pagina = _label_pagina(chunk.get("numero_pagina"))
        header = f"[Documento: {chunk['documento_nome']} | {pagina}]"
        blocos.append(f"{header}\n{chunk['conteudo']}")
    return "\n\n---\n\n".join(blocos)


def _construir_citacoes(chunks: List[dict]) -> List[dict]:
    """
    Constrói a lista de citações estruturadas a partir dos chunks usados.
    Cada citação representa um trecho relevante de um documento específico.
    """
    citacoes = []
    for ordem, chunk in enumerate(chunks, start=1):
        citacoes.append({
            "ordem":          ordem,
            "documento_id":   chunk["documento_id"],
            "documento_nome": chunk["documento_nome"],
            "numero_pagina":  chunk.get("numero_pagina"),
            "trecho":         _extrair_trecho(chunk["conteudo"]),
        })
    return citacoes


# ─── Caso de uso principal ────────────────────────────────────────────────────

class ResponderPergunta:
    """
    Caso de uso: pipeline RAG completo com citações de origem.

    Fluxo:
        1. Gera embedding da pergunta com task_type='retrieval_query'.
        2. Busca os top RERANK_FETCH_K candidatos via pgvector.
        3. Re-ranking MMR para selecionar TOP_K chunks diversos e relevantes.
        4. Monta contexto rotulado (documento + página) e gera resposta via Gemini.
        5. Detecta se o modelo não encontrou resposta (_nao_soube_responder).
        6. Retorna resposta + fontes + citacoes + respondida.
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
            - resposta:   str        — texto gerado pelo Gemini (ou mensagem de erro)
            - fontes:     list[dict] — documentos únicos: {id, nome}
            - citacoes:   list[dict] — trechos usados: {ordem, documento_id, documento_nome,
                                        numero_pagina, trecho}
            - respondida: bool       — True se o modelo encontrou resposta no contexto
            - intencao:   str        — 'rag'
        """
        if not settings.GEMINI_API_KEY:
            return self._sem_resposta(_MENSAGEM_ERRO_API)

        try:
            # 1. Embedding da query
            query_embedding = self._embedding_provider.embed(
                pergunta_processada,
                task_type="retrieval_query",
            )

            # 2. Busca vetorial com mais candidatos para re-ranking
            fetch_k = getattr(settings, "RERANK_FETCH_K", settings.TOP_K * 4)
            candidates = self._chunk_repo.buscar_candidatos(query_embedding, fetch_k)

            if not candidates:
                return self._sem_resposta(_MENSAGEM_SEM_DOCUMENTOS)

            # 3. Re-ranking MMR
            chunks = _mmr_rerank(candidates, top_k=settings.TOP_K)

            # 4. Monta contexto e gera resposta
            contexto = _montar_contexto(chunks)
            prompt = _PROMPT_TEMPLATE.format(
                contexto=contexto,
                pergunta=pergunta_processada,
            )

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.CHAT_MODEL)
            resposta_texto = model.generate_content(prompt).text

            # 5. Detecta resposta vazia/negativa
            if _nao_soube_responder(resposta_texto):
                return self._sem_resposta(_MENSAGEM_SEM_RESPOSTA)

            # 6. Monta fontes (documentos únicos) e citações (trechos individuais)
            fontes = self._deduplicar_fontes(chunks)
            citacoes = _construir_citacoes(chunks)

            return {
                "resposta":   resposta_texto,
                "fontes":     fontes,
                "citacoes":   citacoes,
                "respondida": True,
                "intencao":   "rag",
            }

        except Exception:
            return self._sem_resposta(_MENSAGEM_ERRO_API)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _sem_resposta(mensagem: str) -> dict:
        return {
            "resposta":   mensagem,
            "fontes":     [],
            "citacoes":   [],
            "respondida": False,
            "intencao":   "rag",
        }

    @staticmethod
    def _deduplicar_fontes(chunks: List[dict]) -> List[dict]:
        """Retorna lista de documentos únicos mantendo ordem de relevância."""
        seen: set = set()
        fontes: List[dict] = []
        for chunk in chunks:
            doc_id = chunk["documento_id"]
            if doc_id not in seen:
                seen.add(doc_id)
                fontes.append({"id": doc_id, "nome": chunk["documento_nome"]})
        return fontes


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
