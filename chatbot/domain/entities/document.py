"""Domain entity representing an indexed document."""
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Document:
    def __init__(self, titulo, conteudo, origem, data_criacao, id_categoria, status_indexacao="PENDENTE", id_documento=None):
        self.id_documento = id_documento
        self.titulo = titulo
        self.conteudo = conteudo
        self.origem = origem
        self.data_criacao = data_criacao
        self.id_categoria = id_categoria
        self.status_indexacao = status_indexacao