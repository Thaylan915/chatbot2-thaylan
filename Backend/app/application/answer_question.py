"""Caso de uso: responder pergunta do usuário usando o banco de documentos."""
import re
import math
import threading
import numpy as np
from django.conf import settings
from Backend.app.documents.models import Conversa, Mensagem, ChunkDocumento

# ─── Cache em memória dos embeddings ──────────────────────────────────────────
# Carrega todos os embeddings 1x, mantém na memória do processo Django.
# Invalidar com `_invalidate_embedding_cache()` quando documentos mudarem.
_EMB_LOCK = threading.Lock()
_EMB_CACHE = {
    "matrix": None,           # numpy (N, D) já normalizada
    "chunk_ids": None,        # list[int] alinhado com matrix
    "count": 0,
}


def _invalidate_embedding_cache():
    with _EMB_LOCK:
        _EMB_CACHE["matrix"] = None
        _EMB_CACHE["chunk_ids"] = None
        _EMB_CACHE["count"] = 0


def _carregar_cache_embeddings():
    """Carrega (1x) todos os embeddings da versão ATIVA em uma matriz numpy normalizada."""
    from django.db.models import Q
    # Apenas chunks de versões ativas (ou legacy sem versão)
    base_qs = ChunkDocumento.objects.exclude(embedding=None).filter(
        Q(versao__ativa=True) | Q(versao__isnull=True)
    )
    with _EMB_LOCK:
        # Se a contagem do banco mudou, recarrega
        total_atual = base_qs.count()
        if (
            _EMB_CACHE["matrix"] is not None
            and _EMB_CACHE["count"] == total_atual
        ):
            return _EMB_CACHE["matrix"], _EMB_CACHE["chunk_ids"]

        chunks = list(base_qs.values_list("id", "embedding"))
        if not chunks:
            _EMB_CACHE["matrix"] = None
            _EMB_CACHE["chunk_ids"] = []
            _EMB_CACHE["count"] = 0
            return None, []

        ids = [cid for cid, _ in chunks]
        matrix = np.asarray([emb for _, emb in chunks], dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix = matrix / norms  # normaliza para virar dot product = cos sim

        _EMB_CACHE["matrix"] = matrix
        _EMB_CACHE["chunk_ids"] = ids
        _EMB_CACHE["count"] = total_atual
        return matrix, ids


def preprocessar_pergunta(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.lower()
    texto = re.sub(r'[^\w\s\?\!\.\,\á\é\í\ó\ú\ã\õ\â\ê\ô\ç]', '', texto)
    return texto


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


def _cosseno(a, b):
    """Similaridade de cosseno entre dois vetores."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embeddar(texto: str):
    """Gera embedding usando google.genai."""
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    result = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=texto,
    )
    return result.embeddings[0].values


def _buscar_chunks(embedding_pergunta, top_k: int):
    """Busca os chunks mais relevantes via produto escalar vetorizado (numpy)."""
    matrix, ids = _carregar_cache_embeddings()
    if matrix is None or len(ids) == 0:
        return []

    q = np.asarray(embedding_pergunta, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    if q_norm == 0:
        return []
    q = q / q_norm

    sims = matrix @ q  # (N,) — cosseno, pois ambos já normalizados
    k = min(top_k, len(ids))
    # argpartition para top-k em O(N), depois ordena só os k
    top_idx = np.argpartition(-sims, k - 1)[:k]
    top_idx = top_idx[np.argsort(-sims[top_idx])]
    top_ids = [ids[i] for i in top_idx]

    # Busca os chunks no banco preservando a ordem do ranking
    chunks_qs = ChunkDocumento.objects.filter(id__in=top_ids).select_related("documento")
    chunks_by_id = {c.id: c for c in chunks_qs}
    return [chunks_by_id[cid] for cid in top_ids if cid in chunks_by_id]


def gerar_resposta(pergunta_processada: str) -> str:
    """Busca contexto nos documentos e gera resposta via Gemini."""
    if not settings.GEMINI_API_KEY:
        return "API key do Gemini não configurada."

    try:
        embedding_pergunta = _embeddar(pergunta_processada)
        top_k = getattr(settings, "TOP_K", 5)
        chunks_relevantes = _buscar_chunks(embedding_pergunta, top_k)

        if chunks_relevantes:
            contexto = "\n\n".join(
                f"[{c.documento.nome}]\n{c.conteudo}" for c in chunks_relevantes
            )
            prompt = (
                "Você é um assistente especializado em documentos institucionais. "
                "Use apenas o contexto abaixo para responder em português. "
                "Se a resposta não estiver no contexto, diga que não encontrou a informação.\n\n"
                f"Contexto:\n{contexto}\n\n"
                f"Pergunta: {pergunta_processada}"
            )
        else:
            prompt = (
                "Você é um assistente institucional. "
                "Não há documentos indexados na base de conhecimento ainda. "
                f"Responda em português à pergunta: {pergunta_processada}"
            )

        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.CHAT_MODEL,
            contents=prompt,
        )
        return response.text

    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"


def registrar_resposta(conversa: Conversa, resposta: str) -> Mensagem:
    """Registra a resposta do assistente na conversa."""
    return Mensagem.objects.create(
        conversa=conversa,
        role="assistant",
        conteudo_original=resposta,
        conteudo_processado=resposta,
    )
