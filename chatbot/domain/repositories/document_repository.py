"""Abstract repository interface for documents."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from chatbot.domain.entities.document import Document
import sqlite3


class DocumentRepository:

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


    # READ BY ID
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


    # DELETE
    def delete_document(self, id_documento):

        query = "DELETE FROM documento WHERE id_documento=?"

        self.cursor.execute(query, (id_documento,))
        self.conn.commit()


    # UPDATE STATUS (INDEXADO / PENDENTE)
    def update_status(self, id_documento, status):

        query = """
        UPDATE documento
        SET status_indexacao=?
        WHERE id_documento=?
        """

        self.cursor.execute(query, (status, id_documento))
        self.conn.commit()