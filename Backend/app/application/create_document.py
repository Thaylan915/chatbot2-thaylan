"""
Caso de uso: cadastrar um novo documento. Salva o PDF localmente, cria a v1
ativa do documento, gera chunks + embeddings.
"""
from Backend.app.domain.repositories.document_repository import DocumentRepository
from Backend.app.documents.models import Documento
from Backend.app.application.document_versioning import (
    salvar_arquivo_no_disco,
    extrair_chunks_do_pdf,
    gerar_embeddings,
    criar_versao,
)

TIPOS_VALIDOS = {"portaria", "resolucao", "rod"}


class CreateDocument:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def executar(self, nome: str, tipo: str, conteudo_arquivo: bytes, nome_arquivo: str) -> dict:
        if not nome or not nome.strip():
            raise ValueError("O campo 'nome' é obrigatório.")
        if tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Use um dos valores: {', '.join(TIPOS_VALIDOS)}.")
        if not conteudo_arquivo:
            raise ValueError("O arquivo não pode estar vazio.")

        caminho = salvar_arquivo_no_disco(conteudo_arquivo, nome_arquivo, tipo)

        documento = Documento.objects.create(
            nome=nome.strip(),
            tipo=tipo,
            caminho_arquivo=caminho,
        )

        chunks_texto = extrair_chunks_do_pdf(caminho)
        embeddings = gerar_embeddings(chunks_texto) if chunks_texto else []
        versao = criar_versao(
            documento=documento,
            nome=nome.strip(),
            tipo=tipo,
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
        }
