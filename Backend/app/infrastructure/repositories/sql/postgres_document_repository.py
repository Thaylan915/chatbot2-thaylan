"""
Implementação PostgreSQL do repositório de documentos.
Repository Pattern — ConcreteRepository usando Django ORM + PostgreSQL.
"""

from Backend.app.domain.repositories.document_repository import DocumentRepository
from Backend.app.documents.models import Documento, ChunkDocumento


class PostgresDocumentRepository(DocumentRepository):

    def get_by_id(self, id_documento: int):
        try:
            return Documento.objects.get(id=id_documento)
        except Documento.DoesNotExist:
            return None

    def delete(self, id_documento: int) -> bool:
        documento = self.get_by_id(id_documento)

        if documento is None:
            return False

        # Remove os chunks vinculados e depois o documento
        # (cascade já está configurado no model, mas explicitamos por clareza)
        ChunkDocumento.objects.filter(documento=documento).delete()
        documento.delete()

        return True

    def list_all(self) -> list:
        return list(
            Documento.objects.all().values(
                "id", "nome", "tipo", "caminho_arquivo", "indexado_em"
            )
        )

    def update(self, id_documento: int, campos: dict) -> dict | None:
        documento = self.get_by_id(id_documento)
        if documento is None:
            return None

        campos_permitidos = {"nome", "tipo", "caminho_arquivo"}
        for campo, valor in campos.items():
            if campo in campos_permitidos:
                setattr(documento, campo, valor)

        documento.save()

        return {
            "id": documento.id,
            "nome": documento.nome,
            "tipo": documento.tipo,
            "caminho_arquivo": documento.caminho_arquivo,
            "atualizado_em": documento.atualizado_em.isoformat(),
        }

    def save(self, nome: str, tipo: str, caminho_arquivo: str) -> dict:
        doc = Documento.objects.create(
            nome=nome,
            tipo=tipo,
            caminho_arquivo=caminho_arquivo,
        )
        return {
            "id": doc.id,
            "nome": doc.nome,
            "tipo": doc.tipo,
            "caminho_arquivo": doc.caminho_arquivo,
            "indexado_em": doc.indexado_em.isoformat(),
        }