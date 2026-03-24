"""
Caso de uso: excluir um documento pelo ID com confirmação em dois passos.

Passo 1 — solicitar_exclusao(id_documento):
    Gera um token seguro (válido por 5 minutos) e retorna para o chamador.

Passo 2 — confirmar_exclusao(id_documento, token):
    Valida o token e, se correto, remove o documento do repositório.
"""

import secrets
import time

from Backend.app.domain.repositories.document_repository import DocumentRepository

# Armazena tokens pendentes em memória: {id_documento: {"token": str, "expires": float}}
# Em produção, considere usar o cache do Django (Redis/Memcached) para suporte multi-worker.
_pendentes: dict = {}

EXPIRACAO_SEGUNDOS = 300  # 5 minutos


class DeleteDocument:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def solicitar_exclusao(self, id_documento: int) -> dict:
        """
        Passo 1: verifica se o documento existe e devolve um token de confirmação.
        """
        if not isinstance(id_documento, int) or id_documento <= 0:
            raise ValueError("ID do documento inválido.")

        documento = self.repository.get_by_id(id_documento)
        if documento is None:
            raise LookupError(f"Documento com ID {id_documento} não encontrado.")

        token = secrets.token_urlsafe(32)
        _pendentes[id_documento] = {
            "token": token,
            "expires": time.time() + EXPIRACAO_SEGUNDOS,
        }

        return {
            "message": f"Confirme a exclusão do documento '{documento.nome}'.",
            "token": token,
            "expires_in": EXPIRACAO_SEGUNDOS,
        }

    def confirmar_exclusao(self, id_documento: int, token: str) -> dict:
        """
        Passo 2: valida o token e remove o documento.
        """
        if not isinstance(id_documento, int) or id_documento <= 0:
            raise ValueError("ID do documento inválido.")

        if not token:
            raise ValueError("Token de confirmação é obrigatório.")

        pendente = _pendentes.get(id_documento)
        if pendente is None:
            raise PermissionError("Nenhuma exclusão pendente para este documento.")

        if time.time() > pendente["expires"]:
            del _pendentes[id_documento]
            raise PermissionError("Token expirado. Solicite a exclusão novamente.")

        if pendente["token"] != token:
            raise PermissionError("Token de confirmação inválido.")

        del _pendentes[id_documento]

        documento = self.repository.get_by_id(id_documento)
        if documento is None:
            raise LookupError(f"Documento com ID {id_documento} não encontrado.")

        nome = documento.nome
        self.repository.delete(id_documento)

        return {
            "message": f"Documento '{nome}' excluído com sucesso.",
            "id": id_documento,
        }
