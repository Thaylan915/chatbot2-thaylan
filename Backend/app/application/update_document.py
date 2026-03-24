"""
Caso de uso: editar um documento existente.
Permite atualizar nome, tipo e/ou substituir o arquivo no Gemini.
"""

import tempfile
import os

import google.generativeai as genai
from django.conf import settings

from Backend.app.domain.repositories.document_repository import DocumentRepository

TIPOS_VALIDOS = {"portaria", "resolucao", "rod"}


class UpdateDocument:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def executar(
        self,
        id_documento: int,
        nome: str | None = None,
        tipo: str | None = None,
        conteudo_arquivo: bytes | None = None,
        nome_arquivo: str | None = None,
    ) -> dict:
        if not isinstance(id_documento, int) or id_documento <= 0:
            raise ValueError("ID do documento inválido.")

        if nome is not None and not nome.strip():
            raise ValueError("O campo 'nome' não pode ser vazio.")

        if tipo is not None and tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Use um dos valores: {', '.join(TIPOS_VALIDOS)}.")

        documento = self.repository.get_by_id(id_documento)
        if documento is None:
            raise LookupError(f"Documento com ID {id_documento} não encontrado.")

        campos = {}

        if nome is not None:
            campos["nome"] = nome.strip()

        if tipo is not None:
            campos["tipo"] = tipo

        if conteudo_arquivo:
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY não configurada.")

            genai.configure(api_key=api_key)

            uri_antigo = documento.caminho_arquivo
            novo_uri = self._substituir_arquivo_gemini(
                conteudo_arquivo, nome_arquivo or "documento", campos.get("nome", documento.nome)
            )
            campos["caminho_arquivo"] = novo_uri

            self._remover_arquivo_gemini(uri_antigo)

        if not campos:
            raise ValueError("Nenhum campo para atualizar foi fornecido.")

        return self.repository.update(id_documento, campos)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _substituir_arquivo_gemini(
        self, conteudo: bytes, nome_arquivo: str, display_name: str
    ) -> str:
        """Faz upload do novo arquivo no Gemini e retorna o URI."""
        sufixo = os.path.splitext(nome_arquivo)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as tmp:
            tmp.write(conteudo)
            tmp_path = tmp.name

        try:
            arquivo = genai.upload_file(path=tmp_path, display_name=display_name)
            return arquivo.uri
        finally:
            os.unlink(tmp_path)

    def _remover_arquivo_gemini(self, uri: str) -> None:
        """Remove o arquivo antigo do Gemini a partir do URI armazenado."""
        try:
            # O nome do arquivo no Gemini é a última parte do URI (ex: files/abc123)
            nome = "/".join(uri.rstrip("/").split("/")[-2:])
            genai.delete_file(nome)
        except Exception:
            # Remoção é best-effort: não bloqueia a atualização se falhar
            pass
