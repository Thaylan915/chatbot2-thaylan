"""
Interface abstrata do repositório de documentos.
Repository Pattern (GoF) — a camada de aplicação depende desta interface,
nunca da implementação concreta.
"""

from abc import ABC, abstractmethod


class DocumentRepository(ABC):

    @abstractmethod
    def get_by_id(self, id_documento: int):
        """Retorna o objeto Documento ou None se não encontrado."""
        pass

    @abstractmethod
    def create(self, nome: str, tipo: str, caminho_arquivo: str):
        """Cria e retorna um novo Documento."""
        pass

    @abstractmethod
    def update(self, id_documento: int, nome: str = None, tipo: str = None, caminho_arquivo: str = None):
        """Atualiza e retorna o Documento existente, ou None se não encontrado."""
        pass

    @abstractmethod
    def delete(self, id_documento: int) -> bool:
        """Remove documento e chunks. Retorna True se removido, False se não encontrado."""
        pass

    @abstractmethod
    def list_all(
        self,
        tipo: str = None,
        data_inicio: str = None,
        data_fim: str = None,
    ) -> list:
        """
        Retorna lista de dicts com todos os documentos.
        Filtros opcionais:
          tipo        → 'portaria' | 'resolucao' | 'rod'
          data_inicio → 'YYYY-MM-DD'
          data_fim    → 'YYYY-MM-DD'
        """
        pass