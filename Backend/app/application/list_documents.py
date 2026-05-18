"""
Caso de uso: listar documentos com filtros opcionais por tipo e período.
"""

from Backend.app.domain.repositories.document_repository import DocumentRepository


class ListDocuments:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def executar(
        self,
        tipo: str = None,
        data_inicio: str = None,
        data_fim: str = None,
    ) -> list[dict]:
        """
        Retorna documentos com filtros opcionais:
          tipo        → 'portaria' | 'resolucao' | 'rod'
          data_inicio → 'YYYY-MM-DD'
          data_fim    → 'YYYY-MM-DD'
        """
        return self.repository.list_all(
            tipo=tipo,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )