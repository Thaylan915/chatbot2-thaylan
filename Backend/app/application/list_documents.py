"""
Caso de uso: listar documentos disponíveis na API do Gemini.
Usa genai.list_files() para recuperar os arquivos enviados à API.
"""

import google.generativeai as genai
from django.conf import settings


class ListDocuments:

    def executar(self) -> list[dict]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY não configurada.")

        genai.configure(api_key=api_key)

        arquivos = []
        for arquivo in genai.list_files():
            arquivos.append({
                "name": arquivo.name,
                "display_name": arquivo.display_name,
                "mime_type": arquivo.mime_type,
                "size_bytes": arquivo.size_bytes,
                "state": arquivo.state.name,
                "create_time": arquivo.create_time.isoformat() if arquivo.create_time else None,
                "expiration_time": arquivo.expiration_time.isoformat() if arquivo.expiration_time else None,
                "uri": arquivo.uri,
            })

        return arquivos
