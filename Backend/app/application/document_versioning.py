"""
Helpers para versionamento de documentos: extração de chunks de PDFs,
geração de embeddings e criação/ativação de versões.
"""
from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.db import transaction

from Backend.app.documents.models import (
    Documento,
    VersaoDocumento,
    ChunkDocumento,
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

PASTA_POR_TIPO = {
    "portaria": "portarias",
    "resolucao": "resolucoes",
    "rod": "rod",
}


def salvar_arquivo_no_disco(conteudo: bytes, nome_arquivo: str, tipo: str) -> str:
    """Grava o PDF em Documentos/<pasta-do-tipo>/<nome_arquivo> e retorna o caminho relativo."""
    pasta_nome = PASTA_POR_TIPO.get(tipo, "outros")
    pasta = Path("Documentos") / pasta_nome
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome_arquivo
    # se já existe, adiciona sufixo numérico
    if caminho.exists():
        base = caminho.stem
        ext = caminho.suffix
        i = 2
        while caminho.exists():
            caminho = pasta / f"{base}-v{i}{ext}"
            i += 1
    caminho.write_bytes(conteudo)
    return str(caminho)


def extrair_chunks_do_pdf(caminho_arquivo: str) -> list[str]:
    """Lê o PDF do disco e retorna uma lista de chunks de texto."""
    import pypdf

    texto = []
    with open(caminho_arquivo, "rb") as f:
        reader = pypdf.PdfReader(f)
        for pagina in reader.pages:
            t = pagina.extract_text()
            if t:
                texto.append(t)
    texto_completo = "\n".join(texto)
    if not texto_completo.strip():
        return []

    chunks = []
    inicio = 0
    while inicio < len(texto_completo):
        fim = inicio + CHUNK_SIZE
        chunk = texto_completo[inicio:fim].strip()
        if chunk:
            chunks.append(chunk)
        inicio += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def gerar_embeddings(textos: Iterable[str]) -> list[list[float] | None]:
    """Gera embeddings para uma lista de textos usando google.genai (pode retornar None se falhar)."""
    try:
        from google import genai
    except ImportError:
        return [None] * len(list(textos))

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return [None for _ in textos]

    client = genai.Client(api_key=api_key)
    model = settings.EMBEDDING_MODEL

    out: list[list[float] | None] = []
    for t in textos:
        try:
            r = client.models.embed_content(model=model, contents=t)
            out.append(r.embeddings[0].values)
        except Exception:
            out.append(None)
    return out


@transaction.atomic
def criar_versao(
    documento: Documento,
    nome: str,
    tipo: str,
    caminho_arquivo: str,
    chunks_texto: list[str],
    embeddings: list[list[float] | None],
    ativar: bool = True,
) -> VersaoDocumento:
    """Cria uma nova versão e seus chunks. Opcionalmente, ativa esta versão (desativa as outras)."""
    if ativar:
        VersaoDocumento.objects.filter(documento=documento, ativa=True).update(ativa=False)

    proximo_numero = (
        VersaoDocumento.objects.filter(documento=documento).order_by("-numero").values_list("numero", flat=True).first()
        or 0
    ) + 1

    versao = VersaoDocumento.objects.create(
        documento=documento,
        numero=proximo_numero,
        nome=nome,
        tipo=tipo,
        caminho_arquivo=caminho_arquivo,
        ativa=ativar,
    )

    for i, (texto, emb) in enumerate(zip(chunks_texto, embeddings)):
        ChunkDocumento.objects.create(
            documento=documento,
            versao=versao,
            numero_chunk=i,
            conteudo=texto,
            embedding=emb,
        )

    if ativar:
        documento.nome = nome
        documento.tipo = tipo
        documento.caminho_arquivo = caminho_arquivo
        documento.save(update_fields=["nome", "tipo", "caminho_arquivo", "atualizado_em"])

    # Invalida cache de embeddings em memória (RAG)
    try:
        from Backend.app.application.answer_question import _invalidate_embedding_cache
        _invalidate_embedding_cache()
    except Exception:
        pass

    return versao


@transaction.atomic
def ativar_versao(versao: VersaoDocumento) -> VersaoDocumento:
    """Marca a versão como ativa e desativa as outras do mesmo documento."""
    VersaoDocumento.objects.filter(documento=versao.documento).exclude(id=versao.id).update(ativa=False)
    versao.ativa = True
    versao.save(update_fields=["ativa"])

    # Reflete metadados da versão ativa no Documento
    doc = versao.documento
    doc.nome = versao.nome
    doc.tipo = versao.tipo
    doc.caminho_arquivo = versao.caminho_arquivo
    doc.save(update_fields=["nome", "tipo", "caminho_arquivo", "atualizado_em"])

    try:
        from Backend.app.application.answer_question import _invalidate_embedding_cache
        _invalidate_embedding_cache()
    except Exception:
        pass

    return versao
