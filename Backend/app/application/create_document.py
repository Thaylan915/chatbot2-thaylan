"""
Caso de uso: cadastrar um novo documento via API do Gemini.
Faz upload do arquivo para o Gemini e persiste o registro no banco.
"""

import tempfile
import os

import google.generativeai as genai
from django.conf import settings

from Backend.app.domain.repositories.document_repository import DocumentRepository

TIPOS_VALIDOS = {"portaria", "resolucao", "rod"}


class CreateDocument:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def executar(self, nome: str, tipo: str, conteudo_arquivo: bytes, nome_arquivo: str) -> dict:
        if not nome or not nome.strip():
            raise ValueError("O campo 'nome' é obrigatório.")

        if tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Use um dos valores: {', '.join(TIPOS_VALIDOS)}.")

        if not conteudo_arquivo:
            raise ValueError("O arquivo não pode estar vazio.")

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY não configurada.")

        genai.configure(api_key=api_key)

        uri = self._fazer_upload_gemini(conteudo_arquivo, nome_arquivo, nome)

        documento = self.repository.save(
            nome=nome.strip(),
            tipo=tipo,
            caminho_arquivo=uri,
        )

        return documento

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _fazer_upload_gemini(self, conteudo: bytes, nome_arquivo: str, display_name: str) -> str:
        """Salva o arquivo temporariamente e faz upload para o Gemini. Retorna o URI."""
        sufixo = os.path.splitext(nome_arquivo)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as tmp:
            tmp.write(conteudo)
            tmp_path = tmp.name

        try:
            arquivo = genai.upload_file(
                path=tmp_path,
                display_name=display_name,
            )
            return arquivo.uri
        finally:
            os.unlink(tmp_path)
