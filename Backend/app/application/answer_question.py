"""Caso de uso: responder pergunta do usuário usando o banco de documentos."""
import re
import math
import google.generativeai as genai
from django.conf import settings
from Backend.app.documents.models import Conversa, Mensagem, ChunkDocumento
from Backend.app.application.intent_classifier import (
    classificar_intencao,
    RESPOSTAS_DIRETAS,
)

# Configuração estável do Google
genai.configure(api_key=settings.GEMINI_API_KEY)

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
    mensagem = Mensagem.objects.create(
        conversa=conversa,
        role="user",
        conteudo_original=pergunta_original,
        conteudo_processado=pergunta_processada,
    )
    return mensagem

def _cosseno(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def _embeddar(texto: str):
    import google.generativeai as genai
    from django.conf import settings
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # Este é o modelo que apareceu com "✅" no seu log de indexação:
    modelo_que_funciona = "models/gemini-embedding-001"

    try:
        result = genai.embed_content(
            model=modelo_que_funciona,
            content=texto,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        # Plano B caso o Google queira o nome sem o prefixo 'models/'
        result = genai.embed_content(
            model="gemini-embedding-001",
            content=texto,
            task_type="retrieval_query"
        )
        return result['embedding']
def _buscar_chunks(embedding_pergunta, top_k: int):
    chunks = ChunkDocumento.objects.exclude(embedding=None).select_related("documento")
    scored = []
    for chunk in chunks:
        sim = _cosseno(embedding_pergunta, chunk.embedding)
        scored.append((sim, chunk))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]

def gerar_resposta(pergunta_processada: str) -> tuple[str, str]:
    intencao = classificar_intencao(pergunta_processada)

    if intencao in RESPOSTAS_DIRETAS:
        return RESPOSTAS_DIRETAS[intencao], intencao

    try:
        emb = _embeddar(pergunta_processada)
        top_k = getattr(settings, "TOP_K", 5)
        chunks = _buscar_chunks(emb, top_k)

        contexto = "\n\n".join([f"[{c.documento.nome}]: {c.conteudo}" for c in chunks]) if chunks else "Sem contexto."
        
        prompt = (
            "Você é um assistente institucional do IFES. "
            "Responda à pergunta do usuário de forma clara e educada, baseando-se APENAS no contexto abaixo.\n\n"
            f"Contexto:\n{contexto}\n\n"
            f"Pergunta: {pergunta_processada}"
        )

        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # A CARTADA FINAL: Pega dinamicamente o modelo de texto que o Google aprovar!
        modelo_texto = "gemini-1.5-flash" # Fallback
        try:
            para_chat = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if para_chat:
                modelo_texto = para_chat[0] # Pega o primeiro que funcionar
                # Se tiver a versão flash na lista, dá preferência pra ela que é mais rápida
                for m in para_chat:
                    if 'flash' in m:
                        modelo_texto = m
                        break
        except Exception:
            pass

        model = genai.GenerativeModel(modelo_texto)
        response = model.generate_content(prompt)
            
        return response.text, intencao

    except Exception as e:
        return f"Erro na IA: {str(e)}", intencao

def registrar_resposta(conversa: Conversa, resposta: str) -> Mensagem:
    return Mensagem.objects.create(
        conversa=conversa,
        role="assistant",
        conteudo_original=resposta,
        conteudo_processado=resposta,
    )