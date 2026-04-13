import google.generativeai as genai
from django.conf import settings

RESPOSTAS_DIRETAS = {
    "SAUDACAO": "Olá! Sou o assistente institucional do IFES. Como posso te ajudar com as portarias, resoluções e RODs?",
    "AGRADECIMENTO": "Por nada! Se precisar de mais informações sobre os documentos, estou à disposição.",
    "FORA_CONTEXTO": "Desculpe, mas só consigo responder perguntas relacionadas aos documentos institucionais do IFES.",
}

def classificar_intencao(pergunta: str) -> str:
    # 1. Filtro manual rápido (Garante que o 'oi' funcione mesmo se a API cair)
    pergunta_limpa = pergunta.lower().strip()
    if pergunta_limpa in ['oi', 'ola', 'olá', 'bom dia', 'boa tarde']:
        return "SAUDACAO"

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Usamos o nome completo do modelo para a v1beta não reclamar
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = (
            f"Classifique a intenção: '{pergunta}'\n"
            "Categorias: SAUDACAO, AGRADECIMENTO, CONSULTA_DOCUMENTO, FORA_CONTEXTO.\n"
            "Responda apenas a categoria."
        )
        
        response = model.generate_content(prompt)
        res = response.text.strip().upper()
        
        if "SAUDACAO" in res: return "SAUDACAO"
        if "AGRADECIMENTO" in res: return "AGRADECIMENTO"
        if "FORA_CONTEXTO" in res: return "FORA_CONTEXTO"
        return "CONSULTA_DOCUMENTO"
    except:
        return "CONSULTA_DOCUMENTO"