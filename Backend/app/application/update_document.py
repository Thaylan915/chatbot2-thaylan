"""
Caso de uso: editar um documento.
- Se um novo arquivo for enviado: cria uma nova versão (ativa por padrão).
- Caso contrário: atualiza apenas os metadados da versão ativa.
"""
from Backend.app.domain.repositories.document_repository import DocumentRepository
from Backend.app.documents.models import Documento, VersaoDocumento
from Backend.app.application.document_versioning import (
    salvar_arquivo_no_disco,
    extrair_chunks_do_pdf,
    gerar_embeddings,
    criar_versao,
)

TIPOS_VALIDOS = {"portaria", "resolucao", "rod"}


class UpdateDocument:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def executar(
        self,
        id_documento: int,
        nome: str | None = None,
        tipo: str | None = None,
        conteudo_arquivo: bytes | None = None,
        nome_arquivo: str | None = None,
    ) -> dict:
        if not isinstance(id_documento, int) or id_documento <= 0:
            raise ValueError("ID do documento inválido.")
        if nome is not None and not nome.strip():
            raise ValueError("O campo 'nome' não pode ser vazio.")
        if tipo is not None and tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Use um dos valores: {', '.join(TIPOS_VALIDOS)}.")

        try:
            documento = Documento.objects.get(id=id_documento)
        except Documento.DoesNotExist:
            raise LookupError(f"Documento com ID {id_documento} não encontrado.")

        novo_nome = nome.strip() if nome else documento.nome
        novo_tipo = tipo or documento.tipo

        if conteudo_arquivo:
            # Novo arquivo → nova versão
            caminho = salvar_arquivo_no_disco(
                conteudo_arquivo, nome_arquivo or f"{novo_nome}.pdf", novo_tipo
            )
            chunks_texto = extrair_chunks_do_pdf(caminho)
            embeddings = gerar_embeddings(chunks_texto) if chunks_texto else []
            versao = criar_versao(
                documento=documento,
                nome=novo_nome,
                tipo=novo_tipo,
                caminho_arquivo=caminho,
                chunks_texto=chunks_texto,
                embeddings=embeddings,
                ativar=True,
            )
            return {
                "id": documento.id,
                "nome": documento.nome,
                "tipo": documento.tipo,
                "caminho_arquivo": documento.caminho_arquivo,
                "versao_ativa": versao.numero,
                "qtd_chunks": len(chunks_texto),
                "criou_nova_versao": True,
            }

        # Sem arquivo: atualiza só metadados (na versão ativa e no Documento)
        if nome is None and tipo is None:
            raise ValueError("Nenhum campo para atualizar foi fornecido.")

        ativa = VersaoDocumento.objects.filter(documento=documento, ativa=True).first()
        if ativa:
            campos_v = []
            if nome is not None:
                ativa.nome = novo_nome
                campos_v.append("nome")
            if tipo is not None:
                ativa.tipo = novo_tipo
                campos_v.append("tipo")
            if campos_v:
                ativa.save(update_fields=campos_v)

        if nome is not None:
            documento.nome = novo_nome
        if tipo is not None:
            documento.tipo = novo_tipo
        documento.save(update_fields=["nome", "tipo", "atualizado_em"])

        return {
            "id": documento.id,
            "nome": documento.nome,
            "tipo": documento.tipo,
            "caminho_arquivo": documento.caminho_arquivo,
            "versao_ativa": ativa.numero if ativa else None,
            "criou_nova_versao": False,
        }
