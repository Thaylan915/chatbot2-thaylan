

from Backend.app.application.login_admin import LoginAdmin
from Backend.app.application.delete_document import DeleteDocument
from Backend.app.application.list_documents import ListDocuments
from Backend.app.application.create_document import CreateDocument
from Backend.app.application.update_document import UpdateDocument
from Backend.app.infrastructure.repositories.sql.postgres_document_repository import (
    PostgresDocumentRepository,
)


class AuthFactory:
    @staticmethod
    def make_login() -> LoginAdmin:
        return LoginAdmin()


class DocumentFactory:
    @staticmethod
    def make_delete() -> DeleteDocument:
        repository = PostgresDocumentRepository()
        return DeleteDocument(repository=repository)

    @staticmethod
    def make_list() -> ListDocuments:
        return ListDocuments()

    @staticmethod
    def make_create() -> CreateDocument:
        repository = PostgresDocumentRepository()
        return CreateDocument(repository=repository)

    @staticmethod
    def make_update() -> UpdateDocument:
        repository = PostgresDocumentRepository()
        return UpdateDocument(repository=repository)