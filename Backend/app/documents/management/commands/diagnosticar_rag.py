"""
Diagnóstico do estado da base de conhecimento RAG.

Uso:
    python Backend/manage.py diagnosticar_rag
    python Backend/manage.py diagnosticar_rag --tipo rod
    python Backend/manage.py diagnosticar_rag --pergunta "qual o conteúdo do rod"
"""
import json

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from Backend.app.documents.models import Documento, ChunkDocumento, TipoDocumento


class Command(BaseCommand):
    help = "Diagnostica o estado da base de conhecimento (chunks, embeddings, dimensões)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tipo",
            choices=[t.value for t in TipoDocumento],
            help="Filtra por tipo de documento (portaria | resolucao | rod)",
        )
        parser.add_argument(
            "--pergunta",
            type=str,
            help="Simula uma busca por palavra-chave nos chunks indexados",
        )

    def handle(self, *args, **options):
        tipo = options.get("tipo")
        pergunta = options.get("pergunta")

        # ─── Resumo geral ──────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\n=== RESUMO GERAL ===\n"))
        for t in TipoDocumento:
            docs = Documento.objects.filter(tipo=t.value)
            n_docs = docs.count()
            chunks = ChunkDocumento.objects.filter(documento__tipo=t.value)
            n_chunks = chunks.count()
            n_com_emb = chunks.exclude(embedding__isnull=True).count()
            n_sem_emb = n_chunks - n_com_emb

            cor = self.style.SUCCESS if n_sem_emb == 0 and n_chunks > 0 else self.style.WARNING
            self.stdout.write(cor(
                f"  {t.label:12s} → {n_docs:3d} doc(s) │ "
                f"{n_chunks:5d} chunks │ {n_com_emb:5d} c/embedding │ "
                f"{n_sem_emb:5d} SEM embedding"
            ))

        # ─── Detalhe por documento (se filtrado) ──────────────────────
        if tipo:
            self.stdout.write(self.style.SUCCESS(f"\n=== DETALHE: {tipo.upper()} ===\n"))
            for doc in Documento.objects.filter(tipo=tipo):
                chunks = doc.chunks.all()
                total = chunks.count()
                com_emb = chunks.exclude(embedding__isnull=True).count()

                # Verifica dimensão dos embeddings (se houver)
                primeiro = chunks.exclude(embedding__isnull=True).first()
                dim = "—"
                if primeiro and primeiro.embedding:
                    emb = primeiro.embedding
                    if isinstance(emb, str):
                        try:
                            emb = json.loads(emb)
                        except json.JSONDecodeError:
                            emb = None
                    if isinstance(emb, list):
                        dim = str(len(emb))

                status = "✅" if com_emb == total else "❌"
                self.stdout.write(
                    f"  {status} {doc.nome[:60]:60s} │ "
                    f"{total:4d} chunks │ {com_emb:4d} c/emb │ dim={dim}"
                )

        # ─── Verifica dimensões consistentes ──────────────────────────
        self.stdout.write(self.style.SUCCESS("\n=== CONSISTÊNCIA DE DIMENSÕES ==="))
        amostras = ChunkDocumento.objects.exclude(embedding__isnull=True)[:50]
        dims = {}
        for c in amostras:
            emb = c.embedding
            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except json.JSONDecodeError:
                    continue
            if isinstance(emb, list):
                dims[len(emb)] = dims.get(len(emb), 0) + 1

        if not dims:
            self.stdout.write(self.style.WARNING("  Nenhum embedding encontrado para verificar."))
        elif len(dims) == 1:
            d, n = next(iter(dims.items()))
            self.stdout.write(self.style.SUCCESS(f"  ✅ Todas as {n} amostras têm dim={d}"))
        else:
            self.stdout.write(self.style.ERROR("  ❌ Dimensões INCONSISTENTES detectadas:"))
            for d, n in dims.items():
                self.stdout.write(f"    dim={d}: {n} amostras")
            self.stdout.write(self.style.ERROR(
                "  → Re-indexe TUDO com: python Backend/manage.py indexar_documentos --gerar-embeddings --forcar"
            ))

        # ─── Busca textual de fallback ────────────────────────────────
        if pergunta:
            self.stdout.write(self.style.SUCCESS(f"\n=== BUSCA TEXTUAL: '{pergunta}' ===\n"))
            tokens = [t.lower() for t in pergunta.split() if len(t) >= 3]
            if not tokens:
                self.stdout.write("  Nenhum token relevante na pergunta.")
                return

            q = Q()
            for t in tokens:
                q |= Q(conteudo__icontains=t)

            chunks = ChunkDocumento.objects.filter(q).select_related("documento")[:10]
            if not chunks:
                self.stdout.write(self.style.ERROR(
                    f"  ❌ NENHUM chunk contém os tokens: {tokens}"
                ))
                self.stdout.write(self.style.WARNING(
                    "  → Os documentos provavelmente não foram extraídos corretamente do PDF, "
                    "ou usam termos diferentes da pergunta."
                ))
            else:
                self.stdout.write(f"  Encontrados {chunks.count()} chunks com correspondência textual:")
                for c in chunks:
                    preview = c.conteudo[:120].replace("\n", " ")
                    tem_emb = "✅" if c.embedding else "❌"
                    self.stdout.write(
                        f"  {tem_emb} [{c.documento.tipo}] {c.documento.nome[:40]:40s} "
                        f"p.{c.numero_pagina or '?'} │ {preview}…"
                    )

        self.stdout.write("")
