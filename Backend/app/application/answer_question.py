import re
import math
import google.generativeai as genai
from django.conf import settings
from Backend.app.documents.models import Conversa, Mensagem, ChunkDocumento
from Backend.app.application.intent_classifier import (
    classificar_intencao,
    RESPOSTAS_DIRETAS,
)

genai.configure(api_key=settings.GEMINI_API_KEY)

# Constantes de mensagens integradas
_FRASES_SEM_RESPOSTA = [
    "não encontrei a informação", "não encontrou a informação", "não há informações",
    "não tenho informações", "não está no contexto", "não foi encontrado",
    "não consta", "sem informações", "não possuo informações", "não disponho de informações",
]
_MENSAGEM_SEM_RESPOSTA = "Não encontrei informações suficientes nos documentos disponíveis para responder a essa pergunta. Tente reformular ou consulte diretamente os documentos institucionais."
_MENSAGEM_SEM_DOCUMENTOS = "Ainda não há documentos indexados na base de conhecimento. Adicione documentos antes de fazer perguntas."
_MENSAGEM_ERRO_API = "Não foi possível processar sua pergunta no momento. Verifique sua conexão e tente novamente."

def _nao_soube_responder(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(frase in texto_lower for frase in _FRASES_SEM_RESPOSTA)

def preprocessar_pergunta(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.lower()
    texto = re.sub(r'[^\w\s\?\!\.\,\á\é\í\ó\ú\ã\õ\â\ê\ô\ç]', '', texto)
    return texto

def iniciar_conversa(user=None) -> Conversa:
    return Conversa.objects.create(user=user)

def registrar_mensagem(conversa: Conversa, pergunta_original: str) -> Mensagem:
    pergunta_processada = preprocessar_pergunta(pergunta_original)
    return Mensagem.objects.create(
        conversa=conversa,
        role="user",
        conteudo_original=pergunta_original,
        conteudo_processado=pergunta_processada,
    )

def _cosseno(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a != 0 and norm_b != 0 else 0.0

def _embeddar(texto: str):
    modelo = "models/gemini-embedding-001"
    try:
        return genai.embed_content(model=modelo, content=texto, task_type="retrieval_query")['embedding']
    except:
        return genai.embed_content(model="gemini-embedding-001", content=texto, task_type="retrieval_query")['embedding']

def _buscar_chunks(embedding_pergunta, top_k: int):
    chunks = ChunkDocumento.objects.exclude(embedding=None).select_related("documento")
    scored = sorted([( _cosseno(embedding_pergunta, c.embedding), c) for c in chunks], key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]

def gerar_resposta(pergunta_processada: str) -> tuple[str, str, bool]:
    intencao = classificar_intencao(pergunta_processada)

    if intencao in RESPOSTAS_DIRETAS:
        return RESPOSTAS_DIRETAS[intencao], intencao, True

    if not settings.GEMINI_API_KEY:
        return _MENSAGEM_ERRO_API, intencao, False

    try:
        emb = _embeddar(pergunta_processada)
        top_k = getattr(settings, "TOP_K", 5)
        chunks_relevantes = _buscar_chunks(emb, top_k)

        if not chunks_relevantes:
            return _MENSAGEM_SEM_DOCUMENTOS, intencao, False

        contexto = "\n\n".join(f"[{c.documento.nome}]\n{c.conteudo}" for c in chunks_relevantes)
        prompt = (
            "Você é um assistente especializado em documentos institucionais do IFES. "
            "Use apenas o contexto abaixo para responder em português. "
            "Se a resposta não estiver no contexto, responda EXATAMENTE: "
            "'Não encontrei a informação nos documentos disponíveis.'\n\n"
            f"Contexto:\n{contexto}\n\n"
            f"Pergunta: {pergunta_processada}"
        )

        # Busca dinâmica de modelo para evitar 404
        modelo_texto = "gemini-1.5-flash"
        try:
            para_chat = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            modelo_texto = next((m for m in para_chat if 'flash' in m), para_chat[0])
        except: pass

        model = genai.GenerativeModel(modelo_texto)
        response = model.generate_content(prompt)
        
        if _nao_soube_responder(response.text):
            return _MENSAGEM_SEM_RESPOSTA, intencao, False
            
        return response.text, intencao, True

    except Exception as e:
        print(f"Erro na IA: {e}")
        return _MENSAGEM_ERRO_API, intencao, False

def registrar_resposta(conversa: Conversa, resposta: str) -> Mensagem:
    return Mensagem.objects.create(conversa=conversa, role="assistant", conteudo_original=resposta, conteudo_processado=resposta)