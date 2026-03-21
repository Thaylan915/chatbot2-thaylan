"""
Backend/app/documents/models.py
Modelo para armazenar documentos e seus chunks com embeddings.
"""

from django.db import models


class TipoDocumento(models.TextChoices):
    PORTARIA = "portaria", "Portaria"
    RESOLUCAO = "resolucao", "Resolução"
    ROD = "rod", "ROD"


class Documento(models.Model):
    """
    Representa um arquivo PDF indexado no sistema.
    """

    nome = models.CharField(max_length=512)
    tipo = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        default=TipoDocumento.PORTARIA,
    )
    caminho_arquivo = models.CharField(max_length=1024, unique=True)
    indexado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["tipo", "nome"]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.nome}"


class ChunkDocumento(models.Model):
    """
    Trecho (chunk) de um documento com seu respectivo embedding vetorial.
    O campo 'embedding' é armazenado como JSON (lista de floats).
    Para busca vetorial nativa use pgvector via SQL raw ou psycopg2.
    """

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    numero_pagina = models.PositiveIntegerField(null=True, blank=True)
    numero_chunk = models.PositiveIntegerField()
    conteudo = models.TextField()
    # Embedding armazenado como JSON; o índice vetorial fica no PostgreSQL via pgvector
    embedding = models.JSONField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chunk de Documento"
        verbose_name_plural = "Chunks de Documentos"
        ordering = ["documento", "numero_chunk"]
        unique_together = [["documento", "numero_chunk"]]

    def __str__(self):
        return f"{self.documento.nome} — chunk {self.numero_chunk}"
