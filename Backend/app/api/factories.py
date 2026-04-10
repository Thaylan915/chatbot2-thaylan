from Backend.app.application.login_admin import LoginAdmin
from Backend.app.application.delete_document import DeleteDocument
from Backend.app.application.list_documents import ListDocuments
from Backend.app.application.create_document import CreateDocument
from Backend.app.application.update_document import UpdateDocument
from Backend.app.application.answer_question import ResponderPergunta
from Backend.app.infrastructure.embeddings.gemini_embedding import GeminiEmbeddingProvider
from Backend.app.infrastructure.repositories.sql.postgres_document_repository import (
    PostgresDocumentRepository,
)
from Backend.app.infrastructure.repositories.sql.postgres_chunk_repository import (
    PostgresChunkRepository,
)


class AuthFactory:
    @staticmethod
    def make_login() -> LoginAdmin:
        return LoginAdmin()


class DocumentFactory:

    @staticmethod
    def make_list() -> ListDocuments:
        # Antes: ListDocuments() sem repositório — quebrava em runtime
        return ListDocuments(repository=PostgresDocumentRepository())

    @staticmethod
    def make_create() -> CreateDocument:
        return CreateDocument(repository=PostgresDocumentRepository())

    @staticmethod
    def make_update() -> UpdateDocument:
        return UpdateDocument(repository=PostgresDocumentRepository())

    @staticmethod
    def make_delete() -> DeleteDocument:
        return DeleteDocument(repository=PostgresDocumentRepository())


class ChatFactory:

    @staticmethod
    def make_responder() -> ResponderPergunta:
        return ResponderPergunta(
            chunk_repository=PostgresChunkRepository(),
            embedding_provider=GeminiEmbeddingProvider(),
        )