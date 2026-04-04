"""Caso de uso: responder pergunta do usuário usando o banco de documentos."""
import re
from Backend.app.documents.models import Conversa, Mensagem


def preprocessar_pergunta(texto: str) -> str:
    """
    Pré-processa a pergunta do usuário:
    - Remove espaços extras
    - Converte para minúsculas
    - Remove caracteres especiais desnecessários
    """
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.lower()
    texto = re.sub(r'[^\w\s\?\!\.\,\á\é\í\ó\ú\ã\õ\â\ê\ô\ç]', '', texto)
    return texto


def iniciar_conversa(user=None) -> Conversa:
    """Cria e retorna uma nova conversa. #34"""
    return Conversa.objects.create(user=user)


def registrar_mensagem(conversa: Conversa, pergunta_original: str) -> Mensagem:
    """
    Registra a pergunta original (#36) e a processada (#37).
    Retorna a mensagem criada.
    """
    pergunta_processada = preprocessar_pergunta(pergunta_original)

    mensagem = Mensagem.objects.create(
        conversa=conversa,
        role="user",
        conteudo_original=pergunta_original,       # #36 — pergunta como veio do usuário
        conteudo_processado=pergunta_processada,   # #37 — pergunta após processamento
    )
    return mensagem


def gerar_resposta(pergunta_processada: str) -> str:
    """
    Gera resposta para a pergunta.
    Por enquanto retorna resposta simulada — será integrado ao Gemini futuramente.
    """
    return f"Resposta para: {pergunta_processada}"


def registrar_resposta(conversa: Conversa, resposta: str) -> Mensagem:
    """Registra a resposta do assistente na conversa."""
    return Mensagem.objects.create(
        conversa=conversa,
        role="assistant",
        conteudo_original=resposta,
        conteudo_processado=resposta,
    )