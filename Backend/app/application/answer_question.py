"""Caso de uso: responder pergunta do usuário usando o banco de documentos."""
import re
import math
from django.conf import settings
from Backend.app.documents.models import Conversa, Mensagem, ChunkDocumento


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
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options={"api_version": "v1"},
    )
    result = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=texto,
    )
    return result.embeddings[0].values


def _buscar_chunks(embedding_pergunta, top_k: int):
    """Busca os chunks mais relevantes por similaridade de cosseno."""
    chunks = ChunkDocumento.objects.exclude(embedding=None).select_related("documento")
    scored = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        sim = _cosseno(embedding_pergunta, chunk.embedding)
        scored.append((sim, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


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
        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={"api_version": "v1"},
        )
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
