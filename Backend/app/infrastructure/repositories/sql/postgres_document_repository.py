"""
Implementação PostgreSQL do DocumentRepository.
Resolve issues: #21 (categorias), #24 (origem/categoria/data), #25 (versões), #73 (filtros).
"""

from Backend.app.domain.repositories.document_repository import DocumentRepository
from Backend.app.documents.models import Documento


class PostgresDocumentRepository(DocumentRepository):

    def get_by_id(self, id_documento: int):
        try:
            return Documento.objects.get(id=id_documento)
        except Documento.DoesNotExist:
            return None

    def create(self, nome: str, tipo: str, caminho_arquivo: str):
        return Documento.objects.create(
            nome=nome,
            tipo=tipo,
            caminho_arquivo=caminho_arquivo,
        )

    def update(self, id_documento: int, nome: str = None, tipo: str = None, caminho_arquivo: str = None):
        doc = self.get_by_id(id_documento)
        if not doc:
            return None
        if nome is not None:
            doc.nome = nome
        if tipo is not None:
            doc.tipo = tipo
        if caminho_arquivo is not None:
            doc.caminho_arquivo = caminho_arquivo
        doc.save()
        return doc

    def delete(self, id_documento: int) -> bool:
        doc = self.get_by_id(id_documento)
        if not doc:
            return False
        doc.chunks.all().delete()
        doc.delete()
        return True

    def list_all(
        self,
        tipo: str = None,
        data_inicio: str = None,
        data_fim: str = None,
    ) -> list:
        qs = Documento.objects.prefetch_related("versoes", "chunks")

        # #21 / #73 — filtro por categoria
        if tipo:
            qs = qs.filter(tipo=tipo)

        # #73 — filtro por período
        if data_inicio:
            qs = qs.filter(indexado_em__date__gte=data_inicio)
        if data_fim:
            qs = qs.filter(indexado_em__date__lte=data_fim)

        resultado = []
        for doc in qs.order_by("tipo", "nome"):
            versao_ativa = doc.versoes.filter(ativa=True).first()

            resultado.append({
                "id":           doc.id,
                "nome":         doc.nome,
                # #24 — categoria legível e tipo raw
                "categoria":    doc.get_tipo_display(),
                "tipo":         doc.tipo,
                # #24 — origem do arquivo
                "origem":       doc.caminho_arquivo,
                # #24 — datas formatadas
                "indexado_em":   doc.indexado_em.isoformat() if doc.indexado_em else None,
                "atualizado_em": doc.atualizado_em.isoformat() if doc.atualizado_em else None,                # #25 — versão ativa
                "versao_ativa":  versao_ativa.numero if versao_ativa else None,
                "total_versoes": doc.versoes.count(),
                "total_chunks":  doc.chunks.count(),
            })

        return resultado