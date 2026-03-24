"""
Repositório de documentos.
Mantém a implementação SQLite original e adiciona interface abstrata
para o Repository Pattern (GoF) — permitindo substituição por PostgreSQL.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from chatbot.domain.entities.document import Document
import sqlite3


# ─── Interface abstrata (Repository Pattern) ──────────────────────────────────
# A camada de aplicação depende desta interface, nunca da implementação concreta.
# Isso permite trocar SQLite por PostgreSQL sem alterar os casos de uso.

class DocumentRepository(ABC):

    @abstractmethod
    def get_by_id(self, id_documento: int):
        """Retorna um documento pelo ID ou None se não existir."""
        pass

    @abstractmethod
    def delete(self, id_documento: int) -> bool:
        """
        Remove o documento e todos os seus chunks.
        Retorna True se removido, False se não encontrado.
        """
        pass

    @abstractmethod
    def list_all(self) -> list:
        """Retorna todos os documentos indexados."""
        pass

    @abstractmethod
    def save(self, nome: str, tipo: str, caminho_arquivo: str) -> dict:
        """
        Persiste um novo documento no repositório.
        Retorna um dict com os dados do documento criado.
        """
        pass

    @abstractmethod
    def update(self, id_documento: int, campos: dict) -> dict:
        """
        Atualiza campos de um documento existente.
        Retorna um dict com os dados atualizados ou None se não encontrado.
        """
        pass


# ─── Implementação SQLite (mantida) ───────────────────────────────────────────

class SQLiteDocumentRepository(DocumentRepository):

    def __init__(self, db_path="chatbot.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    # CREATE
    def create_document(self, document: Document):
        query = """
        INSERT INTO documento
        (titulo, conteudo, origem, data_criacao, id_categoria, status_indexacao)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, (
            document.titulo,
            document.conteudo,
            document.origem,
            document.data_criacao,
            document.id_categoria,
            document.status_indexacao
        ))
        self.conn.commit()
        return self.cursor.lastrowid

    # READ ALL
    def list_documents(self):
        query = "SELECT * FROM documento"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        documentos = []
        for row in rows:
            documentos.append(
                Document(
                    id_documento=row[0],
                    titulo=row[1],
                    conteudo=row[2],
                    origem=row[3],
                    data_criacao=row[4],
                    id_categoria=row[5],
                    status_indexacao=row[6]
                )
            )
        return documentos

    # READ BY ID (implementa interface + mantém nome original)
    def get_document(self, id_documento):
        query = "SELECT * FROM documento WHERE id_documento = ?"
        self.cursor.execute(query, (id_documento,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return Document(
            id_documento=row[0],
            titulo=row[1],
            conteudo=row[2],
            origem=row[3],
            data_criacao=row[4],
            id_categoria=row[5],
            status_indexacao=row[6]
        )

    def get_by_id(self, id_documento: int):
        """Alias para compatibilidade com a interface abstrata."""
        return self.get_document(id_documento)

    # UPDATE
    def update_document(self, document: Document):
        query = """
        UPDATE documento
        SET titulo=?, conteudo=?, origem=?, id_categoria=?, status_indexacao=?
        WHERE id_documento=?
        """
        self.cursor.execute(query, (
            document.titulo,
            document.conteudo,
            document.origem,
            document.id_categoria,
            document.status_indexacao,
            document.id_documento
        ))
        self.conn.commit()

    # DELETE (implementa interface + mantém nome original)
    def delete_document(self, id_documento):
        query = "DELETE FROM documento WHERE id_documento=?"
        self.cursor.execute(query, (id_documento,))
        self.conn.commit()

    def delete(self, id_documento: int) -> bool:
        """Alias para compatibilidade com a interface abstrata."""
        documento = self.get_document(id_documento)
        if documento is None:
            return False
        self.delete_document(id_documento)
        return True

    # LIST ALL (implementa interface)
    def list_all(self) -> list:
        return self.list_documents()

    # UPDATE STATUS (INDEXADO / PENDENTE)
    def update_status(self, id_documento, status):
        query = """
        UPDATE documento
        SET status_indexacao=?
        WHERE id_documento=?
        """
        self.cursor.execute(query, (status, id_documento))
        self.conn.commit()