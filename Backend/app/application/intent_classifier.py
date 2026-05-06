RESPOSTAS_DIRETAS = {
    "SAUDACAO": "Olá! Sou o assistente institucional do IFES. Como posso te ajudar com as portarias, resoluções e RODs?",
    "AGRADECIMENTO": "Por nada! Se precisar de mais informações sobre os documentos, estou à disposição.",
    "FORA_CONTEXTO": "Desculpe, mas só consigo responder perguntas relacionadas aos documentos institucionais do IFES.",
}

def classificar_intencao(pergunta: str) -> str:
    pergunta_limpa = pergunta.lower().strip()
    if pergunta_limpa in ['oi', 'ola', 'olá', 'bom dia', 'boa tarde']:
        return "SAUDACAO"
    if pergunta_limpa in ['obrigado', 'obrigada', 'valeu', 'muito obrigado', 'muito obrigada', 'agradecido', 'agradecida']:
        return "AGRADECIMENTO"

    return "CONSULTA_DOCUMENTO"