"""
Backend/app/documents/management/commands/indexar_documentos.py

Comando para indexar os PDFs do projeto no banco de dados.

Uso:
    python manage.py indexar_documentos
    python manage.py indexar_documentos --pasta Documentos
    python manage.py indexar_documentos --gerar-embeddings
"""

import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from Backend.app.documents.models import Documento, ChunkDocumento, TipoDocumento
from Backend.app.infrastructure.embeddings.gemini_embedding import GeminiEmbeddingProvider


# ─── Mapeamento pasta → tipo ──────────────────────────────────────────────────
PASTA_PARA_TIPO = {
    "portarias": TipoDocumento.PORTARIA,
    "resolucoes": TipoDocumento.RESOLUCAO,
    "rod": TipoDocumento.ROD,
}

# Tamanho do chunk em caracteres
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class Command(BaseCommand):
    help = "Indexa os arquivos PDF em Documentos/ no banco de dados PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pasta",
            type=str,
            default="Documentos",
            help="Caminho para a pasta raiz dos documentos (padrão: Documentos)",
        )
        parser.add_argument(
            "--gerar-embeddings",
            action="store_true",
            default=False,
            help="Gera e armazena embeddings via Gemini (requer GEMINI_API_KEY)",
        )
        parser.add_argument(
            "--forcar",
            action="store_true",
            default=False,
            help="Re-indexa arquivos que já estão no banco",
        )

    def handle(self, *args, **options):
        pasta_raiz = Path(options["pasta"])
        gerar_embeddings = options["gerar_embeddings"]
        forcar = options["forcar"]

        if not pasta_raiz.exists():
            self.stderr.write(self.style.ERROR(f"Pasta não encontrada: {pasta_raiz}"))
            return

        self.stdout.write(self.style.SUCCESS(f"\n📂 Pasta raiz: {pasta_raiz.resolve()}"))

        pypdf = self._importar_pypdf()
        if pypdf is None:
            return

        embedding_provider = self._criar_provider_embedding() if gerar_embeddings else None

        total_docs = 0
        total_chunks = 0
        for pasta_nome, tipo in PASTA_PARA_TIPO.items():
            docs, chunks = self._indexar_subpasta(
                pasta_raiz / pasta_nome, pasta_nome, tipo,
                pypdf=pypdf, forcar=forcar,
                gerar_embeddings=gerar_embeddings,
                embedding_provider=embedding_provider,
            )
            total_docs += docs
            total_chunks += chunks

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Indexação concluída: {total_docs} documento(s), {total_chunks} chunk(s)\n"
            )
        )

    def _importar_pypdf(self):
        try:
            import pypdf
            return pypdf
        except ImportError:
            self.stderr.write(self.style.ERROR(
                "pypdf não instalado. Execute: pip install pypdf"
            ))
            return None

    def _indexar_subpasta(self, pasta, pasta_nome, tipo, *, pypdf, forcar,
                          gerar_embeddings, embedding_provider):
        if not pasta.exists():
            self.stdout.write(f"  ⚠️  Subpasta não encontrada: {pasta}")
            return 0, 0

        pdfs = sorted(pasta.glob("*.pdf"))
        self.stdout.write(f"\n📁 {pasta_nome.upper()} — {len(pdfs)} arquivo(s)")

        total_docs = 0
        total_chunks = 0
        for pdf_path in pdfs:
            chunks_criados = self._indexar_pdf(
                pdf_path, tipo, pypdf=pypdf, forcar=forcar,
                gerar_embeddings=gerar_embeddings,
                embedding_provider=embedding_provider,
            )
            if chunks_criados is not None:
                total_docs += 1
                total_chunks += chunks_criados
        return total_docs, total_chunks

    def _indexar_pdf(self, pdf_path, tipo, *, pypdf, forcar,
                     gerar_embeddings, embedding_provider):
        caminho_str = str(pdf_path)
        if not forcar and Documento.objects.filter(caminho_arquivo=caminho_str).exists():
            self.stdout.write(f"  ⏭  Já indexado: {pdf_path.name}")
            return None

        self.stdout.write(f"  📄 Indexando: {pdf_path.name}")
        try:
            paginas = self._extrair_paginas(pdf_path, pypdf)
            chunks = self._criar_chunks_por_pagina(paginas)

            doc, _ = Documento.objects.update_or_create(
                caminho_arquivo=caminho_str,
                defaults={"nome": pdf_path.stem, "tipo": tipo},
            )
            if forcar:
                doc.chunks.all().delete()

            self._persistir_chunks(
                doc, chunks,
                gerar_embeddings=gerar_embeddings,
                embedding_provider=embedding_provider,
            )
            self.stdout.write(f"     ✅ {len(chunks)} chunk(s) criado(s)")
            return len(chunks)
        except Exception as e:
            self.stderr.write(f"     ❌ Erro: {e}")
            return None

    def _persistir_chunks(self, doc, chunks, *, gerar_embeddings, embedding_provider):
        deve_gerar = gerar_embeddings and embedding_provider is not None
        for i, chunk in enumerate(chunks):
            embedding = (
                self._gerar_embedding(embedding_provider, chunk["conteudo"])
                if deve_gerar else None
            )
            ChunkDocumento.objects.create(
                documento=doc,
                numero_chunk=i,
                numero_pagina=chunk["numero_pagina"],
                conteudo=chunk["conteudo"],
                embedding=embedding,
            )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _extrair_paginas(self, pdf_path: Path, pypdf) -> list[dict]:
        """Extrai texto por página de um PDF, preservando o número da página."""
        paginas = []
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for indice, pagina in enumerate(reader.pages, start=1):
                texto = (pagina.extract_text() or "").strip()
                if texto:
                    paginas.append({"numero_pagina": indice, "conteudo": texto})
        return paginas

    def _criar_chunks_por_pagina(self, paginas: list[dict]) -> list[dict]:
        """Divide o texto em chunks com sobreposição mantendo origem da página."""
        if not paginas:
            return []

        chunks = []
        for pagina in paginas:
            texto = pagina["conteudo"]
            inicio = 0
            while inicio < len(texto):
                fim = inicio + CHUNK_SIZE
                chunk = texto[inicio:fim]
                if chunk.strip():
                    chunks.append(
                        {
                            "numero_pagina": pagina["numero_pagina"],
                            "conteudo": chunk.strip(),
                        }
                    )
                inicio += CHUNK_SIZE - CHUNK_OVERLAP

        return chunks

    def _criar_provider_embedding(self):
        """Instancia o GeminiEmbeddingProvider."""
        if not settings.GEMINI_API_KEY:
            self.stderr.write(self.style.WARNING("GEMINI_API_KEY não configurada."))
            return None
        try:
            return GeminiEmbeddingProvider()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro ao criar provider de embedding: {e}"))
            return None

    def _gerar_embedding(self, provider: GeminiEmbeddingProvider, texto: str) -> list[float] | None:
        """Gera embedding de documento (task_type='retrieval_document') via Gemini."""
        try:
            return provider.embed(texto, task_type="retrieval_document")
        except Exception as e:
            self.stderr.write(f"     ⚠️  Erro ao gerar embedding: {e}")
            return None
