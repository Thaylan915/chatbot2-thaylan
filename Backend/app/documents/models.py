"""
Backend/app/documents/models.py
Modelo para armazenar documentos e seus chunks com embeddings.
"""

from django.db import models
from django.contrib.auth.models import User


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


class VersaoDocumento(models.Model):
    """
    Snapshot de uma versão específica de um documento.
    Cada edição com novo arquivo cria uma nova versão; apenas uma é ativa.
    """

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name="versoes",
    )
    numero = models.PositiveIntegerField()
    nome = models.CharField(max_length=512)
    tipo = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        default=TipoDocumento.PORTARIA,
    )
    caminho_arquivo = models.CharField(max_length=1024)
    ativa = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Versão de Documento"
        verbose_name_plural = "Versões de Documentos"
        ordering = ["documento", "-numero"]
        unique_together = [["documento", "numero"]]

    def __str__(self):
        marca = " (ativa)" if self.ativa else ""
        return f"{self.documento.nome} — v{self.numero}{marca}"


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
    versao = models.ForeignKey(
        VersaoDocumento,
        on_delete=models.CASCADE,
        related_name="chunks",
        null=True, blank=True,
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

    def __str__(self):
        return f"{self.documento.nome} — chunk {self.numero_chunk}"
class AdminLog(models.Model):
    ACTIONS = [
        ("LOGIN",   "Login"),
        ("LOGOUT",  "Logout"),
        ("CREATE",  "Criação"),
        ("UPDATE",  "Edição"),
        ("DELETE",  "Exclusão"),
        ("REINDEX", "Reindexação"),
    ]

    user          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action        = models.CharField(max_length=20, choices=ACTIONS)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id   = models.IntegerField(null=True, blank=True)
    resource_name = models.CharField(max_length=255, blank=True)
    details       = models.TextField(blank=True)
    timestamp     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering  = ["-timestamp"]
        app_label = "documents"

    def __str__(self):
        return f"[{self.timestamp}] {self.user} → {self.action} {self.resource_type}"
class Profile(models.Model):
    ROLES = [
        ("admin", "Administrador"),
        ("user",  "Usuário"),
    ]

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role       = models.CharField(max_length=20, choices=ROLES, default="user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "documents"

    def __str__(self):
        return f"{self.user.username} ({self.role})"
class Conversa(models.Model):
    """Representa uma sessão de chat entre um usuário e o chatbot."""
    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    titulo      = models.CharField(max_length=255, blank=True, default="")
    iniciada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "documents"
        ordering  = ["-iniciada_em"]

    def __str__(self):
        return self.titulo or f"Conversa #{self.id} — {self.user}"
class Mensagem(models.Model):
    ROLES = [
        ("user",      "Usuário"),
        ("assistant", "Assistente"),
    ]
    FEEDBACKS = [
        ("positive", "Positivo"),
        ("negative", "Negativo"),
    ]

    conversa             = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name="mensagens")
    role                 = models.CharField(max_length=20, choices=ROLES)
    conteudo_original    = models.TextField()           # pergunta como o usuário digitou (#36)
    conteudo_processado  = models.TextField(blank=True) # pergunta após pré-processamento (#37)
    feedback             = models.CharField(max_length=10, choices=FEEDBACKS, null=True, blank=True)
    foi_reformulada      = models.BooleanField(default=False)  # marcador de "refatoração" (regenerar resposta)
    fontes               = models.ManyToManyField(      # documentos usados na resposta RAG
                               Documento,
                               blank=True,
                               related_name="mensagens_origem",
                           )
    nota                 = models.IntegerField(null=True, blank=True, help_text="Nota de 1 a 5, ou 1 para Like e -1 para Dislike")
    comentario           = models.TextField(null=True, blank=True)
    respondida           = models.BooleanField(
        null=True, blank=True,
        help_text=(
            "Apenas para role='assistant'. True quando o modelo encontrou resposta "
            "no contexto; False quando declarou desconhecimento. NULL para mensagens "
            "do usuário ou registros antigos (pré-instrumentação)."
        ),
    )
    criada_em            = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "documents"
        ordering  = ["criada_em"]

    def __str__(self):
        return f"[{self.role}] Conversa #{self.conversa_id}"   