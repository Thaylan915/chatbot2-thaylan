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

        # Importa pypdf apenas quando o comando roda
        try:
            import pypdf
        except ImportError:
            self.stderr.write(self.style.ERROR(
                "pypdf não instalado. Execute: pip install pypdf"
            ))
            return

        embedding_provider = None
        if gerar_embeddings:
            embedding_provider = self._criar_provider_embedding()

        total_docs = 0
        total_chunks = 0

        for pasta_nome, tipo in PASTA_PARA_TIPO.items():
            pasta = pasta_raiz / pasta_nome
            if not pasta.exists():
                self.stdout.write(f"  ⚠️  Subpasta não encontrada: {pasta}")
                continue

            pdfs = sorted(pasta.glob("*.pdf"))
            self.stdout.write(f"\n📁 {pasta_nome.upper()} — {len(pdfs)} arquivo(s)")

            for pdf_path in pdfs:
                caminho_str = str(pdf_path)

                if not forcar and Documento.objects.filter(caminho_arquivo=caminho_str).exists():
                    self.stdout.write(f"  ⏭  Já indexado: {pdf_path.name}")
                    continue

                self.stdout.write(f"  📄 Indexando: {pdf_path.name}")

                try:
                    texto = self._extrair_texto(pdf_path, pypdf)
                    chunks = self._criar_chunks(texto)

                    doc, _ = Documento.objects.update_or_create(
                        caminho_arquivo=caminho_str,
                        defaults={
                            "nome": pdf_path.stem,
                            "tipo": tipo,
                        },
                    )

                    # Remove chunks antigos caso esteja re-indexando
                    if forcar:
                        doc.chunks.all().delete()

                    for i, chunk_texto in enumerate(chunks):
                        embedding = None
                        if gerar_embeddings and embedding_provider:
                            embedding = self._gerar_embedding(embedding_provider, chunk_texto)

                        ChunkDocumento.objects.create(
                            documento=doc,
                            numero_chunk=i,
                            conteudo=chunk_texto,
                            embedding=embedding,
                        )

                    total_docs += 1
                    total_chunks += len(chunks)
                    self.stdout.write(f"     ✅ {len(chunks)} chunk(s) criado(s)")

                except Exception as e:
                    self.stderr.write(f"     ❌ Erro: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Indexação concluída: {total_docs} documento(s), {total_chunks} chunk(s)\n"
            )
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _extrair_texto(self, pdf_path: Path, pypdf) -> str:
        """Extrai todo o texto de um PDF."""
        texto = []
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for pagina in reader.pages:
                t = pagina.extract_text()
                if t:
                    texto.append(t)
        return "\n".join(texto)

    def _criar_chunks(self, texto: str) -> list[str]:
        """Divide o texto em chunks com sobreposição."""
        if not texto.strip():
            return []

        chunks = []
        inicio = 0
        while inicio < len(texto):
            fim = inicio + CHUNK_SIZE
            chunk = texto[inicio:fim]
            if chunk.strip():
                chunks.append(chunk.strip())
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
